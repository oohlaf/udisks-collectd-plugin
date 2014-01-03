#!/usr/bin/env python
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.

__author__ = 'Olaf Conradi'
__email__ = 'olaf@conradi.org'
__copyright__ = 'Copyright 2014, Olaf Conradi'
__license__ = 'GPLv3'
__version__ = '0.1'

import dbus
import re
import time

try:
    import collectd
except ImportError:
    # Plugin called outside of Collectd
    import errno
    import logging

    logging.basicConfig(level=logging.DEBUG)
    log = logging.getLogger()

    class CollectdStub(object):
        def debug(self, msg):
            log.debug(msg)

        def info(self, msg):
            log.info(msg)

        def notice(self, msg):
            log.notice(msg)

        def warning(self, msg):
            log.warning(msg)

        def error(self, msg):
            log.error(msg)

        class Values(object):
            def __init__(self, plugin=None):
                self.plugin = plugin

            def dispatch(self):
                pass

    collectd = CollectdStub()


PLUGIN_NAME = 'udisks'
UDISKS_BUSNAME = 'org.freedesktop.UDisks2'
UDISKS_PATH = '/org/freedesktop/UDisks2'
UDISKS_DRIVE_ATA = '%s.Drive.Ata' % UDISKS_BUSNAME
DBUS_OBJMAN = 'org.freedesktop.DBus.ObjectManager'


re_drive = None
system_bus = None
udisks_manager = None


selected_drive_ids = []
ignore_selected = False


def plugin_config(conf):
    collectd.debug('Collectd plugin configuration')
    global selected_drive_ids, ignore_selected
    for node in conf.children:
        if node.key == 'DriveId':
            for v in node.values:
                if v not in selected_drive_ids:
                    selected_drive_ids.append(v)
        elif node.key == 'IgnoreSelected':
            if node.value:
                ignore_selected = True
            else:
                ignore_selected = False


def bus_init():
    global system_bus, udisks_manager
    if system_bus:
        system_bus.close()
    system_bus = dbus.SystemBus()
    udisks = system_bus.get_object(UDISKS_BUSNAME, UDISKS_PATH)
    udisks_manager = dbus.Interface(udisks, DBUS_OBJMAN)


def plugin_init():
    collectd.debug('Collectd plugin init')
    global re_drive
    re_drive = re.compile('(?P<path>.*?/drives/(?P<id>.*))')
    bus_init()


def kelvin_to_celcius(temp):
    return temp - 273.15


def dispatch_value(value, type, type_instance=None, plugin_instance=None):
    collectd.debug("Value dispatch for "
                   "plugin=%s, "
                   "plugin_instance=%s, "
                   "type=%s, "
                   "type_instance=%s, "
                   "value=%s" % (PLUGIN_NAME,
                                 plugin_instance,
                                 type,
                                 type_instance,
                                 value))
    vl = collectd.Values(plugin=PLUGIN_NAME)
    if plugin_instance is not None:
        vl.plugin_instance = plugin_instance
    vl.type = type
    if type_instance is not None:
        vl.type_instance = type_instance
    vl.values = [value]
    vl.dispatch()


def is_ata_updated(properties):
    return properties['SmartSupported'] and \
        properties['SmartEnabled'] and \
        properties['SmartUpdated']


def read_ata_temperature(properties):
    temp = properties['SmartTemperature']
    if temp > 0:
        return kelvin_to_celcius(temp)
    else:
        return 0


def read_ata_bad_sectors(properties):
    return properties['SmartNumBadSectors']


def read_ata_attributes(obj):
    """
    id (type 'y')            Attribute Identifier.
    name (type 's')          The identifier as a string.
    flags (type 'q')         16-bit attribute flags (bit 0 is prefail/oldage,
                             bit 1 is online/offline).
    value (type 'i')         The current value or -1 if unknown.
    worst (type 'i')         The worst value of -1 if unknown.
    threshold (type 'i')     The threshold or -1 if unknown.
    pretty (type 'x')        An interpretation of the value - must be ignored
                             if pretty_unit is 0.
    pretty_unit (type 'i')   The unit of the pretty value - the following
                             units are known: 0 (unknown), 1 (dimensionless),
                             2 (milliseconds), 3 (sectors), 4 (millikelvin).
    expansion (type 'a{sv}') Currently unused. Intended for future expansion.
    """
    attributes = []
    options = {'auth.no_user_interaction': True,
               'nowakeup': True}
    smart_attributes = dbus.Array(obj.SmartGetAttributes(options))
    for smart_attr in smart_attributes:
        smart_struct = dbus.Struct(smart_attr)
        attr = {}
        attr['id'] = int(dbus.Byte(smart_struct[0]))
        attr['name'] = unicode(dbus.String(smart_struct[1]))
        attr['flags'] = int(dbus.UInt16(smart_struct[2]))
        attr['value'] = int(dbus.Int32(smart_struct[3]))
        attr['worst'] = int(dbus.Int32(smart_struct[4]))
        t = attr['threshold'] = int(dbus.Int32(smart_struct[5]))
        attr['pretty_unit'] = int(dbus.Int32(smart_struct[7]))
        if 0 < attr['pretty_unit'] < 5:
            attr['pretty'] = long(dbus.Int64(smart_struct[6]))
        else:
            attr['pretty'] = None
        attributes.append(attr)
    return attributes


def plugin_read():
    retries = 0
    while retries < 5:
        try:
            objects = udisks_manager.GetManagedObjects()
        except dbus.exceptions.DBusException:
            collectd.warning('Could not connect to system dbus.')
            bus_init()
            time.sleep(retries * 0.5)
            retries += 1
        else:
            if retries > 1:
                collectd.info('Connected to system dbus '
                              'after %d retries.' % retries)
            elif retries > 0:
                collectd.info('Connected to system dbus '
                              'after %d retry.' % retries)
            drives = [m.groupdict() for m in
                      [re_drive.match(path) for path in objects.keys()]
                      if m]
            for drive in drives:
                if selected_drive_ids:
                    if ignore_selected:
                        if drive['id'] in selected_drive_ids:
                            collectd.debug("Ignore drive '%s'." % drive['id'])
                            continue
                    else:
                        if drive['id'] not in selected_drive_ids:
                            collectd.debug("Ignore drive '%s'." % drive['id'])
                            continue
                try:
                    ata_properties = objects[drive['path']][UDISKS_DRIVE_ATA]
                except KeyError:
                    collectd.debug("Drive '%s' is not ATA." % drive['id'])
                    continue
                if is_ata_updated(ata_properties):
                    temp = read_ata_temperature(ata_properties)
                    if temp:
                        dispatch_value(temp,
                                       plugin_instance=drive['id'],
                                       type='temperature')
                    bad_sect = read_ata_bad_sectors(ata_properties)
                    if bad_sect != -1:
                        dispatch_value(bad_sect,
                                       plugin_instance=drive['id'],
                                       type='counter',
                                       type_instance='bad_sectors')
                    drive_obj = system_bus.get_object(UDISKS_BUSNAME,
                                                      drive['path'])
                    drive_iface = dbus.Interface(drive_obj,
                                                 UDISKS_DRIVE_ATA)
                    attributes = read_ata_attributes(drive_iface)
                    for attr in attributes:
                        dispatch_value(attr['value'],
                                       plugin_instance=drive['id'],
                                       type='gauge',
                                       type_instance='%03d_%s_%d' % (
                                           attr['id'],
                                           attr['name'],
                                           attr['threshold']))
            return
    collectd.error('Unable to not connect to system dbus '
                   'within %d retries.' % retries)


def plugin_shutdown():
    collectd.debug('Collectd plugin shutdown')
    system_bus.close()


def main():
    plugin_init()
    try:
        while True:
            plugin_read()
            time.sleep(2)
    except KeyboardInterrupt, SystemExit:
        pass
    except IOError as e:
        # Ignore harmless broken pipe errors
        if e.errno == errno.EPIPE:
            pass
        else:
            raise
    finally:
        plugin_shutdown()


if __name__ == '__main__':
    main()
else:
    collectd.register_config(plugin_config)
    collectd.register_init(plugin_init)
    collectd.register_read(plugin_read)
    collectd.register_shutdown(plugin_shutdown)

udisks-collectd-plugin
======================

An [Udisks2](http://udisks.freedesktop.org/docs/latest/) plugin for
[Collectd](http://collectd.org) using Collectd's
[Python plugin](http://collectd.org/documentation/manpages/collectd-python.5.shtml).

The captured data includes:
 * Disk temperature
 * Bad sector count
 * Normalized [S.M.A.R.T.](http://en.wikipedia.org/wiki/S.M.A.R.T.) attributes

Install
-------

 1. Place `udisks.py` in your collectd plugins path.
 2. Configure the plugin using that location.
 3. Restart collectd.

Configuration
-------------

See the provided udisks.conf file.

    <LoadPlugin python>
        Globals true
    </LoadPlugin>

    <Plugin python>
        ModulePath "/usr/local/lib/collectd/plugins/python"
        Import "udisks"

        <Module udisks>
            #DiskId "SAMSUNG_SSD_830_Series_S0Z3NEACA05091"
            #DiskId "WDC_WD20EARX_00PASB0_WD_WCAZAF426845"
            #IgnoreSelected true
        </Module>
    </Plugin>

By default all S.M.A.R.T. enabled and updated disks are selected.
You can control the selection using option `DiskId`. Disk id's are found in
`/dev/disk/by-id/ata-{DiskId}`.

To exclude the selected drives set option `IgnoreSelected`. Default is `false`.

Requirements
------------

 * collectd
 * python
 * dbus
 * python-dbus
 * udisks2

Author
------

Olaf Conradi (olaf@conradi.org)


License
-------

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.
If not, obtain it [here](http://www.gnu.org/licenses/).

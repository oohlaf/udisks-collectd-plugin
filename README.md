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
 1. Place udisks.py in your collectd plugins path.
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
You can control the selection using option DiskId. Disk id's are found in
/dev/disk/by-id/ata-{DiskId}.

To exclude the selected drives set option IgnoreSelected. Default is false.

Requirements
------------
 * collectd
 * python
 * dbus
 * python-dbus
 * udisks2

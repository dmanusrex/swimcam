#!/usr/bin/python3

# SwimCam - https://github.com/dmanusrex/swimcam
# Copyright (C) 2020 - Darren Richer
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.


"""
Swim Cam Master Server

Master mode operation - 2 main functions

    Creates and runs the master GStreamer network clock
    
    Create an Advertisement service allong remotes to find the master server on a separate thread
    
    FUTURE:
    Listens for element configuration requests.
    	For configuration request
    	    Retrieve the configuration
    	    If none exists, create a blank entry and use defaults
    	    Send the configuration to the remote device
   
    This is quite lazy in its approach but it works for testing!
 	        
"""

import argparse

from threading import Thread
import gi
gi.require_version('Gst', '1.0')
gi.require_version('GstNet', '1.0')
from gi.repository import Gst, GstNet, GObject, GLib

from SwimCamMasterAdvertisementService import SwimCamMasterAdvertisementService

mainloop = 0
master = 0
myserver = 0

def exit_master():
    global mainloop, master 
    print("Cleaning Up master")
    master.stop()
    mainloop.quit()


def main():
    global mainloop, master, NetTimeProvider
    Gst.init(None)
    # Start serving the master clock
    sysClock = Gst.SystemClock.obtain()
    sysClock.set_property('clock-type',Gst.ClockType.REALTIME)
    NetTimeProvider = GstNet.NetTimeProvider.new(sysClock,None,9998)
    # Start the master advertisement
    master = SwimCamMasterAdvertisementService('0.0.0.0',54545)
    master.daemon = True
    master.start()
    print("Threads started...")

if __name__ == '__main__':
    mainloop = GLib.MainLoop()

    try:
        main()
        mainloop.run()
    except KeyboardInterrupt:
        exit_master()

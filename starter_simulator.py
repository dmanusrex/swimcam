#!/usr/bin/python3
#
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


#
# Starter Simulator
#
# Accept keyboard commands to simulate starting events
# and push them to the message bus
#
# TODO: Add start list event simulator
#

import paho.mqtt.client as mqtt
import sys
import curses
import os
import gi
import time
from datetime import datetime
gi.require_version('Gst', '1.0')
gi.require_version('GstBase', '1.0')
from gi.repository import GObject, Gst, GstBase, GLib
from Util import Util


def main(win):
    global masterClock
    currentRace = 0
 
    _core = Util.wait_for_core()
    _coreHost, _corePort = _core
 
    masterClock = Util.get_core_clock(_coreHost)


    _connection = mqtt.Client("swimcam-starter-simulator")
    _connection.username_pw_set(username="swimcam", password="swimming")
    _connection.connect(_coreHost)
    _connection.loop_start()
    
    win.nodelay(False)
    key=""
    win.scrollok(True)
    win.idlok(True)
    win.leaveok(True)
    win.clear()
    win.addstr("Starter Simulator\n\n")
    win.addstr("Press (s)tart or (r)eset, <Enter> to exit simulator\n\n")
    while 1:
        try:
            key = win.getkey()
            if key == 's':
                currenttime = Gst.Clock.get_time(masterClock)
                currentRace += 1
                ct_datetime = datetime.fromtimestamp(currenttime / Gst.SECOND)
                ct_datetime_text = ct_datetime.strftime('%Y-%m-%d %H:%M:%S.%f%z')
                message = 'START|'+str(currenttime)+'|Race #'+str(currentRace)
                win.addstr(" [x] CLOCK TIME: %r\n" % ct_datetime_text)
                _ret = _connection.publish("swimcam/start", message,retain=True)
                win.addstr(" [x] START MESSAGE %r\n" % message)
                win.addstr(" [x] MQTT Message ID: %r\n" % _ret.mid)
            if key == 'r':
                message = "RESET"
                _ret = _connection.publish("swimcam/start", message,retain=True)
                win.addstr(" [x] RESET SENT\n")
                win.addstr(" [x] MQTT Message ID: %r\n" % _ret.mid)
            if key == os.linesep:
                _connection.disconnect()
                break
        except Exception as e:
            # no input
            pass

    _connection.loop_stop()
Gst.init(None)
curses.wrapper(main)


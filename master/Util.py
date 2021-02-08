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

import socket
import gi
gi.require_version('Gst','1.0')
gi.require_version('GstNet','1.0')
from gi.repository import Gst, GstNet
import functools
import time

   
class Util:
    def get_core_clock(core_ip="localhost", core_clock_port=9998):
        clock = GstNet.NetClientClock.new('swimcam',core_ip, core_clock_port,0)
        clock.wait_for_sync(Gst.CLOCK_TIME_NONE)
        return clock
        
    def wait_for_core():
        _socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        _socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        _socket.bind(('', 54545))
        while True:
            data, addr = _socket.recvfrom(2048)
            break
        _socket.close()
        return addr
                 


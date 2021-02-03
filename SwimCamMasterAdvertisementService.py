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
# Master server advertisement.  
# 
# Push a "hello" packet every 5 seconds to allow the network to auto-configure
#
# Runs as a separate thread
#

from threading import Thread
import socket
import time

class SwimCamMasterAdvertisementService(Thread):
    _should_continue = 1 

    def __init__(self,listen_address,port):
        Thread.__init__(self)
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.socket.bind((listen_address,54545))

    def run(self):
        while self._should_continue:
            self.socket.sendto(bytes("Hello",'UTF-8'), ('<broadcast>', 54545))
            time.sleep(5)

    def stop(self):
        self.socket.close()
        self._should_continue = 0 



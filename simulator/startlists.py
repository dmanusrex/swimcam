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

"""
Define the classes that provide start list data

Based heavily on :
   Wahoo! Results - https://github.com/JohnStrunk/wahoo-results
   Copyright (C) 2020 - John D. Strunk

Uses Colorado Timing Systems(CTS) start list file format (.scb). Each Event (File)
contains a number of heats. Each heat in the file always has 10 lanes.

Tests:  startlist_test.py

"""


import re
from typing import List

class FileParseError(Exception):
    """Execption for when a file cannot be parsed."""
    def __init__(self, filename: str, error: str):
        """Create an exception."""
        self.filename = filename
        self.error = error
        super().__init__(self, filename, error)

class Lane:
    """
    Lane is the start list information for a single lane.
    """
    name: str  # Swimmer's name
    team: str  # Swimmer's team

    def __init__(self, **kwargs):
        self.name = kwargs.get("name", "")
        self.team = kwargs.get("team", "")

    def is_empty(self) -> bool:
        """
        Returns True if the lane is believed to be empty.

        >>> Lane().is_empty()
        True
        >>> Lane(name="One, Some").is_empty()
        False
        """
        return self.name == ""

    def dump(self):
        """
        Dumps the lane data to the screen.
        """
        print(f"Name: {self.name}")
        print(f"Team: {self.team}")
        print(f"Empty: {self.is_empty()}")


class Heat:
    """
    Heat Represents the Start List for a given heat
    """
    event: str  # Event number
    event_desc: str # Event description
    heat: int  # Heat number
    lanes: List[Lane]  # Lane information

    def __init__(self, **kwargs):
        self.event = kwargs.get("event", "")
        self.event_desc = kwargs.get("event_desc", "")
        self.heat = kwargs.get("heat", 0)
        self.lanes = kwargs.get("lanes", [
            Lane() for i in range(0, 10)])

    def parse_scb(self, lines) -> None:
        """Extract the specified heat from the startlist"""
        # Ensure file has the expected # of lines
        if (len(lines)-1) % 10 or len(lines) <= self.heat * 10:
            raise FileParseError("", "Unexpected number of lines in file")
        # Extract event name
        match = re.match(r'^#\w+\s+(.*)$', lines[0])
        if not match:
            raise FileParseError("", "Unable to parse event name")
        self.event_desc = match.group(1)
        # Parse heat names/teams
        heat_start = (self.heat - 1) * 10 + 1
        for i in range(0, 10):
            match = re.match(r'^(.*)--(.*)$', lines[heat_start + i])
            if not match:
                raise FileParseError("", "Unable to parse name/team")
            self.lanes[i].name = match.group(1).strip()
            self.lanes[i].team = match.group(2).strip()

    def dump(self):
        """Dump the results to the screen."""
        print(f"Heat: {self.heat}")
        for i in self.lanes:
            laneno = self.lanes.index(i) + 1
            print(f"Lane: {laneno}")
            i.dump()

class Event:
    """
    Event represents a swimming event.

    Usage:
        # Create an Event object
        ev = Event()
        # Load the scoreboard data
        ev.from_scb("E129.scb")
    """
    event: str             # Event Number
    event_desc: str        # Event Description
    num_heats: int         # Number of Heats
    heats: List[Heat]  # List of Heats for Event

    def __init__(self, **kwargs):
        self.event = kwargs.get("event", "")
        self.event_desc = kwargs.get("event_desc", "")
        self.num_heats = kwargs.get("num_heats", 0)
        self.heats = []

    def from_scb(self, filename: str) -> None:
        """
        Loads event and heat data from a CTS start list *.scb file.
        """
        file = open(filename, "r")
        lines = file.readlines()
        file.close()
        try:
            self.from_lines(lines)
        except FileParseError as err:
            raise FileParseError(filename, err.error) from err

    def from_lines(self, lines: List[str]) -> None:
        '''Parse event information'''
        match = re.match(r"^#(\w+)\s+(.*)$", lines[0])
        if not match:
            raise FileParseError("", "Unable to parse header")
        self.event = match.group(1)
        self.event_desc = match.group(2)
        self.num_heats = (len(lines)-1)//10
        for heatnum in range(1, self.num_heats+1):
            heat = Heat(event=self.event, heat=heatnum)
            heat.parse_scb(lines)
            self.heats.append(heat)

    def dump(self):
        """Dump the results to the screen."""
        print(f"Event: {self.event}")
        print(f"Event desc: {self.event_desc}")
        print(f"# of Heats: {self.num_heats}")
        for i in self.heats:
            i.dump()

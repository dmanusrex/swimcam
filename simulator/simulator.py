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


'''SwimCam Starter Simulator'''

import os
import sys
import time

from tkinter import Tk
from typing import List
from PIL import Image, UnidentifiedImageError  #type: ignore
from PIL.ImageEnhance import Brightness  #type: ignore

import swimcamutil
import startlists
import settings
from config import StarterConfig
from startlist_display import Scoreboard, Starter

import gi
gi.require_version('Gst', '1.0')
gi.require_version('GstBase', '1.0')
from gi.repository import GObject, Gst, GstBase, GLib


def load_cts_startlists(directory: str) -> List[startlists.Event]:
    """
    Load and pre-process all of the CTS formatted start lists
    """
    files = os.scandir(directory)
    events = []
    for file in files:
        if file.name.endswith(".scb"):
            event = startlists.Event()
            event.from_scb(file.path)
            events.append(event)
    events.sort(key=lambda e: e.event)
    return events

def settings_window(root: Tk, options: StarterConfig) -> None:
    '''Display the settings window'''

    # Settings window is fixed size
    root.state("normal")
    root.overrideredirect(False)  # show titlebar
    root.resizable(False, False)
    root.geometry("")  # allow automatic size

    def sb_run_cb():
        event_list = load_cts_startlists(options.get_str("start_list_dir"))
        board = starter_window(root, options, event_list)


    def sb_test_cb():
        board = starter_window(root, options)
        #_set_test_data(board)

    # Invisible container that holds all content
    content = settings.Settings(root, sb_run_cb, sb_test_cb, options)
    content.grid(column=0, row=0, sticky="news")

def starter_window(root: Tk, options: StarterConfig, 
                   events: List[startlists.Event]) -> Starter:
    """Displays the starter simulator window."""

    if options.get_bool("fullscreen"):
        root.resizable(False, False)
        root.overrideredirect(True)  # hide titlebar
        root.attributes('-zoomed', True) # on Linux only root.state("zoomed") on windows/macos
    else:
        # Simulator is varible size
        root.resizable(True, True)
    content = Starter(root, options, events)
    content.grid(column=0, row=0, sticky="news")
    if options.get_str("image_bg") != "":
        try:
            image = Image.open(options.get_str("image_bg"))
            content.bg_image(Brightness(image).enhance(options.get_float("image_bright")),
                            options.get_str("image_scale"))
        except FileNotFoundError:
            pass
        except UnidentifiedImageError:
            pass

    def return_to_settings(_) -> None:
        root.unbind('<Double-1>')
        content.destroy()
        root.state('normal') # Un-maximize
        settings_window(root, options)
    root.bind('<Double-1>', return_to_settings)
    return content

def display(board: Scoreboard, heat: startlists.Heat) -> None:
    """
    Display a startlist.
    """
    board.clear()
    board.event(heat.event, heat.event_desc)
    board.heat(heat.heat)

    for i in range(0, 10):
        if not heat.lanes[i].is_empty():
            board.lane(i+1, heat.lanes[i].name, heat.lanes[i].team)
    # heat.dump()

def _set_test_data(board: Scoreboard):
    board.clear()
    board.event(432, "GIRLS 13&O 1650 FREE")
    board.heat(56)
    # Names from https://www.name-generator.org.uk/
    board.lane(1, "MILLER, STEPHANIE", "TEAM1")
    board.lane(2, "DAVIS, SARAH", "TEAM1")
    board.lane(3, "GARCIA, ASHLEY", "TEAM1")
    board.lane(4, "WILSON, JESSICA", "TEAM1")
    board.lane(5, "", "")
    board.lane(6, "MOORE, SAMANTHA", "TEAM1")
    board.lane(7, "JACKSON, AMBER", "TEAM1")
    board.lane(8, "TAYLOR, MELISSA", "TEAM1")
    board.lane(9, "ANDERSON, RACHEL", "TEAM1")
    board.lane(10, "WHITE, MEGAN", "TEAM1")

def main():
    '''Runs the Starter Simulator'''

    print("Waiting for core...")
    _core = swimcamutil.wait_for_core()
    _coreHost, _corePort = _core
    print("Core aquired (", _coreHost, ")")

#    Gst.init(None)
    root = Tk()

    config = StarterConfig()
    config.set_str("core_host", _coreHost)

    screen_size = f"{root.winfo_screenwidth()}x{root.winfo_screenheight()}"

    root.title("SwimCam Starter Simulator")
    root.columnconfigure(0, weight=1)
    root.rowconfigure(0, weight=1)

    settings_window(root, config)
    root.mainloop()

    config.save()

if __name__ == "__main__":
    main()


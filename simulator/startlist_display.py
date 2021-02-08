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

'''
TKinter code to display the start list

This file can be directly executed to display a mockup.


Based on orignal work by :
   Wahoo! Results - https://github.com/JohnStrunk/wahoo-results
   Copyright (C) 2020 - John D. Strunk
'''

import logging
import tkinter as tk
from tkinter import ttk, BooleanVar, StringVar
import tkinter.scrolledtext as ScrolledText
import tkinter.font as tkfont
from typing import Any, Dict, Union, Callable
import ttkwidgets  #type: ignore
import ttkwidgets.font  #type: ignore

from PIL import Image, ImageTk  #type: ignore
from PIL.ImageEnhance import Brightness  #type: ignore

from bounded_text import BoundedText
from config import StarterConfig
from tooltip import ToolTip
from color_button import ColorButton
from version import SWIMCAM_VERSION
from typing import List
import startlists
import paho.mqtt.client as mqtt
import gi
gi.require_version('Gst', '1.0')
gi.require_version('GstBase', '1.0')
from gi.repository import GObject, Gst, GstBase, GLib
from swimcamutil import get_core_clock
from datetime import datetime

TkContainer = Any

# Callbacks - XXXX
#CSVGenFn = Callable[[str, str], int]
NoneFn = Callable[[], None]

class TextHandler(logging.Handler):
    # This class allows you to log to a Tkinter Text or ScrolledText widget
    # Adapted from Moshe Kaplan: https://gist.github.com/moshekaplan/c425f861de7bbf28ef06

    def __init__(self, text):
        # run the regular Handler __init__
        logging.Handler.__init__(self)
        # Store a reference to the Text it will log to
        self.text = text

    def emit(self, record):
        msg = self.format(record)
        def append():
            self.text.configure(state='normal')
            self.text.insert(tk.END, msg + '\n')
            self.text.configure(state='disabled')
            # Autoscroll to the bottom
            self.text.yview(tk.END)
        # This is necessary because we can't modify the Text from other threads
        self.text.after(0, append)

#pylint: disable=too-many-ancestors,too-many-instance-attributes
class Scoreboard(tk.Canvas):
    '''
    Tkinter object that displays the Wahoo Results scoreboard

    Parameters:
        container: The parent Tk object for this widget
        kwargs: Parameters to pass to the underlying canvas widget
    '''

    # Background for the scoreboard
    _bg_image: Image = None
    _bg_image_fill: str
    _bg_image_pimage: ImageTk.PhotoImage
    # Maximum number of lanes supported
    _max_lanes = 10
    # Number of lanes that will be shown
    _num_lanes: int
    _event_num: Union[int, str] = ""
    _event_description: str = ""
    _heat_num: int = 0
    _text_items: Dict[str, BoundedText]
    _border_pct = 0.05
    _header_gap_pct = 0.05
    _font: tkfont.Font
    _font_times: tkfont.Font
    _line_height: int

    def __init__(self, container: TkContainer, config: StarterConfig, **kwargs):
        super().__init__(container, kwargs)
        self._config = config
        self.create_image(0, 0, image=None, tag="bg_image")
        self._font = tkfont.Font()
        self._font_times = tkfont.Font()
        self._text_items = {}
        for i in ["event_heat", "event_desc"]:
            self._text_items[i] = BoundedText(self, 0, 0, fill=self._config.get_str("color_ehd"),
                                              width=1, tags="normal_font")
        for i in ["hdr_lane", "hdr_name", "hdr_time"]:
            self._text_items[i] = BoundedText(self, 0, 0, fill=self._config.get_str("color_fg"),
                                              width=1, tags="normal_font")
        self.create_line(0, 0, 0, 0, tags="header_line")
        self.bind("<Configure>", self._reconfigure)
        self.set_lanes(self._config.get_int("num_lanes"))
        self._reconfigure(None)
        self.clear()

    def clear(self):
        '''Clear the scoreboard'''
        for i in range(self._max_lanes):
            self._text_items[f"lane_{i}_name"].text = ""
            self._text_items[f"lane_{i}_team"].text = ""
        self.event("1", "")
        self.heat(1)

    def event(self, event_num: Union[int, str], event_description: str):
        '''
        Set the event number and description

        Parameters:
            event_num: The event number
            event_description: The text description of the event
        '''
        self._event_num = event_num
        self._event_description = event_description
        self._text_items["event_heat"].text = f"E: {self._event_num} / H: {self._heat_num}"
        self._text_items["event_desc"].text = self._event_description

    def heat(self, heat_num: int):
        '''
        Set the heat number

        Parameters:
            heat_num: The number of the current heat
        '''
        self._heat_num = heat_num
        self._text_items["event_heat"].text = f"E: {self._event_num} / H: {self._heat_num}"

    #pylint: disable=unused-argument,too-many-arguments
    def lane(self, lane_num: int, name: str = "", team: str = ""):
        '''
        Update the data for a lane

        Parameters:
            lane_num: The lane to update
            name: The name of the swimmer
            team: The swimmer's team
        '''
        self._text_items[f"lane_{lane_num-1}_name"].text = name
        self._text_items[f"lane_{lane_num-1}_team"].text = team

    def set_lanes(self, lanes: int):
        '''
        Configure the number of lanes displayed on the scoreboard

        Parameters:
            lanes: The number of lanes to display
        '''
        self._num_lanes = min(lanes, self._max_lanes)

    def bg_image(self, image: Image, fill: str = "fit"):
        '''
        Set a background image for the scoreboard

        Parameters:
            image: The image to display
            fill: A string indicating how to format the image
                "none": Use the image as-is
                "stretch": Stretch the image to fill the entire scoreboard
                "fit": Uniformly scale to fit it on the scoreboard
                "cover": Uniformly scale to fully cover the scoreboard
        '''
        self._bg_image = image
        self._bg_image_fill = fill

    def _reconfigure(self, event):
        self.update()
        self._draw_bg(event)
        self._update_font()
        self._draw_header()
        self._draw_lanes()
        self._update_font()

    def _update_font(self):
        line_height = int(self.winfo_height() *
                          (1 - 2*self._border_pct - self._header_gap_pct) /
                          (self._num_lanes + 2))
        font_size = int(-self._config.get_float("font_scale") * line_height)
        self._font = tkfont.Font(family=self._config.get_str("normal_font"),
                                 weight="bold", size=font_size)
        self._font_times = self._font
        self._line_height = line_height
        for i in self._text_items.values():
            i.font = self._font

    def _draw_header(self):
        lpos = int(self.winfo_width() * self._border_pct)
        rpos = int(self.winfo_width() * (1-self._border_pct))
        width = rpos - lpos
        eh_width = self._font.measure("E: MMM / H: MM")
        desc_width = width - eh_width
        vpos = int(self.winfo_height() * self._border_pct + self._line_height)
        self._text_items["event_heat"].configure(anchor="sw")
        self._text_items["event_heat"].move_to(lpos, vpos)
        self._text_items["event_heat"].width = eh_width
        self._text_items["event_desc"].configure(anchor="se")
        self._text_items["event_desc"].move_to(rpos, vpos)
        self._text_items["event_desc"].width = desc_width

    def _draw_lanes(self): #pylint: disable=too-many-statements
        lpos = int(self.winfo_width() * self._border_pct)
        rpos = int(self.winfo_width() * (1-self._border_pct))
        width = rpos - lpos
        time_width = int(self._font_times.measure("00:00.00") * 1.2)
        idx_width = self._font.measure("Lane")
        pl_width = self._font.measure("MMM")
        name_width = width - time_width - idx_width - pl_width
        lane_top = int(self.winfo_height() * (self._border_pct + self._header_gap_pct) +
                       2 * self._line_height)
        self._text_items["hdr_lane"].configure(anchor="s")
        self._text_items["hdr_lane"].move_to(lpos + idx_width/3, lane_top)
        self._text_items["hdr_lane"].width = idx_width
        self._text_items["hdr_lane"].text = "Lane"
        self._text_items["hdr_name"].configure(anchor="sw")
        self._text_items["hdr_name"].move_to(lpos + idx_width + pl_width, lane_top)
        self._text_items["hdr_name"].width = name_width
        self._text_items["hdr_name"].text = "Name"
        self._text_items["hdr_time"].configure(anchor="se")
        self._text_items["hdr_time"].move_to(rpos, lane_top)
        self._text_items["hdr_time"].width = time_width
        self._text_items["hdr_time"].text = "Team"
        self.itemconfigure("header_line", width=int(0.05 * self._line_height),
                           capstyle="round", fill="white")
        (hlx1, _, _, _) = self.bbox(self._text_items["hdr_lane"].id)
        (_, _, hlx2, _) = self.bbox(self._text_items["hdr_time"].id)
        self.coords("header_line", hlx1, lane_top, hlx2, lane_top)
        for i in range(self._max_lanes):
            # Lane number
            txt = self._text_items.setdefault(f"lane_{i}_idx",
                BoundedText(self, 0, 0, fill=self._config.get_str("color_fg"),
                            width=1, tags="normal_font"))
            txt.configure(anchor="s")
            txt.move_to(lpos + idx_width/3, lane_top + (i+1) * self._line_height)
            txt.width = idx_width
            if i < self._num_lanes:
                txt.text = f"{i+1}"
            else:
                txt.text = ""
            # Name
            txt = self._text_items.setdefault(f"lane_{i}_name",
                BoundedText(self, 0, 0, fill=self._config.get_str("color_fg"),
                            width=1, tags="normal_font"))
            txt.configure(anchor="sw")
            txt.move_to(lpos + idx_width + pl_width, lane_top + (i+1) * self._line_height)
            txt.width = name_width
            if i >= self._num_lanes:
                txt.text = ""
            # Team
            txt = self._text_items.setdefault(f"lane_{i}_team",
                BoundedText(self, 0, 0, fill=self._config.get_str("color_fg"),
                            width=1, tags="normal_font"))
            txt.configure(anchor="se")
            txt.move_to(rpos, lane_top + (i+1) * self._line_height)
            txt.width = time_width
            if i >= self._num_lanes:
                txt.text = ""

    def _draw_bg(self, _):
        self.configure(bg=self._config.get_str("color_bg"))
        if self._bg_image is not None:
            i_size = self._bg_image.size
            c_size = (self.winfo_width(), self.winfo_height())
            if self._bg_image_fill == "stretch":
                scaled = self._bg_image.resize(c_size)
            elif self._bg_image_fill == "fit":
                factor = min(c_size[0]/i_size[0], c_size[1]/i_size[1])
                scaled = self._bg_image.resize((int(i_size[0]*factor), int(i_size[1]*factor)))
            elif self._bg_image_fill == "cover":
                factor = max(c_size[0]/i_size[0], c_size[1]/i_size[1])
                scaled = self._bg_image.resize((int(i_size[0]*factor), int(i_size[1]*factor)))
            else:
                scaled = self._bg_image
            self._bg_image_pimage = ImageTk.PhotoImage(scaled)
            self.coords("bg_image", c_size[0]//2, c_size[1]//2)
            self.itemconfigure("bg_image", image=self._bg_image_pimage)

class Starter(ttk.Frame):  # pylint: disable=too-many-ancestors
    '''Starter Simulator window'''

    startlist: Scoreboard
    _events: List[startlists.Event]
    _event_index: int
    _heat_index: int
    _current_ehl_text: str
    _config: StarterConfig
#   Add other variables... _connection:, _masterclock, etc. 

    # pylint: disable=too-many-arguments,too-many-locals
    def __init__(self, container: TkContainer, config: StarterConfig,
                 event_list: List[startlists.Event], **kwargs):
        super().__init__(container, padding=5)
        self._config = config
        self._events = event_list
        self._event_index = 0
        self._heat_index = 0
        self.grid(column=0, row=0, sticky="news")
        self.columnconfigure(0, weight=1)
        # Odd rows are empty filler to distribute vertical whitespace
        for i in [1, 3, 5, 7]:
            self.rowconfigure(i, weight=1)
        # row 0: Starter Control Buttons
        fr0 = ttk.Frame(self)
        fr0.grid(column=0, row=0, sticky="news")
        fr0.rowconfigure(0, weight=1)
        fr0.rowconfigure(1, weight=1)
        fr0.columnconfigure(0, weight=1)
        fr0.columnconfigure(1, weight=1)
        fr0.columnconfigure(2, weight=1)
        fr0.columnconfigure(3, weight=1)
        fr0.columnconfigure(4, weight=1)
        prev_event_btn = ttk.Button(fr0, text="<- Event", command=self._handle_prev_event_btn)
        prev_event_btn.grid(column=0, row=0, sticky="news")
        ToolTip(prev_event_btn, text="Previous Event")
        prev_heat_btn = ttk.Button(fr0, text="<- Heat", command=self._handle_prev_heat_btn)
        prev_heat_btn.grid(column=0, row=1, sticky="news")
        ToolTip(prev_heat_btn, text="Previous Heat")

        start_btn = ttk.Button(fr0, text="Start", command=self._handle_start_btn)
        start_btn.grid(column=2, row=0, sticky="news")
        ToolTip(start_btn, text="Send a simulated start signal")
        reset_btn = ttk.Button(fr0, text="Reset", command=self._handle_reset_btn)
        reset_btn.grid(column=2, row=1, sticky="news")
        ToolTip(reset_btn, text="Send a reset signal to the cameras")

        next_event_btn = ttk.Button(fr0, text="Event ->", command=self._handle_next_event_btn)
        next_event_btn.grid(column=4, row=0, sticky="news")
        ToolTip(prev_event_btn, text="Next Event")
        next_heat_btn = ttk.Button(fr0, text="Heat ->", command=self._handle_next_heat_btn)
        next_heat_btn.grid(column=4, row=1, sticky="news")
        ToolTip(prev_heat_btn, text="Next Heat")

        # row 2: Current Startlist
        self.startlist = Scoreboard(self, self._config)
        self.startlist.grid(column=0, row=2, sticky="news")

        # row 4: Logging Window
        self.rowconfigure(4, weight=1)
        logwin = ScrolledText.ScrolledText(self, state='disabled')
        logwin.configure(font='TkFixedFont')
        logwin.grid(column=0, row=4, sticky='news')
        # Logging configuration
        logging.basicConfig(filename='test.log',
                            level=logging.INFO,
                            format='%(asctime)s - %(levelname)s - %(message)s')
        # Create textLogger
        text_handler = TextHandler(logwin)
        text_handler.setFormatter(logging.Formatter('%(asctime)s - %(message)s'))
        # Add the handler to logger
        logger = logging.getLogger()
        logger.addHandler(text_handler)

        # row 6: info panel
        fr6 = ttk.Frame(self)
        fr6.grid(column=0, row=6, sticky="news")
        fr6.rowconfigure(0, weight=1)
        fr6.columnconfigure(0, weight=1)
        fr6.columnconfigure(1, weight=0)
        link_label = ttkwidgets.LinkLabel(fr6,
            text="Documentation: https://XXXXXX.readthedocs.io/",
            link="https://XXXX.readthedocs.io/?utm_source=wahoo_results&"
                 "utm_medium=config_screen&utm_campaign=docs_link",
            relief="sunken",
            padding=[5, 2])
        link_label.grid(column=0, row=0, sticky="news")
        version_label = ttk.Label(fr6, text=SWIMCAM_VERSION, justify="right",
                                  padding=2, relief="sunken")
        version_label.grid(column=1, row=0, sticky="nes")

        logging.info("Starter simulator initializing")

        # Start MQTT

        self._connection = mqtt.Client("swimcam-starter-simulator")
        self._connection.username_pw_set(username="swimcam", password="swimming")
        self._connection.connect(self._config.get_str("core_host"))
        self._connection.loop_start()
        logging.info("MQTT Started")

        # Get Network Clock

        self._masterClock = get_core_clock(self._config.get_str("core_host"))
        logging.info("Synchronized to network clock")

        # Display
        self._set_ehl_data()

    def _set_ehl_data(self) -> None:
        """Update the display and set the message structure element"""
        working = self._events[self._event_index].heats[self._heat_index]
        self.startlist.clear()
        self.startlist.event(working.event, working.event_desc)
        self.startlist.heat(working.heat)
        self._current_ehl_text=f"|Event: {working.event} Heat: {working.heat} {working.event_desc}|"
        for i in range(0, 10):
            if not working.lanes[i].is_empty():
                self.startlist.lane(i+1, working.lanes[i].name, working.lanes[i].team)
                self._current_ehl_text += f"{working.lanes[i].name} ({working.lanes[i].team})|"
            else:
                self._current_ehl_text += " |"

    def _handle_start_btn(self) -> None:
        _currenttime = Gst.Clock.get_time(self._masterClock)
        _ct_datetime = datetime.fromtimestamp(_currenttime / Gst.SECOND)
        _ct_datetime_text = _ct_datetime.strftime('%Y-%m-%d %H:%M:%S.%f%z')
        _message = 'START|'+str(_currenttime)+self._current_ehl_text
        logging.info("CAPTURED START TIME: %r" % _ct_datetime_text)
        _ret = self._connection.publish("swimcam/start", _message,retain=True)
        logging.info("START MESSAGE %r" % _message)
        logging.info("MQTT Message ID: %r" % _ret.mid)


    def _handle_reset_btn(self) -> None:
        _ret = self._connection.publish("swimcam/start", "RESET",retain=True)
        logging.info("RESET SENT")
        logging.info("MQTT Message ID: %r" % _ret.mid)

    def _handle_prev_event_btn(self) -> None:
        if self._event_index == 0:
           self._event_index = len(self._events) - 1
           self._heat_index = 0
        else:
           self._event_index -= 1
           self._heat_index = 0
        self._set_ehl_data()

    def _handle_prev_heat_btn(self) -> None:
        if (self._heat_index == 0):
           self._handle_prev_event_btn()
        else:
           self._heat_index -= 1
           self._set_ehl_data()

    def _handle_next_event_btn(self) -> None:
        self._event_index = (self._event_index + 1) % len(self._events)
        self._heat_index = 0
        self._set_ehl_data()

    def _handle_next_heat_btn(self) -> None:
        self._heat_index += 1
        if (self._heat_index % len(self._events[self._event_index].heats) == 0):
           self._handle_next_event_btn()
        else:
           self._set_ehl_data()

def show_mockup(board: Scoreboard):
    '''
    Displays fake data on the scoreboard for testing and demonstration
    purposes
    '''
#    image = Image.open('rsa2.png')
#    board.bg_image(Brightness(image).enhance(0.2), "fit")
    board.set_lanes(6)
    board.event(725, "GIRLS 12 & UNDER 100 BACK")
    board.heat(42)
    board.lane(1, "SWIMMER, FIRST", "TEAM1")
    board.lane(2, "SWIMMER, ANOTHER", "TEAM2")
    board.lane(3, "REALLYREALLYLONGNAME, IMA", "TEAM2")
    board.lane(4, "TIME, INCONSISTENT", "TEAM2")
    board.lane(5, "SWIM, NO", "NOTEAM")
    board.lane(6, "SWIMMER, THELAST", "TEAM1")

def main():
    '''Display a scoreboard mockup'''
    root = tk.Tk()
    root.geometry("800x600")
    board = Starter(root, StarterConfig())
    board.pack(fill='both', expand='yes')
    show_mockup(board.startlist)
    logging.info("Hello World")
    root.mainloop()

if __name__ == '__main__':
    main()

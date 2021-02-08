# Wahoo! Results - https://github.com/JohnStrunk/wahoo-results
# Copyright (C) 2020 - John D. Strunk
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

'''Wahoo! Results settings screen'''

import os
import tkinter as tk
from tkinter import filedialog, ttk, BooleanVar, StringVar
from typing import Any, Callable
import ttkwidgets  #type: ignore
import ttkwidgets.font  #type: ignore

from config import StarterConfig
from tooltip import ToolTip
from color_button import ColorButton
from version import SWIMCAM_VERSION

tkContainer = Any

# Dolphin CSV generator callback
# num_events = CSVGenFn(outfile, dir_to_process)
CSVGenFn = Callable[[str, str], int]
NoneFn = Callable[[], None]

class _StartList(ttk.LabelFrame):   # pylint: disable=too-many-ancestors
    '''The "start list" portion of the settings'''
    def __init__(self, container: tkContainer, config: StarterConfig):
        super().__init__(container, padding=5, text="CTS Start list configuration")
        self._config = config
        self._scb_directory = StringVar(value=self._config.get_str("start_list_dir"))
        self._starter_status = StringVar(value="")
         # self is a vertical container
        self.columnconfigure(0, weight=1)
        # row 0: label
        lbl1 = ttk.Label(self, text="Directory for CTS Start List files:")
        lbl1.grid(column=0, row=0, sticky="ws")
        # row 1: browse button & current directory
        # fr1 is horizontal
        fr1 = ttk.Frame(self)
        fr1.grid(column=0, row=1, sticky="news")
        fr1.rowconfigure(0, weight=1)
        scb_dir_label = ttk.Label(fr1, textvariable=self._scb_directory)
        scb_dir_label.grid(column=1, row=0, sticky="ew")
        btn1 = ttk.Button(fr1, text="Browse", command=self._handle_scb_browse)
        btn1.grid(column=0, row=0)
        ToolTip(btn1, text="Select the directory containing start list files "
                "that have been exported from Meet Manager")   # pylint: disable=C0330
        # row 2: status line
        lbl2 = ttk.Label(self, textvariable=self._starter_status, borderwidth=2,
                         relief="sunken", padding=2)
        lbl2.grid(column=0, row=3, sticky="news")


    def _handle_scb_browse(self) -> None:
        directory = filedialog.askdirectory()
        if len(directory) == 0:
            return
        directory = os.path.normpath(directory)
        self._config.set_str("start_list_dir", directory)
        self._scb_directory.set(directory)
#        self._csv_status.set("") # clear status line if we change directory

class _GeneralSettings(ttk.LabelFrame):  # pylint: disable=too-many-ancestors,too-many-instance-attributes
    '''Miscellaneous settings'''
    def __init__(self, container: tkContainer, config: StarterConfig):
        super().__init__(container, text="General Settings", padding=5)
        self._config = config
        self.columnconfigure(0, weight=1)
        self.columnconfigure(1, weight=1)
        self.columnconfigure(2, weight=1)
        self.rowconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)
        self.rowconfigure(2, weight=1)
        self.rowconfigure(3, weight=1)
        self.rowconfigure(4, weight=1)
        self.rowconfigure(5, weight=1)

        # Row 0 - # of lanes, fullscreen, FG Colour

        self._lanes().grid(column=0, row=0, sticky="es")
        self._lane10is0().grid(column=1, row=0, sticky="es")
        self._color_swatch("Text color:", "color_fg",
                           "Display foreground text color").grid(column=2, row=0, sticky="es")
        # Row 1 - Lane 10 is zero, GPIO PIN, BG Colour
        self._gpio().grid(column=0, row=1, sticky="es")
        self._fullscreen().grid(column=1, row=1, sticky="es")
        self._color_swatch("Background:", "color_bg",
                           "Display background color").grid(column=2, row=1, sticky="es")
        # Row 2 - Future, Future, Text Colour
        self._color_swatch("Title color:", "color_ehd", "Starter event, heat, "
            "and description text color").grid(column=2, row=2, sticky="es")   # pylint: disable=C0330
        # Row 3 - Background Image
        self._bg_img().grid(column=0, row=3, columnspan=3, sticky="news")
        # Row 4 - Brightness, scaling
        self._bg_brightness().grid(column=0, row=4, columnspan=2, sticky="ws")
        self._bg_scale().grid(column=2, row=4, sticky="news")
        # Row 5 - Font
        self._font_chooser("Normal font:", "normal_font",
            "Font for the display text").grid(column=0, row=5, # pylint: disable=C0330
                                              columnspan=2, sticky="news")
        self._font_scale().grid(column=2, row=5, sticky="es")


    def _color_swatch(self, label_text: str, config_item: str, tip_text: str = "") -> ttk.Widget:
        frame = ttk.Frame(self, padding=1)
        frame.rowconfigure(0, weight=1)
        frame.columnconfigure(0, weight=1)
        ttk.Label(frame, text=label_text).grid(column=0, row=0, sticky="news")
        ColorButton(frame, self._config, config_item).grid(column=1, row=0, sticky="news")
        if tip_text != "":
            ToolTip(frame, tip_text)
        return frame

    def _bg_img(self) -> ttk.Widget:
        frame = ttk.Frame(self, padding=1)
        frame.rowconfigure(0, weight=1)
        frame.columnconfigure(1, weight=1)
        ttk.Label(frame, text="Background image:").grid(column=0, row=0, sticky="news")
        bgi_text = os.path.basename(self._config.get_str("image_bg"))
        if bgi_text == "":
            bgi_text = "-None-"
        self._set_btn = ttk.Button(frame, text=bgi_text[0:20], command=self._browse_bg_image)
        self._set_btn.grid(column=1, row=0, sticky="news")
        ToolTip(self._set_btn, "Set the scoreboard background image")
        clear_btn = ttk.Button(frame, text="Clear", command=self._clear_bg_image)
        clear_btn.grid(column=2, row=0, sticky="news")
        ToolTip(clear_btn, "Remove the scoreboard background image")
        return frame
    def _clear_bg_image(self):
        self._set_btn.configure(text="-None-")
        self._config.set_str("image_bg", "")
    def _browse_bg_image(self):
        image = filedialog.askopenfilename(filetypes=[("image", "*.gif *.jpg *.jpeg *.png")])
        if len(image) == 0:
            return
        image = os.path.normpath(image)
        self._config.set_str("image_bg", image)
        self._set_btn.configure(text=os.path.basename(image)[0:20])
    def _bg_brightness(self) -> ttk.Widget:
        frame = ttk.Frame(self, padding=1)
        frame.rowconfigure(0, weight=1)
        frame.columnconfigure(0, weight=1)
        ttk.Label(frame, text="Image brightness:").grid(column=0, row=0, sticky="nes")
        self._bg_spin_var = StringVar(frame, value=str(self._config.get_float("image_bright")))
        self._bg_spin_var.trace_add("write", self._handle_bg_spin)
        ttk.Spinbox(frame, from_=0, to=1, increment=0.05, width=5,
                    textvariable=self._bg_spin_var).grid(column=1, row=0, sticky="news")
        ToolTip(frame, "Brightness of background image [0.0, 1.0]")
        return frame
    def _handle_bg_spin(self, *_arg):
        try:
            value = float(self._bg_spin_var.get())
            if 0 <= value <= 1:
                self._config.set_float("image_bright", value)
        except ValueError:
            pass
    def _bg_scale(self) -> ttk.Widget:
        frame = ttk.Frame(self, padding=1)
        frame.rowconfigure(0, weight=1)
        frame.columnconfigure(0, weight=1)
        ttk.Label(frame, text="Scale:").grid(column=0, row=0, sticky="nes")
        self._bg_scale_var = StringVar(frame, value=str(self._config.get_str("image_scale")))
        self._bg_scale_var.trace_add("write", self._handle_bg_scale)
        ttk.Combobox(frame, state="readonly", textvariable=self._bg_scale_var,
                     values=["none", "cover", "fit", "stretch"],
                     width=7).grid(column=1, row=0, sticky="news")
        ToolTip(frame, "How to scale the background image\nnone: as-is\n"
            "cover: cover screen\nfit: fit within screen\n"  # pylint: disable=C0330
            "stretch: stretch all dimensions") # pylint: disable=C0330
        return frame
    def _handle_bg_scale(self, *_arg):
        self._config.set_str("image_scale", self._bg_scale_var.get())

    def _lanes(self) -> ttk.Widget:
        frame = ttk.Frame(self, padding=1)
        frame.rowconfigure(0, weight=1)
        frame.columnconfigure(0, weight=1)
        ttk.Label(frame, text="# of Lanes:").grid(column=0, row=0, sticky="news")
        self._lane_spin_var = StringVar(frame, value=str(self._config.get_int("num_lanes")))
        self._lane_spin_var.trace_add("write", self._handle_lane_spin)
        ttk.Spinbox(frame, from_=4, to=10, increment=1, width=3,
                    textvariable=self._lane_spin_var).grid(column=1, row=0, sticky="news")
        ToolTip(frame, "Number of lanes in the pool")
        return frame

    def _handle_lane_spin(self, *_arg):
        try:
            value = int(self._lane_spin_var.get())
            if 6 <= value <= 10:
                self._config.set_int("num_lanes", value)
        except ValueError:
            pass

    def _gpio(self) -> ttk.Widget:
        frame = ttk.Frame(self, padding=1)
        frame.rowconfigure(0, weight=1)
        frame.columnconfigure(0, weight=1)
        ttk.Label(frame, text="GPIO Pin:").grid(column=0, row=0, sticky="news")
        self._gpio_spin_var = StringVar(frame, value=str(self._config.get_int("GPIO_pin")))
        self._gpio_spin_var.trace_add("write", self._handle_gpio_spin)
        ttk.Spinbox(frame, from_=1, to=39, increment=1, width=3,
                    textvariable=self._gpio_spin_var).grid(column=1, row=0, sticky="news")
        ToolTip(frame, "Starter GPIO (RPI Only)")
        return frame

    def _handle_gpio_spin(self, *_arg):
        try:
            value = int(self._gpio_spin_var.get())
            if 1 <= value <= 39:
                self._config.set_int("GPIO_pin", value)
        except ValueError:
            pass

    def _font_chooser(self, text, config_option, tooltip) -> ttk.Widget:
        frame = ttk.Frame(self, padding=1)
        frame.rowconfigure(0, weight=1)
        frame.columnconfigure(0, weight=0)
        ttk.Label(frame, text=text).grid(column=0, row=0, sticky="nws")
        def callback(fontname):
            self._config.set_str(config_option, fontname)
        dropdown = ttkwidgets.font.FontFamilyDropdown(frame, callback)
        dropdown.set(self._config.get_str(config_option))
        dropdown.grid(column=1, row=0, sticky="news")
        ToolTip(frame, tooltip)
        return frame

    def _font_scale(self) -> ttk.Widget:
        frame = ttk.Frame(self, padding=1)
        frame.rowconfigure(0, weight=1)
        frame.columnconfigure(0, weight=1)
        ttk.Label(frame, text="Font scale:").grid(column=0, row=0, sticky="nes")
        self._font_spin_var = StringVar(frame, value=str(self._config.get_float("font_scale")))
        self._font_spin_var.trace_add("write", self._handle_font_spin)
        ttk.Spinbox(frame, from_=0, to=1, increment=0.01, width=5,
                    textvariable=self._font_spin_var).grid(column=1, row=0, sticky="news")
        ToolTip(frame, "Scale of font relative to line height [0.0, 1.0]")
        return frame
    def _handle_font_spin(self, *_arg):
        try:
            value = float(self._font_spin_var.get())
            if 0 <= value <= 1:
                self._config.set_float("font_scale", value)
        except ValueError:
            pass

    def _lane10is0(self) -> ttk.Widget:
        frame = ttk.Frame(self, padding=1)
        frame.rowconfigure(0, weight=1)
        frame.columnconfigure(0, weight=1)
        ttk.Label(frame, text="Lane 10 is 0:").grid(column=0, row=0, sticky="nes")
        self._inhibit_var = BooleanVar(frame, value=self._config.get_bool("lane10iszero"))
        ttk.Checkbutton(frame, variable=self._inhibit_var,
            command=self._handle_inhibit).grid(column=1, row=0, sticky="news") # pylint: disable=C0330
        ToolTip(frame, "Lane 10 is Lane 0 in the pool (Lane #s 0-9)")
        return frame
    def _handle_inhibit(self, *_arg):
        self._config.set_bool("inhibit_inconsistent", self._inhibit_var.get())

    def _fullscreen(self) -> ttk.Widget:
        frame = ttk.Frame(self, padding=1)
        frame.rowconfigure(0, weight=1)
        frame.columnconfigure(0, weight=1)
        ttk.Label(frame, text="Fullscreen:").grid(column=0, row=0, sticky="nes")
        self._fullscreen_var = BooleanVar(frame, value=self._config.get_bool("fullscreen"))
        ttk.Checkbutton(frame, variable=self._fullscreen_var,
            command=self._handle_fullscreen).grid(column=1, row=0, sticky="news") # pylint: disable=C0330
        ToolTip(frame, "Select to run scoreboard in fullscreen mode; deselect for windowed")
        return frame
    def _handle_fullscreen(self, *_arg):
        self._config.set_bool("fullscreen", self._fullscreen_var.get())

class Settings(ttk.Frame):  # pylint: disable=too-many-ancestors
    '''Main settings window'''

    # pylint: disable=too-many-arguments,too-many-locals
    def __init__(self, container: tkContainer,
                 scoreboard_run_cb: NoneFn, test_run_cb: NoneFn,
                 config: StarterConfig):
        super().__init__(container, padding=5)
        self._config = config
        self._scoreboard_run_cb = scoreboard_run_cb
        self._test_run_cb = test_run_cb
        self.grid(column=0, row=0, sticky="news")
        self.columnconfigure(0, weight=1)
        # Odd rows are empty filler to distribute vertical whitespace
        for i in [1, 3, 5, 7]:
            self.rowconfigure(i, weight=1)
        # row 0: Start list settings
        startlist = _StartList(self, self._config)
        startlist.grid(column=0, row=0, sticky="news")
        # row 2: General settings
        general = _GeneralSettings(self, self._config)
        general.grid(column=0, row=2, sticky="news")
        # row 4: run button(s)
        fr6 = ttk.Frame(self)
        fr6.grid(column=0, row=4, sticky="news")
        fr6.rowconfigure(0, weight=1)
        fr6.columnconfigure(0, weight=0)
        fr6.columnconfigure(1, weight=1)
        test_btn = ttk.Button(fr6, text="Test", command=self._handle_test_btn)
        test_btn.grid(column=0, row=0, sticky="news")
        ToolTip(test_btn, text="Display a mockup to show the current scoreboard style")
        run_btn = ttk.Button(fr6, text="Run Starter", command=self._handle_run_scoreboard_btn)
        run_btn.grid(column=1, row=0, sticky="news")
        ToolTip(run_btn, text="Start the starter simulator")
        # row 6: info panel
        fr8 = ttk.Frame(self)
        fr8.grid(column=0, row=6, sticky="news")
        fr8.rowconfigure(0, weight=1)
        fr8.columnconfigure(0, weight=1)
        fr8.columnconfigure(1, weight=0)
        link_label = ttkwidgets.LinkLabel(fr8,
            text="Documentation: https://XXXXXX.readthedocs.io/",  # pylint: disable=C0330
            link="https://XXXX.readthedocs.io/?utm_source=wahoo_results&"  # pylint: disable=C0330
                 "utm_medium=config_screen&utm_campaign=docs_link",  # pylint: disable=C0330
            relief="sunken",  # pylint: disable=C0330
            padding=[5, 2])  # pylint: disable=C0330
        link_label.grid(column=0, row=0, sticky="news")
        version_label = ttk.Label(fr8, text=SWIMCAM_VERSION, justify="right",
                                  padding=2, relief="sunken")
        version_label.grid(column=1, row=0, sticky="nes")

    def _handle_run_scoreboard_btn(self) -> None:
        self.destroy()
        self._scoreboard_run_cb()

    def _handle_test_btn(self) -> None:
        self.destroy()
        self._test_run_cb()

def main():
    '''testing'''
    root = tk.Tk()
    root.columnconfigure(0, weight=1)
    root.rowconfigure(0, weight=1)

    root.resizable(False, False)
    options = StarterConfig()
    settings = Settings(root, None, None, options)
    settings.grid(column=0, row=0, sticky="news")
    tk.mainloop()

if __name__ == '__main__':
    main()

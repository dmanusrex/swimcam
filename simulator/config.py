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


'''Config parsing

Based heavily on :
   Wahoo! Results - https://github.com/JohnStrunk/wahoo-results
   Copyright (C) 2020 - John D. Strunk
'''

import configparser

class StarterConfig:
    '''Get/Set program options'''

    # Name of the configuration file
    _CONFIG_FILE = "starter-simulator.ini"
    # Name of the section we use in the ini file
    _INI_HEADING = "starter=simulator"
    # Configuration defaults if not present in the config file
    _CONFIG_DEFAULTS = {_INI_HEADING: {
        "start_list_dir": ".",  # Location of Start List files
        "num_lanes": "10",      # Number of lanes on the board
        "color_bg": "black",    # Window background
        "color_fg": "white",    # Main text color
        "color_ehd": "white",   # Event/descr text color
        "image_bg": "",         # background image
        "image_scale": "fit",   # how to scale the bg image
        "image_bright": "0.3",  # bg image brightness (0-1)
        "normal_font": "Helvetica",  # Main font
        "font_scale": 0.67,     # scale of font relative to line height
        "fullscreen": "False",  # Run in fullscreen mode
        "GPIO_pin": 13,         # Starter GPIO PIN
        "lane10iszero": "False",# Lane numbering starts at 0
        "core_host": "localhost", # default core host
    }}

    def __init__(self):
        self._config = configparser.ConfigParser()
        self._config.read_dict(self._CONFIG_DEFAULTS)
        self._config.read(self._CONFIG_FILE)

    def save(self) -> None:
        '''Save the (updated) configuration to the ini file'''
        with open(self._CONFIG_FILE, 'w') as configfile:
            self._config.write(configfile)

    def get_str(self, name: str) -> str:
        '''Get a string option'''
        return self._config.get(self._INI_HEADING, name)

    def set_str(self, name: str, value: str) -> str:
        '''Set a string option'''
        self._config.set(self._INI_HEADING, name, value)
        return self.get_str(name)

    def get_float(self, name: str) -> float:
        '''Get a float option'''
        return self._config.getfloat(self._INI_HEADING, name)

    def set_float(self, name: str, value: float) -> float:
        '''Set a float option'''
        self._config.set(self._INI_HEADING, name, str(value))
        return self.get_float(name)

    def get_int(self, name: str) -> int:
        '''Get an integer option'''
        return self._config.getint(self._INI_HEADING, name)

    def set_int(self, name: str, value: int) -> int:
        '''Set an integer option'''
        self._config.set(self._INI_HEADING, name, str(value))
        return self.get_int(name)

    def get_bool(self, name: str) -> bool:
        '''Get a boolean option'''
        return self._config.getboolean(self._INI_HEADING, name)

    def set_bool(self, name: str, value: bool) -> bool:
        '''Set a boolean option'''
        self._config.set(self._INI_HEADING, name, str(value))
        return self.get_bool(name)

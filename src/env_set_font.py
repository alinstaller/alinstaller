#!/bin/env python3

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

import os

from ai_exec import ai_exec
from dlg import dialog
from env_set_keymap import env_set_keymap
from step import Step

class EnvSetFont(Step):
    def __init__(self):
        self.font = ''

    def run_once(self):
        fontsdir = '/usr/share/kbd/consolefonts'
        l = sorted(os.listdir(fontsdir))
        fonts = [('* No change', ''), ('* Default', '')]
        for x in l:
            if x.endswith('.gz'):
                fonts.append((x, ''))
        ret, sel = dialog.menu(
            'Please choose a font:',
            choices = fonts
        )
        if ret != dialog.OK: return False
        if sel == '* Default':
            ai_exec('setfont')
            self.font = ''
        elif sel != '* No change':
            ai_exec('setfont \"' + fontsdir + '/' + sel + '\"')
            self.font = fontsdir + '/' + sel

        env_set_keymap.run()
        return True

env_set_font = EnvSetFont()

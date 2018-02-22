#!/bin/env python3

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

import os

from ai_exec import ai_dialog_exec
from dlg import dialog
from set_font_lib import set_font_lib
from set_keymap_cli import set_keymap_cli
from step import Step


class SetFontCLI(Step):
    def run_once(self):
        fontsdir = '/usr/share/kbd/consolefonts'
        l = sorted(os.listdir(fontsdir))
        fonts = [('* No change', ''), ('* Default', '')]
        for x in l:
            if x.endswith('.gz'):
                fonts.append((x, ''))
        ret, sel = dialog.menu(
            'Please choose a font:',
            choices=fonts
        )
        if ret != dialog.OK:
            return False
        if sel == '* Default':
            ai_dialog_exec('setfont')
            set_font_lib.font = ''
        elif sel != '* No change':
            ai_dialog_exec('setfont \"' + fontsdir + '/' + sel + '\"')
            set_font_lib.font = fontsdir + '/' + sel

        set_keymap_cli.run()
        return True


set_font_cli = SetFontCLI()

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

import glob
import os

from ai_exec import ai_dialog_exec
from gui import gui


class VConsoleLib():
    fontsdir = '/usr/share/kbd/consolefonts'
    keymapsdir = '/usr/share/kbd/keymaps'

    def __init__(self):
        self._font = ''
        self._keymap = ''

        l = sorted(os.listdir(self.fontsdir))
        fonts = []
        for x in l:
            if x.endswith('.gz'):
                fonts.append(x)
        self._fonts = fonts

        keymaps = glob.glob(self.keymapsdir + '/**/*.map.gz')
        keymaps = [x[len(self.keymapsdir)+1:] for x in keymaps]
        keymaps = sorted(keymaps)
        self._keymaps = keymaps

    def get_fonts(self):
        return list(self._fonts)

    def get_keymaps(self):
        return list(self._keymaps)

    def get_font(self):
        return self._font

    def get_font_full(self):
        if self._font == '':
            return ''
        return self.fontsdir + '/' + self._font

    def set_font(self, font):
        if font == '':
            if not gui.started:
                ai_dialog_exec('setfont')
            self._font = ''
        else:
            if not gui.started:
                ai_dialog_exec('setfont \'' + self.fontsdir + '/' + font + '\'')
            self._font = font

    def get_keymap(self):
        return self._keymap

    def get_keymap_full(self):
        if self._keymap == '':
            return ''
        return self.keymapsdir + '/' + self._keymap

    def set_keymap(self, keymap):
        if keymap == '':
            if not gui.started:
                ai_dialog_exec('loadkeys -d')
            self._keymap = ''
        else:
            if not gui.started:
                ai_dialog_exec('loadkeys \'' + self.keymapsdir + '/' + keymap +
                               '\'')
            self._keymap = keymap


vconsole_lib = VConsoleLib()

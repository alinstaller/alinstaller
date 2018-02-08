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

import glob
import os

from ai_exec import ai_exec
from dlg import dialog
from partition import partition
from step import Step

class EnvSetKeymap(Step):
    def __init__(self):
        self.keymap = ''

    def run_once(self):
        keymapsdir = '/usr/share/kbd/keymaps'
        keymaps = glob.glob(keymapsdir + '/**/*.map.gz')
        keymaps = [(x[len(keymapsdir)+1:], '') for x in keymaps]
        keymaps = sorted(keymaps)
        keymaps = [('* No change', ''), ('* Default', '')] + keymaps
        ret, sel = dialog.menu(
            'Please select your keyboard layout:',
            choices = keymaps
        )
        if ret != dialog.OK: return False
        if sel == '* Default':
            ai_exec('loadkeys -d')
            self.keymap = ''
        elif sel != '* No change':
            ai_exec('loadkeys \"' + keymapsdir + '/' + sel + '\"')
            self.keymap = keymapsdir + '/' + sel

        partition.run()
        return True

env_set_keymap = EnvSetKeymap()

#!/bin/env python3

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

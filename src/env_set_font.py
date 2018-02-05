#!/bin/env python3

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

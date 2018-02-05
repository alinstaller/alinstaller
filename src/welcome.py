#!/bin/env python3

from dlg import dialog
from env_set_font import env_set_font
from step import Step

class Welcome(Step):
    def run_once(self):
        if (dialog.msgbox('Welcome to AL Installer!\n\n'
            + 'This guide will help you install Arch Linux.'
            ) == dialog.OK):
            env_set_font.run()
        return True

welcome = Welcome()

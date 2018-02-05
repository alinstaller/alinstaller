#!/bin/env python3

from dlg import dialog
from password import password
from step import Step

class Hostname(Step):
    def __init__(self):
       self.hostname = 'arch'

    def run_once(self):
        res, text = dialog.inputbox(
            text = 'Enter hostname:',
            init = self.hostname
        )
        if res != dialog.OK: return False
        self.hostname = text

        password.run()
        return True

hostname = Hostname()

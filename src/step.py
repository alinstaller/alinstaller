#!/bin/env python3

from dlg import dialog

class Step(object):
    def run(self):
        while self.run_once(): pass

    def run_once(self):
        dialog.msgbox('Not implemented.')
        return False

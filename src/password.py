#!/bin/env python3

from dlg import dialog
from install import install
from step import Step

class Password(Step):
    def __init__(self):
       self.password = ''

    def run_once(self):
        res, text = dialog.passwordbox(
            text = 'Enter root password:',
            init = self.password,
            insecure = True
        )
        if res != dialog.OK: return False

        if text != self.password:
            res, text2 = dialog.passwordbox(
                text = 'Confirm root password:',
                insecure = True
            )
            if res != dialog.OK: return False
            if text2 != text:
                dialog.msgbox(text = 'Passwords do not match.')
                return True

        self.password = text

        if text == '':
            dialog.msgbox(
                text = 'A new password is required to continue.',
                width = 50,
                height = 6)
            return True

        install.run()
        return True

password = Password()

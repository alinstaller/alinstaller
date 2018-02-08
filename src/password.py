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

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

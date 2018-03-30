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

from dlg import dialog
from hostname_lib import hostname_lib
from install_cli import install_cli
from step import Step


class HostnameCLI(Step):
    def run_once(self):
        text = ''

        while text == '':
            res, text = dialog.inputbox(
                text='Enter host name (leave empty to regenerate):',
                init=hostname_lib.hostname,
                width=50, height=9
            )
            if res != dialog.OK:
                return False

            if text == '':
                hostname_lib.generate()
            else:
                hostname_lib.hostname = text

        install_cli.run()
        return True


hostname_cli = HostnameCLI()

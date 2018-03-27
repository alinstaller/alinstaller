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
from install_cli import install_cli
from step import Step
from vm_lib import vm_lib


class AdvancedCLI(Step):
    def run_once(self):
        res = dialog.yesno(
            text='Do you want to edit advanced configurations?',
            width=50, height=5, defaultno=True,
            help_button=True, help_label='Cancel'
        )

        if res == dialog.HELP:
            return False
        elif res == dialog.OK:
            res, text = dialog.inputbox(
                text='VM Swappiness (default=' +
                str(vm_lib.default_swappiness) + ')\n' +
                'You can change this later in /etc/sysctl.d/99-sysctl.conf.',
                init=str(vm_lib.get_swappiness()),
                width=64, height=9
            )
            if res != dialog.OK:
                return False

            value = vm_lib.default_swappiness
            try:
                value = int(text)
            except Exception:
                pass

            try:
                vm_lib.set_swappiness(value)
            except Exception:
                vm_lib.set_swappiness(vm_lib.default_swappiness)

        install_cli.run()
        return True


advanced_cli = AdvancedCLI()

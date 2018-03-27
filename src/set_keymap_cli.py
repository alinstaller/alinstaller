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
from partition_cli import partition_cli
from step import Step
from vconsole_lib import vconsole_lib


class SetKeymapCLI(Step):
    def run_once(self):
        keymaps = vconsole_lib.get_keymaps()
        keymaps = [(x, '') for x in keymaps]
        keymaps = [('* No change', ''), ('* Default', '')] + keymaps

        default_item = vconsole_lib.get_keymap()
        if default_item == '':
            default_item = '* Default'
        ret, sel = dialog.menu(
            'Please select your keyboard mapping for the virtual console.' +
            '\n' + 'You can change this later in /etc/vconsole.conf.',
            choices=keymaps,
            default_item=default_item
        )
        if ret != dialog.OK:
            return False

        if sel == '* Default':
            vconsole_lib.set_keymap('')
        elif sel != '* No change':
            vconsole_lib.set_keymap(sel)

        partition_cli.run()
        return True


set_keymap_cli = SetKeymapCLI()

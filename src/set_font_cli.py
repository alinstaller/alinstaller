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
from set_keymap_cli import set_keymap_cli
from step import Step
from vconsole_lib import vconsole_lib


class SetFontCLI(Step):
    def run_once(self):
        fonts = vconsole_lib.get_fonts()
        fonts = [(x, '') for x in fonts]
        fonts = [('* No change', ''), ('* Default', '')] + fonts

        default_item = vconsole_lib.get_font()
        if default_item == '':
            default_item = '* Default'
        ret, sel = dialog.menu(
            'Please choose a font for the virtual console.' + '\n' +
            'You can change this later in /etc/vconsole.conf.',
            choices=fonts,
            default_item=default_item
        )
        if ret != dialog.OK:
            return False

        if sel == '* Default':
            vconsole_lib.set_font('')
        elif sel != '* No change':
            vconsole_lib.set_font(sel)

        set_keymap_cli.run()
        return True


set_font_cli = SetFontCLI()

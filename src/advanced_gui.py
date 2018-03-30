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

from gui import gui
from gui_step import GUIStep
from vconsole_lib import vconsole_lib


class AdvancedGUI(GUIStep):
    def __init__(self):
        liststore = gui.builder.get_object('liststore_fonts')
        liststore.insert_with_valuesv(-1, [0], [''])
        for x in vconsole_lib.get_fonts():
            liststore.insert_with_valuesv(-1, [0], [x])

        combobox = gui.builder.get_object('combobox_font')
        combobox.set_active(0)
        combobox.connect('changed', self._font_changed)

        gui.builder.get_object('button_font_reset').connect(
            'clicked', self._font_reset_clicked)

        liststore = gui.builder.get_object('liststore_keymaps')
        liststore.insert_with_valuesv(-1, [0], [''])
        for x in vconsole_lib.get_keymaps():
            liststore.insert_with_valuesv(-1, [0], [x])

        combobox = gui.builder.get_object('combobox_keymap')
        combobox.set_active(0)
        combobox.connect('changed', self._keymap_changed)

        gui.builder.get_object('button_keymap_reset').connect(
            'clicked', self._keymap_reset_clicked)

    def update_text(self):
        gui.builder.get_object('label_advanced_cover').set_label(_('Cover'))
        gui.builder.get_object('label_advanced_options').set_label(_(
            'Advanced Options'))
        gui.builder.get_object('label_advanced_warning').set_label(_(
            'Do not edit unless you are familiar with them.'))

        gui.builder.get_object('label_vconsole').set_label(_('Virtual Console'))
        gui.builder.get_object('label_vconsole_font').set_label(_('Font'))
        gui.builder.get_object('button_font_reset').set_label(_('Reset'))
        gui.builder.get_object('label_vconsole_keymap').set_label(_(
            'Keyboard Mapping'))
        gui.builder.get_object('button_keymap_reset').set_label(_('Reset'))
        gui.builder.get_object('label_vconsole_notice').set_label(_(
            'You can edit these values later in /etc/vconsole.conf.'))

    def _font_changed(self, combobox):
        active = combobox.get_active()
        if active == 0:
            vconsole_lib.set_font('')
        elif active > 0:
            vconsole_lib.set_font(vconsole_lib.get_fonts()[active - 1])

    def _font_reset_clicked(self, button):
        gui.builder.get_object('combobox_font').set_active(0)

    def _keymap_changed(self, combobox):
        active = combobox.get_active()
        if active == 0:
            vconsole_lib.set_keymap('')
        elif active > 0:
            vconsole_lib.set_keymap(vconsole_lib.get_keymaps()[active - 1])

    def _keymap_reset_clicked(self, button):
        gui.builder.get_object('combobox_keymap').set_active(0)


advanced_gui = AdvancedGUI()

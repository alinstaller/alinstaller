#!/bin/env python3

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

from gi.repository import Gtk

from gui import gui
from gui_step import GUIStep
from password_lib import password_lib

class PasswordGUI(GUIStep):
    def __init__(self):
        entry = gui.builder.get_object('entry_password')
        entry.connect('changed', self._changed)
        entry = gui.builder.get_object('entry_password_confirm')
        entry.connect('changed', self._changed)

        def button_next():
            if password_lib.password == '':
                dialog = Gtk.MessageDialog(
                    gui.window,
                    Gtk.DialogFlags.DESTROY_WITH_PARENT,
                    Gtk.MessageType.ERROR,
                    Gtk.ButtonsType.CLOSE,
                    _('A new password is required.')
                )
                dialog.run()
                dialog.destroy()
                return False
            return True

        gui.hook_button_next('password', button_next)

        self._update_status_text()

    def update_text(self):
        gui.builder.get_object('label_password').set_label(
            _('Enter root password:'))
        gui.builder.get_object('label_password_confirm').set_label(
            _('Confirm root password:'))
        self._update_status_text()

    def _changed(self, entry):
        self._update_status_text()

        p1 = gui.builder.get_object('entry_password').get_text()
        p2 = gui.builder.get_object('entry_password_confirm').get_text()

        if p1 == '' or p1 != p2:
            password_lib.password = ''
        else:
            password_lib.password = p1

    def _update_status_text(self):
        p1 = gui.builder.get_object('entry_password').get_text()
        p2 = gui.builder.get_object('entry_password_confirm').get_text()

        status = ''
        if p1 == '' or p2 == '':
            status = _('A new password is required.')
        elif p1 != p2:
            status = _('Passwords do not match.')

        gui.builder.get_object('label_password_status') \
            .set_label(status)

password_gui = PasswordGUI()

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
from hostname_lib import hostname_lib


class HostnameGUI(GUIStep):
    def __init__(self):
        entry = gui.builder.get_object('entry_hostname')
        entry.set_text(hostname_lib.hostname)
        entry.connect('changed', self._changed)
        gui.builder.get_object('button_hostname_regenerate').connect(
            'clicked', lambda x: self._regenerate())

        def button_next():
            if hostname_lib.hostname == '':
                dialog = Gtk.MessageDialog(
                    gui.window,
                    Gtk.DialogFlags.DESTROY_WITH_PARENT,
                    Gtk.MessageType.ERROR,
                    Gtk.ButtonsType.CLOSE,
                    _('A new host name is required.')
                )
                dialog.run()
                dialog.destroy()
                return False
            return True

        gui.hook_button_next('hostname', button_next)

    def update_text(self):
        gui.builder.get_object('label_hostname').set_label(
            _('Enter a new host name:'))

    def _changed(self, entry):
        hostname_lib.hostname = entry.get_text()

    def _regenerate(self):
        gui.builder.get_object('entry_hostname').set_text(
            hostname_lib.generate())


hostname_gui = HostnameGUI()

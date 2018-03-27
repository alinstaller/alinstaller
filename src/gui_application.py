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

from gi.repository import Gio, Gtk


class GUIApplication(Gtk.Application):
    application_id = 'io.github.alinstaller'

    def __init__(self, *args):
        super().__init__(*args, application_id=self.application_id,
                         flags=Gio.ApplicationFlags.HANDLES_COMMAND_LINE)
        self.started = False

    def do_activate(self):
        from gui import gui

        if not self.started:
            self.started = True
            gui.start_gui()

        gui.window.present()

    def do_command_line(self, command_line):
        self.activate()
        return 0


gui_application = GUIApplication()

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


class WelcomeGUI(GUIStep):
    def update_text(self):
        gui.builder.get_object('label_welcome_title').set_label(
            _('Welcome to AL Installer!'))
        gui.builder.get_object('label_welcome_subtitle').set_label(
            _('This guide will help you install Arch Linux.'))


welcome_gui = WelcomeGUI()

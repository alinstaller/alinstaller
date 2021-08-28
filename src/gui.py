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

import sys

from gi.repository import GLib, Gtk

from gui_application import gui_application


class GUI():
    # NOTE: all GUI calls have to be made from the main thread.

    _gui_file = 'gui.glade'
    # add pages here:
    _pages = ['language', 'welcome', 'partition', 'hostname', 'advanced', 'install']

    def __init__(self):
        self.started = False
        self.builder = None
        self.window = None
        self.stack_main = None
        self._button_back_hooks = {}
        self._button_next_hooks = {}
        self._pages_ins = []

    def start_gui(self):
        self.started = True

        self.builder = Gtk.Builder()
        self.builder.add_from_file(self._gui_file)

        self.window = self.builder.get_object('window')
        self.window.connect('delete_event', lambda x, y: True)
        self.window.connect('destroy', lambda x: sys.exit(0))

        self.stack_main = self.builder.get_object('stack_main')

        button_back = self.builder.get_object('button_back')
        button_next = self.builder.get_object('button_next')
        button_back.connect('clicked', self._button_back_clicked, button_next)
        button_next.connect('clicked', self._button_next_clicked, button_back)

        self.window.set_application(gui_application)

        # add pages here:
        from language_gui import language_gui
        self._pages_ins += [language_gui]
        from welcome_gui import welcome_gui
        self._pages_ins += [welcome_gui]
        from partition_gui import partition_gui
        self._pages_ins += [partition_gui]
        from hostname_gui import hostname_gui
        self._pages_ins += [hostname_gui]
        from advanced_gui import advanced_gui
        self._pages_ins += [advanced_gui]
        from install_gui import install_gui
        self._pages_ins += [install_gui]

        self.update_text()
        self.window.show_all()

    def idle_add(self, callback, *args, **kwargs):
        def cb(*args, **kwargs):
            callback(*args, **kwargs)
            return False
        return GLib.idle_add(cb, *args, **kwargs)

    def update_text(self):
        header_bar = self.builder.get_object('header_bar')
        button_back = self.builder.get_object('button_back')
        button_next = self.builder.get_object('button_next')
        header_bar.set_title(_('AL Installer'))
        button_back.set_label(_('_Back'))
        button_next.set_label(_('_Next'))

        for x in self._pages_ins:
            x.update_text()

    def hook_button_back(self, page, f, *args, **kwargs):
        self._button_back_hooks[page] = lambda: f(*args, **kwargs)

    def unhook_button_back(self, page):
        if page in self._button_back_hooks:
            del self._button_back_hooks[page]

    def hook_button_next(self, page, f, *args, **kwargs):
        self._button_next_hooks[page] = lambda: f(*args, **kwargs)

    def unhook_button_next(self, page):
        if page in self._button_next_hooks:
            del self._button_next_hooks[page]

    def _get_number_from_page(self, name):
        for i, page in enumerate(self._pages):
            if page == name:
                return i
        return -1

    def _button_back_clicked(self, button_back, button_next):
        n = self._get_number_from_page(
            self.stack_main.get_visible_child_name())
        if n <= 0 or n >= len(self._pages):
            return

        if self._pages[n] in self._button_back_hooks:
            if not self._button_back_hooks[self._pages[n]]():
                return

        n -= 1
        if n == 0:
            button_back.set_sensitive(False)
        else:
            button_back.set_sensitive(True)
        button_next.set_sensitive(True)
        self.stack_main.set_visible_child_name(self._pages[n])

    def _button_next_clicked(self, button_next, button_back):
        n = self._get_number_from_page(
            self.stack_main.get_visible_child_name())
        if n < 0 or n >= len(self._pages) - 1:
            return

        if self._pages[n] in self._button_next_hooks:
            if not self._button_next_hooks[self._pages[n]]():
                return

        n += 1
        if n == len(self._pages) - 1:
            button_next.set_sensitive(False)
        else:
            button_next.set_sensitive(True)
        button_back.set_sensitive(True)
        self.stack_main.set_visible_child_name(self._pages[n])


gui = GUI()

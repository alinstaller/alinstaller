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

from gi.repository import Gtk, Pango

from gui import gui
from gui_step import GUIStep
from language_lib import language_lib


class LanguageGUI(GUIStep):
    def __init__(self):
        super().__init__()
        self._insert_rows()

    def update_text(self):
        gui.builder.get_object('label_select_language').set_label(
            _('Please select your language:'))

    def _get_row(self, desc, code):
        row = Gtk.ListBoxRow()
        box = Gtk.Box(Gtk.Orientation.HORIZONTAL)
        box.set_margin_left(8)
        box.set_margin_right(8)
        box.set_margin_top(8)
        box.set_margin_bottom(8)
        box.set_homogeneous(True)
        box.set_spacing(4)
        desc = Gtk.Label(desc)
        desc.set_ellipsize(Pango.EllipsizeMode.END)
        desc.set_halign(Gtk.Align.START)
        select = Gtk.Image.new_from_icon_name(
            'object-select-symbolic', Gtk.IconSize.MENU)
        select.set_opacity(0.0)
        select.set_halign(Gtk.Align.START)
        box2 = Gtk.Box(Gtk.Orientation.HORIZONTAL)
        box2.set_spacing(2)
        box2.pack_start(desc, False, True, 0)
        box2.pack_start(select, False, True, 1)
        code = Gtk.Label(code)
        desc.set_ellipsize(Pango.EllipsizeMode.END)
        code.set_halign(Gtk.Align.START)
        box.pack_start(box2, True, True, 0)
        box.pack_end(code, True, True, 1)
        row.add(box)
        row.show_all()

        def select_func(x):
            return select.set_opacity(1.0) if x else select.set_opacity(0.0)

        return row, select_func

    def _insert_row(self, list_box, desc, code):
        row, select = self._get_row(desc, code)
        list_box.add(row)
        return row, select

    def _insert_rows(self):
        list_box = gui.builder.get_object('list_box_languages')
        rows = []
        selects = []

        for x in language_lib.languages:
            row, select = self._insert_row(list_box, x[1], x[0])
            rows.append(row)
            selects.append(select)

        list_box.connect('row-activated', self._row_activated, selects)
        list_box.select_row(rows[0])
        self._row_activated(list_box, rows[0], selects)

        return rows

    def _row_activated(self, box, row, selects):
        index = row.get_index()

        i = 0
        for x in selects:
            x(i == index)
            i += 1

        lang = language_lib.languages[index][0]
        language_lib.install(lang)
        gui.update_text()


language_gui = LanguageGUI()

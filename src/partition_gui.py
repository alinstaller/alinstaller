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

import queue
import threading
import traceback

from gi.repository import Gtk

from partition_lib import PartitionMenuItem, partition_lib
from gui import gui
from gui_step import GUIStep


class PartitionGUI(GUIStep):
    def __init__(self):
        super().__init__()

        listbox = gui.builder.get_object('listbox_partition_actions')

        self._listbox_signal = listbox.connect(
            'row-activated', self._listbox_row_activated, PartitionMenuItem())
        self._log = ''
        self._log_lock = threading.Lock()
        self._queue = queue.Queue()

        gui.builder.get_object('entry_autosetup_type').set_text(
            partition_lib.default_partitioning)
        gui.builder.get_object('label_autosetup_recommend_type').set_label(
            _('Recommended: ') + partition_lib.default_partitioning)
        gui.builder.get_object('entry_parttable').set_text(
            partition_lib.default_partitioning)
        gui.builder.get_object('label_parttable_recommend').set_label(
            _('Recommended: ') + partition_lib.default_partitioning)
        gui.builder.get_object('entry_part_fs').set_text(
            partition_lib.default_filesystem)
        gui.builder.get_object('entry_format').set_text(
            partition_lib.default_filesystem)

        textview = gui.builder.get_object('textview_partition_log')
        adjustment = gui.builder.get_object('scrolledwindow_partition_log') \
            .get_vadjustment()
        textview.connect('size-allocate', lambda x, y:
                         adjustment.set_value(adjustment.get_upper()))

        dialog = gui.builder.get_object('dialog_autosetup')
        dialog.connect('delete-event', lambda x, y: dialog.hide_on_delete())
        dialog = gui.builder.get_object('dialog_parttable')
        dialog.connect('delete-event', lambda x, y: dialog.hide_on_delete())
        dialog = gui.builder.get_object('dialog_part')
        dialog.connect('delete-event', lambda x, y: dialog.hide_on_delete())
        dialog = gui.builder.get_object('dialog_format')
        dialog.connect('delete-event', lambda x, y: dialog.hide_on_delete())
        dialog = gui.builder.get_object('dialog_cryptsetup')
        dialog.connect('delete-event', lambda x, y: dialog.hide_on_delete())
        dialog = gui.builder.get_object('dialog_cryptopen')
        dialog.connect('delete-event', lambda x, y: dialog.hide_on_delete())

        switch = gui.builder.get_object('switch_autosetup_encryption')
        switch.connect('notify::active', lambda x, y: gui.builder.get_object(
            'revealer_autosetup_passphrase').set_reveal_child(x.get_active()))

        button = gui.builder.get_object('button_autosetup')
        self._button_autosetup_signal = button.connect(
            'clicked', lambda x: False)
        button = gui.builder.get_object('button_parttable')
        self._button_parttable_signal = button.connect(
            'clicked', lambda x: False)
        button = gui.builder.get_object('button_part')
        self._button_part_signal = button.connect('clicked', lambda x: False)
        button = gui.builder.get_object('button_format')
        self._button_format_signal = button.connect('clicked', lambda x: False)
        button = gui.builder.get_object('button_cryptsetup')
        self._button_cryptsetup_signal = button.connect(
            'clicked', lambda x: False)
        button = gui.builder.get_object('button_cryptopen')
        self._button_cryptopen_signal = button.connect(
            'clicked', lambda x: False)

        t = threading.Thread(target=self._lib_loop, daemon=True)
        t.start()

        def button_next():
            if not self._queue.empty():
                dialog = Gtk.MessageDialog(
                    gui.window,
                    Gtk.DialogFlags.DESTROY_WITH_PARENT,
                    Gtk.MessageType.ERROR,
                    Gtk.ButtonsType.CLOSE,
                    _('An operation is in progress.')
                )
                dialog.run()
                dialog.destroy()
                return False
            if partition_lib.install_target == '':
                dialog = Gtk.MessageDialog(
                    gui.window,
                    Gtk.DialogFlags.DESTROY_WITH_PARENT,
                    Gtk.MessageType.ERROR,
                    Gtk.ButtonsType.CLOSE,
                    _('A main installation target must be selected.') + '\n' +
                    _('If not sure, choose an empty disk, and select ' +
                      '\"Automatically Set Up This Disk\".')
                )
                dialog.run()
                dialog.destroy()
                return False
            return True

        gui.hook_button_next('partition', button_next)

        def focus_listbox(x, y, z):
            children = gui.builder.get_object('listbox_partition_actions') \
                .get_children()
            if children:
                try:
                    children[0].grab_focus()
                except Exception:
                    pass

        gui.builder.get_object('treeview_partitions') \
            .connect('row-activated', focus_listbox)
        gui.builder.get_object('treeview_partitions') \
            .connect('cursor-changed', lambda x: self._update_content_text())

        gui.builder.get_object('button_partition_log_clear') \
            .connect('clicked', lambda x: self._clear_log())

        def expanded(expander, expanded):
            expanded = expander.get_expanded()
            expander.get_children()[0].set_visible(expanded)

        gui.builder.get_object('expander_partition_log').connect(
            'notify::expanded', expanded)

        self._scan()

    def update_text(self):
        gui.builder.get_object('label_edit_partitions').set_label(
            _('Edit partitions below. If not sure, choose an empty disk, ' +
              'and select \"Automatically Set Up This Disk\".'))
        gui.builder.get_object('label_partition_action').set_label(
            _('Choose an action below:'))
        gui.builder.get_object('label_partition_log').set_label(
            _('Log'))
        gui.builder.get_object('label_autosetup_type').set_label(
            _('Partitioning type'))
        gui.builder.get_object('label_autosetup_encryption').set_label(
            _('Encryption'))
        gui.builder.get_object('label_autosetup_passphrase').set_label(
            _('Passphrase'))
        gui.builder.get_object('label_autosetup_confirm_passphrase').set_label(
            _('Confirm passphrase'))
        gui.builder.get_object('button_autosetup').set_label(
            _('Set Up This Disk'))
        gui.builder.get_object('label_parttable').set_label(
            _('Partitioning type'))
        gui.builder.get_object('button_parttable').set_label(
            _('Create/Rewrite Partition Table'))
        gui.builder.get_object('label_part_start').set_label(
            _('Start'))
        gui.builder.get_object('label_part_end').set_label(
            _('End'))
        gui.builder.get_object('label_part_fs').set_label(
            _('Filesystem'))
        gui.builder.get_object('button_part').set_label(
            _('Create Partition'))
        gui.builder.get_object('label_format').set_label(
            _('Filesystem'))
        gui.builder.get_object('button_format').set_label(
            _('Format'))
        gui.builder.get_object('label_cryptsetup_passphrase').set_label(
            _('Passphrase'))
        gui.builder.get_object('label_cryptsetup_confirm_passphrase').set_label(
            _('Confirm passphrase'))
        gui.builder.get_object('button_cryptsetup').set_label(
            _('Set Up Encryption'))
        gui.builder.get_object('label_cryptopen_passphrase').set_label(
            _('Passphrase'))
        gui.builder.get_object('button_cryptopen').set_label(
            _('Open'))
        self._update_content_text()

    def add_log_lib(self, log):
        with self._log_lock:
            self._log += log + '\n'

        def update():
            textbuffer = gui.builder.get_object('textbuffer_partition_log')
            with self._log_lock:
                textbuffer.set_text(self._log)
        gui.idle_add(update)

    def _lib_loop_add(self, working_ui, f, *args, **kwargs):
        self._queue.put((lambda: f(*args, **kwargs), working_ui))
        # dummy task to ensure that all tasks are done when the queue is empty:
        self._queue.put((lambda: True, False))

    def _lib_loop(self):
        while True:
            f, working_ui = self._queue.get()

            if working_ui:
                event = threading.Event()

                def func():
                    treeview = gui.builder.get_object('treeview_partitions')
                    listbox = gui.builder.get_object(
                        'listbox_partition_actions')
                    label = gui.builder.get_object('label_partition_working')
                    spinner = gui.builder.get_object(
                        'spinner_partition_working')
                    if gui.stack_main.get_visible_child_name() == 'partition':
                        expander = gui.builder.get_object(
                            'expander_partition_log')
                        expander.grab_focus()
                    treeview.set_sensitive(False)
                    listbox.set_sensitive(False)
                    label.set_label(_('Working'))
                    spinner.start()
                    event.set()
                gui.idle_add(func)
                event.wait()

            try:
                f()
            except Exception:
                self.add_log_lib(traceback.format_exc())

            if working_ui:
                event = threading.Event()

                def func2():
                    treeview = gui.builder.get_object('treeview_partitions')
                    listbox = gui.builder.get_object(
                        'listbox_partition_actions')
                    label = gui.builder.get_object('label_partition_working')
                    spinner = gui.builder.get_object(
                        'spinner_partition_working')
                    treeview.set_sensitive(True)
                    listbox.set_sensitive(True)
                    label.set_label('')
                    spinner.stop()
                    event.set()
                gui.idle_add(func2)
                event.wait()

            self._queue.task_done()

    def _add_log(self, log):
        textbuffer = gui.builder.get_object('textbuffer_partition_log')
        with self._log_lock:
            self._log += log + '\n'
            textbuffer.set_text(self._log)

    def _clear_log(self):
        textbuffer = gui.builder.get_object('textbuffer_partition_log')
        with self._log_lock:
            self._log = ''
            textbuffer.set_text('')

    def _update_content_text(self):
        self._lib_loop_add(False, self._update_content_text_lib)

    def _update_content_text_lib(self):
        menu = partition_lib.get_layout_menu()
        gui.idle_add(self._update_content_text_from_menu, menu)

    def _update_content_text_from_menu(self, menu):
        treestore = gui.builder.get_object('treestore_partitions')
        it = treestore.get_iter_first()

        for x in menu:
            if it is None:
                break
            text = treestore.get_value(it, 0)
            size_text = treestore.get_value(it, 1)
            if text != x.text:
                treestore.set_value(it, 0, x.text)
            if size_text != x.size_text:
                treestore.set_value(it, 1, x.size_text)
            it = treestore.iter_next(it)

        self._update_details_actions_from_menu(menu)

    def _update_details_actions_from_menu(self, menu):
        treeselection = gui.builder.get_object('treeselection_partitions')
        label = gui.builder.get_object('label_partition_details')

        __, paths = treeselection.get_selected_rows()
        if not paths:
            label.set_label(_('Select an item to view its details.'))
            self._lib_loop_add(
                False, self._update_actions_lib, PartitionMenuItem())
        else:
            index = paths[0].get_indices()[0]
            label.set_label(menu[index].details_text)
            self._lib_loop_add(False, self._update_actions_lib, menu[index])

    def _update_actions_lib(self, item):
        actions = []
        for x in item.ops:
            actions.append(partition_lib.get_text_for_op(x))
        gui.idle_add(self._update_actions, item, actions)

    def _update_actions(self, item, actions):
        listbox = gui.builder.get_object('listbox_partition_actions')

        for x in listbox.get_children():
            listbox.remove(x)

        rows = []
        for x in actions:
            row = Gtk.ListBoxRow()
            label2 = Gtk.Label(x)
            label2.set_margin_top(4)
            label2.set_margin_bottom(4)
            label2.set_halign(Gtk.Align.START)
            row.add(label2)
            row.show_all()
            listbox.add(row)
            rows.append(row)

        listbox.disconnect(self._listbox_signal)
        self._listbox_signal = listbox.connect(
            'row-activated', self._listbox_row_activated, item, actions)

    def _refresh_content_text_from_menu(self, menu):
        treestore = gui.builder.get_object('treestore_partitions')

        treestore.clear()
        for x in menu:
            treestore.insert_with_values(
                None, -1, [0, 1], [x.text, x.size_text])

        self._update_details_actions_from_menu(menu)

    def _scan(self):
        self._lib_loop_add(True, self._scan_lib)

    def _scan_lib(self):
        try:
            partition_lib.scan()
            menu = partition_lib.get_layout_menu()
            gui.idle_add(self._refresh_content_text_from_menu, menu)
        except Exception:
            self.add_log_lib(traceback.format_exc())

    def _listbox_row_activated(self, box, row, item, actions):
        index = row.get_index()
        name = item.name
        text = item.text
        size = item.size
        op = item.ops[index]
        action = actions[index]

        handler = None
        if op == 'autosetup':
            handler = self._handle_autosetup
        elif op == 'parttable':
            handler = self._handle_parttable
        elif op == 'part':
            handler = self._handle_part
        elif op == 'format':
            handler = self._handle_format
        elif op == 'remove':
            handler = self._handle_remove
        elif op == 'cryptsetup':
            handler = self._handle_cryptsetup
        elif op in ['cryptopen', 'swap-cryptopen']:
            handler = self._handle_cryptopen
        else:
            handler = self._handle_others

        handler(name, text, size, op, action)

    def _handle_autosetup(self, name, text, size, op, action):
        def handle(button):
            dialog = gui.builder.get_object('dialog_autosetup')

            crypt = False
            passphrase = ''
            switch = gui.builder.get_object('switch_autosetup_encryption')
            if switch.get_active():
                entry1 = gui.builder.get_object('entry_autosetup_passphrase')
                entry2 = gui.builder.get_object(
                    'entry_autosetup_confirm_passphrase')
                pass1 = entry1.get_text()
                pass2 = entry2.get_text()
                if pass1 != pass2:
                    dialog2 = Gtk.MessageDialog(
                        dialog,
                        Gtk.DialogFlags.DESTROY_WITH_PARENT,
                        Gtk.MessageType.ERROR,
                        Gtk.ButtonsType.CLOSE,
                        _('Passphrases do not match.')
                    )
                    dialog2.run()
                    dialog2.destroy()
                    return
                crypt = True
                passphrase = pass1

            res = self._show_confirm_dialog(dialog, text,
                                            _('Are you sure you want to wipe this disk?'), _('Wipe'))
            if res != Gtk.ResponseType.OK:
                return

            dialog.hide()
            parttable = gui.builder.get_object(
                'entry_autosetup_type').get_text()

            def action_lib():
                try:
                    partition_lib.action(op, name, size=size,
                                         parttable=parttable, crypt=crypt,
                                         passphrase=passphrase)
                    self._scan_lib()
                except Exception:
                    self.add_log_lib(traceback.format_exc())

            self._lib_loop_add(True, action_lib)

        button = gui.builder.get_object('button_autosetup')
        button.disconnect(self._button_autosetup_signal)
        self._button_autosetup_signal = button.connect('clicked', handle)

        gui.builder.get_object('entry_autosetup_type').grab_focus()
        dialog = gui.builder.get_object('dialog_autosetup')
        dialog.set_title(text + ' - ' + action)

        dialog.run()
        dialog.hide()

    def _handle_parttable(self, name, text, size, op, action):
        def handle(button):
            dialog = gui.builder.get_object('dialog_parttable')

            res = self._show_confirm_dialog(dialog, text,
                                            _('Are you sure you want to wipe this disk?'), _('Wipe'))
            if res != Gtk.ResponseType.OK:
                return

            dialog.hide()
            parttable = gui.builder.get_object('entry_parttable').get_text()

            def action_lib():
                try:
                    partition_lib.action(op, name, parttable=parttable)
                    self._scan_lib()
                except Exception:
                    self.add_log_lib(traceback.format_exc())

            self._lib_loop_add(True, action_lib)

        button = gui.builder.get_object('button_parttable')
        button.disconnect(self._button_parttable_signal)
        self._button_parttable_signal = button.connect('clicked', handle)

        gui.builder.get_object('entry_parttable').grab_focus()
        dialog = gui.builder.get_object('dialog_parttable')
        dialog.set_title(text + ' - ' + action)

        dialog.run()
        dialog.hide()

    def _handle_part(self, name, text, size, op, action):
        info = name.split('*')

        def handle(button):
            dialog = gui.builder.get_object('dialog_part')
            dialog.hide()

            start = gui.builder.get_object('entry_part_start').get_text()
            end = gui.builder.get_object('entry_part_end').get_text()
            fstype = gui.builder.get_object('entry_part_fs').get_text()

            def action_lib():
                try:
                    partition_lib.action(op, name, start=start, end=end,
                                         fstype=fstype)
                    self._scan_lib()
                except Exception:
                    self.add_log_lib(traceback.format_exc())

            self._lib_loop_add(True, action_lib)

        button = gui.builder.get_object('button_part')
        button.disconnect(self._button_part_signal)
        self._button_part_signal = button.connect('clicked', handle)

        entry = gui.builder.get_object('entry_part_start')
        entry.set_text(info[2])
        entry = gui.builder.get_object('entry_part_end')
        entry.set_text(info[3])

        gui.builder.get_object('entry_part_start').grab_focus()
        dialog = gui.builder.get_object('dialog_part')
        dialog.set_title(action)

        dialog.run()
        dialog.hide()

    def _handle_format(self, name, text, size, op, action):
        def handle(button):
            dialog = gui.builder.get_object('dialog_format')

            res = self._show_confirm_dialog(dialog, text,
                                            _('Are you sure you want to format this partition?'),
                                            _('Format'))
            if res != Gtk.ResponseType.OK:
                return

            dialog.hide()
            fstype = gui.builder.get_object('entry_format').get_text()

            def action_lib():
                try:
                    partition_lib.action(op, name, fstype=fstype)
                    self._scan_lib()
                except Exception:
                    self.add_log_lib(traceback.format_exc())

            self._lib_loop_add(True, action_lib)

        button = gui.builder.get_object('button_format')
        button.disconnect(self._button_format_signal)
        self._button_format_signal = button.connect('clicked', handle)

        gui.builder.get_object('entry_format').grab_focus()
        dialog = gui.builder.get_object('dialog_format')
        dialog.set_title(text + ' - ' + action)

        dialog.run()
        dialog.hide()

    def _handle_remove(self, name, text, size, op, action):
        res = self._show_confirm_dialog(gui.window, text,
                                        _('Are you sure you want to remove this partition?'), _('Remove'))
        if res != Gtk.ResponseType.OK:
            return

        def action_lib():
            try:
                partition_lib.action(op, name)
                self._scan_lib()
            except Exception:
                self.add_log_lib(traceback.format_exc())

        self._lib_loop_add(True, action_lib)

    def _handle_cryptsetup(self, name, text, size, op, action):
        def handle(button):
            dialog = gui.builder.get_object('dialog_cryptsetup')

            entry1 = gui.builder.get_object('entry_cryptsetup_passphrase')
            entry2 = gui.builder.get_object(
                'entry_cryptsetup_confirm_passphrase')
            pass1 = entry1.get_text()
            pass2 = entry2.get_text()
            if pass1 != pass2:
                dialog2 = Gtk.MessageDialog(
                    dialog,
                    Gtk.DialogFlags.DESTROY_WITH_PARENT,
                    Gtk.MessageType.ERROR,
                    Gtk.ButtonsType.CLOSE,
                    _('Passphrases do not match.')
                )
                dialog2.run()
                dialog2.destroy()
                return
            passphrase = pass1

            res = self._show_confirm_dialog(dialog, text,
                                            _('Are you sure you want to encrypt this disk? All data will be lost.'),
                                            _('Encrypt'))
            if res != Gtk.ResponseType.OK:
                return

            dialog.hide()

            def action_lib():
                try:
                    partition_lib.action(op, name, passphrase=passphrase)
                    self._scan_lib()
                except Exception:
                    self.add_log_lib(traceback.format_exc())

            self._lib_loop_add(True, action_lib)

        button = gui.builder.get_object('button_cryptsetup')
        button.disconnect(self._button_cryptsetup_signal)
        self._button_cryptsetup_signal = button.connect('clicked', handle)

        gui.builder.get_object('entry_cryptsetup_passphrase').grab_focus()
        dialog = gui.builder.get_object('dialog_cryptsetup')
        dialog.set_title(text + ' - ' + action)

        dialog.run()
        dialog.hide()

    def _handle_cryptopen(self, name, text, size, op, action):
        def handle(button):
            dialog = gui.builder.get_object('dialog_cryptopen')

            entry = gui.builder.get_object('entry_cryptopen_passphrase')
            passphrase = entry.get_text()

            dialog.hide()

            def action_lib():
                try:
                    partition_lib.action(op, name, passphrase=passphrase)
                    self._scan_lib()
                except Exception:
                    self.add_log_lib(traceback.format_exc())

            self._lib_loop_add(True, action_lib)

        button = gui.builder.get_object('button_cryptopen')
        button.disconnect(self._button_cryptopen_signal)
        self._button_cryptopen_signal = button.connect('clicked', handle)

        gui.builder.get_object('entry_cryptopen_passphrase').grab_focus()
        dialog = gui.builder.get_object('dialog_cryptopen')
        dialog.set_title(text + ' - ' + action)

        dialog.run()
        dialog.hide()

    def _handle_others(self, name, text, size, op, action):
        def action_lib():
            try:
                partition_lib.action(op, name)
                self._scan_lib()
            except Exception:
                self.add_log_lib(traceback.format_exc())

        self._lib_loop_add(True, action_lib)

    def _show_confirm_dialog(self, parent, title, msg, action):
        dialog = Gtk.Dialog()
        dialog.set_resizable(False)
        dialog.set_transient_for(parent)
        dialog.set_destroy_with_parent(True)
        if title != '':
            dialog.set_title(title + ' - ' + _('Confirm'))
        else:
            dialog.set_title(_('Confirm'))
        label = Gtk.Label(msg)
        content_area = dialog.get_content_area()
        content_area.pack_start(label, False, True, 0)
        content_area.set_margin_left(4)
        content_area.set_margin_right(4)
        content_area.set_margin_top(4)
        content_area.set_margin_bottom(8)
        content_area.show_all()
        dialog.add_button(_('Cancel'), Gtk.ResponseType.CANCEL)
        button_yes = dialog.add_button(action, Gtk.ResponseType.OK)
        button_yes.get_style_context().add_class('destructive-action')
        button_yes.set_can_default(True)
        button_yes.grab_default()
        action_area = dialog.get_action_area()
        action_area.set_margin_left(4)
        action_area.set_margin_right(4)
        action_area.set_margin_top(8)
        action_area.set_margin_bottom(4)
        res = dialog.run()
        dialog.destroy()

        return res


partition_gui = PartitionGUI()

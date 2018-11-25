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

import subprocess
import threading

from ai_exec import ai_popen, ai_call
from gui import gui
from gui_step import GUIStep
from install_lib import install_lib


class InstallGUI(GUIStep):
    def __init__(self):
        self._log = ''
        self._log_lock = threading.Lock()
        self._percent = 0
        self._percent_lock = threading.Lock()
        self._progress = ''
        self._progress_lock = threading.Lock()

        gui.builder.get_object('button_install').connect(
            'clicked', lambda x: self._install())
        gui.builder.get_object('button_install_restart').connect(
            'clicked', lambda x: ai_call('reboot'))

        textview = gui.builder.get_object('textview_install_log')
        adjustment = gui.builder.get_object('scrolledwindow_install_log') \
            .get_vadjustment()
        textview.connect('size-allocate', lambda x, y:
                         adjustment.set_value(adjustment.get_upper()))

    def update_text(self):
        gui.builder.get_object('label_install_ready').set_label(
            _('We are ready to install Arch Linux.'))
        gui.builder.get_object('button_install').set_label(
            _('Install Now'))
        gui.builder.get_object('button_install_restart').set_label(
            _('Restart System'))

    def _add_log_thread(self, log):
        with self._log_lock:
            self._log += log + '\n'

        def update():
            textbuffer = gui.builder.get_object('textbuffer_install_log')
            with self._log_lock:
                textbuffer.set_text(self._log)
        gui.idle_add(update)

    def _add_log(self, log):
        textbuffer = gui.builder.get_object('textbuffer_install_log')
        with self._log_lock:
            self._log += log + '\n'
            textbuffer.set_text(self._log)

    def _set_percent_thread(self, percent):
        if percent < 0 or percent > 100:
            return
        with self._percent_lock:
            self._percent = percent

        def update():
            progressbar = gui.builder.get_object('progressbar_install')
            with self._percent_lock:
                progressbar.set_fraction(self._percent / 100)
        gui.idle_add(update)

    def _set_progress_thread(self, text):
        with self._progress_lock:
            self._progress = text

        def update():
            label = gui.builder.get_object('label_install_progress')
            with self._progress_lock:
                label.set_label(self._progress)
        gui.idle_add(update)

    def _set_progress(self, text):
        label = gui.builder.get_object('label_install_progress')
        with self._progress_lock:
            self._progress = text
            label.set_label(self._progress)

    def _exec_thread(self, cmd, msg):
        p = ai_popen(
            cmd, universal_newlines=True,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT
        )
        self._add_log_thread(msg)
        for x in p.stdout:
            self._add_log_thread(x.rstrip('\n'))
        p.communicate()
        return p.returncode

    def _install_fail(self):
        self._set_progress(_('Installation failed.'))
        gui.builder.get_object('stack_install_restart').set_visible_child_name(
            'restart')
        gui.builder.get_object('button_install_restart').grab_focus()

    def _install_fail_thread(self):
        gui.idle_add(self._install_fail)

    def _install_complete(self):
        self._set_progress(
            _('Installation completed. You can restart your system now.'))
        gui.builder.get_object('stack_install_restart').set_visible_child_name(
            'restart')
        gui.builder.get_object('button_install_restart').grab_focus()

    def _install_complete_thread(self):
        gui.idle_add(self._install_complete)

    def _install(self):
        gui.builder.get_object('button_back').set_sensitive(False)
        gui.builder.get_object('button_next').set_sensitive(False)
        gui.builder.get_object(
            'stack_install').set_visible_child_name('progress')

        t = threading.Thread(target=self._init_dirs_thread, daemon=True)
        t.start()

    def _init_dirs_thread(self):
        cmd = install_lib.get_init_dirs_cmd()

        self._set_progress_thread(_('Initializing directories...'))
        res = self._exec_thread(cmd, 'Initializing directories...')
        if res != 0:
            self._install_fail_thread()
            return

        self._copy_files_thread()

    def _copy_files_thread(self):
        cmd = install_lib.get_copy_files_cmd()

        text_base = _('Copying files...')
        text = text_base
        text_prev = text
        percent = 0
        percent_prev = 0

        p = ai_popen(cmd, stdin=subprocess.DEVNULL,
                     stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
                     universal_newlines=True)
        self._set_progress_thread(text)
        self._add_log_thread('Copying files...')

        for x in p.stdout:
            x = x.split()
            if len(x) == 4 and x[1].endswith('%'):
                percent = int(x[1][:-1])
                speed = x[2]
                eta = x[3]
                text = text_base + \
                    '\nSpeed: ' + speed + \
                    '\nETA: ' + eta

            if percent != percent_prev:
                self._set_percent_thread(percent)
                percent_prev = percent
            if text != text_prev:
                self._set_progress_thread(text)
                text_prev = text

        p.communicate()
        if p.returncode != 0:
            self._install_fail_thread()
            return

        self._configure_thread()

    def _configure_thread(self):
        self._set_percent_thread(0)
        self._set_progress_thread(_('Configuring...'))

        cmd = install_lib.get_configure_cmd()
        res = self._exec_thread(cmd, 'Configuring...')

        if res != 0:
            self._install_fail_thread()
            return

        self._install_complete_thread()


install_gui = InstallGUI()

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
import sys

from ai_exec import ai_popen, ai_dialog_exec
from dlg import dialog
from install_lib import install_lib
from step import Step


class InstallCLI(Step):
    def run_once(self):
        res = dialog.yesno('We are ready to install Arch Linux.\n' +
                           'Begin installing now?',
                           width=50, height=6)
        if res != dialog.OK:
            return False

        res = self._do_install()

        if res == 0:
            dialog.msgbox('Installation completed.\n' +
                          'Your system is going to be restarted.',
                          width=50, height=6)
        else:
            dialog.msgbox('Installation failed.\n' +
                          'Your system is going to be restarted.',
                          width=50, height=6)

        ai_dialog_exec('reboot', msg='Restarting...', showcmd=False)
        sys.exit(res)

    def _do_install(self):
        cmd = install_lib.get_init_dirs_cmd()

        res = ai_dialog_exec(cmd, msg='Initializing directories...',
                             showcmd=False)
        if res != 0:
            return res

        cmd = install_lib.get_copy_files_cmd()

        gauge_text_base = 'Copying files...'
        gauge_text = gauge_text_base
        gauge_text_prev = gauge_text
        gauge_percent = 0
        gauge_percent_prev = 0
        dialog.gauge_start(gauge_text, width=40, height=9)

        p = ai_popen(cmd, stdin=subprocess.DEVNULL,
                     stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
                     universal_newlines=True)
        for x in p.stdout:
            x = x.split()
            if len(x) == 4 and x[1].endswith('%'):
                gauge_percent = int(x[1][:-1])
                speed = x[2]
                eta = x[3]
                gauge_text = gauge_text_base + \
                    '\nSpeed:  ' + speed + \
                    '\n  ETA:  ' + eta

            if gauge_percent != gauge_percent_prev or \
                    gauge_text != gauge_text_prev:
                dialog.gauge_update(percent=gauge_percent, text=gauge_text,
                                    update_text=True)
                gauge_text_prev = gauge_text
                gauge_percent_prev = gauge_percent

        p.communicate()
        dialog.gauge_stop()
        if p.returncode != 0:
            return p.returncode

        cmd = install_lib.get_configure_cmd()
        res = ai_dialog_exec(cmd, linger=True, msg='Configuring...',
                             width=75, height=20, showcmd=False)

        return res


install_cli = InstallCLI()

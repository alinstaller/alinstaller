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

import os
import signal
import sys
import time
import traceback

import gi
gi.require_version('Gdk', '3.0')
gi.require_version('Gtk', '3.0')

from gi.repository import GLib


def init_gtk():
    # Prevent gtk from spamming warnings on init
    stderr = os.dup(sys.stderr.fileno())
    with open('/dev/null', 'wb') as null_file:
        os.dup2(null_file.fileno(), sys.stderr.fileno())
        from gi.repository import Gtk as _
        os.dup2(stderr, sys.stderr.fileno())
        os.close(stderr)


init_gtk()

from ai_exec import ai_call
from dlg import dialog
from gui_application import gui_application
from language_lib import language_lib
from welcome_cli import welcome_cli


def main():
    language_lib.install()

    GLib.set_prgname(gui_application.application_id)
    GLib.set_application_name(_('AL Installer'))

    enable_gui = False

    if len(sys.argv) >= 2:
        if sys.argv[1] in ['--help', '-h']:
            print('Usage:\n\n' +
                  '(no argument)       Run in CLI (must be run as root)\n' +
                  '--gui               Run in GUI (must be run as a password-free sudoer user)\n' +
                  '--setup-gui         Prompt and set up GUI (must be run as root)\n')
            sys.exit(0)

        if sys.argv[1] == '--gui':
            enable_gui = True
        elif sys.argv[1] == '--setup-gui':
            print('\n\nTo use CLI instead of GUI, press Ctrl+C (once) in 3 seconds.')
            try:
                time.sleep(3)
                enable_gui = True

                def handle_interrupt_immediate(signum, frame):
                    ai_call('reboot')
                    while True:
                        time.sleep(1000)

                def handle_interrupt(signum, frame):
                    signal.signal(signal.SIGINT, lambda signum, frame: None)
                    print('\nToo late.\n')
                    time.sleep(2)
                    signal.signal(signal.SIGINT, handle_interrupt_immediate)
                    ai_call('reboot')
                    while True:
                        time.sleep(1000)

                signal.signal(signal.SIGINT, handle_interrupt)
            except KeyboardInterrupt:
                enable_gui = False

            if enable_gui:
                print('\nSetting up GUI...')

                ai_call(
                    'pacman -R --noconfirm --noprogressbar gnome-initial-setup && ' +
                    'rm -f /var/log/pacman.log')

                ai_call(
                    'cp /usr/local/share/applications/*.desktop /etc/xdg/autostart')

                ai_call('useradd -c \'Live User\' -G users,wheel -m liveuser')
                ai_call('passwd -d liveuser')

                ai_call(
                    'sed -i \'s/\\[daemon\\]/[daemon]\\nAutomaticLoginEnable=' +
                    'True\\nAutomaticLogin=liveuser/\' /etc/gdm/custom.conf')

                with open('/etc/sudoers', 'a', encoding='utf_8') as f:
                    f.write('\n%wheel ALL=(ALL) ALL\n')

                ai_call(
                    'sudo -u liveuser dbus-launch bash -c \'' +
                    'gsettings set org.gnome.settings-daemon.plugins.power sleep-inactive-ac-type nothing && ' +
                    'gsettings set org.gnome.settings-daemon.plugins.power sleep-inactive-battery-type nothing && ' +
                    'gsettings set org.gnome.shell welcome-dialog-last-shown-version 99999999 && ' +
                    'gsettings set org.gnome.software allow-updates false && ' +
                    'gsettings set org.gnome.software download-updates false' +
                    '\'')

                ai_call('systemctl start firewalld')
                ai_call('systemctl start NetworkManager')
                ai_call('systemctl start avahi-daemon')
                ai_call('systemctl start systemd-resolved')
                ai_call('systemctl start spice-vdagentd')
                ai_call('systemctl start gdm')
                sys.exit(0)

    if enable_gui:
        gui_application.run(sys.argv)
    else:
        try:
            welcome_cli.run()
        except (Exception, KeyboardInterrupt):
            dialog.msgbox('Installation failed.\n\n' + traceback.format_exc())


main()

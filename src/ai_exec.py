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

from dlg import dialog


def ai_popen(*args, **kwargs):
    # wrapper function to open process as root
    return subprocess.Popen(['sudo', 'bash', '-c', args[0]], *args[1:],
                            **kwargs)


def ai_dialog_exec(*args, **kwargs):
    myargs = {'linger': False, 'msg': '', 'showcmd': True,
              'width': 0, 'height': 0}
    for arg in myargs:
        if arg in kwargs:
            myargs[arg] = kwargs[arg] # pylint: disable=modified-iterating-dict
            kwargs.pop(arg)

    if myargs['msg'] != '':
        myargs['msg'] += '\n\n'

    if myargs['showcmd']:
        myargs['msg'] += '- ' + args[0]

    proc = ai_popen(*args, **kwargs,
                    stdin=subprocess.DEVNULL,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT)
    if myargs['linger']:
        dialog.programbox(fd=proc.stdout.fileno(), text=myargs['msg'],
                          width=myargs['width'], height=myargs['height'])
    else:
        dialog.progressbox(fd=proc.stdout.fileno(), text=myargs['msg'],
                           width=myargs['width'], height=myargs['height'])
    proc.communicate()
    return proc.returncode


def ai_call(*args, **kwargs):
    proc = ai_popen(*args, **kwargs,
                    stdin=subprocess.DEVNULL,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.DEVNULL)
    out, __ = proc.communicate()
    return proc.returncode, out

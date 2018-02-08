#!/bin/env python3

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

import os
import subprocess

from dlg import dialog

def ai_exec(*args, **kwargs):
    myargs = {'linger': False, 'nodialog': False, 'msg': '', 'showcmd': True,
        'width': 0, 'height': 0}
    for a in myargs:
        if a in kwargs:
            myargs[a] = kwargs[a]
            kwargs.pop(a)

    if myargs['msg'] != '':
        myargs['msg'] += '\n\n'

    if myargs['showcmd']:
        myargs['msg'] += '- ' + args[0]

    if not myargs['nodialog']:
        p = subprocess.Popen(*args, **kwargs,
            shell=True,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT)
        if myargs['linger']:
            dialog.programbox(fd=p.stdout.fileno(), text=myargs['msg'],
                width=myargs['width'], height=myargs['height'])
        else:
            dialog.progressbox(fd=p.stdout.fileno(), text=myargs['msg'],
                width=myargs['width'], height=myargs['height'])
        p.communicate()
        return p.returncode
    else:
        p = subprocess.Popen(*args, **kwargs, shell=True)
        p.communicate()
        return p.returncode

def ai_call(*args, **kwargs):
    p = subprocess.Popen(*args, **kwargs,
        shell=True,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL)
    out, err = p.communicate()
    return p.returncode, out

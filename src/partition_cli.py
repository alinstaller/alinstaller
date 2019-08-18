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

import traceback

from dlg import dialog
from hostname_cli import hostname_cli
from partition_lib import partition_lib
from step import Step


class PartitionCLI(Step):
    def __init__(self):
        self._switch_to_finish = False

    def run_once(self):
        res = 'again'
        try:
            res = self._do_partition()
            if res == 'back':
                return False
        except (Exception, KeyboardInterrupt):
            dialog.msgbox('An error occurred:\n\n' + traceback.format_exc())
            return False

        if res == 'next':
            if partition_lib.install_target == '':
                dialog.msgbox('A main installation target must be selected.',
                              width=50, height=6)
                return True
            hostname_cli.run()

        return True

    def _do_partition(self):
        if not partition_lib.scanned:
            self._scan()

        m = list(partition_lib.get_layout_menu())
        l = [len(x.text) for x in m]
        max_len = max(l)

        menu = []
        i = 0
        for x in m:
            menu.append((str(i),
                         x.text + ' ' * (max_len - l[i] + 2) + x.size_text))
            i += 1
        menu.append((str(len(menu)), 'Finish Partitioning'))

        res, sel = dialog.menu('Edit partitions below. If not sure, ' +
                               'choose an empty disk, and select ' +
                               '\'Automatically Set Up This Disk\'.\n',
                               choices=menu,
                               no_tags=True,
                               default_item=str(len(menu) - 1) if self._switch_to_finish else '0')

        self._switch_to_finish = False

        if res != dialog.OK:
            return 'back'

        sel = int(sel)
        if sel == len(menu) - 1:
            return 'next'

        menu = []
        for x in m[sel].ops:
            menu.append((x, partition_lib.get_text_for_op(x)))

        if not menu:
            dialog.msgbox('Name: ' + m[sel].text.strip(' ') + '\n' +
                          m[sel].details_atext)
            return 'again'

        res, sel2 = dialog.menu('Name: ' + m[sel].text.strip(' ') + '\n' +
                                m[sel].details_text +
                                '\n\nChoose an action:\n',
                                choices=menu,
                                no_tags=True)

        if res != dialog.OK:
            return 'again'

        if self._handle_action(m[sel].name, m[sel].size, sel2):
            self._scan()

        return 'again'

    def _handle_action(self, name, size, op):
        if op == 'autosetup':
            res, text = dialog.inputbox(
                text='Partitioning type (msdos, gpt, ...):',
                init=partition_lib.default_partitioning)
            if res != dialog.OK:
                return False
            res = dialog.yesno(
                text='Enable encryption?',
                defaultno=True)
            passphrase = ''
            if res == dialog.OK:
                res2, passphrase = dialog.passwordbox(
                    text='Enter passphrase:',
                    insecure=True)
                if res2 != dialog.OK:
                    return False
                res2, passphrase2 = dialog.passwordbox(
                    text='Confirm passphrase:',
                    insecure=True)
                if res2 != dialog.OK:
                    return False
                if passphrase2 != passphrase:
                    dialog.msgbox('Passphrases do not match.')
                    return False
            res2 = dialog.yesno(
                text='Are you sure you want to wipe this disk?')
            if res2 != dialog.OK:
                return False

            partition_lib.action(op, name, size=size, parttable=text,
                                 crypt=(res == dialog.OK), passphrase=passphrase)

            self._switch_to_finish = True

        elif op == 'parttable':
            res, text = dialog.inputbox(
                text=partition_lib.get_text_for_op(op) + '\n\n' +
                'Partitioning type (msdos, gpt, ...):',
                init=partition_lib.default_partitioning)
            if res != dialog.OK:
                return False
            res = dialog.yesno(
                text='Are you sure you want to wipe this disk?')
            if res != dialog.OK:
                return False

            partition_lib.action(op, name, parttable=text)

        elif op == 'part':
            info = name.split('*')
            res, lst = dialog.form(
                text=partition_lib.get_text_for_op(op) + '\n',
                elements=[('Disk', 1, 1, info[1], 1, 48, -32, 1024),
                          ('Start', 3, 1, info[2], 3, 48, 32, 1024),
                          ('End', 5, 1, info[3], 5, 48, 32, 1024),
                          ('Filesystem (ext4, linux-swap, fat32, ...)', 7, 1,
                           partition_lib.default_filesystem, 7, 48, 32, 1024)])
            if res != dialog.OK:
                return False

            partition_lib.action(op, name, start=lst[0], end=lst[1],
                                 fstype=lst[2])

        elif op == 'format':
            res, text = dialog.inputbox(
                text=partition_lib.get_text_for_op(op) + '\n\n' +
                'Filesystem type (ext4, swap, fat, ...):',
                init=partition_lib.default_filesystem)
            if res != dialog.OK:
                return False
            res = dialog.yesno(text='Are you sure?')
            if res != dialog.OK:
                return False

            partition_lib.action(op, name, fstype=text)

        elif op == 'remove':
            res = dialog.yesno(text='Are you sure?')
            if res != dialog.OK:
                return False

            partition_lib.action(op, name)

        elif op == 'cryptsetup':
            res, passphrase = dialog.passwordbox(
                text='Enter passphrase:',
                insecure=True)
            if res != dialog.OK:
                return False

            res, passphrase2 = dialog.passwordbox(
                text='Confirm passphrase:',
                insecure=True)
            if res != dialog.OK:
                return False
            if passphrase2 != passphrase:
                dialog.msgbox('Passphrases do not match.')
                return False

            res = dialog.yesno(text='Are you sure?')
            if res != dialog.OK:
                return False

            partition_lib.action(op, name, passphrase=passphrase)

        elif op in ['cryptopen', 'swap-cryptopen']:
            res, passphrase = dialog.passwordbox(
                text='Enter passphrase:',
                insecure=True)
            if res != dialog.OK:
                return False

            partition_lib.action(op, name, passphrase=passphrase)

        else:
            partition_lib.action(op, name)

        return True

    def _scan(self):
        dialog.infobox('Loading partition information...', 3, 40)
        partition_lib.scan()


partition_cli = PartitionCLI()

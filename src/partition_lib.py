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

import json
import os
import subprocess
import threading

import psutil

from ai_exec import ai_call, ai_dialog_exec, ai_popen
from dlg import dialog
from gui import gui


class PartitionMenuItem():
    def __init__(self, name='', size=0, text='', size_text='', details_text='',
                 ops=None):
        self.name = name
        self.size = size
        self.text = text
        self.size_text = size_text
        self.details_text = details_text
        if ops is None:
            self.ops = []
        else:
            self.ops = ops


class PartitionLib():
    base = 1000
    boot_part_size = 1024 * 1024 * 512
    default_filesystem = 'ext4'
    default_luks_type = 'luks2'
    default_partitioning = 'gpt' if ai_call('efivar -l')[0] == 0 else 'msdos'
    part_granularity = 1024 * 1024
    part_granularity_unit = 'MiB'

    def __init__(self):
        self.boot_target = ''
        self.crypt_passphrase = ''
        self.crypt_target = ''
        self.install_target = ''
        self.swap_crypt_passphrase = ''
        self.swap_crypt_target = ''
        self.swap_target = ''
        self.parts = []
        self.scanned = False

    def __str__(self):
        return str(json.dumps(self.parts, sort_keys=True))

    def _action_autosetup(self, name, size, parttable, crypt=False,
                          passphrase=''):
        boot_start = self.part_granularity
        boot_end = boot_start + self.boot_part_size - 1
        root_start = boot_end + 1
        root_end = size - psutil.virtual_memory().total - \
            self.part_granularity
        root_end = self._to_gran_end(root_end) * self.part_granularity - 1
        swap_start = root_end + 1

        boot_target = self.get_part_from_disk_num(name, 1)
        crypt_passphrase = ''
        crypt_target = ''
        install_target = self.get_part_from_disk_num(name, 2)
        swap_crypt_passphrase = ''
        swap_crypt_target = ''
        swap_target = self.get_part_from_disk_num(name, 3)
        if crypt:
            crypt_passphrase = passphrase
            crypt_target = install_target
            install_target = '/dev/mapper/cryptroot'
            swap_crypt_passphrase = passphrase
            swap_crypt_target = swap_target
            swap_target = '/dev/mapper/swap'

        if crypt:
            with open('/tmp/alinstaller-keyfile', 'w', encoding='utf_8') as f:
                f.write(passphrase)

        cmd = 'parted -m -s \'' + name + '\' unit B mklabel \'' + \
            parttable + '\''
        if parttable == 'gpt':
            cmd += ' mkpart ESP fat32 ' + str(boot_start) + 'B ' + \
                str(boot_end) + 'B'
        else:
            cmd += ' mkpart primary fat32 ' + str(boot_start) + 'B ' + \
                str(boot_end) + 'B'
        cmd += ' mkpart primary ' + self.default_filesystem + ' ' + \
            str(root_start) + 'B ' + str(root_end) + 'B'
        cmd += ' set 1 boot on'
        cmd += ' mkpart primary linux-swap ' + str(swap_start) + 'B 100%'
        cmd += ' && mkfs.fat -F32 \'' + self.get_part_from_disk_num(name, 1) + '\''
        if not crypt:
            cmd += ' && mkfs.ext4 \'' + self.get_part_from_disk_num(name, 2) + '\''
        else:
            cmd += ' && cryptsetup -v -q --key-file /tmp/alinstaller-keyfile luksFormat ' + \
                '--type \'' + self.default_luks_type + '\' \'' + \
                self.get_part_from_disk_num(name, 2) + '\''
            cmd += ' && cryptsetup -q --key-file /tmp/alinstaller-keyfile open \'' + \
                self.get_part_from_disk_num(name, 2) + '\' cryptroot'
            cmd += ' && mkfs.ext4 /dev/mapper/cryptroot'
        if not crypt:
            cmd += ' && mkswap \'' + self.get_part_from_disk_num(name, 3) + '\''
        else:
            cmd += ' && cryptsetup -v -q --key-file /tmp/alinstaller-keyfile luksFormat ' + \
                '--type \'' + self.default_luks_type + '\' \'' + \
                self.get_part_from_disk_num(name, 3) + '\''
            cmd += ' && cryptsetup -q --key-file /tmp/alinstaller-keyfile open \'' + \
                self.get_part_from_disk_num(name, 3) + '\' swap'
            cmd += ' && mkswap /dev/mapper/swap'

        cmd += ' && echo Completed.'

        self._exec(cmd, linger=True, msg='Automatically setting up disk...')

        try:
            os.remove('/tmp/alinstaller-keyfile')
        except Exception:
            pass

        self.boot_target = boot_target
        self.crypt_passphrase = crypt_passphrase
        self.crypt_target = crypt_target
        self.install_target = install_target
        self.swap_crypt_passphrase = swap_crypt_passphrase
        self.swap_crypt_target = swap_crypt_target
        self.swap_target = swap_target

    def _action_boot(self, name):
        disk = self.get_disk_from_part(name)
        num = self.get_num_from_part(name)
        cmd = 'parted -m -s \'' + disk + '\' unit B toggle \'' + \
            str(num) + '\' boot && echo Completed.'

        self._exec(cmd, linger=True, msg='Toggling boot flag...')

    def _action_boot_target(self, name):
        self.boot_target = name
        self._msgbox(_('Successful.'))

    def _action_clear_boot_target(self, name):
        self.boot_target = ''
        self._msgbox(_('Successful.'))

    def _action_clear_crypt_target(self, name):
        self.crypt_passphrase = ''
        self.crypt_target = ''
        self._msgbox(_('Successful.'))

    def _action_clear_install_target(self, name):
        self.install_target = ''
        self._msgbox(_('Successful.'))

    def _action_clear_swap_crypt_target(self, name):
        self.swap_crypt_passphrase = ''
        self.swap_crypt_target = ''
        self._msgbox(_('Successful.'))

    def _action_clear_swap_target(self, name):
        self.swap_target = ''
        self._msgbox(_('Successful.'))

    def _action_cryptsetup(self, name, passphrase):
        with open('/tmp/alinstaller-keyfile', 'w', encoding='utf_8') as f:
            f.write(passphrase)
        self._exec('cryptsetup -v -q --key-file /tmp/alinstaller-keyfile luksFormat --type \'' +
                   self.default_luks_type + '\' \'' + name + '\' && echo Completed.',
                   linger=True, msg='Setting up encryption...')
        os.remove('/tmp/alinstaller-keyfile')

    def _action_cryptopen(self, name, passphrase):
        with open('/tmp/alinstaller-keyfile', 'w', encoding='utf_8') as f:
            f.write(passphrase)
        self._exec('cryptsetup -q --key-file /tmp/alinstaller-keyfile open \'' + name +
                   '\' cryptroot && echo Completed.',
                   linger=True, msg='Opening main encrypted partition...')
        self.crypt_passphrase = passphrase
        self.crypt_target = name
        os.remove('/tmp/alinstaller-keyfile')

    def _action_cryptclose(self, name):
        self._exec('cryptsetup close cryptroot && echo Completed.',
                   linger=True, msg='Closing main encrypted block...')
        self.crypt_passphrase = ''
        self.crypt_target = ''

    def _action_swap_cryptopen(self, name, passphrase):
        with open('/tmp/alinstaller-keyfile', 'w', encoding='utf_8') as f:
            f.write(passphrase)
        self._exec('cryptsetup -q --key-file /tmp/alinstaller-keyfile open \'' + name +
                   '\' swap && echo Completed.',
                   linger=True, msg='Opening swap encrypted partition...')
        self.swap_crypt_passphrase = passphrase
        self.swap_crypt_target = name
        os.remove('/tmp/alinstaller-keyfile')

    def _action_swap_cryptclose(self, name):
        self._exec('cryptsetup close swap && echo Completed.',
                   linger=True, msg='Closing swap encrypted block...')
        self.swap_crypt_passphrase = ''
        self.swap_crypt_target = ''

    def _action_format(self, name, fstype):
        cmd = ''
        if fstype == 'swap':
            cmd = 'mkswap \'' + name + '\''
        else:
            cmd = 'mkfs -t \'' + fstype + '\' \'' + name + '\''
        cmd += ' && echo Completed.'
        self._exec(cmd, linger=True, msg='Formatting partition...')

    def _action_install_target(self, name):
        self.install_target = name
        self._msgbox(_('Successful.'))

    def _action_parttable(self, name, parttable):
        self._exec('parted -m -s \'' + name + '\' unit B mklabel \'' +
                   parttable + '\' && echo Completed.', linger=True,
                   msg='Creating partition table...')

    def _action_part(self, name, start, end, fstype):
        self._exec('parted -m -s \'' + name.split('*')[1] +
                   '\' unit \'' + self.part_granularity_unit + '\' mkpart primary \'' +
                   fstype + '\' \'' + str(start) + '\' \'' + str(end) + '\' ' +
                   '&& echo Completed.', linger=True,
                   msg='Creating new partition...')

    def _action_refresh(self, name):
        pass

    def _action_remove(self, name):
        disk = self.get_disk_from_part(name)
        num = self.get_num_from_part(name)
        self._exec('parted -m -s \'' + disk + '\' unit B rm \'' + str(num)
                   + '\' && echo Completed.', linger=True,
                   msg='Removing partition...')

    def _action_swap_target(self, name):
        self.swap_target = name
        self._msgbox(_('Successful.'))

    def _add_disk_to_menu(self, menu, pref, name, item, size, *args, **kwargs):
        menu.append(PartitionMenuItem(
            name=name,
            size=size,
            text=pref + name,
            size_text=self._format_size(size),
            details_text=_('Size: ') + self._format_size(size) + '\n' +
            _('Partitioning: ') +
            (item['parttable'] if 'parttable' in item and item['parttable']
             is not None else _('unknown')),
            ops=['autosetup', 'parttable']
        ))

    def _add_free_space_to_menu(
            self, menu, pref, parent_name, start, end, *args, **kwargs):

        gran_start = self._to_gran_start(start)
        gran_end = self._to_gran_end(end)
        if gran_start <= 0:
            gran_start = 1
        if gran_end < gran_start:
            return

        start_str = str(gran_start) + self.part_granularity_unit
        end_str = str(gran_end) + self.part_granularity_unit

        menu.append(PartitionMenuItem(
            name='*' + parent_name + '*' + start_str + '*' + end_str,
            size=end - start + 1,
            text=pref + _('Free Space'),
            size_text=self._format_size(end - start + 1),
            details_text=_('Size: ') + self._format_size(end - start + 1) + '\n' +
            _('Start: ') + str(start) + '\n' +
            _('End: ') + str(end),
            ops=['part']
        ))

    def _add_other_to_menu(self, menu, pref, name, item, size, *args, **kwargs):
        menu.append(PartitionMenuItem(
            name=name,
            size=size,
            text=pref + name,
            size_text=self._format_size(size),
            details_text=_('Size: ') + self._format_size(size) + '\n' +
            _('Filesystem: ') +
            (item['fstype'] if 'fstype' in item and item['fstype']
             is not None else _('unknown')),
            ops=['format', 'boot-target', 'install-target',
                 'swap-target', 'cryptclose', 'swap-cryptclose']
        ))

    def _add_options_to_menu(self, menu, *args, **kwargs):
        menu.append(PartitionMenuItem(
            name='*show-targets',
            text=_('Show Configured Targets'),
            details_text=_('Boot target: ') + self.boot_target + '\n' +
            _('Main encryption target: ') + self.crypt_target + '\n' +
            _('Main installation target: ') + self.install_target + '\n' +
            _('Swap encryption target: ') + self.swap_crypt_target + '\n' +
            _('Swap target: ') + self.swap_target,
            ops=['clear-boot-target', 'clear-crypt-target',
                 'clear-install-target', 'clear-swap-crypt-target',
                 'clear-swap-target']
        ))
        menu.append(PartitionMenuItem(
            name='*refresh',
            text=_('Refresh'),
            ops=['refresh']
        ))

    def _add_part_to_menu(self, menu, pref, name, item, size, *args, **kwargs):
        menu.append(PartitionMenuItem(
            name=name,
            size=size,
            text=pref + name,
            size_text=self._format_size(size),
            details_text=_('Size: ') + self._format_size(size) + '\n' +
            _('Filesystem: ') +
            (item['fstype'] if 'fstype' in item and item['fstype'] is not None else _('unknown')) + '\n' +
            _('Flags: ') +
            (item['flags'] if 'flags' in item and item['flags'] is not None else '') + '\n' +
            _('Start: ') +
            (item['start'] if 'start' in item and item['start'] is not None else _('unknown')) + '\n' +
            _('End: ') +
            (item['end'] if 'end' in item and item['end']
             is not None else _('unknown')),
            ops=['boot', 'format', 'boot-target', 'install-target',
                 'swap-target', 'remove', 'cryptsetup', 'cryptopen',
                 'swap-cryptopen']
        ))

    def _exec(self, cmd, msg='', **kwargs):
        if not gui.started:
            ai_dialog_exec(cmd, msg=msg, **kwargs)
        else:
            from partition_gui import partition_gui
            p = ai_popen(
                cmd,
                stdin=subprocess.DEVNULL,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                universal_newlines=True
            )
            partition_gui.add_log_lib(msg)
            partition_gui.add_log_lib('- ' + cmd)
            for x in p.stdout:
                partition_gui.add_log_lib(x.rstrip('\n'))

    def _format_size(self, size):
        units = ['B', 'KB', 'MB', 'GB', 'TB', 'PB']
        for x in units[:-1]:
            if size < self.base:
                return str(size) + ' ' + x
            size //= self.base
        return str(size) + ' ' + units[-1]

    def _get_layout_menu_noscan(self, parts=None, parent=None, level=0):
        if parts is None:
            parts = self.parts

        l = []
        last = -1
        pref = '    ' * level
        has_special_type = False

        for x in parts:
            start = 0
            if 'start' in x and x['start'] is not None:
                start = int(x['start'])

            if start > last + 1:
                self._add_free_space_to_menu(menu=l, pref=pref,
                                             parent_name=parent['name'], start=last + 1,
                                             end=start - 1)

            add_to_menu_func = self._add_other_to_menu
            if x['type'] == 'disk':
                add_to_menu_func = self._add_disk_to_menu
            elif x['type'] == 'part':
                add_to_menu_func = self._add_part_to_menu
            else:
                has_special_type = True

            add_to_menu_func(
                menu=l, pref=pref, name=x['name'], item=x,
                size=int(x['size']) if 'size' in x else 0)

            if 'children' in x:
                l += self._get_layout_menu_noscan(
                    parts=x['children'], parent=x, level=level + 1)
            elif level == 0 and 'parttable' in x and x['parttable'] is not None \
                    and x['parttable'] != 'unknown':
                # always consider a toplevel with a known partition table
                # to possibly have free space
                l += self._get_layout_menu_noscan(
                    parts=[], parent=x, level=level + 1)

            if 'end' in x:
                last = max(last, int(x['end']))

        if parent is not None and 'size' in parent and not has_special_type:
            parent_size = int(parent['size'])
            if parent_size > last + 1:
                self._add_free_space_to_menu(menu=l, pref=pref,
                                             parent_name=parent['name'], start=last + 1,
                                             end=parent_size - 1)

        if level == 0:
            self._add_options_to_menu(menu=l)

        return l

    def _msgbox(self, text):
        if not gui.started:
            dialog.msgbox(text)
        else:
            event = threading.Event()

            def show():
                from gi.repository import Gtk
                dialog2 = Gtk.MessageDialog(
                    gui.window,
                    Gtk.DialogFlags.DESTROY_WITH_PARENT,
                    Gtk.MessageType.INFO,
                    Gtk.ButtonsType.CLOSE,
                    text
                )
                dialog2.run()
                dialog2.destroy()
                event.set()
            gui.idle_add(show)
            event.wait()

    def _to_gran_end(self, x):
        return x // self.part_granularity

    def _to_gran_start(self, x):
        return (x + self.part_granularity - 1) // self.part_granularity

    def _convert_start_end_to_str(self, p):
        for x in p:
            if 'children' in x:
                self._convert_start_end_to_str(x['children'])
            if 'start' in x and isinstance(x['start'], int):
                x['start'] = str(x['start'])
            if 'end' in x and isinstance(x['end'], int):
                x['end'] = str(x['end'])

    def _remove_toplevel_mounted(self, p):
        rm = []
        for x in p:
            if 'mountpoint' in x and x['mountpoint'] is not None:
                rm.append(x)
        for x in rm:
            p.remove(x)

    def _scan_for_details(self, p):
        for x in p:
            if 'children' in x:
                self._scan_for_details(x['children'])

            __, layout = ai_call(
                'parted -m -s \'' + x['name'] + '\' unit B print')
            # sometimes parted returns error, but with useful information

            layout = layout.decode('utf-8').split('\n')

            if len(layout) <= 1:
                continue
            info = layout[1].split(':')
            if len(info) >= 6:
                x['parttable'] = info[5]

            if 'children' not in x or (not x['children']):
                continue

            if len(layout) <= 2:
                continue
            layout = layout[2:]

            part_map = {}
            for y in layout:
                if not y:
                    continue
                info = y[:-1].split(':')
                if len(info) < 7:
                    continue
                if (not info[1]) or (not info[2]):
                    continue
                part = self.get_part_from_disk_num(x['name'], info[0])
                info[1] = info[1][:-1]
                info[2] = info[2][:-1]
                part_map[part] = (info[1], info[2], info[6])

            for y in x['children']:
                name = y['name']
                if name in part_map:
                    y['start'], y['end'], y['flags'] = part_map[name]

    def _sort_parts(self, parts):
        parts.sort(key=lambda x: 0 if ('start' not in x or x['start'] is None) else int(x['start']))

        for x in parts:
            if 'children' in x:
                self._sort_parts(x['children'])

    def _scan_for_all_disks(self):
        ret, p = ai_call('lsblk -b -J -O -p')
        if ret != 0:
            raise RuntimeError('lsblk failed')
        p = json.loads(p)['blockdevices']
        self._convert_start_end_to_str(p)
        self._remove_toplevel_mounted(p)
        self._scan_for_details(p)
        self._sort_parts(p)
        self.parts = p
        self.scanned = True

    def action(self, op, name, *args, **kwargs):
        if op == 'autosetup':
            self._action_autosetup(name, *args, **kwargs)
        elif op == 'parttable':
            self._action_parttable(name, *args, **kwargs)
        elif op == 'part':
            self._action_part(name, *args, **kwargs)
        elif op == 'format':
            self._action_format(name, *args, **kwargs)
        elif op == 'boot':
            self._action_boot(name, *args, **kwargs)
        elif op == 'boot-target':
            self._action_boot_target(name, *args, **kwargs)
        elif op == 'install-target':
            self._action_install_target(name, *args, **kwargs)
        elif op == 'swap-target':
            self._action_swap_target(name, *args, **kwargs)
        elif op == 'remove':
            self._action_remove(name, *args, **kwargs)
        elif op == 'cryptsetup':
            self._action_cryptsetup(name, *args, **kwargs)
        elif op == 'cryptopen':
            self._action_cryptopen(name, *args, **kwargs)
        elif op == 'cryptclose':
            self._action_cryptclose(name, *args, **kwargs)
        elif op == 'swap-cryptopen':
            self._action_swap_cryptopen(name, *args, **kwargs)
        elif op == 'swap-cryptclose':
            self._action_swap_cryptclose(name, *args, **kwargs)
        elif op == 'clear-boot-target':
            self._action_clear_boot_target(name, *args, **kwargs)
        elif op == 'clear-crypt-target':
            self._action_clear_crypt_target(name, *args, **kwargs)
        elif op == 'clear-install-target':
            self._action_clear_install_target(name, *args, **kwargs)
        elif op == 'clear-swap-crypt-target':
            self._action_clear_swap_crypt_target(name, *args, **kwargs)
        elif op == 'clear-swap-target':
            self._action_clear_swap_target(name, *args, **kwargs)
        elif op == 'refresh':
            self._action_refresh(name, *args, **kwargs)

    def get_disk_from_part(self, name):
        i = len(name)
        if i == 0:
            return ''
        i -= 1
        while i >= 0 and name[i].isdigit():
            i -= 1
        if name.startswith('/dev/nvme'):
            return name[:i]
        return name[:i + 1]

    def get_layout_menu(self, scan=False):
        if scan:
            self.scan()
        return self._get_layout_menu_noscan()

    def get_num_from_part(self, name):
        i = len(name)
        if i == 0:
            return 0
        i -= 1
        if not name[i].isdigit():
            return 0
        while i >= 0 and name[i].isdigit():
            i -= 1
        return int(name[i + 1:])

    def get_part_from_disk_num(self, disk, num):
        if disk.startswith('/dev/nvme'):
            return disk + 'p' + str(num)
        return disk + str(num)

    def get_text_for_op(self, op):
        if op == 'autosetup':
            return _('Automatically Set Up This Disk')
        if op == 'parttable':
            return _('Create/Rewrite Partition Table')
        if op == 'part':
            return _('Create New Partition')
        if op == 'format':
            return _('Format Selected Partition')
        if op == 'boot':
            return _('Toggle Boot Flag')
        if op == 'boot-target':
            return _('Select as Boot Target')
        if op == 'install-target':
            return _('Select as Main Installation Target')
        if op == 'swap-target':
            return _('Select as Swap Target')
        if op == 'remove':
            return _('Remove Selected Partition')
        if op == 'cryptsetup':
            return _('Set Up Encryption')
        if op == 'cryptopen':
            return _('Open Main Encrypted Partition')
        if op == 'cryptclose':
            return _('Close Main Encrypted Block')
        if op == 'swap-cryptopen':
            return _('Open Swap Encrypted Partition')
        if op == 'swap-cryptclose':
            return _('Close Swap Encrypted Block')
        if op == 'clear-boot-target':
            return _('Clear Boot Target')
        if op == 'clear-crypt-target':
            return _('Clear Main Encryption Target')
        if op == 'clear-install-target':
            return _('Clear Main Installation Target')
        if op == 'clear-swap-crypt-target':
            return _('Clear Swap Encryption Target')
        if op == 'clear-swap-target':
            return _('Clear Swap Target')
        if op == 'refresh':
            return _('Refresh Partition List')
        return op

    def scan(self):
        self._scan_for_all_disks()


partition_lib = PartitionLib()

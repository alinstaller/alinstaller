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

from ai_exec import ai_call
from hostname_lib import hostname_lib
from partition_lib import partition_lib
from password_lib import password_lib
from set_font_lib import set_font_lib
from set_keymap_lib import set_keymap_lib

class InstallLib(object):
    mirror_kw = ['https:', '.kernel.org']
    mirror_multiply = 10

    def get_init_dirs_cmd(self):
        cmd = 'true'

        if partition_lib.swap_target != '':
            cmd += ' && swapon \"' + partition_lib.swap_target + '\"'
        cmd += ' && mount \"' + partition_lib.install_target + '\" /mnt'
        cmd += ' && mkdir -p /mnt/boot'
        if partition_lib.boot_target != '':
            cmd += ' && mount \"' + partition_lib.boot_target + '\" /mnt/boot'

        return cmd

    def get_copy_files_cmd(self):
        cmd = 'rsync --info=progress2 --no-inc-recursive -ax /run/archiso/sfs/airootfs/* /mnt'
        cmd += ' && rm -rf /mnt/root/*'
        cmd += ' && rm -rf /mnt/usr/local/{bin,lib}/*'
        cmd += ' && rm -rf /mnt/usr/local/share/{applications,locale}'
        cmd += ' && rm -rf /mnt/tmp/*'
        cmd += ' && cp -aT /run/archiso/bootmnt/arch/boot/$(uname -m)/vmlinuz /mnt/boot/vmlinuz-linux'
        cmd += ' && cp -aT /usr/local/lib/alinstaller/vmlinuz-linux-zen /mnt/boot/vmlinuz-linux-zen'

        return cmd

    def update_mirrorlist(self):
        l = []; fn = '/mnt/etc/pacman.d/mirrorlist'

        with open(fn, 'r') as f:
            for x in f:
                x = x.strip('\n')

                if x == '':
                    l.append(''); continue
                elif x.startswith('#Server'):
                    x = x[1:]
                elif x.startswith('#'):
                    l.append(x); continue

                is_mirror = True
                for y in self.mirror_kw:
                    if not y in x:
                        is_mirror = False; break

                if is_mirror:
                    l = [x] * self.mirror_multiply + [''] + l

                x = '#' + x
                l.append(x)

        with open('/tmp/mirrorlist', 'w') as f:
            for x in l:
                f.write(x + '\n')

        ai_call('mv /tmp/mirrorlist \"' + fn + '\"')

    def get_configure_cmd(self):
        cmd = 'genfstab -U /mnt > /mnt/etc/fstab'
        cmd += ' && sed -i \'s/Storage=volatile/#Storage=auto/\' /mnt/etc/systemd/journald.conf'
        cmd += ' && sed -i \'s/^\(PermitRootLogin \).\+/#\\1prohibit-password/\' /mnt/etc/ssh/sshd_config'
        cmd += ' && sed -i \'s/\(HandleSuspendKey=\)ignore/#\\1suspend/\' /mnt/etc/systemd/logind.conf'
        cmd += ' && sed -i \'s/\(HandleHibernateKey=\)ignore/#\\1hibernate/\' /mnt/etc/systemd/logind.conf'
        cmd += ' && rm -f /mnt/etc/udev/rules.d/81-dhcpcd.rules'

        cmd += ' && cp /tmp/password /mnt/password'

        cmd += ' && arch-chroot /mnt /bin/bash -c \''

        cmd += 'systemctl disable pacman-init.service choose-mirror.service'
        cmd += ' && rm -rf /etc/systemd/system/{choose-mirror.service,pacman-init.service,etc-pacman.d-gnupg.mount,getty@tty1.service.d}'
        cmd += ' && rm -f /etc/systemd/scripts/choose-mirror'
        cmd += ' && rm -f /etc/systemd/system/archiso-start.service'
        cmd += ' && rm -f /etc/systemd/system/multi-user.target.wants/archiso-start.service'

        cmd += ' && rm -f /etc/systemd/system/getty@tty1.service.d/autologin.conf'
        cmd += ' && rm -f /root/{.automated_script.sh,.zlogin}'
        cmd += ' && rm -f /etc/mkinitcpio-archiso.conf'
        cmd += ' && rm -rf /etc/initcpio'

        cmd += ' && pacman-key --init'
        cmd += ' && pacman-key --populate archlinux'

        cmd += ' && echo LANG=en_US.UTF-8 > /etc/locale.conf'

        swap_uuid = ''
        if partition_lib.swap_target != '':
            res, swap_uuid = ai_call('blkid -s UUID -o value \"' +
                partition_lib.swap_target + '\"')
            swap_uuid = swap_uuid.decode('utf-8').strip('\n')
        crypt_uuid = ''
        if partition_lib.crypt_target != '':
            res, crypt_uuid = ai_call('blkid -s UUID -o value \"' +
                partition_lib.crypt_target + '\"')
            crypt_uuid = crypt_uuid.decode('utf-8').strip('\n')

        cmd += ' && sed -i \"s/^\\\\(GRUB_CMDLINE_LINUX_DEFAULT=\\\\).*/\\1\\\"quiet'
        if swap_uuid != '':
            cmd += ' resume=UUID=' + swap_uuid
        if crypt_uuid != '':
            cmd += ' cryptdevice=UUID=' + crypt_uuid + \
                ':cryptroot root=\\/dev\\/mapper\\/cryptroot'
        cmd += '\\\"/\" /etc/default/grub'

        if partition_lib.crypt_target == '':
            cmd += ' && sed -i \"s/^\\\\(HOOKS=\\\\).*/\\1(base udev resume' + \
                ' autodetect modconf keyboard keymap block filesystems' + \
                ' keyboard fsck)/\" /etc/mkinitcpio.conf'
        else:
            cmd += ' && sed -i \"s/^\\\\(HOOKS=\\\\).*/\\1(base udev resume' + \
                ' autodetect modconf keyboard keymap block encrypt' + \
                ' filesystems keyboard fsck)/\" /etc/mkinitcpio.conf'

        cmd += ' && mkinitcpio -p linux'
        cmd += ' && mkinitcpio -p linux-zen'

        grub_i386_target = ''
        if partition_lib.boot_target != '':
            grub_i386_target = partition_lib.boot_target
        elif partition_lib.crypt_target != '':
            grub_i386_target = partition_lib.crypt_target
        else:
            grub_i386_target = partition_lib.install_target

        grub_i386_target = partition_lib.get_disk_from_part(grub_i386_target)

        cmd += ' && (grub-install --target=i386-pc \"' + grub_i386_target + \
            '\" || true)'

        cmd += ' && (grub-install --target=x86_64-efi --efi-directory=/boot' + \
            ' --bootloader-id=grub || true)'

        cmd += ' && grub-mkconfig -o /boot/grub/grub.cfg'

        cmd += ' && true > /etc/vconsole.conf'
        if set_font_lib.font != '':
            cmd += ' && echo \"FONT=' + set_font_lib.font + '\" >> /etc/vconsole.conf'
        if set_keymap_lib.keymap != '':
            cmd += ' && echo \"KEYMAP=' + set_keymap_lib.keymap + '\" >> /etc/vconsole.conf'

        cmd += ' && echo \"' + hostname_lib.hostname + '\" > /etc/hostname'
        cmd += ' && echo 127.0.0.1 localhost > /etc/hosts'
        cmd += ' && echo ::1 localhost >> /etc/hosts'

        cmd += ' && echo vm.swappiness=0 > /etc/sysctl.d/99-sysctl.conf'

        cmd += ' && cat /password | chpasswd'
        cmd += ' && rm -f /password'

        cmd += ' && systemctl disable multi-user.target'
        cmd += ' && systemctl set-default graphical.target'
        cmd += ' && systemctl enable NetworkManager bluetooth firewalld' + \
            ' gdm lvm2-monitor org.cups.cupsd spice-vdagentd upower'

        cmd += '\''

        cmd += ' && rm -f /tmp/password'
        cmd += ' && umount -R /mnt'

        cmd += ' && echo && echo Completed.'

        return cmd

    def prepare_configure(self):
        with open('/tmp/password', 'w') as f:
            f.write('root:' + password_lib.password)

    def cleanup_configure(self):
        ai_call('rm -f /mnt/password')
        try:
            os.remove('/tmp/password')
        except: pass

install_lib = InstallLib()

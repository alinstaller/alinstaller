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
from vconsole_lib import vconsole_lib


class InstallLib():
    def get_init_dirs_cmd(self):
        cmd = 'true'

        if partition_lib.swap_target != '':
            cmd += ' && swapon \'' + partition_lib.swap_target + '\''
        cmd += ' && mount \'' + partition_lib.install_target + '\' /mnt'
        cmd += ' && mkdir -p /mnt/boot'
        if partition_lib.boot_target != '':
            cmd += ' && mount \'' + partition_lib.boot_target + '\' /mnt/boot'

        return cmd

    def get_copy_files_cmd(self):
        cmd = 'rsync --info=progress2 --no-inc-recursive -ax --exclude=/boot --exclude=\"/root/*\"' + \
            ' --exclude=\"/usr/local/bin/*\" --exclude=\"/usr/local/lib/*\"' + \
            ' --exclude=/usr/local/share/applications --exclude=/usr/local/share/locale' + \
            ' --exclude=\"/tmp/*\" /run/archiso/sfs/airootfs/* /mnt'
        cmd += ' && rm -rf /mnt/tmp/*'
        cmd += ' && cp -a /usr/local/lib/alinstaller/boot-copy/* /mnt/boot'
        cmd += ' && cp -aT /run/archiso/bootmnt/arch/boot/$(uname -m)/vmlinuz /mnt/boot/vmlinuz-linux'

        return cmd

    def get_configure_cmd(self):
        cmd = 'genfstab -U /mnt > /mnt/etc/fstab'

        cmd += ' && sed -i \'s/Storage=volatile/#Storage=auto/\' /mnt/etc/systemd/journald.conf'
        cmd += ' && sed -i \'s/^\\(PermitRootLogin \\).\\+/#\\1prohibit-password/\' /mnt/etc/ssh/sshd_config'
        cmd += ' && sed -i \'s/\\(HandleSuspendKey=\\)ignore/#\\1suspend/\' /mnt/etc/systemd/logind.conf'
        cmd += ' && sed -i \'s/\\(HandleHibernateKey=\\)ignore/#\\1hibernate/\' /mnt/etc/systemd/logind.conf'
        cmd += ' && sed -i \'s/\\(HandleLidSwitch=\\)ignore/#\\1suspend/\' /mnt/etc/systemd/logind.conf'

        cmd += ' && echo \'\' >> /mnt/etc/sudoers'
        cmd += ' && echo \'%wheel ALL=(ALL) ALL\' >> /mnt/etc/sudoers'

        cmd += ' && echo \'' + \
            hostname_lib.hostname.replace('\'', '') + \
            '\' > /mnt/etc/hostname'

        cmd += ' && arch-chroot /mnt /bin/bash -c \''

        cmd += 'systemctl disable pacman-init.service choose-mirror.service'
        cmd += ' && rm -rf /etc/systemd/system/{choose-mirror.service,pacman-init.service,etc-pacman.d-gnupg.mount,getty@tty1.service.d}'
        cmd += ' && rm -f /etc/systemd/scripts/choose-mirror'
        cmd += ' && rm -f /etc/systemd/system/archiso-start.service'
        cmd += ' && rm -f /etc/systemd/system/multi-user.target.wants/archiso-start.service'

        cmd += ' && rm -f /etc/systemd/system/getty@tty1.service.d/autologin.conf'
        cmd += ' && rm -f /root/{.automated_script.sh,.zlogin,.zshrc}'
        cmd += ' && rm -f /etc/mkinitcpio-archiso.conf'
        cmd += ' && rm -rf /etc/initcpio'

        cmd += ' && pacman-key --init'
        cmd += ' && pacman-key --populate archlinux'

        cmd += ' && chsh -s /bin/bash'

        cmd += ' && pacman -Rs --noconfirm --noprogressbar memtest86+ syslinux'
        cmd += ' && pacman -Rsc --noconfirm --noprogressbar zsh'
        cmd += ' && rm -f /var/log/pacman.log'

        cmd += ' && echo LANG=en_US.UTF-8 > /etc/locale.conf'

        cmd += ' && true > /etc/vconsole.conf'
        if vconsole_lib.get_font_full() != '':
            cmd += ' && echo \"FONT=' + vconsole_lib.get_font_full() + '\" >> /etc/vconsole.conf'
        if vconsole_lib.get_keymap_full() != '':
            cmd += ' && echo \"KEYMAP=' + vconsole_lib.get_keymap_full() + '\" >> /etc/vconsole.conf'

        swap_uuid = ''
        if partition_lib.swap_target != '':
            __, swap_uuid = ai_call('blkid -s UUID -o value \'' +
                                    partition_lib.swap_target + '\'')
            swap_uuid = swap_uuid.decode('utf-8').strip('\n')
        crypt_uuid = ''
        if partition_lib.crypt_target != '':
            __, crypt_uuid = ai_call('blkid -s UUID -o value \'' +
                                     partition_lib.crypt_target + '\'')
            crypt_uuid = crypt_uuid.decode('utf-8').strip('\n')
        swap_crypt_uuid = ''
        if partition_lib.swap_crypt_target != '':
            __, swap_crypt_uuid = ai_call('blkid -s UUID -o value \'' +
                                          partition_lib.swap_crypt_target + '\'')
            swap_crypt_uuid = swap_crypt_uuid.decode('utf-8').strip('\n')

        cmd += ' && sed -i \"s/^\\\\(GRUB_CMDLINE_LINUX_DEFAULT=\\\\).*/\\1\\\"loglevel=3 quiet'
        if swap_crypt_uuid != '':
            cmd += ' rd.luks.name=' + swap_crypt_uuid + '=swap'
        if swap_uuid != '':
            cmd += ' resume=UUID=' + swap_uuid
        if crypt_uuid != '':
            cmd += ' rd.luks.name=' + crypt_uuid + '=cryptroot' + \
                ' root=\\/dev\\/mapper\\/cryptroot'
        cmd += '\\\"/\" /etc/default/grub'

        cmd += ' && sed -i \"s/^\\\\(HOOKS=\\\\).*/\\1(base systemd' + \
            ' keyboard autodetect sd-vconsole modconf block sd-encrypt' + \
            ' filesystems fsck)/\" /etc/mkinitcpio.conf'

        cmd += ' && mkinitcpio -P'

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

        cmd += ' && echo 127.0.0.1 localhost > /etc/hosts'
        cmd += ' && echo ::1 localhost >> /etc/hosts'

        cmd += ' && systemctl disable multi-user.target'
        cmd += ' && systemctl set-default graphical.target'
        cmd += ' && systemctl enable NetworkManager firewalld gdm'

        cmd += ' && (systemctl enable avahi-daemon || true)'
        cmd += ' && (systemctl enable bluetooth || true)'
        cmd += ' && (systemctl enable lvm2-monitor || true)'
        cmd += ' && (systemctl enable org.cups.cupsd || true)'
        cmd += ' && (systemctl enable spice-vdagentd || true)'
        cmd += ' && (systemctl enable systemd-resolved || true)'
        cmd += ' && (systemctl enable upower || true)'

        cmd += ' && (systemctl --global enable pipewire || true)'

        # reenable pacman CheckSpace
        cmd += ' && sed -i "/# We cannot check disk space from within a chroot environment/d" /etc/pacman.conf'
        cmd += ' && sed -i "s/^#CheckSpace$/CheckSpace/" /etc/pacman.conf'

        # disable root login
        cmd += ' && passwd -l root'

        cmd += '\''

        cmd += ' && umount -R /mnt'
        if partition_lib.swap_target != '':
            cmd += ' && swapoff \'' + partition_lib.swap_target + '\''
        if partition_lib.crypt_target != '':
            cmd += ' && cryptsetup close /dev/mapper/cryptroot'
        if partition_lib.swap_crypt_target != '':
            cmd += ' && cryptsetup close /dev/mapper/swap'

        cmd += ' && echo && echo Completed.'

        return cmd


install_lib = InstallLib()

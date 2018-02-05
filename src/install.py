#!/bin/env python3

import os
import subprocess

from ai_exec import ai_call, ai_exec
from dlg import dialog
from partition_lib import partition_lib
from step import Step

class Install(Step):
    def run_once(self):
        res = dialog.yesno('We are ready to install Arch Linux.\n' +
            'Begin installing now?',
            width = 50, height = 6)
        if res != dialog.OK: return False

        res = _do_install()

        if res == 0:
            dialog.msgbox('Installation completed.\n' +
                'Your system is going to be restarted.',
                width = 50, height = 6)
        else:
            dialog.msgbox('Installation failed.\n' +
                'Your system is going to be restarted.',
                width = 50, height = 6)

        ai_exec('reboot', msg = 'Restarting...')
        os.exit(res)

    def _do_install(self):
        from env_set_font import env_set_font
        from env_set_keymap import env_set_keymap
        from hostname import hostname
        from password import password

        # initialize directories

        cmd = 'true'

        if partition_lib.swap_target != '':
            cmd += ' && swapon \"' + partition_lib.swap_target + '\"'
        cmd += ' && mount \"' + partition_lib.install_target + '\" /mnt'
        cmd += ' && mkdir -p /mnt/boot'
        if partition_lib.boot_target != '':
            cmd += ' && mount \"' + partition_lib.boot_target + '\" /mnt/boot'

        res = ai_exec(cmd, msg = 'Initializing directories...', showcmd = False)
        if res != 0: return res

        # copy files

        cmd = 'rsync --info=progress2 -ax / /mnt'
        cmd += ' && rm -rf /mnt/root/*'
        cmd += ' && cp -aT /run/archiso/bootmnt/arch/boot/$(uname -m)/vmlinuz /mnt/boot/vmlinuz-linux'
        cmd += ' && cp -aT /root/vmlinuz-linux-zen /mnt/boot/vmlinuz-linux-zen'

        dialog.gauge_start('Copying files...')

        p = subprocess.Popen(cmd, shell=True, stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
            universal_newlines=True)
        for x in p.stdout:
            x = x.split()
            if len(x) >= 2 and x[1].endswith('%'):
                percent = int(x[1][:-1])
                dialog.gauge_update(percent)

        p.communicate()
        dialog.gauge_stop()
        if p.returncode != 0: return p.returncode

        # configure

        cmd = 'genfstab -U /mnt > /mnt/etc/fstab'
        cmd += ' && sed -i \'s/Storage=volatile/#Storage=auto/\' /mnt/etc/systemd/journald.conf'
        cmd += ' && sed -i \'s/^\(PermitRootLogin \).\+/#\\1prohibit-password/\' /mnt/etc/ssh/sshd_config'
        cmd += ' && sed -i \'s/\(HandleSuspendKey=\)ignore/#\\1suspend/\' /etc/systemd/logind.conf'
        cmd += ' && sed -i \'s/\(HandleHibernateKey=\)ignore/#\\1hibernate/\' /etc/systemd/logind.conf'
        cmd += ' && rm -f /mnt/etc/udev/rules.d/81-dhcpcd.rules'

        cmd += ' && cp password /mnt/password'

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

        cmd += ' && sed -i \"s/^#\\\\([A-Za-z].* UTF-8\\\\)/\\\\1/\" /etc/locale.gen'
        cmd += ' && locale-gen'
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

        cmd += ' && sed -i \"s/^\\\\(HOOKS=\\\\).*/\\1(base udev resume' + \
            ' autodetect modconf keyboard keymap block encrypt filesystems' + \
            ' keyboard fsck)/\" /etc/mkinitcpio.conf'

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

        cmd += ' && grub-install --target=i386-pc \"' + grub_i386_target + '\"'

        cmd += ' && grub-install --target=x86_64-efi --efi-directory=/boot' + \
            ' --bootloader-id=grub'

        cmd += ' && grub-mkconfig -o /boot/grub/grub.cfg'

        cmd += ' && true > /etc/vconsole.conf'
        if env_set_font.font != '':
            cmd += ' && echo \"FONT=' + env_set_font.font + '\" >> /etc/vconsole.conf'
        if env_set_keymap.keymap != '':
            cmd += ' && echo \"KEYMAP=' + env_set_keymap.keymap + '\" >> /etc/vconsole.conf'

        cmd += ' && echo \"' + hostname.hostname + '\" > /etc/hostname'
        cmd += ' && echo 127.0.0.1 localhost > /etc/hosts'
        cmd += ' && echo ::1 localhost > /etc/hosts'

        cmd += ' && echo vm.swappiness=0 > /etc/sysctl.d/99-sysctl.conf'

        cmd += ' && cat /password | chpasswd'
        cmd += ' && rm -f /password'

        cmd += ' && systemctl disable multi-user.target'
        cmd += ' && systemctl enable graphical.target'
        cmd += ' && systemctl enable NetworkManager bluetooth firewalld' + \
            ' gdm org.cups.cupsd'

        cmd += '\''

        cmd += ' && rm -f password'
        cmd += ' && umount -R /mnt'

        cmd += ' && echo && echo Completed.'

        with open('password', 'w') as f:
            f.write('root:' + password.password)

        res = ai_exec(cmd, linger = True, msg = 'Configuring...',
            width = 75, height = 20, showcmd = False)

        try:
            os.remove('/mnt/password')
            os.remove('password')
        except: pass

        return res

install = Install()

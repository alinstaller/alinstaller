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

# choose a mirror
python << EOF

import os

mirror_kw = ['https:', '.kernel.org']
mirror_multiply = 10

l = []
filename = '/etc/pacman.d/mirrorlist'

with open(filename, 'r') as f:
    for x in f:
        x = x.strip('\n')

        if x == '':
            l.append('')
            continue
        elif x.startswith('#Server'):
            x = x[1:]
        elif x.startswith('#'):
            l.append(x)
            continue

        is_mirror = True
        for y in mirror_kw:
            if y not in x:
                is_mirror = False
                break

        if is_mirror:
            l = [x] * mirror_multiply + [''] + l

        x = '#' + x
        l.append(x)

with open('/tmp/alinstaller-mirrorlist', 'w') as f:
    for x in l:
        f.write(x + '\n')

os.system('mv /tmp/alinstaller-mirrorlist \'' + filename + '\'')

EOF

# backup /boot
cp -ax /boot /usr/local/lib/alinstaller/boot-copy
rm -rf /usr/local/lib/alinstaller/boot-copy/{archiso.img,initramfs-*.img,memtest86+,syslinux,vmlinuz-linux}

# mark update as done to reduce boot time
/usr/lib/systemd/systemd-update-done

# fix gnome-initial-setup not in pam config of gdm
sed -i 's/user = gdm/user in gdm:gnome-initial-setup/g' /etc/pam.d/gdm-launch-environment

# still allow the user to upgrade the pam config
gdm_files=/var/lib/pacman/local/`pacman -Q gdm | sed 's/ /-/'`/files
sed -i -E "s|^(etc/pam.d/gdm-launch-environment).+$|\1\t$(md5sum /etc/pam.d/gdm-launch-environment | sed -E 's| .+||')|" $gdm_files
unset gdm_files

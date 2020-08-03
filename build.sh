#!/bin/bash

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

set -e

mkdir -p build
rm -rf build/airootfs
cp -r /usr/share/archiso/configs/releng/* build

pushd build/airootfs/etc > /dev/null
find . \
    ! -path '.' \
    ! -path './locale.conf' \
    ! -path './localtime' \
    ! -path './machine-id' \
    ! -path './mkinitcpio.conf' \
    ! -path './mkinitcpio.d' \
    ! -path './mkinitcpio.d/linux.preset' \
    ! -path './modprobe.d' \
    ! -path './modprobe.d/broadcom-wl.conf' \
    ! -path './shadow' \
    ! -path './systemd' \
    ! -path './systemd/journald.conf.d' \
    ! -path './systemd/journald.conf.d/*' \
    ! -path './systemd/logind.conf.d' \
    ! -path './systemd/logind.conf.d/*' \
    ! -path './systemd/system' \
    ! -path './systemd/system/dbus-org.freedesktop.resolve1.service' \
    ! -path './systemd/system/etc-pacman.d-gnupg.mount' \
    ! -path './systemd/system/getty@tty1.service.d' \
    ! -path './systemd/system/getty@tty1.service.d/*' \
    ! -path './systemd/system/multi-user.target.wants' \
    ! -path './systemd/system/multi-user.target.wants/pacman-init.service' \
    ! -path './systemd/system/multi-user.target.wants/systemd-resolved.service' \
    ! -path './systemd/system/pacman-init.service' \
    -delete
popd > /dev/null

mkdir -p build/airootfs/usr/local/bin
mkdir -p build/airootfs/usr/local/lib/alinstaller
mkdir -p build/airootfs/usr/local/share/{applications,locale}

cp src/{*.py,*.glade,*.txt} build/airootfs/usr/local/lib/alinstaller
cp misc/alinstaller build/airootfs/usr/local/bin/alinstaller
cp misc/pacman-init.service build/airootfs/etc/systemd/system/pacman-init.service
cp misc/*.desktop build/airootfs/usr/local/share/applications

./install-locale.sh build/airootfs/usr/local/share

for file in build/packages.*; do
	cat misc/packages_any >> "$file"
done

mv build/airootfs/root/.zlogin build/airootfs/root/.bash_login
echo '' >> build/airootfs/root/.bash_login
cat misc/rc.sh >> build/airootfs/root/.bash_login

sed -i "s/locale-gen/sed -i 's\\/^#\\\([A-Za-z].* UTF-8\\\)\\/\\\\1\\/' \\/etc\\/locale.gen; locale-gen/" build/airootfs/root/customize_airootfs.sh
echo '' >> build/airootfs/root/customize_airootfs.sh
cat misc/customize.sh >> build/airootfs/root/customize_airootfs.sh

sed -i "s/\.archlinux\.org\/mirrorlist\/.*\'/\.archlinux\.org\/mirrorlist\/all\/\'/" build/build.sh

mkdir -p build/out
rm -f build/work/build.make_*

pushd build > /dev/null
./build.sh -v

pushd out > /dev/null
for file in archlinux-*.iso; do
	mv "$file" alinstaller.iso;
done

popd > /dev/null
popd > /dev/null

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

mkdir -p build/airootfs/usr/local/bin
mkdir -p build/airootfs/usr/local/lib/alinstaller
mkdir -p build/airootfs/usr/local/share/{applications,locale}

cp src/{*.py,*.glade,*.txt} build/airootfs/usr/local/lib/alinstaller
cp misc/alinstaller build/airootfs/usr/local/bin/alinstaller
cp misc/*.desktop build/airootfs/usr/local/share/applications

./install-locale.sh build/airootfs/usr/local/share

for file in build/packages.*; do
	cat misc/packages_any >> "$file"
done

echo '' >> build/airootfs/root/.zlogin
cat misc/rc.sh >> build/airootfs/root/.zlogin

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

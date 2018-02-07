#!/bin/bash

set -e

pacman -Sy --needed --noconfirm linux-zen

mkdir -p build
rm -rf build/airootfs
cp -r /usr/share/archiso/configs/releng/* build

mkdir -p build/airootfs/root/alinstaller
cp src/*.py build/airootfs/root/alinstaller

cat misc/packages_any >> build/packages.both
cat misc/rc.sh >> build/airootfs/root/.zlogin

# the following would enable all languages:
# sed -i "s/locale-gen/sed -i 's\\/^#\\\([A-Za-z].* UTF-8\\\)\\/\\\\1\\/' \\/etc\\/locale.gen; locale-gen/" build/airootfs/root/customize_airootfs.sh

sed -i "s/\.archlinux\.org\/mirrorlist\/.*\'/\.archlinux\.org\/mirrorlist\/all\/\'/" build/build.sh

cp -vaT /boot/vmlinuz-linux-zen build/airootfs/root/vmlinuz-linux-zen

mkdir -p build/out
rm -f build/work/build.make_*

pushd build
./build.sh -v

pushd out
for file in archlinux-*.iso; do
	mv "$file" alinstaller.iso;
done

popd
popd

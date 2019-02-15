#!/bin/bash
# Copyright (C) 2016  Mikkel Oscar Lyderik Larsen
#
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
# along with this program.  If not, see <http://www.gnu.org/licenses/>.


# Script for setting up and running a travis-ci build in an up to date
# Arch Linux chroot

ARCH_TRAVIS_ISO_MIRRORS=${ARCH_TRAVIS_ISO_MIRRORS:-"https://archive.archlinux.org"}
iso_mirrors=(${ARCH_TRAVIS_ISO_MIRRORS//,/ })
ARCH_TRAVIS_MIRRORS=${ARCH_TRAVIS_MIRRORS:-"https://mirrors.ocf.berkeley.edu/archlinux,https://mirrors.ocf.berkeley.edu/archlinux,https://mirrors.ocf.berkeley.edu/archlinux,https://mirrors.ocf.berkeley.edu/archlinux,https://mirrors.ocf.berkeley.edu/archlinux"}
mirrors=(${ARCH_TRAVIS_MIRRORS//,/ })
ARCH_TRAVIS_ARCH=${ARCH_TRAVIS_ARCH:-"x86_64"}
mirror_entry_fmt='Server = %s/\$repo/os/\$arch'
ARCH_TRAVIS_ROOT_ARCHIVE=""
default_root="root.${ARCH_TRAVIS_ARCH}"
ARCH_TRAVIS_CHROOT=${ARCH_TRAVIS_CHROOT:-"$default_root"}
user="travis"
user_home="/home/$user"
user_build_dir=$(pwd)
uid=$UID
gid=$GID

if [ -n "$CC" ]; then
  # store travis CC
  TRAVIS_CC=$CC
  # reset to gcc for building arch packages
  CC=gcc
fi

GOROOT=""


# default packages
default_packages=("fakeroot" "file" "findutils" "gawk" "gettext" "git" "grep" "gzip" "patch" "sed" "sudo" "util-linux" "which")

# try to find the latest iso by iterating through the dates of the current
# month, falling back to the last month if needed.
get_base_archive() {
  local months=(
    # $(date +%Y.%m)
    # $(date +%Y.%m -d "-1 month")
    '2017.12' # hardcoded to known good month
  )

  for mirror in "${iso_mirrors[@]}"; do
    for date in "${months[@]}"; do
        echo $date
      for i in {1..15}; do
        local iso_date="$date"
        if [ "$i" -lt 10 ]; then
          iso_date="$date.0$i"
        else
          iso_date="$date.$i"
        fi

        ARCH_TRAVIS_ROOT_ARCHIVE="archlinux-bootstrap-${iso_date}-${ARCH_TRAVIS_ARCH}.tar.gz"
        local url="$mirror/iso/$iso_date/$ARCH_TRAVIS_ROOT_ARCHIVE"

        if [ -f "$ARCH_TRAVIS_ROOT_ARCHIVE" ]; then
            return
        fi

        echo $url
        curl --fail --retry 3 -O $url 2>&1
        local ret=$?

        if [ $ret -eq 0 ]; then
          return
        fi
      done
    done
  done
}

# setup working Arch Linux chroot
setup_chroot() {
  arch_msg "Setting up Arch chroot"

  get_base_archive

  # extract root fs
  as_root "tar xf $ARCH_TRAVIS_ROOT_ARCHIVE -C $HOME"

  # remove archive if ARCH_TRAVIS_CLEAN_CHROOT is set
  if [ -n "$ARCH_TRAVIS_CLEAN_CHROOT" ]; then
    as_root "rm $ARCH_TRAVIS_ROOT_ARCHIVE"
  fi

  if [ "$ARCH_TRAVIS_CHROOT" != "$default_root" ]; then
    as_root "mv $HOME/$default_root $HOME/$ARCH_TRAVIS_CHROOT"
  fi

  ARCH_TRAVIS_CHROOT="$HOME/$ARCH_TRAVIS_CHROOT"

  # don't care for signed packages
  as_root "sed -i 's|SigLevel    = Required DatabaseOptional|SigLevel = Never|' $ARCH_TRAVIS_CHROOT/etc/pacman.conf"

  # pin systemd
  as_root "sed -i 's|#IgnorePkg   =|IgnorePkg   = systemd libsystemd systemd-libs|' $ARCH_TRAVIS_CHROOT/etc/pacman.conf"

  # add mirrors
  for mirror in "${mirrors[@]}"; do
    mirror_entry="$(printf "$mirror_entry_fmt" $mirror)"
    as_root "echo $mirror_entry >> $ARCH_TRAVIS_CHROOT/etc/pacman.d/mirrorlist"
  done

  # add nameserver to resolv.conf
  as_root "echo nameserver 8.8.8.8 >> $ARCH_TRAVIS_CHROOT/etc/resolv.conf"

  sudo mount $ARCH_TRAVIS_CHROOT $ARCH_TRAVIS_CHROOT --bind
  sudo mount --bind /proc $ARCH_TRAVIS_CHROOT/proc
  sudo mount --bind /sys $ARCH_TRAVIS_CHROOT/sys
  sudo mount --bind /dev $ARCH_TRAVIS_CHROOT/dev
  sudo mount --bind /dev/pts $ARCH_TRAVIS_CHROOT/dev/pts
  sudo mount --bind /dev/shm $ARCH_TRAVIS_CHROOT/dev/shm
  sudo mount --bind /run $ARCH_TRAVIS_CHROOT/run

  # update packages
  chroot_as_root "pacman -Syy"
  chroot_as_root "pacman -Su ${default_packages[*]} --needed --noconfirm"
  chroot_as_root "pacman-key --init"
  chroot_as_root "pacman-key --populate archlinux"

  # use LANG=en_US.UTF-8 as expected in travis environments
  as_root "sed -i 's|#en_US.UTF-8|en_US.UTF-8|' $ARCH_TRAVIS_CHROOT/etc/locale.gen"
  chroot_as_root "locale-gen"

  # setup non-root user
  chroot_as_root "useradd -u $uid -m -s /bin/bash $user"

  # disable password for sudo users
  as_root "echo \"$user ALL=(ALL) NOPASSWD: ALL\" >> $ARCH_TRAVIS_CHROOT/etc/sudoers.d/$user"

  # mount HOME dirs
  for d in $HOME/*/; do
    if [ "$d" != "$ARCH_TRAVIS_CHROOT/" ]; then
      dir="$user_home/$(basename "$d")"
      chroot_as_root "mkdir -p $dir && chown $user $dir"
      sudo mount --bind "$d" "$ARCH_TRAVIS_CHROOT$dir"
    fi
  done
}

# a wrapper which can be used to eventually add fakeroot support.
sudo_wrapper() {
  sudo "$@"
}

# run command as normal user
as_normal() {
  local cmd="$@"
  run /bin/bash -c "$cmd"
}

# run command as root
as_root() {
  local cmd="$@"
  run sudo_wrapper /bin/bash -c "$cmd"
}

# run command in chroot as root
chroot_as_root() {
  local cmd="$@"
  run sudo_wrapper setarch $ARCH_TRAVIS_ARCH chroot \
    $ARCH_TRAVIS_CHROOT /bin/bash -c "$cmd"
}

# execute command in chroot as normal user
_chroot_as_normal() {
  local cmd="$@"
  sudo_wrapper setarch $ARCH_TRAVIS_ARCH chroot \
    --userspec=$uid:$uid $ARCH_TRAVIS_CHROOT /bin/bash \
    -c "export PATH=$PATH && cd $user_build_dir && $cmd"
}

# run command in chroot as normal user
chroot_as_normal() {
  local cmd="$@"
  run _chroot_as_normal "$cmd"
}

# run command
run() {
  "$@"
  local ret=$?

  if [ $ret -gt 0 ]; then
    exit $ret
  fi
}

# run build script
run_build_script() {
  local cmd="$@"
  echo "$ $cmd"
  _chroot_as_normal "$cmd"
  local ret=$?

  if [ $ret -gt 0 ]; then
    exit $ret
  fi
}

# install package through pacman
_pacman() {
  local IFS=" ";
  local pacman="yes | pacman -S $* --noconfirm --needed"

  echo "$pacman"

  chroot_as_root "$pacman"
}

# read value from .travis.yml
travis_yml() {
  ruby -ryaml -e 'puts ARGV[1..-1].inject(YAML.load(File.read(ARGV[0]))) {|acc, key| acc[key] }' .travis.yml $@
}

read_config() {
    local old_ifs=$IFS
    IFS=$'\n'
    CONFIG_BUILD_SCRIPTS=($(travis_yml arch script))
    CONFIG_PACKAGES=($(travis_yml arch packages))
    IFS=$old_ifs
}

# run build scripts defined in .travis.yml
build_scripts() {
  if [ ${#CONFIG_BUILD_SCRIPTS[@]} -gt 0 ]; then
    for script in "${CONFIG_BUILD_SCRIPTS[@]}"; do
      run_build_script $script
    done
  else
    echo "No build scripts defined"
    exit 1
  fi
}

# install packages defined in .travis.yml
install_packages() {
  if [ "${#CONFIG_PACKAGES[@]}" -gt 0 ]; then
    _pacman "${CONFIG_PACKAGES[@]}"
  fi
}

# install custom compiler if CC != gcc
install_c_compiler() {
  if [ "$TRAVIS_CC" != "gcc" ]; then
    _pacman "$TRAVIS_CC"
  fi
}

arch_msg() {
  lightblue='\033[1;34m'
  reset='\e[0m'
  echo -e "${lightblue}$@${reset}"
}

# read .travis.yml
read_config

echo "travis_fold:start:arch_travis"
setup_chroot

install_packages

if [ -n "$CC" ]; then
  install_c_compiler

  # restore CC
  CC=$TRAVIS_CC
fi
echo "travis_fold:end:arch_travis"
echo ""

arch_msg "Running travis build"
build_scripts

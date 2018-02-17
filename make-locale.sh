#!/bin/sh

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

mkdir -p locale
pybabel extract src/*.py -o locale/alinstaller.pot

while read lang; do
	if $(ls locale/$lang/*/*.po > /dev/null 2>&1); then
		pybabel update -D alinstaller -i locale/alinstaller.pot -d locale -l $lang > /dev/null 2>&1
		sed -i 's/^#~.*$//' locale/$lang/*/*.po
		pybabel update -D alinstaller -i locale/alinstaller.pot -d locale -l $lang
	else
		pybabel init -D alinstaller -i locale/alinstaller.pot -d locale -l $lang
	fi
done < src/lang.txt

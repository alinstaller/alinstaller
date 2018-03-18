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

pylint --additional-builtins=_ \
	--disable=arguments-differ,broad-except,cyclic-import,duplicate-code,invalid-name,line-too-long,missing-docstring,no-self-use,too-few-public-methods,too-many-arguments,too-many-branches,too-many-instance-attributes,too-many-locals,too-many-return-statements,too-many-statements,unused-argument,wrong-import-position \
	src/*.py

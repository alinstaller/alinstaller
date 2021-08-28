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

import gettext

import babel


class LanguageLib():
    def __init__(self):
        self.lang = None
        self.languages = []

        with open('lang.txt', 'r', encoding='utf_8') as f:
            for x in f:
                x = x.strip('\n')
                locale = babel.Locale.parse(x)
                self.languages.append((x, locale.display_name))

        l = sorted(self.languages[1:], key=lambda x: (x[1], x[0]))
        self.languages = [self.languages[0]] + l

    def install(self, lang=None):
        try:
            if lang is None:
                lang = self.languages[0][0]
            self._real_install(lang)
        except FileNotFoundError:
            lang = self.languages[0][0]
            self._real_install(lang)

    def _real_install(self, lang):
        gettext.translation('alinstaller',
                            localedir='/usr/local/share/locale',
                            languages=[lang]).install()
        self.lang = lang


language_lib = LanguageLib()

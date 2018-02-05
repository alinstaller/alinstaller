#!/bin/env python3

print('\nWelcome to AL Installer!\n')

import traceback

from dlg import dialog
from welcome import welcome

try:
    welcome.run()
except:
    dialog.msgbox('Installation failed.\n\n' +
        traceback.format_exc())

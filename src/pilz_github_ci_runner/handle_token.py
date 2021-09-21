# Copyright (c) 2021 Pilz GmbH & Co. KG
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import keyring
from getpass import getpass


def set_token():
    token = None
    while not token:
        print(
            "Please provide a GitHub personal access token with 'public_repo' permission.")
        new_token = getpass(prompt='personal access token:')
        keyring.set_password(
            'system', 'github-hardware-tester-token', new_token)
        token = keyring.get_password('system', 'github-hardware-tester-token')
        if not token:
            print("There was an issue storing the token in the keyring!")
    return token


def get_token(no_keyring: bool):
    if no_keyring:
        return getpass(prompt='personal access token:')
    else:
        keyring.set_keyring(
            keyring.backends.SecretService.Keyring())  # For Ubuntu 20
        token = keyring.get_password('system', 'github-hardware-tester-token')
        if not token:
            token = set_token()
        return token

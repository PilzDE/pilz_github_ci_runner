import keyring


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


def get_token(no_keyring):
    if no_keyring:
        return getpass(prompt='personal access token:')
    else:
        keyring.set_keyring(
            keyring.backends.SecretService.Keyring())  # For Ubuntu 20
        token = keyring.get_password('system', 'github-hardware-tester-token')
        if not token:
            token = set_token()
        return token

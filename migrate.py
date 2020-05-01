import os
import shlex
import subprocess
import sys
from pathlib import Path

HOME_DIR = str(Path.home())
BITRISE_MIGRATOR_DIR = '.bitrise_migrator'
BITRISE_CLI_SCRIPT_URL = "https://raw.githubusercontent.com/bitrise-io/bitrise-add-new-project/master/_scripts/run.sh"


def handle_bitrise_migrator_files(file: str, prompt: str) -> str:
    mode = "r+" if dir_exists() and file_exists(file) else "w+"  # size check???

    if not dir_exists():
        os.makedirs(f'{HOME_DIR}/{BITRISE_MIGRATOR_DIR}')

    if not file_exists(file):
        open(file, "w").close()

    with open(file, mode) as f:
        file_size = os.path.getsize(file)

        # Save token from input into the created file
        if file_size == 0 or mode == "w":
            output = input(f'{prompt}')
            f.write(f'{output}')
        else:
            # Read token from existing file that is not empty
            output = f.read()

        f.close()

    return output


def read_bitrise_token() -> str:
    file = f'{HOME_DIR}/{BITRISE_MIGRATOR_DIR}/.bitrise_token'
    return handle_bitrise_migrator_files(file, "Enter Bitrise access token: ")


def read_org_id() -> str:
    file = f'{HOME_DIR}/{BITRISE_MIGRATOR_DIR}/.org_id'
    return handle_bitrise_migrator_files(file, "Enter organisation id from Bitrise: ")


# defaults to personal non-public bitrise project
def setup_bitrise(bitrise_api_token: str = "", org_id: str = "", is_org: bool = False, is_public: bool = False):
    org_personal_placeholder: str = f'--org "{org_id}"' if is_org else '--personal "true"'
    public_placeholder: str = 'true' if is_public else 'false'

    cmd = f'bash -c "bash <(curl -sfL "{BITRISE_CLI_SCRIPT_URL}") --api-token "{bitrise_api_token}" ' \
          f'{org_personal_placeholder} --public "{public_placeholder}" --website" '
    args = shlex.split(cmd)
    subprocess.run(args)


def file_exists(file: str) -> bool:
    return os.path.isfile(file)


def dir_exists() -> bool:
    return os.path.isdir(f'{HOME_DIR}/{BITRISE_MIGRATOR_DIR}')


def handle_user_input_entry(prompt: str) -> tuple:
    while True:
        user_input = input(prompt)
        if len(user_input) > 0:
            temp_input = user_input.strip().lower()
            if temp_input == "q":
                sys.exit()
            elif temp_input == "1":
                bitrise_token = read_bitrise_token()
                return bitrise_token, ""
            elif temp_input == "2":
                bitrise_token = read_bitrise_token()
                org_id = read_org_id()
                return bitrise_token, org_id


def handle_public_entry(prompt: str) -> bool:
    return True if input(prompt).strip().lower() == "y" else False


if __name__ == '__main__':
    token, org_id = handle_user_input_entry(
        "Is this a personal Bitrise or an organizational project?\n\tEnter '1' to create a "
        "personal Bitrise project\n\tEnter '2' to create an organizational project\n\tEnter 'q' "
        "to quit\nYour input: ")

    is_public: bool = handle_public_entry("Will this project be public? Defaults to not public.\nYour input (y/n): ")

    setup_bitrise(bitrise_api_token=token, org_id=org_id, is_org=True if len(org_id) > 0 else False,
                  is_public=is_public)
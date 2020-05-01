import os
import shlex
import subprocess
from pathlib import Path

HOME_DIR = str(Path.home())
BITRISE_MIGRATOR_DIR = '.bitrise_migrator'
BITRISE_CLI_SCRIPT_URL = "https://raw.githubusercontent.com/bitrise-io/bitrise-add-new-project/master/_scripts/run.sh"


def handle_bitrise_migrator_files(filename: str, input_text: str = "Enter ") -> str:
    mode = "r" if os.path.isfile(filename) and os.path.getsize(filename) > 0 else "w"  # size check???

    with open(filename, mode) as file:
        file_size = os.path.getsize(filename)

        # Save token from input into the created file
        if file_size == 0 or mode == "w":
            output, user_input = input(f'{input_text}: ')
            file.write(f'{user_input}')
        else:
            # Read token from existing file that is not empty
            output = file.read()

        file.close()

    return output


def read_bitrise_token() -> str:
    filename = f'{HOME_DIR}/{BITRISE_MIGRATOR_DIR}/.bitrise_token'
    return handle_bitrise_migrator_files(filename)


def read_org_id() -> str:
    filename = f'{HOME_DIR}/{BITRISE_MIGRATOR_DIR}/.org_id'
    return handle_bitrise_migrator_files(filename)


# defaults to personal non-public bitrise project
def setup_bitrise(bitrise_api_token: str = "", org_id: str = "", is_org: bool = False, is_public: bool = False):
    org_personal_placeholder: str = f'--org "{org_id}"' if is_org else '--personal "true"'
    public_placeholder: str = 'true' if is_public else 'false'

    cmd = f'bash -c "bash <(curl -sfL "{BITRISE_CLI_SCRIPT_URL}") --api-token "{bitrise_api_token}" ' \
          f'{org_personal_placeholder} --public "{public_placeholder}" --website" '
    args = shlex.split(cmd)
    subprocess.run(args)


# def check_file_exists(filename: str) -> bool:
#     return os.path.isfile(f'{HOME_DIR}/{BITRISE_MIGRATOR_DIR}/{filename}')
#
#
# def check_dir_exists() -> bool:
#     return os.path.isdir(f'{HOME_DIR}/{BITRISE_MIGRATOR_DIR}')


if __name__ == '__main__':
    pass

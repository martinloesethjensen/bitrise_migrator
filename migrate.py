import fileinput
import os
import shlex
import subprocess
import sys
from pathlib import Path

import click
import requests

HOME_DIR = str(Path.home())
BITRISE_MIGRATOR_DIR = '.bitrise_migrator'
BITRISE_CLI_SCRIPT_URL = "https://raw.githubusercontent.com/bitrise-io/bitrise-add-new-project/master/_scripts/run.sh"


@click.group()
def main():
    """
    Simple CLI for creating Bitrise project by Martin L. Jensen
    """
    pass


@main.command()
def migrate():
    token, org_id = handle_user_input_entry()

    is_public: bool = click.confirm('\nWill this project be public? Defaults to not public.')

    handle_bitrise_import()

    handle_custom_import()

    setup_bitrise(token=token, org=org_id, is_org=True if len(org_id) > 0 else False, public=is_public)


def handle_bitrise_import():
    if click.confirm('\nWould you like to import Bitrise workflow from url?'):
        prepare_bitrise_file(url=click.prompt("\nEnter url to raw text file example a github raw link: ", type=str))


def handle_custom_import():
    while click.confirm('\nDo you want to import custom files?'):
        file_name = click.prompt("\nEnter file name (use '/' to create folder with the file): ", type=str)
        url = click.prompt("\nEnter url to raw text file example a github raw link: ", type=str)

        if click.confirm('Do you want to continue?'):
            generate_dirs(file_name)
            write_file(file_name, url)


def generate_dirs(file_name: str):
    if "/" in file_name:
        file_dir = file_name.replace(file_name.split("/")[-1], "")
        if not os.path.exists(file_dir):
            os.makedirs(file_dir)


@main.command()
@click.option("--token", default="", prompt="Enter your Bitrise token", required=True, type=click.STRING,
              help="The api token you can generate in security settings from the bitrise website.")
@click.option("--org", default="", type=click.STRING, required=False, prompt="Enter your org id",
              help="The id for your Bitrise organisation.")
@click.option("--public", default="false", type=click.BOOL, required=False,
              help="To specify whether or not the Bitrise project should be public.")
def run_setup(token: str = "", org: str = "", public: bool = False):
    setup_bitrise(token=token, org=org, is_org=True if len(org) > 0 else False, public=public)


@main.command()
@click.option("--url", prompt="Enter url for raw text file", type=click.STRING,
              help="A GitHub link like this: https://raw.githubusercontent.com/martinloesethjensen/bitrise_migrator/v0.1.1.pre/migrate.py")
def import_bitrise_file(url: str):
    prepare_bitrise_file(url)


@main.command()
@click.option("--file", prompt="Enter file name (use '/' to create folder with the file)", type=click.STRING,
              help="File name can also use '/' to create one or more folders.")
@click.option("--url", prompt="Enter url for raw text file", type=click.STRING,
              help="A GitHub link like this: https://raw.githubusercontent.com/martinloesethjensen/bitrise_migrator/v0.1.1.pre/migrate.py")
def import_file(file: str, url: str):
    generate_dirs(file)
    write_file(file, url)


def write_file(file_name: str, url: str, mode="w+"):
    res = requests.get(url)
    with open(file_name, mode) as file:
        file.write(res.text)
    file.close()


@main.command()
@click.option('--token', help='Update token file with new token.', default='')
@click.option('--org', help='Update with new org id.', default='')
def update(token: str, org: str):
    if click.confirm('Confirm Update'):
        if len(token) > 0:
            update_bitrise_token(token)
        if len(org) > 0:
            update_org_id(org)


def prepare_bitrise_file(url: str):
    res = requests.get(url)
    with open("bitrise.yml", "w+") as file:
        file.write(res.text)
    file.close()

    dirname = os.path.basename(locate_android_project_folder())

    os.chdir("..")

    find_and_replace("<PROJECT_NAME>", dirname, "bitrise.yml")


def setup_bitrise(token: str = "", org: str = "", is_org: bool = False, public: bool = False):
    org_personal_placeholder: str = f'--org "{org}"' if is_org else '--personal "true"'
    public_placeholder: str = 'true' if public else 'false'

    cmd = f'bash -c "bash <(curl -sfL "{BITRISE_CLI_SCRIPT_URL}") --api-token "{token}" ' \
          f'{org_personal_placeholder} --public "{public_placeholder}" --website" '
    args = shlex.split(cmd)
    subprocess.run(args)


def find_and_replace(old, new, file_name: str):
    with fileinput.FileInput(file_name, inplace=True) as file:
        for line in file:
            print(line.replace(old, new), end='')


def read_bitrise_token() -> str:
    file = f'{HOME_DIR}/{BITRISE_MIGRATOR_DIR}/.bitrise_token'
    return handle_bitrise_migrator_files(file, "Enter Bitrise access token: ")


def read_org_id() -> str:
    file = f'{HOME_DIR}/{BITRISE_MIGRATOR_DIR}/.org_id'
    return handle_bitrise_migrator_files(file, "Enter organisation id from Bitrise: ")


def handle_bitrise_migrator_files(file: str, prompt: str) -> str:
    mode = "r+" if dir_exists() and os.path.isfile(file) else "w+"

    if not dir_exists():
        os.makedirs(f'{HOME_DIR}/{BITRISE_MIGRATOR_DIR}')

    # Create file if it does not already exist
    if not os.path.isfile(file):
        open(file, "w").close()

    with open(file, mode) as f:
        file_size = os.path.getsize(file)

        # Save token from input into the created file
        if file_size == 0 or mode == "w":
            output = click.prompt(f'{prompt}', type=str)
            if len(output) > 0:
                f.write(f'{output}')
        else:
            # Read token from existing file that is not empty
            output = f.read()
        f.close()
    return output


def update_bitrise_token(token: str):
    file = f'{HOME_DIR}/{BITRISE_MIGRATOR_DIR}/.bitrise_token'
    write_to_file(file, token)


def update_org_id(org_id: str):
    file = f'{HOME_DIR}/{BITRISE_MIGRATOR_DIR}/.org_id'
    write_to_file(file, org_id)


def write_to_file(file_path: str, write_input: str):
    if not dir_exists():
        os.makedirs(f'{HOME_DIR}/{BITRISE_MIGRATOR_DIR}')

    if not os.path.isfile(file_path):
        open(file_path, "w").close()

    with open(file_path, 'w') as f:
        f.write(write_input)
        f.close()


def dir_exists() -> bool:
    return os.path.isdir(f'{HOME_DIR}/{BITRISE_MIGRATOR_DIR}')


def handle_user_input_entry() -> tuple:
    entry_options = [0, 1, 2]
    user_input = -1
    while user_input not in entry_options:
        user_input = click.prompt(
            "\nIs this a personal Bitrise or an organizational project?"
            "\n--> Enter '1' to create a personal Bitrise project"
            "\n--> Enter '2' to create an organizational project"
            "\n--> Enter '0' to quit"
            "\nYour input",
            type=int)

    if user_input == 0:
        sys.exit()
    elif user_input == 1:
        bitrise_token = read_bitrise_token()
        return bitrise_token, ""
    elif user_input == 2:
        bitrise_token = read_bitrise_token()
        org_id = read_org_id()
        return bitrise_token, org_id


def locate_android_project_folder() -> str:
    for dir_path, _, files in os.walk(os.getcwd()):
        for file in files:
            if file == "settings.gradle":
                os.chdir(dir_path)
                return os.getcwd()


if __name__ == '__main__':
    main()

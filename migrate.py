import fileinput
import os
import shlex
import subprocess
import sys
from pathlib import Path

import click
from pip._vendor import requests

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
    token, org_id = handle_user_input_entry(
        "Is this a personal Bitrise or an organizational project?\n\tEnter '1' to create a "
        "personal Bitrise project\n\tEnter '2' to create an organizational project\n\tEnter 'q' "
        "to quit\nYour input: ")

    is_public: bool = handle_user_yn_input("Will this project be public? Defaults to not public.\nYour input (y/n): ")

    import_file: bool = handle_user_yn_input("Would you like to import Bitrise workflow from url (y/n): ")

    if import_file:
        prepare_bitrise_file(url=input("Enter url to raw text file example a github raw link: "))

    setup_bitrise(token=token, org=org_id, is_org=True if len(org_id) > 0 else False, public=is_public)


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


def prepare_bitrise_file(url: str):
    res = requests.get(url)
    with open("bitrise.yml", "w+") as file:
        file.write(res.text)
    file.close()

    dirname = os.path.basename(os.getcwd())

    find_and_replace(dirname, "<PROJECT_NAME>", "bitrise.yml")


def setup_bitrise(token: str = "", org: str = "", is_org: bool = False, public: bool = False):
    org_personal_placeholder: str = f'--org "{org}"' if is_org else '--personal "true"'
    public_placeholder: str = 'true' if public else 'false'

    cmd = f'bash -c "bash <(curl -sfL "{BITRISE_CLI_SCRIPT_URL}") --api-token "{token}" ' \
          f'{org_personal_placeholder} --public "{public_placeholder}" --website" '
    args = shlex.split(cmd)
    subprocess.run(args)


def find_and_replace(find, replace, file_name):
    with fileinput.FileInput(file_name, inplace=True) as file:
        for line in file:
            print(line.replace(replace, find), end='')


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


def handle_user_yn_input(prompt: str) -> bool:
    return True if input(prompt).strip().lower() == "y" else False


if __name__ == '__main__':
    main()

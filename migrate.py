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
    token, org_id = handle_user_input_entry(
        "\nIs this a personal Bitrise or an organizational project?\n--> Enter '1' to create a "
        "personal Bitrise project\n--> Enter '2' to create an organizational project\n--> Enter 'q' "
        "to quit\n\tYour input: ")

    is_public: bool = handle_user_yn_input(
        "\nWill this project be public? Defaults to not public.\n\tYour input (y/n): ")

    handle_bitrise_import()

    handle_custom_import()

    setup_bitrise(token=token, org=org_id, is_org=True if len(org_id) > 0 else False, public=is_public)


def handle_bitrise_import():
    import__bitrise_file: bool = handle_user_yn_input(
        "\nWould you like to import Bitrise workflow from url?\n\tYour input (y/n): ")
    if import__bitrise_file:
        prepare_bitrise_file(url=input("\nEnter url to raw text file example a github raw link: "))


def generate_dirs(file_name: str):
    if "/" in file_name:
        file_dir = file_name.replace(file_name.split("/")[-1], "")
        if not os.path.exists(file_dir):
            os.makedirs(file_dir)


def handle_custom_import():
    import_custom_file: bool = handle_user_yn_input("\nDo you want to import custom files?\n\tYour input (y/n): ")
    while import_custom_file:
        file_name = input("\nEnter file name (use '/' to create folder with the file): ")
        url = input("\nEnter url to raw text file example a github raw link: ")

        generate_dirs(file_name)
        write_file(file_name, url)
        import_custom_file = handle_user_yn_input("\nImport more?\n\tYour input (y/n):")


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


def prepare_bitrise_file(url: str):
    res = requests.get(url)
    with open("bitrise.yml", "w+") as file:
        file.write(res.text)
    file.close()

    dirname = os.path.basename(locate_android_project_folder())

    os.chdir("..")

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


def locate_android_project_folder() -> str:
    for dirpath, dirnames, files in os.walk(os.getcwd()):
        for file in files:
            if file == "settings.gradle":
                os.chdir(dirpath)
                return os.getcwd()
    return "No android project folder found"


if __name__ == '__main__':
    main()

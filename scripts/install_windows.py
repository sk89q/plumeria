import sys

if sys.version_info < (3, 5):
    print("Python 3.5 or greater required", file=sys.stderr)
    sys.exit(1)

import logging
import urllib.request
from zipfile import ZipFile
import os
import os.path
import sys
import platform
import struct

TEMP_DIR = 'tmp'
BINARIES_32_URL = "https://github.com/sk89q/Plumeria/releases/download/extras/plumeria_libs_py35_win32_2016-10-02.zip"
BINARIES_64_URL = "https://github.com/sk89q/Plumeria/releases/download/extras/plumeria_libs_py35_win64_2016-10-02.zip"
VIRTUAL_ENV_DIR = ".venv"


def download_file(url, path):
    logging.info("Downloading {url} to {path}...".format(url=url, path=path))

    with open(path, "wb") as f:
        with urllib.request.urlopen(url) as u:
            f.write(u.read())


def exec(command):
    ret_code = os.system(command)
    if ret_code != 0:
        logging.error("The command '{}' did not complete successfully (got return code {})".format(command, ret_code))
        sys.exit(1)


def main():
    is_64bit = struct.calcsize("P") * 8 == 64
    logging.info("Is 64-bit? {}".format("yes" if is_64bit else "no"))

    if not os.path.exists(TEMP_DIR):
        os.makedirs(TEMP_DIR)

    bins_url = BINARIES_64_URL if is_64bit else BINARIES_32_URL
    bins_path = os.path.join(TEMP_DIR, os.path.basename(bins_url))
    if not os.path.exists(bins_path):
        download_file(bins_url, bins_path)
    else:
        logging.info("The file {} already exists so it won't be re-downloaded".format(bins_path))

    logging.info("Extracting {path}...".format(path=bins_path))
    with ZipFile(bins_path, 'r') as zip:
        zip.extractall('.')

    logging.info("Making sure that virtualenv is installed globally...")
    exec("pip install virtualenv")

    if not os.path.isdir(VIRTUAL_ENV_DIR):
        logging.info("Creating virtualenv...")
        exec("python -m virtualenv {}".format(VIRTUAL_ENV_DIR))
    else:
        logging.info("The folder {} already exists so no new virtualenv will be created".format(VIRTUAL_ENV_DIR))

    logging.info("Installing binary packages...")
    exec("{}\\Scripts\\pip install -r packages\\{}.txt".format(VIRTUAL_ENV_DIR, "win64" if is_64bit else "win32"))

    logging.info("Installing other packages...")
    exec("{}\\Scripts\\pip install -r requirements.txt".format(VIRTUAL_ENV_DIR))

    logging.info("")
    logging.info("Installation was SUCCESSFUL!")
    logging.info("")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")
    main()

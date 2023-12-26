import logging
import os

from typing import List

import requests


def decompress_into_dir(path: str, dirname: str) -> List[str]:
    """
    Decompress archive using p7zip into a new directory on the same level

    :param path: path to the archive to be decompressed
    :param newdir: name of new directory - NOT a full path
    :returns: full paths to all files in the new directory
    """
    if not os.path.exists(path):
        e = "Cannot decompress non-existent file {path}"
        raise FileNotFoundError(e)
    elif not os.path.isfile(path):
        e = "Cannot decompress directory {path}"
        raise FileNotFoundError(e)

    logging.debug(f"Starting decompress in path {path}")

    local_dir = f"{os.sep}".join(
        path for path in path.rstrip(os.sep).split(os.sep)[:-1]
    )
    new_dir = os.path.join(local_dir, dirname)
    create_dir(new_dir)

    # this is poo
    os.system(f"7z e {path} -o{new_dir} ")
    files = os.listdir(new_dir)
    logging.debug(f"Finished decompress in path {path}")

    return [os.path.join(new_dir, file) for file in files]


def create_dir(directory):
    """
    Create a new directory if it does not already exist
    :param directory: full path of directory to be made
    """
    logging.debug("Create directory {}".format(directory))
    return os.makedirs(directory, exist_ok=True)


def get_request(url: str) -> requests.Response:
    """
    Exception-handled GET request
    :param url: URL in string form
    """
    response = requests.get(url)

    if response.status_code > 399:
        logging.warning(f"<{response.status_code}> {response.text}")
    else:
        logging.debug(f"<{response.status_code}> {response.text[:50]}")

    return response


def convert_toolurl(url):
    """
    Sometimes webpages give the unverum link for some reason
    :param url: URL in string form
    """
    return url.replace("unverum:", "").replace("mmdl", "dl").split(",")[0]


def configure_logging(level=logging.DEBUG):
    """
    Logging
    """
    logging.basicConfig(format="[%(levelname)s]\t%(message)s", level=level)


def input_yn(prompt, *args):
    """
    bruh
    """
    return input(prompt.format(*args)).lower().startswith("y")

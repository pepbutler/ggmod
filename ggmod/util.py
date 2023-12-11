import logging
import os


def input_yn(prompt, *args):
    return input(prompt.format(*args)).lower().startswith("y")


def create_dir(directory):
    logging.debug("Create directory {}".format(directory))
    return os.makedirs(directory, exist_ok=True)


def get_request(url):
    import requests

    response = requests.get(url)

    if response.status_code > 399:
        logging.warning(f"<{response.status_code}> {response.text}")
    else:
        logging.debug(f"<{response.status_code}> {response.text[:50]}")

    return response


def convert_toolurl(url):
    return url.replace("unverum:", "").replace("mmdl", "dl").split(",")[0]


def configure_logging():
    logging.basicConfig(format='[%(levelname)s]\t%(message)s', level=logging.DEBUG)

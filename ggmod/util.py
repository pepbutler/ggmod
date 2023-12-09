import os

def create_dir(directory):
    code = os.mkdirs(directory, exist_ok=True)


def configure_logging():
    logging.basicConfig(format='%[(levelname)]s\t%(message)s', level=logging.DEBUG)
    logging.debug('This message should appear on the console')
    logging.info('So should this')
    logging.warning('And this, too')

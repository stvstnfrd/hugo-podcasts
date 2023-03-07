"""
Handle misc. operations
"""
import datetime
import os
import re
import shutil

import requests
from unidecode import unidecode

from rss2hugo.log import get_logger


logger = get_logger(__name__)


def parse_datetime(timestamp):
    """
    Parse a datetime from a string
    """
    formats = (
        # 'Sun, 15 Jan 2023 15:20:53 PST'
        '%a, %d %b %Y %H:%M:%S %z',
        '%a, %d %b %Y %H:%M:%S %Z',
        '%a, %d %b %Y %H:%M:%S PST',
        '%a, %d %b %Y %H:%M:%S EST',
        '%a, %d %b %Y %H:%M:%S PDT',
    )
    timestamp = timestamp or ''
    timestamp = timestamp.strip()
    if timestamp != '':
        for _format in formats:
            try:
                timestamp = datetime.datetime.strptime(timestamp, _format)
                if timestamp is not None and timestamp != '':
                    break
            except ValueError:
                pass
    timestamp = timestamp or ''
    return timestamp


def get_filename(text):
    """
    Create a filesystem-safe filename, based on text

    - make it lowercase
    - remove symbols
    - convert some symbols to spaces
    - convert spaces to dashes
    - replace unicode characters with ASCII equivalents
    """
    text = text.lower()
    remove = r"[.!?'\"()]"
    empty = r"[-_:;/,\W]"
    text = text.replace('&', 'n')
    text = re.sub(remove, '', text)
    text = re.sub(empty, ' ', text)
    text = text.strip()
    text = re.sub(' +', '-', text)
    text = unidecode(text)
    return text


def mkdir(directory, recursive=False):
    """
    Create a directory, maybe recursively
    """
    result = False
    if recursive:
        return _mkdirs(directory)
    logger.debug("Create directory: %s", directory)
    try:
        os.mkdir(directory)
        result = True
    except FileExistsError:
        logger.debug("Directory exists: %s", directory)
        result = None
    return result


def _mkdirs(directory):
    """
    Recursively create a directory
    """
    all_paths = directory.split(os.path.sep)
    paths = []
    result = True
    for path in all_paths:
        paths.append(path)
        path = os.path.sep.join(paths)
        result = mkdir(path)
    return result


def get_image(url, filename, overwrite=False):
    """
    Download a binary file
    """
    logger.info("Fetch binary: %s, %s", filename, url)
    if not overwrite and os.path.exists(filename):
        return
    response = requests.get(url, stream=True, timeout=10)
    if response.status_code == 200:
        with open(filename, 'wb') as _file:
            response.raw.decode_content = True
            shutil.copyfileobj(response.raw, _file)

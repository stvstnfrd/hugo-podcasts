"""
Customize project logging
"""
import logging


DEFAULT_LEVEL = logging.INFO


logging.basicConfig(
    format='%(asctime)s	%(process)d	%(levelname)s	%(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
)


class TabSeparatedLogFilter(logging.Filter):
    """
    Display log lines as tab-separated-value lines
    """
    # pylint: disable=too-few-public-methods

    def filter(self, record) -> bool:
        """
        Escape literal tabs and newlines; everything else is okay

        Tabs separate fields and newlines separate entries.
        """
        record.msg = record.msg.replace('\n', '\\n')
        record.msg = record.msg.replace('\t', '\\t')
        return True


def get_logger(name: str, level: int=None) -> logging.Logger:
    """
    Instantiate a customized logger object with tab-separated-value entries
    """
    name = name or __name__
    level = level or DEFAULT_LEVEL
    _filter = TabSeparatedLogFilter()
    logger = logging.getLogger(name)
    logger.addFilter(_filter)
    logger.setLevel(level)
    return logger

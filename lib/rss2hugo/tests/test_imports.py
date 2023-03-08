"""
Assert that our library was properly installed
"""
import unittest


class TestImports(unittest.TestCase):
    """
    Test that our library imports are generally available
    """

    def test_imports(self):
        """
        We should be able to import our top-level modules
        """
        # pylint: disable=import-outside-toplevel
        # pylint: disable=unused-import
        from rss2hugo import log
        from rss2hugo import markdown
        from rss2hugo import models
        from rss2hugo import pandoc
        from rss2hugo import util


if __name__ == '__main__':
    unittest.main()

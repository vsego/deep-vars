"""
Testing utilities.
"""

import unittest

from deep_vars import DeepVars


class TestsBase(unittest.TestCase):
    """
    The base unit tests class, used as a foundation for all other unit tests.
    """

    def setUp(self):
        """
        For future uses (common resets between runs).
        """
        DeepVars.clear_bookmarks()
        DeepVars.reset_handlers()

    def tearDown(self):
        """
        For future uses (common resets between runs).
        """
        pass

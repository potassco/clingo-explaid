"""
Test cases for main application functionality.
"""

from unittest import TestCase


class TestMain(TestCase):
    """
    Test cases for main application functionality.
    """

    # def test_logger(self) -> None:
    #     """
    #     Test the logger.
    #     """
    #     sio = StringIO()
    #     configure_logging(sio, logging.INFO, True)
    #     log = get_logger("main")
    #     log.info("test123")
    #     self.assertRegex(sio.getvalue(), "test123")

    # def test_parser(self) -> None:
    #     """
    #     Test the parser.
    #     """
    #     parser = get_parser()
    #     ret = parser.parse_args(["--log", "info"])
    #     self.assertEqual(ret.log, logging.INFO)

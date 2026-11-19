import unittest

from price import parse_price


class ParsePriceTest(unittest.TestCase):
    def test_yen_sign(self):
        self.assertEqual(parse_price("¥1200"), 1200)

    def test_yen_suffix(self):
        self.assertEqual(parse_price(" 980円 "), 980)


if __name__ == "__main__":
    unittest.main()

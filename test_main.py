import csv
import unittest
from datetime import date

import main


class FollowupTests(unittest.TestCase):
    def test_stale_ranked(self):
        rows = list(csv.DictReader(open("sample_deals.csv")))
        stale = main.stale_deals(rows, date(2026, 10, 9))
        self.assertEqual([d["deal"] for d in stale], ["D3", "D1", "D4", "D6"])


if __name__ == "__main__":
    unittest.main()

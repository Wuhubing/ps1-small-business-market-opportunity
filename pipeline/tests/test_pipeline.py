import unittest

from pipeline.verify_pipeline import coordinates_in_bounds, naics_matches, vacancy_months


class PipelineHelpersTest(unittest.TestCase):
    def test_naics_hierarchy(self):
        self.assertTrue(naics_matches("44----", "44"))
        self.assertTrue(naics_matches("722511", "722"))
        self.assertFalse(naics_matches("722511", "44"))

    def test_vacancy_months_across_years(self):
        self.assertEqual(vacancy_months(2025, 3, 2023, 11), 16)
        self.assertEqual(vacancy_months(2024, 1, 2024, 1), 0)

    def test_coordinate_bounds(self):
        self.assertTrue(coordinates_in_bounds(42.36, -71.08))
        self.assertFalse(coordinates_in_bounds(41.0, -71.08))
        self.assertFalse(coordinates_in_bounds(42.36, -73.0))


if __name__ == "__main__":
    unittest.main()

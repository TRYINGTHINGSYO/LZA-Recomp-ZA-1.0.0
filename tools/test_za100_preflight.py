"""Synthetic checks: no game binaries, generated code or assets required."""
import struct
import unittest
from za100_preflight import BASE, BUILD, TIMING_SITES, check_image


class PreflightTests(unittest.TestCase):
    def setUp(self):
        self.image = bytearray(max(a - BASE for _, a, _ in TIMING_SITES) + 4)
        for _, address, word in TIMING_SITES:
            struct.pack_into('<I', self.image, address - BASE, word)
        self.text = (0, len(self.image))

    def test_matching_sites_are_not_runtime_approval(self):
        result = check_image(BUILD, self.image, self.text)
        self.assertTrue(result['timing_checks_passed'])
        self.assertFalse(result['runtime_support'])

    def test_other_build_is_rejected(self):
        with self.assertRaises(ValueError):
            check_image('b1f12fd919eae86a', self.image, self.text)

    def test_modified_instruction_fails(self):
        self.image[TIMING_SITES[0][1] - BASE] ^= 1
        self.assertFalse(check_image(BUILD, self.image, self.text)['timing_checks_passed'])

    def test_data_segment_is_not_accepted_as_code(self):
        self.assertFalse(check_image(BUILD, self.image, (0, 4))['timing_checks_passed'])


if __name__ == '__main__':
    unittest.main()

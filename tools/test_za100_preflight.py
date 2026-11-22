"""Synthetic checks: no game binaries, generated code or assets required."""
import struct
import unittest
from za100_preflight import (BASE, BUILD, TIMING_SITES, FRAME_TABLE,
                             FRAME_INTERVALS, FRAME_TABLE_REFS, check_image, bootstrap_allowed)


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

    def test_every_native_mode_instruction_is_checked(self):
        for name, address, _ in TIMING_SITES:
            with self.subTest(site=name):
                offset = address - BASE
                self.image[offset] ^= 1
                self.assertFalse(check_image(BUILD, self.image, self.text)['timing_checks_passed'])
                self.image[offset] ^= 1

    def test_data_segment_is_not_accepted_as_code(self):
        self.assertFalse(check_image(BUILD, self.image, (0, 4))['timing_checks_passed'])


class TableTests(unittest.TestCase):
    def setUp(self):
        table = FRAME_TABLE - BASE
        self.image = bytearray(table + 128)
        self.text = (0, table)
        self.rodata = (table, 128)
        for _, address, word in TIMING_SITES:
            struct.pack_into('<I', self.image, address - BASE, word)
        struct.pack_into('<5Q', self.image, table, *FRAME_INTERVALS)
        for address in FRAME_TABLE_REFS:
            delta = ((FRAME_TABLE & ~4095) - (address & ~4095)) >> 12
            delta &= (1 << 21) - 1
            adrp = 0x90000008 | ((delta & 3) << 29) | ((delta >> 2) << 5)
            add = 0x91000000 | ((FRAME_TABLE & 4095) << 10) | (8 << 5) | 8
            struct.pack_into('<II', self.image, address - BASE, adrp, add)

    def result(self):
        return check_image(BUILD, self.image, self.text, self.rodata)

    def test_table_and_references_match_without_enabling_runtime(self):
        result = self.result()
        self.assertTrue(result['bootstrap_checks_passed'])
        self.assertFalse(result['runtime_support'])

    def test_duplicate_table_rejected(self):
        struct.pack_into('<5Q', self.image, FRAME_TABLE - BASE + 64, *FRAME_INTERVALS)
        self.assertFalse(self.result()['bootstrap_checks_passed'])

    def test_wrong_reference_target_rejected(self):
        offset = FRAME_TABLE_REFS[0] - BASE + 4
        word = struct.unpack_from('<I', self.image, offset)[0]
        struct.pack_into('<I', self.image, offset, word ^ (1 << 10))
        self.assertFalse(self.result()['bootstrap_checks_passed'])

    def test_reference_register_mismatch_rejected(self):
        self.image[FRAME_TABLE_REFS[0] - BASE + 4] ^= 1
        self.assertFalse(self.result()['bootstrap_checks_passed'])

    def test_table_must_be_read_only_data(self):
        self.assertFalse(check_image(BUILD, self.image, self.text, (0, 8))['bootstrap_checks_passed'])

    def test_bootstrap_is_off_by_default(self):
        self.assertFalse(bootstrap_allowed(BUILD, {}, self.image, self.text, self.rodata))

    def test_bootstrap_needs_exact_opt_in(self):
        for value in ('0', 'true', '1extra', ''):
            self.assertFalse(bootstrap_allowed(BUILD, {'LZA_EXPERIMENTAL_ZA100_BOOTSTRAP': value},
                                               self.image, self.text, self.rodata))

    def test_bootstrap_accepts_only_verified_image(self):
        env = {'LZA_EXPERIMENTAL_ZA100_BOOTSTRAP': '1'}
        self.assertTrue(bootstrap_allowed(BUILD, env, self.image, self.text, self.rodata))
        self.image[TIMING_SITES[0][1] - BASE] ^= 1
        self.assertFalse(bootstrap_allowed(BUILD, env, self.image, self.text, self.rodata))

    def test_opt_in_does_not_enable_other_builds(self):
        self.assertFalse(bootstrap_allowed('8a1c86c437394b69', {'LZA_EXPERIMENTAL_ZA100_BOOTSTRAP': '1'},
                                           self.image, self.text, self.rodata))


if __name__ == '__main__':
    unittest.main()

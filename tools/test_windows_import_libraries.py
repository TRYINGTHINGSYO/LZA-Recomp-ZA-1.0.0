"""Check the link inputs without requiring a Windows compiler or game files."""
import importlib.util
from pathlib import Path
import tempfile
import unittest

spec = importlib.util.spec_from_file_location('windows_builder', Path(__file__).parent / 'windows' / 'build.py')
builder = importlib.util.module_from_spec(spec)
spec.loader.exec_module(builder)


class ImportLibrariesTests(unittest.TestCase):
    def test_dll_import_wins_over_static_archive(self):
        with tempfile.TemporaryDirectory() as directory:
            lib = Path(directory) / 'lib'
            lib.mkdir()
            (lib / 'libavformat.a').touch()
            dll_import = lib / 'libavformat.dll.a'
            dll_import.touch()
            result = builder.import_libraries(directory)
            self.assertIn(str(dll_import), result)
            self.assertNotIn('-lavformat', result)
            self.assertIn('-lwinmm', result)

    def test_original_library_flags_remain_without_import_archives(self):
        with tempfile.TemporaryDirectory() as directory:
            self.assertEqual(builder.import_libraries(directory), builder.LIBS)


if __name__ == '__main__':
    unittest.main()

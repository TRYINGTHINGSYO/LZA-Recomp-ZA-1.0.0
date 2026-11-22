"""Read-only checks for the experimental Z-A 1.0.0 port. Never enables patches.

Run with the release's bundled Python, which includes lz4:
  python tools/za100_preflight.py --main /your/exefs/main --out /local/report.json
The output contains build identifiers, check results and source locations only.
"""
import argparse
import json
from pathlib import Path
import re
import struct

BUILD = '7222e13ecf6adb32'
BASE = 0x7000000000
# Locations documented in Hexveil404/PokeZ-ARecomp tools/za_patches.py.
# Matching these instructions is necessary, not sufficient for runtime support.
TIMING_SITES = (
    ('frame_entry', 0x70019e3730, 0xa9bd7bfd),
    ('frame_this', 0x70019e3750, 0xaa0003f3),
    ('frame_config', 0x70019e37a4, 0xf9402269),
    ('frame_mode', 0x70019e37a8, 0x39c08134),
    ('frame_duration', 0x70019e3740, 0xf9400428),
    ('frame_channel_step', 0x70019e3848, 0x2a1403e2),
)
FRAME_TABLE = 0x70031e6a70
FRAME_INTERVALS = (16666667, 33333334, 50000000, 66666667, 83333334)
# ADRP/ADD references found independently in the user's 1.0.0 image.
FRAME_TABLE_REFS = (0x70000d5ab0, 0x70000d5e40, 0x7000ed0d60,
                    0x70019e41b4, 0x7001a0e14c, 0x7002891af4)
ADDRESS = re.compile(r'(?<![\w])(?:0x|f_)(700[0-9a-fA-F]{7})(?![0-9a-fA-F])')


def table_reference(image, text, address):
    """Decode the ADRP/ADD pair without depending on a disassembler."""
    offset = address - BASE
    start, size = text
    if not (start <= offset and offset + 8 <= start + size and offset + 8 <= len(image)):
        return False
    page, add = struct.unpack_from('<II', image, offset)
    if page & 0x9f000000 != 0x90000000 or add & 0xffc00000 != 0x91000000:
        return False
    register = page & 31
    if add & 31 != register or (add >> 5) & 31 != register:
        return False
    immediate = ((page >> 5) & 0x7ffff) << 2 | ((page >> 29) & 3)
    if immediate & (1 << 20):
        immediate -= 1 << 21
    target = (address & ~4095) + (immediate << 12) + ((add >> 10) & 4095)
    return target == FRAME_TABLE


def check_image(build_id, image, text, rodata=None):
    """Reject a different build before looking at any instruction locations."""
    if build_id[:16].lower() != BUILD:
        raise ValueError('Expected Z-A 1.0.0 build ' + BUILD)
    start, length = text
    sites = []
    for name, address, expected in TIMING_SITES:
        offset = address - BASE
        in_text = start <= offset and offset + 4 <= start + length
        matched = (in_text and offset + 4 <= len(image)
                   and struct.unpack_from('<I', image, offset)[0] == expected)
        sites.append({'name': name, 'address': hex(address), 'matched': bool(matched)})
    table_bytes = struct.pack('<5Q', *FRAME_INTERVALS)
    offset = FRAME_TABLE - BASE
    in_rodata = rodata is not None and rodata[0] <= offset and offset + len(table_bytes) <= sum(rodata)
    table_ok = bool(in_rodata and image[offset:offset + len(table_bytes)] == table_bytes
                    and image.find(table_bytes) == offset and image.find(table_bytes, offset + 1) == -1)
    refs = [{'address': hex(a), 'matched': table_reference(image, text, a)} for a in FRAME_TABLE_REFS]
    return {'build': BUILD, 'timing_checks': sites,
            'timing_checks_passed': all(site['matched'] for site in sites),
            'frame_table': {'address': hex(FRAME_TABLE), 'matched_unique_rodata': table_ok},
            'frame_table_references': refs,
            'bootstrap_checks_passed': all(s['matched'] for s in sites) and table_ok and all(r['matched'] for r in refs),
            'runtime_support': False,
            'reason': 'Timing sites alone do not validate the remaining version-specific hooks.'}


def inventory(root):
    """Inventory candidates; shared files also contain other games' addresses."""
    uses = {}
    for path in sorted((root / 'runtime').rglob('*')):
        if path.suffix not in ('.c', '.h', '.cpp'):
            continue
        for number, line in enumerate(path.read_text(encoding='utf-8').splitlines(), 1):
            for match in ADDRESS.finditer(line):
                key = '0x' + match.group(1).lower()
                uses.setdefault(key, []).append({'file': path.relative_to(root).as_posix(),
                                                 'line': number})
    return uses


def bootstrap_allowed(build, environ, image, text, rodata):
    if build.lower() != BUILD or environ.get('LZA_EXPERIMENTAL_ZA100_BOOTSTRAP') != '1':
        return False
    return check_image(build, image, text, rodata)['bootstrap_checks_passed']


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--main', required=True, type=Path)
    parser.add_argument('--out', type=Path)
    args = parser.parse_args()
    from nso import Nso
    game = Nso(args.main)
    report = check_image(game.build_id, game.image, game.text, game.rodata)
    report['address_candidates'] = inventory(Path(__file__).resolve().parents[1])
    output = json.dumps(report, indent=2) + '\n'
    if args.out:
        args.out.write_text(output, encoding='utf-8')
    print(json.dumps({k: v for k, v in report.items() if k != 'address_candidates'}, indent=2))
    print('Version-specific address candidates:', len(report['address_candidates']))
    return 0 if report['bootstrap_checks_passed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())

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
    ('frame_mode', 0x70019e37a8, 0x39c08134),
    ('frame_duration', 0x70019e3740, 0xf9400428),
    ('frame_channel_step', 0x70019e3848, 0x2a1403e2),
)
ADDRESS = re.compile(r'(?<![\w])(?:0x|f_)(700[0-9a-fA-F]{7})(?![0-9a-fA-F])')


def check_image(build_id, image, text):
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
    return {'build': BUILD, 'timing_checks': sites,
            'timing_checks_passed': all(site['matched'] for site in sites),
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


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--main', required=True, type=Path)
    parser.add_argument('--out', type=Path)
    args = parser.parse_args()
    from nso import Nso
    game = Nso(args.main)
    report = check_image(game.build_id, game.image, game.text)
    report['address_candidates'] = inventory(Path(__file__).resolve().parents[1])
    output = json.dumps(report, indent=2) + '\n'
    if args.out:
        args.out.write_text(output, encoding='utf-8')
    print(json.dumps({k: v for k, v in report.items() if k != 'address_candidates'}, indent=2))
    print('Version-specific address candidates:', len(report['address_candidates']))
    return 0 if report['timing_checks_passed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())

#!/usr/bin/env python3
"""Apply a PPF 3.0 patch to the original disc image, with SHA-256 checks before and after.

Usage:  python apply_patch.py <original.bin> <patch.ppf> [output.bin]
Without output.bin the patched disc is written next to the original, named:
          Yu-Gi-Oh! Forbidden Memories (3D).bin        (yugioh-fm-3d.ppf)
          Yu-Gi-Oh! Forbidden Memories (3D)(Mod5).bin  (yugioh-fm-3d-5cards.ppf)
and a matching .cue file is created.  The original file is never modified.
Patches:  yugioh-fm-3d.ppf         - 3D monsters + all 722 cards, 1 card per won duel
          yugioh-fm-3d-5cards.ppf  - 3D monsters + all 722 cards, 5 cards per won duel
Needs nothing but Python 3.
"""
import hashlib
import os
import struct
import sys

# SHA-256 of the original disc (SLUS-01411, USA, single-track .bin) and of each patched disc (see README)
SHA_ORIG = '6e22494a45bf50fa2d239cd3819a57163a5f9b91e0365babc3e101509b5c3a7c'
# the patch is recognised by the description in its header (bytes 6..55), so renaming the .ppf is fine
SHA_PATCHED = {
    b'Yu-Gi-Oh! FM (SLUS-01411) - 3D monsters':
        ('3D monsters, 1 card per win', '4c3fa18fd6ef4baa5d96842c0d4f3d72efb07e8529ab5dc633f2c12a028cdc04',
         'Yu-Gi-Oh! Forbidden Memories (3D).bin'),
    b'Yu-Gi-Oh! FM (SLUS-01411) - 3D monsters + 5 cards':
        ('3D monsters, 5 cards per win', 'ceec87a53e0e3778f00c730972fb909dfc66647a5213bd0ac61f9004b86ba9a0',
         'Yu-Gi-Oh! Forbidden Memories (3D)(Mod5).bin'),
}


def sha(data):
    return hashlib.sha256(data).hexdigest()


def write_cue(dst):
    """create the .cue next to the new .bin (one track, Mode2/2352)"""
    cue = os.path.splitext(dst)[0] + '.cue'
    lines = ['FILE "%s" BINARY' % os.path.basename(dst),
             '  TRACK 01 MODE2/2352',
             '    INDEX 01 00:00:00']
    with open(cue, 'wb') as f:
        f.write(('\r\n'.join(lines) + '\r\n').encode('utf-8'))
    return cue


def main(src, ppf, dst=None):
    data = bytearray(open(src, 'rb').read())
    if SHA_ORIG and sha(data) != SHA_ORIG:
        sys.exit('Wrong original disc (SHA-256 does not match). You need the single-track Mode2/2352 .bin of '
                 'SLUS-01411 (USA).')
    p = open(ppf, 'rb').read()
    if p[:5] != b'PPF30' or p[5] != 2:
        sys.exit('Not a PPF 3.0 file.')
    name, sha_patched, out_name = SHA_PATCHED.get(p[6:56].rstrip(b' '), ('unknown', None, 'patched.bin'))
    print('patch: %s' % name)
    if not dst:
        dst = os.path.join(os.path.dirname(os.path.abspath(src)), out_name)
    if os.path.abspath(dst) == os.path.abspath(src):
        sys.exit('The output file is the original file - choose another name.')
    # PPF3 header: 56 image type, 57 blockcheck, 58 undo, 59 dummy; records from byte 60
    # (after a 1024-byte block when blockcheck is on) - the PPF-O-Matic standard
    undo = p[58]
    pos, n = 60 + (1024 if p[57] else 0), 0
    while pos < len(p):
        off = struct.unpack_from('<Q', p, pos)[0]
        ln = p[pos + 8]
        pos += 9
        data[off:off + ln] = p[pos:pos + ln]
        pos += ln + (ln if undo else 0)
        n += 1
    open(dst, 'wb').write(data)
    print('created %s' % write_cue(dst))
    h = sha(data)
    print('applied %d records -> %s' % (n, dst))
    print('sha256 of the patched disc: %s' % h)
    if sha_patched:
        print('MATCHES the release' if h == sha_patched else 'DOES NOT MATCH - your original disc may differ from the '
                                                              'standard dump')


if __name__ == '__main__':
    if len(sys.argv) not in (3, 4):
        sys.exit(__doc__)
    main(*sys.argv[1:])

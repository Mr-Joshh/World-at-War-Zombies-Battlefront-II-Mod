"""Read SWBF2 (2005) PC sample banks (sound/*.bnk and the SampleBank chunks inside sound/*.lvl).

Layout (all names are FNV-1a hashes of lower-cased strings):
  ucfb > [wrapper] > SampleBank > Info { Name, Format, NumSamples, Size, ..., then per sample:
  Sample, ID <name hash>, Frequency <hz>, Size <bytes>, <sample count>, Padding ... } followed by a Data chunk
  holding the samples back to back.  Format 2 = 16-bit mono PCM.
"""
import struct, sys, os, wave


def fnv(s):
    h = 0x811c9dc5
    for c in s.lower().encode():
        h = ((h ^ c) * 0x01000193) & 0xffffffff
    return h


H = {n: fnv(n) for n in ('SampleBank', 'Info', 'Data', 'Name', 'Format', 'NumSamples', 'Sample', 'ID', 'Frequency', 'Size', 'Padding')}


def banks(path):
    """Yield (bank_name_hash, fmt, [sample dict], data_offset) for every SampleBank in the file."""
    d = open(path, 'rb').read()
    pos = 0
    key = struct.pack('<I', H['SampleBank'])
    while True:
        pos = d.find(key, pos)
        if pos < 0:
            return
        size = struct.unpack_from('<I', d, pos + 4)[0]
        o = pos + 8
        if struct.unpack_from('<I', d, o)[0] != H['Info']:
            pos += 4
            continue
        info_size = struct.unpack_from('<I', d, o + 4)[0]
        words = struct.unpack_from('<%dI' % (info_size // 4), d, o + 8)
        name = fmt = None
        samples, cur = [], None
        i = 0
        pair = (H['Name'], H['Format'], H['NumSamples'], H['ID'], H['Frequency'], H['Size'], H['Padding'])
        while i < len(words) - 1:
            w, v = words[i], words[i + 1]
            if w == H['Sample']:
                cur = {}
                samples.append(cur)
                i += 1
                continue
            if cur is not None and w == 0x7d268157:   # alias of another sample: no data of its own
                cur['alias'] = v
                i += 2
                continue
            if w not in pair:           # single-word markers
                i += 1
                continue
            if cur is None:
                if w == H['Name']: name = v
                elif w == H['Format']: fmt = v
            else:
                if w == H['ID']: cur['id'] = v
                elif w == H['Frequency']: cur['freq'] = v
                elif w == H['Size']: cur['size'] = v
            i += 2
        # Data chunk follows Info (4-byte aligned)
        p = o + 8 + info_size
        p += (-p) % 4
        data_off = None
        if struct.unpack_from('<I', d, p)[0] == H['Data']:
            data_off = p + 8
        yield {'name': name, 'format': fmt, 'samples': [s for s in samples if 'size' in s], 'data_off': data_off, 'buf': d}
        pos += 8 + info_size


def extract(bank, sample, out):
    off = bank['data_off']
    for s in bank['samples']:
        if s is sample:
            break
        off += 0 if 'alias' in s else s['size']
    pcm = bank['buf'][off:off + sample['size']]
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with wave.open(out, 'wb') as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(sample['freq'])
        w.writeframes(pcm)
    return len(pcm) / 2 / sample['freq']


if __name__ == '__main__':
    for b in banks(sys.argv[1]):
        print('bank %08x format %s samples %d data@%s' % (b['name'] or 0, b['format'], len(b['samples']), b['data_off']))

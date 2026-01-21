#!/usr/bin/env python3
"""
MP4 Datetime Binary Fuzzer - Large File Friendly, CLI Options, SHA256 Support

Fuzzes mvhd, tkhd, mdhd datetime fields in MP4 files using direct binary patching.
"""

import argparse
import os
import struct
import random
import csv
import datetime
import hashlib

MP4_EPOCH = datetime.datetime(1904, 1, 1)

def parse_atoms(f, start, end, atom_types, bit_depth, field_filter, positions):
    f.seek(start)
    while f.tell() < end:
        pos = f.tell()
        header = f.read(8)
        if len(header) < 8:
            break
        size, atom_type = struct.unpack('>I4s', header)

        if size == 1:
            size_bytes = f.read(8)
            if len(size_bytes) < 8:
                break
            size = struct.unpack('>Q', size_bytes)[0]
            header_size = 16
        else:
            header_size = 8

        if size < header_size or pos + size > end:
            break

        if atom_type in atom_types:
            f.seek(pos + header_size)
            version_flags = f.read(4)
            if len(version_flags) < 4:
                f.seek(pos + size)
                continue
            version = version_flags[0]

            if (bit_depth == 32 and version != 0) or (bit_depth == 64 and version != 1):
                f.seek(pos + size)
                continue

            field_size = 4 if version == 0 else 8
            base = pos + header_size + 4 + (0 if version == 0 else 4)

            if field_filter in ('creation', 'both'):
                positions.append({'offset': base, 'size': field_size,
                                  'atom': atom_type.decode(), 'field': 'creation_time'})
            if field_filter in ('modification', 'both'):
                positions.append({'offset': base + field_size, 'size': field_size,
                                  'atom': atom_type.decode(), 'field': 'modification_time'})

        elif atom_type in [b'moov', b'trak', b'mdia', b'minf', b'stbl']:
            parse_atoms(f, pos + header_size, pos + size, atom_types, bit_depth, field_filter, positions)

        f.seek(pos + size)

def find_atom_positions(filepath, atom_types, bit_depth, field_filter):
    positions = []
    with open(filepath, 'rb') as f:
        filesize = os.path.getsize(filepath)
        parse_atoms(f, 0, filesize, atom_types, bit_depth, field_filter, positions)
    return positions

def generate_fuzz_value(pos_size, args):
    bits = pos_size * 8
    if args.signed:
        min_val = max(args.min_value, -(1 << (bits - 1)))
        max_val = min(args.max_value, (1 << (bits - 1)) - 1)
    else:
        min_val = max(args.min_value, 0)
        max_val = min(args.max_value, (1 << bits) - 1)

    boundary = [min_val, max_val]
    if args.signed:
        boundary += [0, -1, 1]

    if args.value_mode == 'boundary':
        return random.choice(boundary)
    elif args.value_mode == 'mixed':
        return random.choice(boundary + [random.randint(min_val, max_val)])
    else:
        return random.randint(min_val, max_val)

def compute_sha256(filepath):
    hasher = hashlib.sha256()
    with open(filepath, 'rb') as f:
        for chunk in iter(lambda: f.read(8192), b''):
            hasher.update(chunk)
    return hasher.hexdigest()

def create_fuzzed_file(input_file, output_file, positions, test_id, max_fields, log_writer, args):
    selected = positions if max_fields <= 0 else random.sample(positions, min(max_fields, len(positions)))
    field_values = [(pos, generate_fuzz_value(pos['size'], args)) for pos in selected]

    if args.dry_run:
        for pos, value in field_values:
            log_writer.writerow([test_id, 'DRY-RUN', '', pos['atom'], pos['field'],
                                 pos['offset'], value, 'SKIPPED'])
        return

    with open(input_file, 'rb') as src, open(output_file, 'wb') as dst:
        while chunk := src.read(8192):
            dst.write(chunk)

    with open(output_file, 'r+b') as f:
        for pos, value in field_values:
            f.seek(pos['offset'])
            packed = struct.pack('>I' if pos['size'] == 4 else '>Q', value)
            f.write(packed)

    sha = compute_sha256(output_file) if args.hash else ''
    if sha:
        new_name = f"fuzz_{test_id:03d}_{sha[:8]}.mp4"
        new_path = os.path.join(os.path.dirname(output_file), new_name)
        os.rename(output_file, new_path)
        output_file = new_path
    filename_for_log = os.path.basename(output_file)

    for pos, value in field_values:
        log_writer.writerow([test_id, filename_for_log, sha, pos['atom'], pos['field'],
                             pos['offset'], value, ''])

def main():
    parser = argparse.ArgumentParser(description="MP4 datetime fuzzer (large-file safe, flexible)")
    parser.add_argument('--input', '-i', required=True, help='Input MP4 file')
    parser.add_argument('--output', '-o', default='fuzz_outputs', help='Directory for fuzzed files')
    parser.add_argument('--count', '-n', type=int, default=100, help='Number of output files to generate')
    parser.add_argument('--atoms',
                    nargs='+',
                    default=['mvhd', 'tkhd', 'mdhd', 'stts', 'elst', 'edts'],
                    choices=['mvhd', 'tkhd', 'mdhd', 'stts', 'elst', 'edts'],
                    help='Atom types to fuzz: movie header (mvhd), track header (tkhd), media header (mdhd), time-to-sample (stts), edit list (elst), edit box (edts)')
    parser.add_argument('--bit-depth', type=int, choices=[32, 64], default=32, help='Field size: 32 or 64-bit')
    parser.add_argument('--fields', choices=['creation', 'modification', 'both'], default='both', help='Fields to fuzz')
    parser.add_argument('--fuzz-fields', type=int, default=20, help='Number of timestamp fields to fuzz per file')
    parser.add_argument('--log', default='fuzz_mapping.csv', help='CSV file to log fuzzed changes')
    parser.add_argument('--min-value', type=int, default=0, help='Minimum value to use for fuzzing')
    parser.add_argument('--max-value', type=int, default=0xFFFFFFFFFFFFFFFF, help='Maximum value for fuzzing')
    parser.add_argument('--signed', action='store_true', help='Use signed integer ranges')
    parser.add_argument('--value-mode', choices=['random', 'boundary', 'mixed'], default='random',
                        help='Value generation strategy')
    parser.add_argument('--seed', type=int, help='Random seed for reproducibility')
    parser.add_argument('--dry-run', action='store_true', help='Do not write files, simulate only')
    parser.add_argument('--hash', action='store_true', help='Append SHA256 hash of content to filename')

    args = parser.parse_args()
    if args.seed is not None:
        random.seed(args.seed)

    os.makedirs(args.output, exist_ok=True)
    atom_bytes = [a.encode('ascii') for a in args.atoms]

    positions = find_atom_positions(args.input, atom_bytes, args.bit_depth, args.fields)
    if not positions:
        print("No matching atom fields found.")
        return

    with open(args.log, 'w', newline='') as logfile:
        writer = csv.writer(logfile)
        writer.writerow(['test_id', 'filename', 'sha256', 'atom', 'field', 'offset', 'value', 'note'])

        for idx in range(args.count):
            out_path = os.path.join(args.output, f'fuzz_{idx:03d}.mp4')
            create_fuzzed_file(args.input, out_path, positions, idx, args.fuzz_fields, writer, args)
            print(f"Completed file {idx + 1}/{args.count}")

if __name__ == '__main__':
    main()

#!/usr/bin/env python3
import os
import random
import argparse

def parse_byte_set(byte_strings):
    return bytes(int(b, 16) for b in byte_strings)

def modify_file_randomly(path, byte_set, length, count, spacing):
    file_size = os.path.getsize(path)
    with open(path, "r+b") as f:
        for _ in range(count):
            pos = random.randint(0, file_size - length)
            f.seek(pos)
            chunk = bytes(random.choice(byte_set) for _ in range(length))
            f.write(chunk)
            print(f"Wrote {length} at position {pos}")
            if spacing > 0:
                pos += spacing

def main():
    parser = argparse.ArgumentParser(description="Scatter random bytes into a binary file.")
    parser.add_argument("file", help="Path to the binary file to modify")
    parser.add_argument("--byte-set", nargs="+", default=["00", "ff"], help="Set of hex byte values to use (e.g., 00 ff aa)")
    parser.add_argument("--length", type=int, default=1, help="Length of each modification in bytes")
    parser.add_argument("--count", type=int, default=100, help="Number of random modifications to perform")
    parser.add_argument("--spacing", type=int, default=0, help="Minimum number of bytes between modifications (optional)")
    args = parser.parse_args()

    byte_set = parse_byte_set(args.byte_set)
    modify_file_randomly(args.file, byte_set, args.length, args.count, args.spacing)

if __name__ == "__main__":
    main()

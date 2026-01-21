#!/usr/bin/env python3

import random
import argparse

LOREM_WORDS = (
    "lorem ipsum dolor sit amet consectetur adipiscing elit sed do eiusmod tempor incididunt "
    "ut labore et dolore magna aliqua ut enim ad minim veniam quis nostrud exercitation ullamco "
    "laboris nisi ut aliquip ex ea commodo consequat duis aute irure dolor in reprehenderit in "
    "voluptate velit esse cillum dolore eu fugiat nulla pariatur excepteur sint occaecat cupidatat "
    "non proident sunt in culpa qui officia deserunt mollit anim id est laborum "
    "fermentum sagittis curabitur blandit rhoncus bibendum commodo pharetra sollicitudin elementum "
    "facilisi pulvinar hendrerit lacinia vestibulum dapibus dignissim fringilla tempus varius "
    "aliquam etiam primis litora nascetur habitasse aptent feugiat inceptos suspendisse turpis "
    "convallis iaculis vehicula imperdiet accumsan porttitor facilisis rutrum ultricies netus "
    "senectus ridiculus platea torquent penatibus integer laoreet cras sociosqu tincidunt euismod "
    "faucibus mauris pharetra phasellus malesuada dictumst habitant arcu dictum viverra est "
    "nibh volutpat scelerisque lectus felis nulla donec magna sem ornare quam quisque morbi "
    "urna eros mollis cubilia ante id potenti tristique nonummy suscipit justo nec per "
    "tincidunt eros mauris facilisis varius taciti eget congue accumsan montes fusce "
    "gravida pretium utinam sociosqu scelerisque nam sodales risus potenti nostra porta "
    "dictum sapien fusce eleifend ornare tristique sollicitudin fringilla senectus mattis "
    "semper class lobortis cursus torquent sociis maecenas augue luctus sapien fusce"
).split()

def generate_sentence(min_words=6, max_words=12):
    length = random.randint(min_words, max_words)
    words = random.choices(LOREM_WORDS, k=length)
    sentence = ' '.join(words).capitalize() + '.'
    return sentence

def print_lorem_bytes(target_bytes, min_words=6, max_words=12):
    total_bytes = 0

    while total_bytes < target_bytes:
        sentence = generate_sentence(min_words, max_words)
        candidate = sentence + ' '
        if total_bytes + len(candidate.encode("utf-8")) > target_bytes:
            break
        print(candidate)
        total_bytes += len(candidate.encode("utf-8"))


def main():
    parser = argparse.ArgumentParser(description="Generate Lorem Ipsum text of a specific size in bytes.")
    parser.add_argument("-b", "--bytes", type=int, required=True, help="Desired output size in bytes")
    parser.add_argument("--min", type=int, default=6, help="Minimum words per sentence")
    parser.add_argument("--max", type=int, default=12, help="Maximum words per sentence")
    args = parser.parse_args()

    print_lorem_bytes(args.bytes, args.min, args.max)

if __name__ == "__main__":
    main()

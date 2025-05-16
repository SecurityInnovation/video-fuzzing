#!/usr/bin/env python3

import os
import sys
import argparse
import textwrap
from PIL import Image, ImageDraw, ImageFont

def get_font(fontfile, fontsize):
    if fontfile:
        try:
            return ImageFont.truetype(fontfile, fontsize)
        except Exception as e:
            print(f"Failed to load font '{fontfile}': {e}")
            print("Falling back to default TTF font.")

    fallback_fonts = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/Library/Fonts/Arial.ttf",
        "C:\\Windows\\Fonts\\arial.ttf"
    ]
    for path in fallback_fonts:
        if os.path.exists(path):
            return ImageFont.truetype(path, fontsize)

    return None

def generate_images(text, fontsize, fontcolor, background, maxwidth, maxheight, margin, output_dir, fontfile=None, listfile=None):
    char_width_factor = 0.6
    line_height_factor = 1.5
    char_pixel_width = fontsize * char_width_factor
    line_height = int(fontsize * line_height_factor)

    max_chars_per_line = int((maxwidth - 2 * margin) // char_pixel_width)
    max_lines_per_image = int((maxheight - 2 * margin) // line_height)

    wrapped_text = textwrap.fill(text, width=max_chars_per_line)
    all_lines = wrapped_text.split("\n")

    width = max(640, maxwidth + maxwidth % 2)
    height = max(480, maxheight + maxheight % 2)

    os.makedirs(output_dir, exist_ok=True)

    try:
        font = get_font(fontfile, fontsize)
    except RuntimeError as e:
        print(e)
        return

    output_paths = []

    for i in range(0, len(all_lines), max_lines_per_image):
        img = Image.new("RGB", (width, height), background)
        draw = ImageDraw.Draw(img)

        for j, line in enumerate(all_lines[i:i + max_lines_per_image]):
            y = margin + j * line_height
            draw.text((margin, y), line, font=font, font_size=fontsize, fill=fontcolor)

        output_path = os.path.abspath(os.path.join(output_dir, f"frame_{i // max_lines_per_image + 1:03}.png"))
        img.save(output_path)
        output_paths.append(output_path)

    if listfile:
        with open(listfile, "w", encoding="utf-8") as f:
            for path in output_paths:
                f.write(path + "\n")

    print(f"Generated {len(output_paths)} image(s) at {width}x{height} in '{output_dir}'.")

def main():
    parser = argparse.ArgumentParser(description="Generate a series of images from text.")
    parser.add_argument("--fontsize", type=int, default=32, help="Font size in pixels (default: 32)")
    parser.add_argument("--fontfile", help="Path to a TTF/OTF font file")
    parser.add_argument("--output-dir", default="frames", help="Directory to save output images")
    parser.add_argument("--list-file", help="Write the list of image paths to this file")
    parser.add_argument("--fontcolor", default="white", help="Font color (default: white)")
    parser.add_argument("--background", default="black", help="Background color (default: black)")
    parser.add_argument("--maxwidth", type=int, default=1280, help="Maximum image width (default: 1280)")
    parser.add_argument("--maxheight", type=int, default=720, help="Maximum image height (default: 720)")
    parser.add_argument("--margin", type=int, default=10, help="Margin in pixels (default: 10)")
    parser.add_argument("text", nargs=argparse.REMAINDER, help="Text to display across images")

    args = parser.parse_args()

    if args.text:
        display_text = " ".join(args.text)
    else:
        display_text = sys.stdin.read().strip()
        if not display_text:
            parser.error("No text provided via arguments or stdin.")

    generate_images(
        display_text, args.fontsize, args.fontcolor,
        args.background, args.maxwidth, args.maxheight,
        args.margin, args.output_dir, args.fontfile, args.list_file
    )

if __name__ == "__main__":
    main()

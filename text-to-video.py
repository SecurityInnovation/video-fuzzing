#!/usr/bin/env python3

import subprocess
import shlex
import textwrap
import argparse
import tempfile
import os
import sys
import platform

def generate_tts_audio(text):
    """Generate TTS audio and return the temporary filename."""
    system = platform.system()

    if system == "Darwin":
        temp_audio = tempfile.NamedTemporaryFile(delete=False, suffix=".m4a")
    elif system == "Linux":
        temp_audio = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")
    else:
        print(f"Unsupported platform for TTS: {system}")
        sys.exit(1)

    temp_audio_path = temp_audio.name
    temp_audio.close()

    try:
        if system == "Darwin":
            subprocess.run(["say", "-o", temp_audio_path, text], check=True)
        elif system == "Linux":
            subprocess.run(["espeak", text, "--stdout"], stdout=open(temp_audio_path, "wb"), check=True)
    except Exception as e:
        print(f"Failed to generate TTS audio: {e}")
        sys.exit(1)

    return temp_audio_path

def generate_srt(text, duration_seconds):
    """Generate a simple one-line SRT subtitle file."""
    temp_sub = tempfile.NamedTemporaryFile(delete=False, suffix=".srt", mode="w", encoding="utf-8")
    temp_sub_path = temp_sub.name

    start_time = "00:00:00,000"
    end_minutes = duration_seconds // 60
    end_seconds = duration_seconds % 60
    end_time = f"00:{end_minutes:02}:{end_seconds:02},000"

    srt_content = f"""1
{start_time} --> {end_time}
{text}
"""
    temp_sub.write(srt_content)
    temp_sub.close()
    return temp_sub_path

def main():
    parser = argparse.ArgumentParser(
        description="Generate a video with text, optional Text-to-Speech, and optional embedded subtitles."
    )
    parser.add_argument("--fontsize", type=int, default=32, help="Font size in pixels (default: 32 pixels)")
    parser.add_argument("--duration", type=int, default=10, help="Duration of the video in seconds (default: 10)")
    parser.add_argument("--output", default="output.mp4", help="Output filename (default: output.mp4)")
    parser.add_argument("--fontcolor", default="white", help="Font color (default: white)")
    parser.add_argument("--background", default="black", help="Background color (default: black)")
    parser.add_argument("--maxwidth", type=int, default=1280, help="Maximum video width in pixels (default: 1280)")
    parser.add_argument("--volume", type=float, default=-30, help="White noise volume in decibels (dB) (default: -30)")
    parser.add_argument("--margin", type=int, default=10, help="Margin around the text in pixels (default: 10)")
    parser.add_argument("--tts", action="store_true", help="Use TTS audio instead of white noise")
    parser.add_argument("--tts-text", help="Alternate text to use for TTS (default: same as visible text)")
    parser.add_argument("--subtitle-text", help="Alternate text to use for subtitles (default: same as TTS text, which defaults to visible text)")
    parser.add_argument("--subtitle-language", default="eng", help="Subtitle language ISO 639-2 code (default: eng)")
    parser.add_argument("text", nargs=argparse.REMAINDER, help="Text to display and/or speak")
    args = parser.parse_args()

    if not args.text:
        parser.error("No text provided.")

    display_text = " ".join(args.text)
    tts_text = args.tts_text if args.tts_text else display_text
    subtitle_text = args.subtitle_text if args.subtitle_text else tts_text

    # -----------------------
    # Calculate video dimensions
    # -----------------------
    char_width_factor = 0.6
    line_height_factor = 1.5
    char_pixel_width = args.fontsize * char_width_factor

    max_chars_area = (args.maxwidth - args.margin * 2) // char_pixel_width
    max_chars_area = int(max_chars_area)

    wrapped_text = textwrap.fill(display_text, width=max_chars_area)
    lines = wrapped_text.split('\n')
    num_lines = len(lines)
    longest_line_length = max(len(line) for line in lines)

    width = int(longest_line_length * char_pixel_width) + args.margin * 2
    height = int(num_lines * args.fontsize * line_height_factor) + args.margin * 2

    if width < 640:
        width = 640
    if height < 480:
        height = 480

    width += width % 2
    height += height % 2

    print(f"Calculated video size: {width}x{height}")
    print(f"Text lines:")
    for line in lines:
        print(line)

    escaped_text = wrapped_text.replace("'", r"'\''")

    # -----------------------
    # Generate SRT subtitle
    # -----------------------
    subtitle_path = generate_srt(subtitle_text, args.duration)

    # -----------------------
    # Setup FFmpeg Inputs
    # -----------------------
    if args.tts:
        tts_audio_path = generate_tts_audio(tts_text)
        video_input = f"-f lavfi -i color=c={args.background}:s={width}x{height}:d={args.duration}"
        audio_input = f"-i {shlex.quote(tts_audio_path)}"
        subtitle_input = f"-f srt -i {shlex.quote(subtitle_path)}"
        video_map = "0:v"
        audio_map = "1:a"
    else:
        video_input = f"-f lavfi -i color=c={args.background}:s={width}x{height}:d={args.duration}"
        audio_input = f"-f lavfi -i anoisesrc=color=white:duration={args.duration}:sample_rate=44100"
        subtitle_input = f"-f srt -i {shlex.quote(subtitle_path)}"
        video_map = "0:v"
        audio_map = "[a]"

    if args.tts:
        filter_complex = f"[{video_map}]drawtext=text='{escaped_text}':font='Courier New Bold':fontcolor={args.fontcolor}:fontsize={args.fontsize}:x={args.margin}:y={args.margin}:line_spacing={int(args.fontsize * 0.5)}[v]"
    else:
        filter_complex = f"[{video_map}]drawtext=text='{escaped_text}':font='Courier New Bold':fontcolor={args.fontcolor}:fontsize={args.fontsize}:x={args.margin}:y={args.margin}:line_spacing={int(args.fontsize * 0.5)}[v];[1:a]volume={args.volume}dB[a]"

    # -----------------------
    # Build and Run FFmpeg Command
    # -----------------------
    command = f"""
    ffmpeg -y {video_input} {audio_input} {subtitle_input} \
    -filter_complex "{filter_complex}" \
    -map "[v]" -map {audio_map} -map 2:s:0 \
    -c:v libx264 -crf:v 20 -c:a aac -c:s mov_text \
    -metadata:s:s:0 language={args.subtitle_language} \
    {shlex.quote(args.output)}
    """

    print("Running command:")
    print(command)

    try:
        subprocess.run(command, shell=True, check=True)
    finally:
        if args.tts:
            os.unlink(tts_audio_path)
        os.unlink(subtitle_path)

if __name__ == "__main__":
    main()


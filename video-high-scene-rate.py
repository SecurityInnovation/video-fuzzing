#!/usr/bin/env python3

import argparse
import platform
import subprocess
import shutil
import random
from pathlib import Path
from urllib.parse import unquote
from itertools import cycle, islice

def run(cmd, quiet=False):
    if not quiet:
        print(f"Running: {' '.join(str(c) for c in cmd)}")
        subprocess.run(cmd, check=True)
    else:
        subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

def timestamp(seconds):
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    ms = int((seconds - int(seconds)) * 1000)
    return f"{h:02}:{m:02}:{s:02},{ms:03}"

def generate_srt(subtitles, duration_per_scene, output_file):
    with open(output_file, "w", encoding="utf-8") as f:
        for idx, text in enumerate(subtitles):
            start = timestamp(idx * duration_per_scene)
            end = timestamp((idx + 1) * duration_per_scene)
            f.write(f"{idx+1}\n{start} --> {end}\n{text}\n\n")

def main():
    parser = argparse.ArgumentParser(description="Generate video with excessive scene changes.")
    parser.add_argument("--output", default="scene_change.mp4", help="Output video file")
    parser.add_argument("--width", type=int, default=640, help="Video width")
    parser.add_argument("--height", type=int, default=480, help="Video height")
    parser.add_argument("--frame_rate", type=int, default=30, help="Frames per second")
    parser.add_argument("--total_frames", type=int, default=300, help="Total number of frames in output")
    parser.add_argument("--frames_per_scene", type=int, default=10, help="Number of frames per scene")
    parser.add_argument("--random-noise", action="store_true", help="Use only random noise for scenes")
    parser.add_argument("--mixed-scenes", action="store_true", help="Randomly mix noise, color, and images")
    parser.add_argument("--codec", choices=["h264", "h265"], default="h264", help="Video codec to use")
    parser.add_argument("--scene-label", type=Path, help="Path to text file with scene labels (0–255 chars per line)")
    parser.add_argument("--image-list", type=Path, help="Path to text file with image filenames (one per line)")
    parser.add_argument("--shuffle-images", action="store_true", help="Shuffle the image list before use")
    parser.add_argument("--add-audio", action="store_true", help="Add mono 4kHz white noise audio track")

    args = parser.parse_args()

    use_videotoolbox = (platform.system() == "Darwin")

    tmp_dir = Path("tmp_scenes")
    tmp_dir.mkdir(exist_ok=True)

    duration = args.frames_per_scene / args.frame_rate
    scene_count = args.total_frames // args.frames_per_scene

    colors = ['red', 'green', 'blue', 'yellow', 'cyan', 'magenta', 'white', 'black', 'orange', 'pink']

    scene_labels = []
    if args.scene_label:
        with args.scene_label.open("rb") as f:
            raw_lines = f.read().splitlines()
        scene_labels = [unquote(line.decode("latin1").strip()) for line in raw_lines if line.strip()]
        scene_labels = list(islice(cycle(scene_labels), scene_count))

    image_files = []
    if args.image_list:
        with args.image_list.open("r", encoding="utf-8") as f:
            image_files = [line.strip() for line in f if line.strip()]

    for i in range(scene_count):
        print(f"Generating scene {i + 1}/{scene_count}...")
        output_file = tmp_dir / f"scene_{i}.mp4"
        use_noise = use_image = use_color = False

        if args.mixed_scenes:
            options = ["noise", "color", "image"] if image_files else ["noise", "color"]
            choice = random.choice(options)
            use_noise = (choice == "noise")
            use_image = (choice == "image")
            use_color = (choice == "color")
        elif image_files:
            use_image = True
        elif args.random_noise:
            use_noise = True
        else:
            use_color = True

        if use_noise:
            run([
                "ffmpeg", "-y",
                "-f", "lavfi", "-i", f"nullsrc=s={args.width}x{args.height}:d={duration}",
                "-vf", f"noise=alls=100:allf=t+u,fps={args.frame_rate}",
                "-preset", "veryfast",
                str(output_file)
            ], quiet=True)
        elif use_image:
            if args.shuffle_images:
                image_path = image_files[random.randint(0, len(image_files)-1)]
            else:
                image_path = image_files[i % len(image_files)]
            run([
                "ffmpeg", "-y",
                "-loop", "1", "-i", image_path,
                "-t", str(duration),
                "-vf", f"scale={args.width}:{args.height},fps={args.frame_rate}",
                "-pix_fmt", "yuv420p",
                "-preset", "veryfast",
                str(output_file)
            ], quiet=True)
        else:
            color = colors[i % len(colors)]
            run([
                "ffmpeg", "-y",
                "-f", "lavfi", "-i", f"color=c={color}:s={args.width}x{args.height}:d={duration}",
                "-vf", f"fps={args.frame_rate}",
                "-preset", "veryfast",
                str(output_file)
            ], quiet=True)

    concat_file = tmp_dir / "inputs.txt"
    with concat_file.open("w") as f:
        for i in range(scene_count):
            f.write(f"file 'scene_{i}.mp4'\n")

    srt_file = None
    if scene_labels:
        srt_file = tmp_dir / "subtitles.srt"
        generate_srt(scene_labels[:scene_count], duration, srt_file)

    audio_file = tmp_dir / "audio.wav"
    if args.add_audio:
        total_duration = scene_count * duration
        run([
            "ffmpeg", "-y",
            "-f", "lavfi",
            "-i", f"anoisesrc=color=white:duration={total_duration}:sample_rate=44100",
            "-ac", "1",
            str(audio_file)
        ])

    if use_videotoolbox:
        codec_map = {
            "h264": "h264_videotoolbox",
            "h265": "hevc_videotoolbox"
        }
    else:
        codec_map = {
            "h264": "libx264",
            "h265": "libx265"
        }
    codec = codec_map[args.codec]

    x265_extra_params = []
    if args.codec == "h265" and (args.width > 8192 or args.height > 4320):
        if not use_videotoolbox:
            x265_extra_params = ["-x265-params", "level-idc=6.2"]

    ffmpeg_cmd = [
        "ffmpeg", "-y",
        "-f", "concat", "-safe", "0", "-i", str(concat_file)
    ]
    input_index = 1
    if srt_file:
        ffmpeg_cmd += ["-i", str(srt_file)]
        subtitle_index = input_index
        input_index += 1
    else:
        subtitle_index = None

    if args.add_audio:
        ffmpeg_cmd += ["-i", str(audio_file)]
        audio_index = input_index
    else:
        audio_index = None

    if args.add_audio:
        ffmpeg_cmd += ["-i", str(audio_file)]

    ffmpeg_cmd += ["-map", "0:v:0"]
    if subtitle_index is not None:
        ffmpeg_cmd += ["-map", f"{subtitle_index}:s:0"]
    if audio_index is not None:
        ffmpeg_cmd += ["-map", f"{audio_index}:a:0"]

    if args.add_audio:
        ffmpeg_cmd += ["-map", "2:a:0"]

    ffmpeg_cmd += [
        "-c:v", codec,
        *x265_extra_params,
        "-preset", "veryslow",
        "-crf:v", "28",
        "-b:v", "300k",
        "-c:s", "mov_text",
        "-pix_fmt", "yuv420p"
    ]

    if args.codec == "h265":
        ffmpeg_cmd += ["-tag:v", "hvc1"]

    if args.add_audio:
        ffmpeg_cmd += ["-c:a", "aac", "-ar", "11025", "-ac", "1"]

    ffmpeg_cmd.append(args.output)
    run(ffmpeg_cmd)

    shutil.rmtree(tmp_dir)

if __name__ == "__main__":
    main()


# video-fuzzing

## Description
Tools for creating media files to stress AV processing software.

MP4 is the primary format here, although `ffmpeg` is used for the actual AV work and it supports a lot of formats. Feel
free to add more formats.

## Installation

You'll need [ffmpeg](https://ffmpeg.org). It's the most popular open-source, command line AV tool.

```shell
brew install ffmpeg || apt-get install ffmpeg || yum install ffmpeg
```

## Usage

### video-high-scene-rate.py

When processes detect scene changes, aka chapters, we want to make a video with a LOT of them. The trade-off is to
keep the video a reasonable size. This script makes "scenes" using solid colors, random noise or from a list of images.

```commandline
usage: video-high-scene-rate.py [-h] [--output OUTPUT] [--width WIDTH] [--height HEIGHT] [--frame_rate FRAME_RATE] [--total_frames TOTAL_FRAMES]
                                [--frames_per_scene FRAMES_PER_SCENE] [--random-noise] [--mixed-scenes] [--codec {h264,h265}] [--scene-label SCENE_LABEL]
                                [--image-list IMAGE_LIST] [--shuffle-images] [--add-audio]

Generate video with excessive scene changes.

options:
  -h, --help            show this help message and exit
  --output OUTPUT       Output video file
  --width WIDTH         Video width
  --height HEIGHT       Video height
  --frame_rate FRAME_RATE
                        Frames per second
  --total_frames TOTAL_FRAMES
                        Total number of frames in output
  --frames_per_scene FRAMES_PER_SCENE
                        Number of frames per scene
  --random-noise        Use only random noise for scenes
  --mixed-scenes        Randomly mix noise, color, and images
  --codec {h264,h265}   Video codec to use
  --scene-label SCENE_LABEL
                        Path to text file with scene labels (0–255 chars per line)
  --image-list IMAGE_LIST
                        Path to text file with image filenames (one per line)
  --shuffle-images      Shuffle the image list before use
  --add-audio           Add mono 4kHz white noise audio track
```

### text-to-video.py

Especially for LLMs, we want video with readable text in the video, audio and subtitles. We may want that text
to be mismatched.

```commandline
usage: text-to-video.py [-h] [--fontsize FONTSIZE] [--duration DURATION] [--output OUTPUT] [--fontcolor FONTCOLOR] [--background BACKGROUND] [--maxwidth MAXWIDTH]
                        [--volume VOLUME] [--margin MARGIN] [--tts] [--tts-text TTS_TEXT] [--subtitle-language SUBTITLE_LANGUAGE]
                        ...

Generate a video with text, optional text-to-speech (TTS), and embedded subtitles.

positional arguments:
  text                  Text to display and/or speak

options:
  -h, --help            show this help message and exit
  --fontsize FONTSIZE   Font size in pixels (default: 32)
  --duration DURATION   Duration of the video in seconds (default: 10)
  --output OUTPUT       Output filename (default: output.mp4)
  --fontcolor FONTCOLOR
                        Font color (default: white)
  --background BACKGROUND
                        Background color (default: black)
  --maxwidth MAXWIDTH   Maximum video width in pixels (default: 1280)
  --volume VOLUME       White noise volume in dB (default: -30)
  --margin MARGIN       Margin around the text in pixels (default: 10)
  --tts                 Use TTS audio instead of white noise
  --tts-text TTS_TEXT   Alternate text to use for TTS (default: same as visible text)
  --subtitle-language SUBTITLE_LANGUAGE
                        Subtitle language code (default: eng)
```

### text-to-image.py

Produce images from text, intended to test OCR.

```commandline
usage: text-to-image.py [-h] [--fontsize FONTSIZE] [--fontfile FONTFILE] [--output-dir OUTPUT_DIR] [--list-file LIST_FILE] [--fontcolor FONTCOLOR] [--background BACKGROUND]
                        [--maxwidth MAXWIDTH] [--maxheight MAXHEIGHT] [--margin MARGIN]
                        ...

Generate a series of images from text.

positional arguments:
  text                  Text to display across images

optional arguments:
  -h, --help            show this help message and exit
  --fontsize FONTSIZE   Font size in pixels (default: 32)
  --fontfile FONTFILE   Path to a TTF/OTF font file
  --output-dir OUTPUT_DIR
                        Directory to save output images
  --list-file LIST_FILE
                        Write the list of image paths to this file
  --fontcolor FONTCOLOR
                        Font color (default: white)
  --background BACKGROUND
                        Background color (default: black)
  --maxwidth MAXWIDTH   Maximum image width (default: 1280)
  --maxheight MAXHEIGHT
                        Maximum image height (default: 720)
  --margin MARGIN       Margin in pixels (default: 10)
```

### mp4_datetime_fuzzer.py

Videos have timestamps in the frames. Let's fuzz those to see if something breaks :)

```commandline
usage: mp4_datetime_fuzzer.py [-h] --input INPUT [--output OUTPUT] [--count COUNT] [--atoms ATOMS [ATOMS ...]] [--bit-depth {32,64}] [--fields {creation,modification,both}]
                              [--fuzz-fields FUZZ_FIELDS] [--log LOG] [--min-value MIN_VALUE] [--max-value MAX_VALUE] [--signed] [--value-mode {random,boundary,mixed}]
                              [--seed SEED] [--dry-run] [--hash]

MP4 datetime fuzzer (large-file safe, flexible)

options:
  -h, --help            show this help message and exit
  --input, -i INPUT     Input MP4 file
  --output, -o OUTPUT   Directory for fuzzed files
  --count, -n COUNT     Number of output files to generate
  --atoms ATOMS [ATOMS ...]
                        Atom types to fuzz
  --bit-depth {32,64}   Field size: 32 or 64-bit
  --fields {creation,modification,both}
                        Fields to fuzz
  --fuzz-fields FUZZ_FIELDS
                        Number of timestamp fields to fuzz per file
  --log LOG             CSV file to log fuzzed changes
  --min-value MIN_VALUE
                        Minimum value to use for fuzzing
  --max-value MAX_VALUE
                        Maximum value for fuzzing
  --signed              Use signed integer ranges
  --value-mode {random,boundary,mixed}
                        Value generation strategy
  --seed SEED           Random seed for reproducibility
  --dry-run             Do not write files, simulate only
  --hash                Append SHA256 hash and log it
```

### scatter_bytes.py

This script writes random bytes throughout a file. It isn't specifically for videos. (You could try it on your hard drive to see how resilient the filesystem is.)

```commandline
usage: scatter_bytes.py [-h] [--byte-set BYTE_SET [BYTE_SET ...]] [--length LENGTH] [--count COUNT] [--spacing SPACING] file

Scatter random bytes into a binary file using random access.

positional arguments:
  file                  Path to the binary file to modify

options:
  -h, --help            show this help message and exit
  --byte-set BYTE_SET [BYTE_SET ...]
                        Set of hex byte values to use (e.g., 00 ff aa)
  --length LENGTH       Length of each modification in bytes
  --count COUNT         Number of random modifications to perform
  --spacing SPACING     Minimum number of bytes between modifications (optional)
```

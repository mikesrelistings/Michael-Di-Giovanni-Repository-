#!/usr/bin/env python3
"""Cut the pauses between lines out of a take (jump cuts) and re-time the lines to match.

Usage:
  python3 tools/tighten-take.py <take.mov> <timings.json> <out.mp4> <out-timings.json> [--pad 0.15]

Each line is kept from (start - pad) to (end + pad); everything between lines is removed.
The output timings refer to the tightened clip and can be passed to render-video.cjs --timings.
"""
import json
import subprocess
import sys


def main():
    args = sys.argv[1:]
    pad = 0.15
    if "--pad" in args:
        i = args.index("--pad")
        pad = float(args[i + 1])
        del args[i:i + 2]
    if len(args) != 4:
        print(__doc__)
        sys.exit(2)
    take, timings_path, out_clip, out_timings = args
    lines = json.load(open(timings_path, encoding="utf-8"))["lines"]

    # Snap cut points to the video's frame grid so video and audio segments have identical
    # lengths and the re-timed lines stay exact after concatenation.
    rate = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries",
                           "stream=avg_frame_rate", "-of", "csv=p=0", take],
                          capture_output=True, text=True, check=True).stdout.strip()
    num, den = (rate.split("/") + ["1"])[:2]
    fps = float(num) / float(den)
    snap = lambda x: round(x * fps) / fps

    keep = []
    for i, (a, b) in enumerate(lines):
        start = snap(max(0.0, a - pad))
        if keep and start < keep[-1][1]:  # pause shorter than 2 x pad: merge into previous segment
            start = keep[-1][1]
        keep.append([start, snap(b + pad)])

    filters, labels = [], []
    for i, (a, b) in enumerate(keep):
        filters.append(f"[0:v]trim=start={a:.3f}:end={b:.3f},setpts=PTS-STARTPTS[v{i}]")
        filters.append(f"[0:a]atrim=start={a:.3f}:end={b:.3f},asetpts=PTS-STARTPTS,"
                       f"afade=t=in:d=0.02,afade=t=out:st={max(0.0, b - a - 0.02):.3f}:d=0.02[a{i}]")
        labels.append(f"[v{i}][a{i}]")
    filters.append("".join(labels) + f"concat=n={len(keep)}:v=1:a=1[v][a]")
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", take, "-filter_complex", ";".join(filters),
                    "-map", "[v]", "-map", "[a]", "-c:v", "libx264", "-preset", "medium", "-crf", "16",
                    "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k", out_clip], check=True)

    new_lines, t = [], 0.0
    for (a, b), (ka, kb) in zip(lines, keep):
        new_lines.append([round(t + (a - ka), 3), round(t + (b - ka), 3)])
        t += kb - ka
    json.dump({"source": out_clip, "tightened_from": take, "pad": pad, "lines": new_lines},
              open(out_timings, "w", encoding="utf-8"), indent=2)
    print(f"wrote {out_clip} ({t:.2f}s) and {out_timings}")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Time a script's lines to a recorded take using the pauses between them.

The speaker reads one line at a time with a short pause (about one beat) between lines.
ffmpeg's silencedetect finds the pauses; a dynamic program picks the N-1 pauses that best
match where each line boundary should fall given its word count, preferring longer pauses.

Usage:
  python3 tools/align-script.py <take.mov> <lines.txt> <out.json>

lines.txt holds one spoken line per row (blank rows ignored). The output is
{"lines": [[start, end], ...]} in seconds, ready for render-video.cjs --timings.
"""
import json
import re
import subprocess
import sys


def detect_silences(clip, noise_db, min_dur):
    proc = subprocess.run(
        ["ffmpeg", "-hide_banner", "-nostats", "-i", clip, "-vn",
         "-af", f"silencedetect=noise={noise_db}dB:d={min_dur}", "-f", "null", "-"],
        capture_output=True, text=True)
    log = proc.stderr
    dur = re.search(r"Duration: (\d+):(\d+):([\d.]+)", log)
    total = int(dur.group(1)) * 3600 + int(dur.group(2)) * 60 + float(dur.group(3)) if dur else None
    starts = [float(x) for x in re.findall(r"silence_start: ([\d.]+)", log)]
    ends = [float(x) for x in re.findall(r"silence_end: ([\d.]+)", log)]
    if len(ends) < len(starts):  # trailing silence runs to the end of the file
        ends.append(total)
    return total, list(zip(starts, ends))


def align(total, silences, words):
    n = len(words)
    speech_start = 0.0
    speech_end = total
    if silences and silences[0][0] <= 0.05:
        speech_start = silences[0][1]
        silences = silences[1:]
    if silences and total - silences[-1][1] <= 0.05:
        speech_end = silences[-1][0]
        silences = silences[:-1]
    gaps = [(s, e) for s, e in silences if s > speech_start and e < speech_end]
    if len(gaps) < n - 1:
        return None, speech_start, speech_end

    span = speech_end - speech_start
    cum = 0
    expected = []
    for w in words[:-1]:
        cum += w
        expected.append(speech_start + span * cum / sum(words))
    avg_line = span / n

    def score(k, j):
        s, e = gaps[j]
        mid = (s + e) / 2
        return min(e - s, 1.5) - 0.6 * abs(mid - expected[k]) / avg_line

    m = len(gaps)
    neg = float("-inf")
    best = [[neg] * m for _ in range(n - 1)]
    back = [[-1] * m for _ in range(n - 1)]
    for j in range(m):
        best[0][j] = score(0, j)
    for k in range(1, n - 1):
        run_best, run_idx = neg, -1
        for j in range(m):
            if j - 1 >= 0 and best[k - 1][j - 1] > run_best:
                run_best, run_idx = best[k - 1][j - 1], j - 1
            if run_idx >= 0:
                best[k][j] = run_best + score(k, j)
                back[k][j] = run_idx
    j = max(range(m), key=lambda x: best[n - 2][x])
    chosen = [j]
    for k in range(n - 2, 0, -1):
        j = back[k][j]
        chosen.append(j)
    chosen.reverse()

    bounds = [gaps[j] for j in chosen]
    lines = []
    start = speech_start
    for s, e in bounds:
        lines.append([round(start, 3), round(s, 3)])
        start = e
    lines.append([round(start, 3), round(speech_end, 3)])
    return lines, speech_start, speech_end


def main():
    if len(sys.argv) != 4:
        print(__doc__)
        sys.exit(2)
    clip, lines_path, out_path = sys.argv[1:]
    script = [ln.strip() for ln in open(lines_path, encoding="utf-8") if ln.strip()]
    words = [max(1, len(ln.split())) for ln in script]

    for noise_db, min_dur in [(-35, 0.35), (-32, 0.28), (-30, 0.22), (-28, 0.18)]:
        total, silences = detect_silences(clip, noise_db, min_dur)
        lines, s0, s1 = align(total, silences, words)
        if lines:
            break
    else:
        sys.exit(f"Found too few pauses for {len(script)} lines. Re-record with a clear beat between lines.")

    with open(out_path, "w", encoding="utf-8") as f:
        json.dump({"source": clip, "noise_db": noise_db, "min_pause": min_dur, "lines": lines}, f, indent=2)
    for (a, b), text, w in zip(lines, script, words):
        rate = w / max(b - a, 0.01)
        flag = "  <-- check" if rate < 1.2 or rate > 4.5 else ""
        print(f"{a:6.2f} {b:6.2f}  {rate:4.1f} w/s  {text[:60]}{flag}")
    print(f"wrote {out_path}")


if __name__ == "__main__":
    main()

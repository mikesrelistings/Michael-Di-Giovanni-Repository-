# Open Real Estate Short (video)

- `open-real-estate-short-v1.mp4`: 1080 x 1920, 30 fps, 59.5 seconds, silent audio track. Captions are burned in and timed to the Short script in `../research-and-content.md`, so the video works muted and you can record a voiceover over it.
- `short.html`: the editable source. All text, timing and captions live in this one file.
- `assets/`: Real knockout logo (background removed for Cobalt), Chicago Luxe Group logo on Cobalt. Both pulled from Michael's Google Drive.

## Re-render after edits

From the repo root:

```
node tools/render-video.cjs content/open-real-estate/video/short.html content/open-real-estate/video/open-real-estate-short-v2.mp4
```

Preview single frames without rendering the whole video:

```
node tools/render-video.cjs content/open-real-estate/video/short.html /tmp/stills --stills 2.5,9.5,17.5
```

## Before posting

1. Add audio: your own voiceover (read the captions) or a trending track in the Instagram or YouTube app.
2. Click the starred sources in `../research-and-content.md`.
3. Check Real's social media policy (Real REMAX Group is a founder).

## v2: talking-head version (look #5, burgundy + grey)

- `short-v2.html`: split screen. Graphics on top, Michael's clip on the bottom, captions on the seam. Scene timing follows the 16 spoken lines, so it adapts to the real take.
- `script-lines.txt`: the 16 lines, one per row (must match `LINES` in `short-v2.html`).
- `filming-guide-v2.md`: outfit, framing, light, and how to read it.
- `v2-layout-preview.jpg`: layout with a placeholder figure.

Build steps once the take is in (from the repo root):

```
python3 tools/align-script.py take.mov content/open-real-estate/video/script-lines.txt take-timings.json
python3 tools/tighten-take.py take.mov take-timings.json take-tight.mp4 take-tight.json
node tools/render-video.cjs content/open-real-estate/video/short-v2.html content/open-real-estate/video/open-real-estate-short-v2.mp4 --camera take-tight.mp4 --timings take-tight.json
```

`--camera-crop-y` (default 300) moves the camera window up or down the frame if the framing needs adjusting. `--max-seconds 10` renders a quick test.

# Off The Clock - cinematic social trailer

9:16 (1080x1920), 30 fps, 14.5 s, silent. Built with HyperFrames (HTML + GSAP), rendered to H.264 MP4.

## Files
- `off-the-clock.mp4` - the rendered video, ready to post (add trending audio in the app)
- `index.html` - the HyperFrames composition (all timing and animation lives here)
- `assets/michael.jpg` - source photo
- `assets/gsap.min.js`, `assets/fonts/`, `assets/grain.png` - vendored so the render needs no network
- `preview-contact-sheet.png` - key frames for a quick look

## Re-render
```bash
npm run check    # lint + runtime checks
npm run render   # writes output.mp4 (requires Node 22 and FFmpeg)
```

## Swap in a video instead of the photo
Replace the `<img id="hero">` in `index.html` with a muted `<video>` pointing at your clip, keep the same `class="photo"`, and adjust the `data-duration` values to the clip length.

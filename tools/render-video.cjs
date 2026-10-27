#!/usr/bin/env node
// Renders an HTML composition to a vertical MP4 (or still frames) with Playwright + ffmpeg.
//
// The page must expose:
//   window.__DURATION  total length in seconds
//   window.__render(t) draw the frame for time t (seconds), deterministic
//
// Optional camera mode composites a recorded clip under the page: the page is captured with a
// transparent background, the clip is scaled to the frame width, cropped to the camera window,
// and its audio is used as the soundtrack. The page sees window.__CAMERA_MODE = true.
//
// Usage:
//   node tools/render-video.cjs <page.html> <out.mp4> [--fps 30] [--width 1080] [--height 1920]
//   node tools/render-video.cjs <page.html> <out-dir> --stills 1.5,8,20
//   node tools/render-video.cjs <page.html> <out.mp4> --camera take.mov --timings take.json
//        [--camera-top 1060] [--camera-crop-y 300] [--max-seconds 10]
const path = require('path');
const fs = require('fs');
const { spawn } = require('child_process');
const { chromium } = require('playwright');

function parseArgs(argv) {
  const args = { _: [], fps: 30, width: 1080, height: 1920, stills: null,
    camera: null, timings: null, cameraTop: 1060, cameraCropY: 300, maxSeconds: null };
  for (let i = 0; i < argv.length; i++) {
    const a = argv[i];
    if (a === '--fps') args.fps = +argv[++i];
    else if (a === '--width') args.width = +argv[++i];
    else if (a === '--height') args.height = +argv[++i];
    else if (a === '--stills') args.stills = argv[++i].split(',').map(Number);
    else if (a === '--camera') args.camera = argv[++i];
    else if (a === '--timings') args.timings = argv[++i];
    else if (a === '--camera-top') args.cameraTop = +argv[++i];
    else if (a === '--camera-crop-y') args.cameraCropY = +argv[++i];
    else if (a === '--max-seconds') args.maxSeconds = +argv[++i];
    else args._.push(a);
  }
  return args;
}

function ffmpegArgs(args, out, duration) {
  const common = ['-c:v', 'libx264', '-preset', 'medium', '-crf', '18', '-pix_fmt', 'yuv420p',
    '-c:a', 'aac', '-b:a', '160k', '-movflags', '+faststart', out];
  if (!args.camera) {
    return ['-y', '-loglevel', 'error',
      '-f', 'image2pipe', '-framerate', String(args.fps), '-c:v', 'png', '-i', '-',
      '-f', 'lavfi', '-i', 'anullsrc=r=48000:cl=stereo',
      '-shortest', ...common];
  }
  const camH = args.height - args.cameraTop;
  const filter = [
    // Scale the clip to frame width, hold its last frame if the page runs longer, crop the camera window,
    // and place it on a Cobalt canvas below the graphics panel.
    `[0:v]fps=${args.fps},scale=${args.width}:-2,tpad=stop_mode=clone:stop_duration=30,` +
      `crop=${args.width}:${camH}:0:${args.cameraCropY},` +
      `pad=${args.width}:${args.height}:0:${args.cameraTop}:color=0x050E3D,setsar=1[cam]`,
    `[cam][1:v]overlay=0:0:format=auto,format=yuv420p[v]`,
    `[0:a]apad[a]`,
  ].join(';');
  return ['-y', '-loglevel', 'error',
    '-i', args.camera,
    '-f', 'image2pipe', '-framerate', String(args.fps), '-c:v', 'png', '-i', '-',
    '-filter_complex', filter, '-map', '[v]', '-map', '[a]',
    '-t', duration.toFixed(3), ...common];
}

async function main() {
  const args = parseArgs(process.argv.slice(2));
  const [page_, out] = args._;
  if (!page_ || !out) {
    console.error('usage: render-video.cjs <page.html> <out.mp4|out-dir> [--fps 30] [--stills t1,t2] [--camera clip --timings t.json]');
    process.exit(2);
  }
  const url = 'file://' + path.resolve(page_);
  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width: args.width, height: args.height }, deviceScaleFactor: 1 });
  const init = {};
  if (args.timings) init.__TIMINGS = JSON.parse(fs.readFileSync(args.timings, 'utf8'));
  if (args.camera) init.__CAMERA_MODE = true;
  await page.addInitScript(vals => Object.assign(window, vals), init);
  await page.goto(url, { waitUntil: 'load' });
  await page.evaluate(async () => {
    await document.fonts.ready;
    await Promise.all([...document.images].map(img => img.complete ? null : new Promise(r => { img.onload = img.onerror = r; })));
  });
  let duration = await page.evaluate(() => window.__DURATION);
  if (args.maxSeconds) duration = Math.min(duration, args.maxSeconds);
  const shot = { type: 'png', omitBackground: !!args.camera };

  if (args.stills) {
    fs.mkdirSync(out, { recursive: true });
    for (const t of args.stills) {
      await page.evaluate(t => window.__render(t), t);
      const file = path.join(out, `still-${String(t).replace('.', '_')}s.png`);
      await page.screenshot({ ...shot, path: file });
      console.log('wrote', file);
    }
    await browser.close();
    return;
  }

  const frames = Math.round(duration * args.fps);
  const ff = spawn('ffmpeg', ffmpegArgs(args, out, frames / args.fps), { stdio: ['pipe', 'inherit', 'inherit'] });
  const done = new Promise((resolve, reject) => ff.on('close', code => code === 0 ? resolve() : reject(new Error('ffmpeg exited ' + code))));

  for (let i = 0; i < frames; i++) {
    await page.evaluate(t => window.__render(t), i / args.fps);
    const buf = await page.screenshot(shot);
    if (!ff.stdin.write(buf)) await new Promise(r => ff.stdin.once('drain', r));
    if (i % (args.fps * 5) === 0) console.log(`frame ${i}/${frames}`);
  }
  ff.stdin.end();
  await done;
  await browser.close();
  console.log('wrote', out, `(${frames} frames @ ${args.fps}fps)`);
}

main().catch(err => { console.error(err); process.exit(1); });

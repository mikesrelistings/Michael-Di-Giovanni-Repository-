#!/usr/bin/env node
// Renders an HTML composition to a vertical MP4 (or still frames) with Playwright + ffmpeg.
//
// The page must expose:
//   window.__DURATION  total length in seconds
//   window.__render(t) draw the frame for time t (seconds), deterministic
//
// Usage:
//   node tools/render-video.cjs <page.html> <out.mp4> [--fps 30] [--width 1080] [--height 1920]
//   node tools/render-video.cjs <page.html> <out-dir> --stills 1.5,8,20
const path = require('path');
const fs = require('fs');
const { spawn } = require('child_process');
const { chromium } = require('playwright');

function parseArgs(argv) {
  const args = { _: [], fps: 30, width: 1080, height: 1920, stills: null };
  for (let i = 0; i < argv.length; i++) {
    const a = argv[i];
    if (a === '--fps') args.fps = +argv[++i];
    else if (a === '--width') args.width = +argv[++i];
    else if (a === '--height') args.height = +argv[++i];
    else if (a === '--stills') args.stills = argv[++i].split(',').map(Number);
    else args._.push(a);
  }
  return args;
}

async function main() {
  const args = parseArgs(process.argv.slice(2));
  const [page_, out] = args._;
  if (!page_ || !out) {
    console.error('usage: render-video.cjs <page.html> <out.mp4|out-dir> [--fps 30] [--stills t1,t2]');
    process.exit(2);
  }
  const url = 'file://' + path.resolve(page_);
  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width: args.width, height: args.height }, deviceScaleFactor: 1 });
  await page.goto(url, { waitUntil: 'load' });
  await page.evaluate(async () => {
    await document.fonts.ready;
    await Promise.all([...document.images].map(img => img.complete ? null : new Promise(r => { img.onload = img.onerror = r; })));
  });
  const duration = await page.evaluate(() => window.__DURATION);

  if (args.stills) {
    fs.mkdirSync(out, { recursive: true });
    for (const t of args.stills) {
      await page.evaluate(t => window.__render(t), t);
      const file = path.join(out, `still-${String(t).replace('.', '_')}s.png`);
      await page.screenshot({ path: file });
      console.log('wrote', file);
    }
    await browser.close();
    return;
  }

  const frames = Math.round(duration * args.fps);
  const ff = spawn('ffmpeg', [
    '-y', '-loglevel', 'error',
    '-f', 'image2pipe', '-framerate', String(args.fps), '-c:v', 'png', '-i', '-',
    '-f', 'lavfi', '-i', 'anullsrc=r=48000:cl=stereo',
    '-shortest',
    '-c:v', 'libx264', '-preset', 'medium', '-crf', '18', '-pix_fmt', 'yuv420p',
    '-c:a', 'aac', '-b:a', '128k',
    '-movflags', '+faststart',
    out,
  ], { stdio: ['pipe', 'inherit', 'inherit'] });
  const done = new Promise((resolve, reject) => ff.on('close', code => code === 0 ? resolve() : reject(new Error('ffmpeg exited ' + code))));

  for (let i = 0; i < frames; i++) {
    await page.evaluate(t => window.__render(t), i / args.fps);
    const buf = await page.screenshot({ type: 'png' });
    if (!ff.stdin.write(buf)) await new Promise(r => ff.stdin.once('drain', r));
    if (i % (args.fps * 5) === 0) console.log(`frame ${i}/${frames}`);
  }
  ff.stdin.end();
  await done;
  await browser.close();
  console.log('wrote', out, `(${frames} frames @ ${args.fps}fps)`);
}

main().catch(err => { console.error(err); process.exit(1); });

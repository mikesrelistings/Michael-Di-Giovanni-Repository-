# Filming Guide: Open Real Estate Short v2 (talking head)

Layout: branded graphics on the top half, you on the bottom half, captions on the line between them. You record one take; I time the graphics and captions to your voice, cut the pauses, and assemble it.

## Outfit

Look #5 from the rotation: **burgundy shirt, grey pants.** Only your head and chest show in this layout, so the shirt does the work. Burgundy contrasts well with the Cobalt panel above you.

## Camera

- Phone held **vertical**, at eye level, on a stand or tripod.
- Video set to **1080p, 30 fps**, and **HDR video off** (HDR footage tends to look washed out once it's edited).
- Use the back camera if you can. Lock focus and exposure on your face.

## Framing

- Head and shoulders, centered.
- **Eyes about one third of the way down the screen.** The final video uses roughly the band from just above your head to mid-chest, so leave a little headroom and don't frame too tight.

## Background and light

- Plain, uncluttered background: white, light grey, or a tidy room. Avoid red or burgundy walls (your shirt disappears) and busy patterns.
- Face a window or a soft light. Don't sit with a window behind you.

## Sound

- Quiet room, no fan or TV. A clip-on mic is best; otherwise keep the phone within arm's length.

## How to read it

- Read **one line, pause one beat** (half a second to a second), then the next line. The pauses tell my tool where each line starts. I cut them out afterward, so the final video won't drag.
- Small stumbles: keep going. A bad stumble: start a fresh take. Send only the clean take.
- Natural pace is fine. The final cut will run about 60 to 65 seconds. YouTube Shorts allow up to 3 minutes and Instagram Reels at least 90 seconds, so you have room.

## Script (16 lines)

1. If you sell your home next year, this decides who gets to see it.
2. On October 26th, Keller Williams, HomeServices of America, eXp's parent AGNT, and Real REMAX Group launched Open Real Estate.
3. Your agent enters your listing once.
4. It goes to the MLS, the home search sites, and other brokerages.
5. Free for any brokerage to join.
6. Why? Private listings.
7. And Chicago is ground zero.
8. Chicago's MLS, MRED, partnered with Compass on a private listing network, and Zillow sued them both.
9. The fine print: it isn't live yet, the target is early 2027,
10. and brokers can still keep a listing participant-only.
11. Does private cost you money?
12. Zillow says off-MLS homes sold for about 1.5% less.
13. Compass says its private-first marketing sells for more.
14. Both have skin in the game.
15. So before you sign, ask one question: who will see my home, and when?
16. DM me EXPOSURE for my checklist.

The on-screen disclosure ("I'm an agent with Real. Real REMAX Group is one of the four founders.") is in the graphics, so you don't need to say it.

## Send it

Attach the video file in this chat. Then I will:

1. Time each of the 16 lines to your take (`tools/align-script.py`).
2. Cut the pauses (`tools/tighten-take.py`).
3. Composite you under the graphics with your audio (`tools/render-video.cjs --camera`).
4. Send it back for your approval. Nothing gets posted.

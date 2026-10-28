# Crystal Rachel: massage and reflexology site

Single-file site (`index.html`). No build step, no frameworks, no paid services.

## What's in it

- **Live 3D hero.** A real-time WebGL scene: balanced river stones over dark water, lit by a drifting candle light, with out-of-focus string lights behind. Tapping the water sends ripples across it. Quality adjusts to the phone's speed, and it pauses when scrolled away.
- **Reflexology foot map.** Tap a zone on either foot (toes, ball, arches, heel, inner edge) to see what reflexology charts map it to.
- **Session builder.** The client picks the service, length, pressure, focus areas and timing. The page writes the booking text and opens it in Messages addressed to her.
- **One-minute breathing guide**, with an optional generated ambient tone.
- **Gift card** section with a text-to-buy button.
- Google structured data (LocalBusiness) built from the config.

## Before launch

Every field she still needs to confirm is in the `window.SITE` block at the top of `<body>`. Anything still in `[brackets]` shows on the page with a dashed underline.

1. Business name exactly as it appears on her Google listing
2. Phone, street address, city and ZIP, hours
3. Service lengths and prices
4. Illinois massage license number (Illinois law requires it on advertising)
5. Whether she wants to sell gift sessions (`gifts: true/false`)
6. Facebook Messenger link and Google review link (optional; the buttons hide until these are filled)
7. Delete the `<meta name="robots" content="noindex">` line so Google can index the site

## Launch

1. Drag this folder onto https://app.netlify.com/drop and claim the site with her email so she owns it.
2. Buy her domain and connect it in Netlify under Domain settings.
3. Paste the domain into the Website field on her Google Business Profile.

# Cook Dialer Campaign — Takeover Status
**Last updated:** Thu Oct 8, 2026
**Owner:** Michael Di Giovanni
**Goal:** Move the 3 Cook dialer campaigns (expired / PF / vacant) off Grok Bot's token-metered infrastructure onto Michael's own always-on MSI laptop (WSL2 Ubuntu), so the campaign no longer depends on Grok Bot's weekly/on-demand usage. Grok Bot stays as cold standby until the new host is proven out.

Source plans this builds on (uploaded by Michael, authored by Grok Bot / Codex on the Grok Bot box):
- `HANDOFF-ALL.md` — alert-relay-only redesign, original blocker (webhook creds wrong scheme)
- `ASSESSMENT.md` — Codex's read-only snapshot of the 3 live lanes + feasibility review
- `WSL-MIGRATION-PLAN.md` — the step-by-step WSL2-on-PC migration this status file tracks against
- `codex-takeover-package.zip` — the exported code (stdlib-only Python, no secrets), reviewed, no leaked credentials found

## Decisions locked in (Michael, Oct 8)
| Decision | Answer |
|---|---|
| Execution host | Michael's MSI laptop, via WSL2 (not a VPS) — required because Codex/Jarvis need actual browser/desktop control, which a headless VPS can't give them |
| Cutover timing | 8:00 PM CT (right after the box's 7:55 PM stop) |
| Primary operator after cutover | Rotating between Claude Code, Codex, Hermes — tracked in this file, not fixed to one tool |
| Alert delivery | Direct SMS to Michael's cell via Twilio (not Telegram, not the Grok Bot webhook) |
| PC power settings | Already set to never sleep. Laptop is manually shut down ~30 min somewhere between 5:30–6:00 PM daily. |
| Daily shutdown handling | **Flexible for now** — no auto-pause/resume scripted around it yet. Revisit once the migration is live and we see how it actually plays out. |

## Host hardware (confirmed from nameplate photo, Oct 8)
- **MSI Prestige A16 AI+**, SKU `A3HMG-016US-SSARI36532GXXDX11NGP`, S/N `K2409N0076251`, manufactured 2024/09.
- Current-gen AMD Ryzen AI chipset — virtualization/WSL2 support is standard on this line, no hardware blocker.
- Still need: exact Windows version/build from Settings > System > About (not expected to be an issue, just unconfirmed).

## Still open
- **"Jarvis"** — Michael's own private harness, built in a separate Claude Code session (not this repo). Candidates from his session list, unconfirmed: *"Personal AI agent system profile"*, *"Real estate AI agent system"*, *"Grokbot agents wholesale workflow"*. Needs Michael to confirm which one before Jarvis is wired into the rotation.
- Exact coordination page ("clicker page") Michael is setting up for Codex/Hermes — tool/link not yet shared.
- OneDrive folder `Desktop\Codex-1\drg-campaign-shared` confirmed as **docs/handoff only** — live state (queues, results, secrets) must never touch it (sync conflicts would corrupt in-flight CSV/JSONL files).

## Hard constraints (carried over from the source handoffs — still in force)
- Never pause/stop/change Cook expired, Cook PF, or Cook vacant without Michael's explicit yes.
- **Never run two hosts dialing at once** — box must be fully stopped (watchd, selfheal, the 5-min agent routine) before the PC starts, per the migration plan's cutover sequence.
- No agent active unless there's a problem — scripts do the work; agents only get woken on a real alert.
- Secrets live only in a local `.env` (chmod 600) on whichever host is live. Never in this repo, never in chat, never in logs.
- Live lead data (queues, results, PII) never touches OneDrive or this git repo — box-to-PC transfer only, direct copy, verified by sha256.
- TCPA/DNC compliance is non-negotiable; any ambiguity here goes to counsel, not worked around.

## Next concrete steps (nothing executes without Michael's go-ahead)
1. Confirm Windows version on the MSI (Settings > System > About) — low bar for WSL2, just need to verify.
2. Install WSL2 + Ubuntu 24.04 per `WSL-MIGRATION-PLAN.md` section 1.
3. Set up the folder layout (section 2) and drop in the reviewed code from the takeover package.
4. Michael enters real secrets into local `.env` himself (section 4) — never typed into chat or committed here.
5. Dry rehearsal on the PC (section 5) — no calls placed, confirm scripts run clean.
6. Cutover at 8:00 PM CT on an agreed date: stop the box cleanly, copy state over (sha256-verified), start the PC, confirm first call next morning continues from the correct row.
7. Keep Grok Bot box as cold standby + rollback path until the PC proves stable.

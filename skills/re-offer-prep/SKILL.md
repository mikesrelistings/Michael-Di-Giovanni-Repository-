---
name: re-offer-prep
description: Turn a screenshot of a buyer's text ("can we offer 150k on this" plus a Zillow or MLS link) into a ready-to-sign Multi-Board 8.0 offer for Michael Di Giovanni. Use when Michael sends a text screenshot, a listing link with a price, or says "write an offer", "get these purchase ready", or "start the contract". Pulls the buyer's standard terms from the buyer profile, pulls listing data from connectMLS, fills the contract in connectMLS Forms, stages it in Remine, and drafts the listing agent email with the disclosure request. Stops for Michael's approval before anything is sent. Hands off to re-deal-intake once an offer is accepted.
---

# Offer Prep: screenshot to signed offer

You are Michael's offer writer. A buyer texts "can we offer X on this" with a listing link. Your job is to get that offer to the point where Michael only has to read it and say "send".

Michael is a broker, not an attorney. You fill blanks on the standard Multi-Board 8.0 form. You never write custom clause language. Anything beyond the standard blanks goes to the buyer's attorney (Castle Law) first.

## Hard rules

1. Never send anything. No Remine signature request, no email, no MLS submission, until Michael says "send" for that specific item.
2. Never sign or initial for anyone.
3. Never guess the buyer entity. Brandon has bought both in his personal name and in Rich Regardless Realty Group LLC. Ask every time if it is not stated.
4. Never guess the price unit. "270" from Brandon has always meant $270,000, but confirm if anything else in the thread suggests otherwise.
5. Label every field as VERIFIED (with source) or ASSUMED (from buyer defaults). Do not put an unverified number in the contract.
6. No em dashes or en dashes in anything you write for Michael.

## Step 1: Read the screenshot

For each property in the screenshot, extract:
- Address (from the link card) and city, ZIP
- Price the buyer named, and the words used ("cash", "hard money", nothing)
- Who asked (sender name) and when (timestamp in the thread)
- Who else is in the thread (a group thread with Martez Malone usually means a partnership deal)
- Anything Michael already promised in his reply

## Step 2: Load the buyer profile and pipeline

- Read `references/buyer-profiles.md` for the buyer's standard terms.
- Query the Notion "Offers & Pipeline Tracker" (data source `collection://86ca1cdc-a9a9-4a78-b0cc-f05342783ed4`) for an existing row with this address. If none, create one with Status "On Deck", Buyer, Offer Price, and a note citing the screenshot.

## Step 3: Pull the listing data

Preferred: connectMLS through Claude in Chrome (Cowork on Michael's computer). Follow `references/mls-browser-runbook.md`.

If no browser is connected: ask Michael for the MLS "Agent Full" sheet as a PDF (print to PDF from connectMLS). Do not fall back to Zillow or Redfin numbers for the contract. Public sites are only for a sanity check and must be labeled unverified.

Fields to capture:
- MLS number, status (must be Active, not Contingent or Pending), list price, days on market
- Property type and unit count, year built, PIN, most recent taxes
- Listing agent name, brokerage, phone, email
- Broker private remarks: where offers go, required earnest money, proof of funds or pre-approval rules, highest and best deadlines, survey, as-is language
- Seller type flags: REO or bank owned, estate, trust, court sale, government
- Documents tab: which disclosures are already uploaded

## Step 4: Build the term sheet

Use `references/offer-terms.md` to map buyer defaults plus MLS data onto each Multi-Board 8.0 paragraph. Flag every conflict, for example:
- Broker remarks require 10% earnest money, buyer default is $1,000
- Buyer said "cash" but the profile shows hard money (8b vs 8c)
- 5 or more units: ask Castle Law before using the residential form
- Built before 1978: Lead-Based Paint disclosure and EPA pamphlet are required (federal)
- Pre-qualification letter missing, older than 30 days, or naming a different property or lender than the contract

**Gate 1.** Show Michael one table per property: every field, VERIFIED or ASSUMED, and the open questions. List the exact text for Michael to send the buyer if answers are missing. Wait.

## Step 5: Fill the contract

After Michael says go:
- Fill Multi-Board Residential Real Estate Contract 8.0 in connectMLS Forms, field by field per `references/offer-terms.md`.
- Save it. Export the PDF. Upload it to the buyer's Remine deal and place signature and initial tags for the buyer (Brandon first, then Martez when he is on the deal).
- Do not send the signature request.

**Gate 2.** Send Michael the PDF and a 5 line summary (price, financing paragraph, earnest money and escrowee, closing date, inspection and as-is). Wait for "send to Brandon".

## Step 6: Listing agent email

Draft (do not send) a Gmail message to the listing agent using `references/listing-agent-email.md`:
- Before the offer: availability check and disclosure request
- With the offer: signed contract, PQL or proof of funds, MLS sheet, disclosure request if still missing

**Gate 3.** Michael sends it himself or says "send".

## Step 7: Update the pipeline

After Michael confirms the offer went out: set the Notion row to "Submitted", fill List Price, MLS, Listing Agent, and add a dated note with terms and where the documents live.

On acceptance: run the `re-deal-intake` skill for deadlines, calendar, and the deal summary.

## Output to Michael

Short. One table per property, then "Need from you" with numbered questions, then the drafted buyer text. No preamble.

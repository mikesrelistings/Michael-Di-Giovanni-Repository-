# Estate Sale Radar

Finds Cook County homes showing the paper trail that usually comes before an estate sale or a clean-out, using free public data from the Cook County Assessor.

## What it looks for

The Assessor publishes, for every parcel and every year, who the property tax bill goes to and where it is mailed. The radar compares this year to last year and flags homes where:

| Signal | Points | What it usually means |
|---|---|---|
| Estate, heirs, executor, administrator or successor trustee on the tax bill | 50 (+10 if new this year) | The owner has died and an estate is handling the house |
| Tax bill passed to another family member | 30 | First-named owner is gone and a spouse, child or family trust took over the bill. Most common pattern: husband's name replaced by wife's |
| Tax bill moved away from the house | 30 | Owner moved to care, to a smaller place, or out of state, or family now pays the bills |
| A co-owner came off the tax bill | 20 | Two names became one |
| Bill now goes "c/o" someone | 15 | Family member or attorney is now handling mail |
| Long-time owner (no sale in 25+ years) | +10 | A full house of 25+ years of contents |

Family and move signals only count for owners of 10+ years, so recent buyers who moved out and rented the place don't show up.

It skips homes that look already sold: a recorded sale since the start of last year, a builder, LLC or land trust now on the bill, or a bill now in a different family's name.

## How to run it

Needs Python 3 (already on most Macs; type `python3 --version` in Terminal to check) and internet. No installs.

```
python3 estate_radar.py --zips 60091 60025 60302
```

It writes `estate_radar_leads.csv`, highest score first, with the property address, who gets the bill now and last year, where it is mailed, last sale date, and a link to the Assessor page for each house. Open it in Excel or Google Sheets.

Options:
- `--out oak_park.csv` to name the file
- `--min-score 40` to see only the strongest leads (default 30)

A 3-ZIP run (Wilmette, Glenview, Oak Park) takes about 15 seconds and returned 77 leads on the October 2026 data.

## Before you mail anyone

1. Open the `assessor_page` link. The exemption history shows whether a Senior exemption was on the house, which tells you the owner was 65+.
2. Mail goes to the `tax_bill_address`, not the house, when the bill has moved. That's where the family is.
3. Treat every lead as a maybe. A name change can also be a divorce, a refinance or someone setting up a living trust.

## Limits

- Cook County only.
- The county updates this data every two weeks, but says owner and mailing names change only intermittently in its source system. This catches what the paperwork shows, often weeks or months after the fact. It complements PropStream Pre-Probate and probate court filings; it doesn't replace them.
- Bill names are cut off around 22 characters, so some names look odd (`CAROLE A TAYLOR LIVING`).
- Lead CSVs contain private names and are ignored by git. Keep them out of the repo.

## Data sources

- [Assessor - Parcel Addresses](https://datacatalog.cookcountyil.gov/Property-Taxation/Assessor-Parcel-Addresses/3723-97qp) (tax bill name and mailing address by year)
- [Assessor - Parcel Sales](https://datacatalog.cookcountyil.gov/Property-Taxation/Assessor-Parcel-Sales/wvhk-k5uv)
- [Assessor - Parcel Universe (Current)](https://datacatalog.cookcountyil.gov/Property-Taxation/Assessor-Parcel-Universe-Current-/pabr-t5kh) (property class, to keep only homes)

If you run it a lot and hit rate limits, the script will use a Socrata app token from the `SOCRATA_APP_TOKEN` environment variable.

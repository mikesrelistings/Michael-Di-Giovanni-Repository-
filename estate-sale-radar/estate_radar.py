#!/usr/bin/env python3
"""Estate Sale Radar: flag Cook County homes showing early estate signals.

Pulls free public Cook County Assessor open data and scores residential
parcels on signals that tend to show up before an estate sale or clean-out:

  * Tax bill addressed to an estate, heirs, executor, administrator or
    successor trustee
  * Tax bill moved away from the house this year with no sale recorded
    (owner moved to care or a smaller place, or family now handles the bills)
  * Tax bill name changed within the family or into a family trust
  * Tax bill now goes "c/o" someone else
  * Long-time owner (booster only)

Skips parcels that look already sold: a recorded sale since the start of last
year, a business or land trust now on the bill, or a bill now in a different
family's name. Move and name-change signals only count for owners of 10+ years.

Standard library only. Needs Python 3.8+ and internet access.

Usage:
    python3 estate_radar.py --zips 60091 60093 60025
    python3 estate_radar.py --zips 60302 60305 --out oak_park_leads.csv
"""

import argparse
import csv
import json
import os
import re
import sys
import urllib.parse
import urllib.request
from datetime import date
from difflib import SequenceMatcher

BASE = "https://datacatalog.cookcountyil.gov/resource/{}.json"
ADDRESSES = "3723-97qp"  # Assessor - Parcel Addresses (owner + mailing, by year)
SALES = "wvhk-k5uv"  # Assessor - Parcel Sales
UNIVERSE = "pabr-t5kh"  # Assessor - Parcel Universe (Current), for property class

# Cook County residential classes that are actual homes: single-family,
# 2-6 unit buildings, townhomes and condos. Excludes vacant land and garages.
HOME_CLASSES = {
    "202", "203", "204", "205", "206", "207", "208", "209", "210",
    "211", "212", "234", "278", "295", "299",
}

ESTATE_RE = re.compile(
    r"\b(ESTATE OF|EST OF|THE ESTATE|HEIRS?|EXECUTOR|EXECUTRIX|EXEC|"
    r"ADMINISTRATOR|ADMINISTRATRIX|ADMR|ADMX|INDEP ADM|DECEASED|DECD|"
    r"LEGATEES?|SUCC(ESSOR)? (TR|TRS|TRUSTEE|TRSTE))\b"
)
BUSINESS_RE = re.compile(
    r"\b(LLC|L L C|INC|CORP|CO|COMPANY|LTD|LIAB|LP|REAL ESTATE|REALTY|PROPERT\w*|"
    r"HOLDINGS?|MANAGEMENT|MGMT|BANK|PARTNERS|INVEST\w*|CAPITAL|VENTURES?|GROUP|"
    r"HOMES|CUSTOM|CONSTR\w*|BUIL\w*|DEVELOP\w*|LAND TRU\w*|CTLT|TITLE|BK|PROP|SERIES)\b"
)
# Two or more people on one bill, e.g. "FRANK & ISABEL ANZALDI".
JOINT_RE = re.compile(r"&|\bAND\b")
# Words that say nothing about who the person is when comparing names.
NAME_FILLER = {
    "THE", "AND", "OR", "AS", "HER", "HIS", "NOT", "IND", "TR", "TRS", "TRST",
    "DCLRTN", "DTD", "OF", "JR", "SR", "II", "III", "IV",
}
# Tax bill names are cut off around 22 characters, so "TRUS" or "REVOCAB" count too.
NAME_FILLER_WORDS = ("TRUSTEE", "REVOCABLE", "LIVING", "FAMILY", "ESTATE", "DATED", "DECLARATION")
CARE_OF_RE = re.compile(r"\bC\s*/\s*O\b|\bCARE OF\b")
DIRECTIONS = {"N", "S", "E", "W", "NORTH", "SOUTH", "EAST", "WEST"}

PAGE = 50000


def soql(dataset, params):
    """Run one Socrata query and return the rows."""
    url = BASE.format(dataset) + "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url)
    token = os.environ.get("SOCRATA_APP_TOKEN")
    if token:
        req.add_header("X-App-Token", token)
    with urllib.request.urlopen(req, timeout=120) as resp:
        return json.load(resp)


def soql_all(dataset, params):
    """Page through a query until every row is returned."""
    rows, offset = [], 0
    while True:
        page = soql(dataset, {**params, "$limit": PAGE, "$offset": offset, "$order": ":id"})
        rows.extend(page)
        if len(page) < PAGE:
            return rows
        offset += PAGE


def quoted_list(values):
    return ",".join("'{}'".format(v.replace("'", "''")) for v in values)


def clean(text):
    return re.sub(r"\s+", " ", re.sub(r"[^A-Z0-9/ ]", " ", (text or "").upper())).strip()


def street_key(address):
    """House number plus first street-name word, e.g. '914 ROBERT'."""
    tokens = clean(address).split()
    if len(tokens) < 2 or not tokens[0][0].isdigit():
        return None
    words = [t for t in tokens[1:] if t not in DIRECTIONS]
    return "{} {}".format(tokens[0], words[0]) if words else None


def occupied(row):
    """True when the tax bill goes to the house itself."""
    prop, mail = street_key(row.get("prop_address_full")), street_key(row.get("mail_address_full"))
    return prop is not None and prop == mail


def business_name(name):
    return bool(BUSINESS_RE.search(clean(name)))


def estate_name(name):
    return bool(ESTATE_RE.search(clean(name))) and not business_name(name)


def name_words(name):
    """Words of a name in order, minus trust/legal filler and numbers."""
    return [w for w in clean(name).replace("/", " ").split()
            if w not in NAME_FILLER and not w[0].isdigit()
            and not (len(w) >= 3 and any(full.startswith(w) for full in NAME_FILLER_WORDS))]


def same_word(a, b):
    """Same name word, allowing initials, cut-off names and small typos."""
    if a == b:
        return True
    if len(a) == 1 or len(b) == 1:
        return a[0] == b[0]
    if min(len(a), len(b)) >= 3 and (a.startswith(b) or b.startswith(a)):
        return True
    return SequenceMatcher(None, a, b).ratio() >= 0.8


def name_change(old_name, new_name):
    """Classify how the tax bill name changed from last year to this year.

    'handoff': the first-named owner is gone and someone else with the same last
               name now gets the bill (surviving spouse, child, family trust)
    'dropped': a co-owner came off the bill and nobody new was added
    'other':   a different family entirely, which usually means a sale
    None:      same people (spelling fixes, a spouse or trust wrapper added)
    """
    old_all, new_all = name_words(old_name), name_words(new_name)
    old = [w for w in old_all if len(w) >= 3]
    new = [w for w in new_all if len(w) >= 3]
    if not old or not new:
        return None

    def found(word, pool):
        return any(same_word(word, p) for p in pool)

    if not any(found(w, new) for w in old):
        return "other"
    added = [w for w in new if not found(w, old)]
    # Initials only count where a first name sits (the start, or right after "&"),
    # so "CHESTER" doesn't match "MARK C PINAS" but "NITIN" matches "ANJALI KUMAR & N".
    raw_new = (new_name or "").upper()
    first_names = new_all[:1]
    if "&" in raw_new:
        first_names += name_words(raw_new.split("&", 1)[1])[:1]
    first_kept = found(old_all[0], first_names + [w for w in new_all if len(w) > 1])
    if added and not first_kept:
        if raw_new.rstrip().endswith("&"):
            return None  # the name after "&" was cut off, so we can't tell who it is
        return "handoff"
    dropped = [w for w in old if not found(w, new_all)]
    if dropped and not added and JOINT_RE.search((old_name or "").upper()):
        return "dropped"
    return None


def care_of(row):
    return bool(CARE_OF_RE.search(clean(row.get("mail_address_name")) + " " + clean(row.get("mail_address_full"))))


def latest_year():
    return int(soql(ADDRESSES, {"$select": "max(year) AS y"})[0]["y"])


def fetch_homes(zips):
    rows = soql_all(UNIVERSE, {
        "$select": "pin, class",
        "$where": "zip_code in ({})".format(quoted_list(zips)),
    })
    return {r["pin"] for r in rows if r.get("class") in HOME_CLASSES}


def fetch_addresses(zips, years):
    rows = soql_all(ADDRESSES, {
        "$select": ",".join([
            "pin", "year", "prop_address_full", "prop_address_city_name",
            "prop_address_zipcode_1", "mail_address_name", "mail_address_full",
            "mail_address_city_name", "mail_address_state", "mail_address_zipcode_1",
            "owner_address_name",
        ]),
        "$where": "prop_address_zipcode_1 in ({}) AND year in ({})".format(
            quoted_list(zips), quoted_list(str(y) for y in years)),
    })
    by_pin = {}
    for r in rows:
        by_pin.setdefault(r["pin"], {})[int(r["year"])] = r
    return by_pin


def fetch_last_sales(pins):
    """Most recent recorded sale for each PIN."""
    last = {}
    pins = sorted(pins)
    for i in range(0, len(pins), 150):
        chunk = pins[i:i + 150]
        rows = soql_all(SALES, {
            "$select": "pin, sale_date, sale_price, deed_type",
            "$where": "pin in ({})".format(quoted_list(chunk)),
        })
        for r in rows:
            if r["pin"] not in last or r["sale_date"] > last[r["pin"]]["sale_date"]:
                last[r["pin"]] = r
    return last


def flag_parcel(cur, prev):
    """Signals from this year's and last year's tax bill records.

    Returns None when the parcel should be skipped because it looks already sold.
    """
    name = cur.get("mail_address_name")
    if business_name(name) or clean(cur.get("prop_address_full")) in ("", "UNKNOWN"):
        return None
    flags = {}
    if any(estate_name(n) for n in (name, cur.get("owner_address_name"))):
        flags["estate"] = True
        flags["estate_new"] = bool(prev) and not any(
            estate_name(n) for n in (prev.get("mail_address_name"), prev.get("owner_address_name")))
    if not prev:
        return flags or None
    if occupied(prev) and not occupied(cur):
        flags["moved"] = " ".join(filter(None, [cur.get("mail_address_city_name"), cur.get("mail_address_state")]))
    if care_of(cur) and not care_of(prev):
        flags["care_of"] = True
    if not business_name(prev.get("mail_address_name")):
        change = name_change(prev.get("mail_address_name"), name)
        if change == "other" and not flags.get("estate") and not flags.get("care_of"):
            return None  # likely a sale not yet in the sales data
        if change in ("handoff", "dropped"):
            flags[change] = True
    return flags or None


def score_parcel(flags, years_owned):
    """Turn flags plus years owned (None when no sale is on record) into a score."""
    long_owner = years_owned is None or years_owned >= 10
    score, signals = 0, []
    if flags.get("estate"):
        score += 50
        signals.append("Estate/heir/trustee name on tax bill")
        if flags.get("estate_new"):
            score += 10
            signals.append("Estate name is new this year")
    if flags.get("moved") and long_owner:
        score += 30
        signals.append("Tax bill moved away from the house (now {})".format(flags["moved"]))
    if flags.get("handoff") and long_owner:
        score += 30
        signals.append("Tax bill passed to another family member")
    if flags.get("dropped") and long_owner:
        score += 20
        signals.append("A co-owner came off the tax bill")
    if flags.get("care_of"):
        score += 15
        signals.append("Bill now goes c/o someone")
    if score and (years_owned is None or years_owned >= 25):
        score += 10
        signals.append("Long-time owner (no sale in 25+ years)")
    return score, signals


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--zips", nargs="+", required=True, help="Cook County ZIP codes to scan")
    ap.add_argument("--out", default="estate_radar_leads.csv", help="CSV file to write")
    ap.add_argument("--min-score", type=int, default=30, help="Lowest score to keep (default 30)")
    args = ap.parse_args()

    year = latest_year()
    print("Scanning ZIPs {} for tax year {} vs {}".format(", ".join(args.zips), year, year - 1))
    homes = fetch_homes(args.zips)
    addresses = fetch_addresses(args.zips, [year, year - 1])
    print("  {} home parcels, {} parcels with address records".format(len(homes), len(addresses)))

    candidates = {}
    for pin, years in addresses.items():
        if pin not in homes or year not in years:
            continue
        flags = flag_parcel(years[year], years.get(year - 1))
        if flags:
            candidates[pin] = flags
    print("  {} parcels with at least one signal; checking sales history".format(len(candidates)))

    sales = fetch_last_sales(candidates)
    cutoff = "{}-01-01".format(year - 1)
    leads = []
    for pin, flags in candidates.items():
        sale = sales.get(pin)
        if sale and sale["sale_date"] >= cutoff:
            continue  # change is explained by a recent sale; the house already sold
        last_sale = sale["sale_date"][:10] if sale else ""
        score, signals = score_parcel(flags, date.today().year - int(last_sale[:4]) if sale else None)
        if score < args.min_score:
            continue
        cur, prev = addresses[pin][year], addresses[pin].get(year - 1, {})
        leads.append({
            "score": score,
            "signals": "; ".join(signals),
            "property_address": cur.get("prop_address_full", ""),
            "city": cur.get("prop_address_city_name", ""),
            "zip": cur.get("prop_address_zipcode_1", ""),
            "pin": pin,
            "owner_name": cur.get("owner_address_name", ""),
            "tax_bill_name": cur.get("mail_address_name", ""),
            "tax_bill_address": " ".join(filter(None, [
                cur.get("mail_address_full"), cur.get("mail_address_city_name"),
                cur.get("mail_address_state"), cur.get("mail_address_zipcode_1")])),
            "last_year_tax_bill_name": prev.get("mail_address_name", ""),
            "last_year_tax_bill_address": " ".join(filter(None, [
                prev.get("mail_address_full"), prev.get("mail_address_city_name")])),
            "last_sale_date": last_sale,
            "last_sale_price": sale.get("sale_price", "") if sale else "",
            "last_deed_type": sale.get("deed_type", "") if sale else "",
            "assessor_page": "https://www.cookcountyassessoril.gov/pin/{}".format(pin),
        })

    # One row per house: some homes span two PINs.
    best = {}
    for lead in leads:
        key = (lead["property_address"], lead["zip"])
        if key not in best or lead["score"] > best[key]["score"]:
            best[key] = lead
    leads = sorted(best.values(), key=lambda r: (-r["score"], r["zip"], r["property_address"]))
    if not leads:
        print("No leads at or above score {}.".format(args.min_score))
        return
    with open(args.out, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(leads[0]))
        writer.writeheader()
        writer.writerows(leads)
    print("Wrote {} leads to {}".format(len(leads), args.out))


if __name__ == "__main__":
    sys.exit(main())

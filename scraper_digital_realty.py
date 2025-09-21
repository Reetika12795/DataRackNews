import argparse
import json
import re
from typing import List, Dict, Optional

import requests
from bs4 import BeautifulSoup


OPERATOR = "Digital Realty"
BASE = "https://www.digitalrealty.com/data-centers"


def build_city_url(city: str, region: str) -> str:
    city_slug = city.strip().lower().replace(" ", "-")
    region_slug = region.strip().lower()
    return f"{BASE}/{region_slug}/{city_slug}"


def fetch(url: str, timeout: int = 20) -> str:
    r = requests.get(url, timeout=timeout, headers={
        "User-Agent": "DataRackNewsBot/1.0"
    })
    r.raise_for_status()
    return r.text


def parse_facilities(html: str, url: str, city: Optional[str], country: Optional[str]) -> List[Dict]:
    soup = BeautifulSoup(html, "html.parser")
    items: List[Dict] = []

    for wrapper in soup.find_all("div", class_="wrapper"):
        title_el = wrapper.select_one(".top-part .top-left .title")
        if not title_el:
            continue
        raw_title = title_el.get_text(strip=True)
        # Extract facility code like PAR6, LGW14, NYC1, etc.
        m = re.search(r"([A-Z]{2,4}\d+)", raw_title)
        code = m.group(1) if m else raw_title

        addr_el = wrapper.select_one(".sub-title")
        address = addr_el.get_text(strip=True) if addr_el else ""

        # Minimal record
        rec = {
            "facility_id": f"digital-realty-{code.lower()}-{(city or '').lower().replace(' ', '-') or 'unknown'}",
            "title": code,
            "operator": OPERATOR,
            "location": {
                "city": city,
                "country": country,
                "address": address,
            },
            "source_url": url,
        }
        items.append(rec)

    return items


def main():
    parser = argparse.ArgumentParser(description="Scrape a Digital Realty metro page for facilities")
    parser.add_argument("--url", help="Digital Realty metro URL, e.g. https://www.digitalrealty.com/data-centers/emea/paris")
    parser.add_argument("--city", help="City name, e.g. Paris")
    parser.add_argument("--region", help="Region segment used by DR (emea, americas, asia-pacific)")
    parser.add_argument("--country", help="Country name (optional)")
    args = parser.parse_args()

    if not args.url:
        if not (args.city and args.region):
            raise SystemExit("Provide --url or both --city and --region")
        url = build_city_url(args.city, args.region)
    else:
        url = args.url

    html = fetch(url)

    # Use provided city/country if given; otherwise try to infer city from URL last segment
    city = args.city
    if not city:
        # Parse city slug from URL
        try:
            city_slug = url.rstrip("/").split("/")[-1]
            city = city_slug.replace("-", " ").title()
        except Exception:
            city = None

    country = args.country  # optional; leave None if not provided

    facilities = parse_facilities(html, url, city, country)
    print(json.dumps(facilities, ensure_ascii=False))


if __name__ == "__main__":
    main()
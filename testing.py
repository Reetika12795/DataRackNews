import json, os
from pathlib import Path
from orchestrator import build_db_payload


def main():
    # Popular EU data center cities (country, city)
    targets = [
        ("france", "paris"),
        ("france","lyon"),
        ("germany", "frankfurt"),
        ("netherlands", "amsterdam"),
        ("united kingdom", "london"),
        ("ireland", "dublin"),
        ("spain", "madrid"),
        ("spain", "barcelona"),
        ("italy", "milan"),
        ("sweden", "stockholm"),
       # ("denmark", "copenhagen"),
        ("norway", "oslo"),
        ("switzerland", "zurich"),
        ("austria", "vienna"),
        ("czechia", "prague"),
        ("poland", "warsaw"),
        ("germany", "berlin"),
        ("germany", "munich"),
    ]

    out_dir = Path("output")
    out_dir.mkdir(parents=True, exist_ok=True)

    for country, city in targets:
        print(f"\n=== Building payload for {city}, {country} ===")
        payload = build_db_payload(
            country=country,
            city=city,
            geocode=True,                 # geocode lat/lon via SerpAPI (default)
            geocode_provider="serpapi",
            include_news=True,
            news_days=14,
            max_news_per_dc=5,
        )

        # Safe filename
        fname = f"{country.replace(' ', '_')}_{city.replace(' ', '_')}.json"
        out_path = out_dir / fname
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)
        print(f"Wrote {out_path}")


if __name__ == "__main__":
    main()
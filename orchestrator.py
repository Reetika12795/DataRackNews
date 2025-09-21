import argparse
import json
import os
from typing import Dict, List, Optional
from datetime import datetime, timezone

# Local imports
from scraper_datacenters_com import (
    scrape_facilities,
    facilities_to_db_payload,
)
from energy_analyzer import EnergyAnalyzer
from operator_analyzer import OperatorAnalyzer
from dotenv import load_dotenv


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def build_db_payload(
    country: str,
    city: Optional[str] = None,
    serpapi_token: Optional[str] = None,
    include_news: bool = False,
    news_days: int = 14,
    max_news_per_dc: int = 5,
    geocode: bool = False,
    email: Optional[str] = None,
    geocode_provider: str = "serpapi",
) -> Dict[str, List[Dict]]:
    """
    End-to-end pipeline that:
      1) Scrapes facilities for a country/city from datacenters.com
      2) Normalizes them to `data_centers` and `search_cache`
      3) Computes a `metrics` record for each data center using EnergyAnalyzer (SerpAPI-backed)
      4) Optionally enriches with operator news into `articles` linked per data center

    Returns a dict with: data_centers, search_cache, metrics, articles
    """
    # Resolve token if not provided (supports programmatic usage without calling main())
    if not serpapi_token:
        try:
            load_dotenv()
        except Exception:
            pass
        serpapi_token = os.getenv("SERPAPI_TOKEN")

    # 1) Scrape
    facilities = scrape_facilities(country=country, city=city)

    # 2) Normalize to DB shapes
    base_payload = facilities_to_db_payload(
        facilities,
        geocode=geocode,
        email=email,
        geocode_provider=geocode_provider,
        serpapi_token=serpapi_token,
    )
    data_centers = base_payload.get("data_centers", [])
    search_cache = base_payload.get("search_cache", [])

    # 3) Energy metrics
    energy = EnergyAnalyzer(serpapi_key=serpapi_token)
    metrics: List[Dict] = []
    for dc in data_centers:
        try:
            m = energy.metrics_from_data_center_record(dc)
            if isinstance(m, dict) and "error" not in m:
                metrics.append(m)
            else:
                # Still add a placeholder record with recorded_at for traceability or skip entirely
                # Here we skip to avoid inserting invalid rows
                pass
        except Exception as e:
            # Skip this DC metrics if anything unexpected happens
            print(f"[metrics] Failed for {dc.get('name')}: {e}")

    # 4) Operator news -> articles (optional)
    articles: List[Dict] = []
    # Guard against missing/placeholder token to avoid 401s
    token_ok = bool(serpapi_token) and serpapi_token != "YOUR_TOKEN"
    if include_news and token_ok:
        op = OperatorAnalyzer(serpapi_key=serpapi_token)
        for dc in data_centers:
            operator = (dc.get("operator") or "").strip()
            if not operator:
                continue
            # Build query as operator + city (per request)
            loc_city = (dc.get("city") or "").strip()
            query_parts = [operator]
            if loc_city:
                query_parts.append(loc_city)
            query = " ".join(query_parts)

            try:
                news_results = op.news_analyzer.search_news(query, days_back=news_days) or []
                news_items = op.news_analyzer.parse_news_items(news_results, operator) or []
                if max_news_per_dc and max_news_per_dc > 0:
                    news_items = news_items[:max_news_per_dc]
                article_rows = op.news_analyzer.news_to_articles_records(dc["id"], news_items)
                articles.extend(article_rows)
            except Exception as e:
                print(f"[news] Failed for {operator}: {e}")
    elif include_news and not token_ok:
        print("[news] Skipping news enrichment: missing or placeholder SERPAPI token. Set SERPAPI_TOKEN or pass --serpapi-token.")

    return {
        "data_centers": data_centers,
        "search_cache": search_cache,
        "metrics": metrics,
        "articles": articles,
    }


def main():
    parser = argparse.ArgumentParser(description="End-to-end orchestrator for DataRackNews DB payloads")
    parser.add_argument("--country", required=True, help="Country to scrape, e.g. 'france' or 'spain'")
    parser.add_argument("--city", help="Optional city filter, e.g. 'paris'")
    parser.add_argument("--include-news", action="store_true", help="Include operator news mapped to articles table")
    parser.add_argument("--news-days", type=int, default=14, help="Days back for news search (default 14)")
    parser.add_argument("--max-news-per-dc", type=int, default=5, help="Max number of news items per data center (default 5)")
    parser.add_argument("--serpapi-token", help="SerpAPI token. If omitted, tries SERPAPI_TOKEN env var")
    parser.add_argument("--geocode", action="store_true", help="Geocode addresses to fill latitude/longitude in data_centers")
    parser.add_argument("--email", help="Contact email for geocoding User-Agent (recommended)")
    parser.add_argument("--geocode-provider", choices=["nominatim", "serpapi"], default="serpapi", help="Geocoder to use for lat/lon (default serpapi)")
    parser.add_argument("--output", help="Output JSON file path. If omitted, prints to stdout")

    args = parser.parse_args()

    # Load .env for local development
    try:
        load_dotenv()
    except Exception:
        pass

    # Load SERPAPI token from env if not provided
    serpapi_token = args.serpapi_token or os.getenv("SERPAPI_TOKEN")

    payload = build_db_payload(
        country=args.country,
        city=args.city,
        serpapi_token=serpapi_token,
        include_news=args.include_news,
        news_days=args.news_days,
        max_news_per_dc=args.max_news_per_dc,
        geocode=args.geocode,
        email=args.email,
        geocode_provider=args.geocode_provider,
    )

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)
        print(f"✅ Wrote payload to {args.output}")
    else:
        print(json.dumps(payload, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

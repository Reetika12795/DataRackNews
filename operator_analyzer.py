from typing import Dict, List, Optional, Tuple
import requests
import json
import re
from datetime import datetime, timedelta
from dataclasses import dataclass

@dataclass
class FinancialMetrics:
    """Data class for financial metrics"""
    symbol: str
    company_name: str
    current_price: float
    price_change: float
    price_change_percent: float
    market_cap: str
    pe_ratio: Optional[float]
    dividend_yield: Optional[float]
    fifty_two_week_high: Optional[float]
    fifty_two_week_low: Optional[float]
    volume: Optional[str]
    avg_volume: Optional[str]
    beta: Optional[float]
    eps: Optional[float]
    revenue: Optional[str]
    timestamp: str
    google_finance_url: Optional[str]

@dataclass
class NewsItem:
    """Data class for news items"""
    title: str
    source: str
    date: str
    snippet: str
    url: str

class FinancialAnalyzer:
    """Analyzes data center operators using SerpAPI Google Finance API"""
    
    def __init__(self, serpapi_key: str = None):
        self.serpapi_key = serpapi_key
        self.serpapi_base = "https://serpapi.com/search"
        
        # Major data center operators and their stock symbols
        self.known_operators = {
            "Digital Realty": "DLR",
            "Equinix": "EQIX", 
            "American Tower": "AMT",
            "Crown Castle": "CCI",
            "CoreSite": "COR",
            "QTS Realty": "QTS",
            "CyrusOne": "CONE",
            "Iron Mountain": "IRM",
            "SBA Communications": "SBAC",
            "Prologis": "PLD",
            "Realty Income": "O",
            "Digital Bridge": "DBRG",
            "Vantage Data Centers": None,  # Private
            "Switch": "SWCH",
            "NextDC": "NXT.AX",
            "Interxion": None,  # Acquired by Digital Realty
            "Global Switch": None,  # Private
            "NTT Communications": "9432.T",
            "KDDI": "9433.T",
            "Telehouse": None,  # Part of KDDI
            "Colt Data Centre Services": None,  # Private
            "Cyxtera": "CYXT"
        }
    
    def get_stock_symbol(self, operator_name: str) -> Optional[str]:
        """Get stock symbol for an operator, with fuzzy matching"""
        
        # Direct match
        if operator_name in self.known_operators:
            return self.known_operators[operator_name]
        
        # Fuzzy matching
        operator_lower = operator_name.lower()
        for known_name, symbol in self.known_operators.items():
            if known_name.lower() in operator_lower or operator_lower in known_name.lower():
                return symbol
        
        return None
    
    def search_financial_data(self, operator_name: str) -> Optional[Dict]:
        """Search for financial data using SerpAPI Google Finance"""
        
        if not self.serpapi_key:
            print("Warning: No SerpAPI key provided. Cannot fetch financial data.")
            return None
        
        # Get the stock symbol first
        symbol = self.get_stock_symbol(operator_name)
        if not symbol:
            print(f"⚠️  No stock symbol found for {operator_name}")
            return None
        
        # Try different search formats
        search_formats = [
            symbol,  # Just the symbol (e.g., "EQIX")
            f"NASDAQ:{symbol}",  # NASDAQ format
            f"NYSE:{symbol}",    # NYSE format
            f"{symbol}:NASDAQ",  # Alternative format
            f"{symbol}:NYSE"     # Alternative format
        ]
        
        for search_query in search_formats:
            params = {
                "engine": "google_finance",
                "q": search_query,
                "api_key": self.serpapi_key,
                "hl": "en"
            }
            
            try:
                print(f"📈 Trying search: {search_query} for {operator_name}...")
                response = requests.get(self.serpapi_base, params=params, timeout=15)
                response.raise_for_status()
                
                data = response.json()
                
                # Check if we got actual stock data (not just market indices)
                if self._has_stock_data(data, symbol):
                    print(f"✅ Found stock data with query: {search_query}")
                    return data
                else:
                    print(f"❌ No stock data found with query: {search_query}")
                
            except Exception as e:
                print(f"❌ Error with query {search_query}: {e}")
                continue
        
        print(f"❌ Failed to find stock data for {operator_name} ({symbol}) with any search format")
        return None
    
    def _has_stock_data(self, data: Dict, symbol: str) -> bool:
        """Check if the API response contains actual stock data for our symbol"""
        
        # Check for direct summary/quote data
        if "summary" in data or "quote" in data:
            return True
        
        # Check if markets data contains our specific stock
        if "markets" in data:
            for market_region, stocks in data["markets"].items():
                for stock in stocks:
                    stock_symbol = stock.get("stock", "")
                    if symbol in stock_symbol or stock_symbol.endswith(f":{symbol}"):
                        return True
        
        return False
    
    def parse_financial_metrics(self, data: Dict, operator_name: str) -> Optional[FinancialMetrics]:
        """Parse financial metrics from SerpAPI Google Finance response.
        Handles multiple response shapes and avoids attribute errors when fields are scalars."""
        
        try:
            # Debug (short): print top-level keys only to avoid huge logs
            try:
                print(f"🔍 Debug - API keys: {list(data.keys())}")
            except Exception:
                pass
            
            symbol = self.get_stock_symbol(operator_name)
            summary = None
            
            # 1) Preferred: dedicated summary/quote object
            if isinstance(data.get("summary"), dict):
                summary = data["summary"]
            elif isinstance(data.get("quote"), dict):
                summary = data["quote"]
            
            # 2) Fallback: try to locate in markets[] blocks
            if summary is None and isinstance(data.get("markets"), dict):
                for _, items in data["markets"].items():
                    if isinstance(items, list):
                        for item in items:
                            if isinstance(item, dict):
                                stock_code = item.get("stock", "")
                                name = item.get("name", "")
                                if (symbol and (symbol in stock_code or stock_code.endswith(f":{symbol}"))) or operator_name.lower() in name.lower():
                                    summary = item
                                    break
                    if summary is not None:
                        break
            
            # 3) If still no summary, allow minimal object using URL presence
            if summary is None:
                gf_url = data.get("search_metadata", {}).get("google_finance_url", "")
                if symbol and symbol in gf_url:
                    print(f"ℹ️ Found stock page but no inline quote JSON: {gf_url}")
                    return FinancialMetrics(
                        symbol=symbol,
                        company_name=operator_name,
                        current_price=0.0,
                        price_change=0.0,
                        price_change_percent=0.0,
                        market_cap=None,
                        pe_ratio=None,
                        dividend_yield=None,
                        fifty_two_week_high=None,
                        fifty_two_week_low=None,
                        volume=None,
                        avg_volume=None,
                        beta=None,
                        eps=None,
                        revenue=None,
                        timestamp=datetime.now().isoformat(),
                        google_finance_url=gf_url,
                    )
                print("❌ No recognizable stock data block in response")
                return None
            
            # Helpers that accept dicts or scalars (and strings with symbols)
            def read_number(val) -> Optional[float]:
                try:
                    if val is None:
                        return None
                    if isinstance(val, (int, float)):
                        return float(val)
                    if isinstance(val, str):
                        # Extract first numeric token (handles $1,234.56, 1.23%, etc.)
                        m = re.search(r"-?\d{1,3}(?:,\d{3})*(?:\.\d+)?|-?\d+(?:\.\d+)?", val)
                        if m:
                            return float(m.group(0).replace(",", ""))
                        return None
                    if isinstance(val, dict):
                        # Common shapes: { extracted_value: 123.4 } or { value: 123.4 } or { raw: 123.4 }
                        for k in ("extracted_value", "value", "raw"):
                            if k in val:
                                return read_number(val.get(k))
                        # Or nested single-key dicts
                        for v in val.values():
                            n = read_number(v)
                            if n is not None:
                                return n
                        return None
                except Exception:
                    return None
                return None
            
            def read_text(container, key) -> Optional[str]:
                if not isinstance(container, dict):
                    return None
                val = container.get(key)
                if isinstance(val, str):
                    return val
                if isinstance(val, dict):
                    for k in ("extracted_value", "value", "raw", "text"):
                        if k in val and val[k] is not None:
                            return str(val[k])
                    return None
                if isinstance(val, (int, float)):
                    return str(val)
                return None
            
            def first_present(container: Dict, keys: List[str]):
                if not isinstance(container, dict):
                    return None
                for k in keys:
                    if k in container:
                        return container[k]
                return None
            
            # Extract basic fields from summary with defensive checks
            price_source = ""
            # Try common price keys in summary
            price_candidate = first_present(summary, [
                "price",
                "last",
                "current_price",
                "regular_market_price",
                "last_price",
            ])
            current_price = read_number(price_candidate)
            if current_price:
                price_source = "summary"
            
            # If still 0/None, try additional nested possibilities
            if not current_price:
                # Some shapes embed under a nested object like { price: { raw: ... } } already handled by read_number
                # Try knowledge_graph price if present
                kg = data.get("knowledge_graph")
                if isinstance(kg, dict):
                    kg_price = first_present(kg, ["price", "current_price", "last"])
                    current_price = read_number(kg_price) or current_price
                    if current_price:
                        price_source = "knowledge_graph"
            
            # If still 0, try graph latest price keys
            if (not current_price or current_price == 0.0) and isinstance(data.get("graph"), list) and data["graph"]:
                last_point = data["graph"][-1]
                if isinstance(last_point, dict):
                    graph_price = first_present(last_point, ["price", "close", "value"])
                    current_price = read_number(graph_price) or current_price
                    if current_price:
                        price_source = "graph"
            
            pm = summary.get("price_movement") if isinstance(summary, dict) else None
            price_change = read_number(pm.get("value")) if isinstance(pm, dict) else None
            price_change_percent = read_number(pm.get("percentage")) if isinstance(pm, dict) else None
            
            company_name = (
                read_text(summary, "name")
                or read_text(summary, "title")
                or operator_name
            )
            
            # Parse key statistics from 'financials' when present
            financials = data.get("financials")
            key_stats = None
            if isinstance(financials, dict):
                for ks_key in ("key_stats", "statistics", "data", "sections"):
                    if isinstance(financials.get(ks_key), list):
                        key_stats = financials.get(ks_key)
                        break
            
            def find_stat(names: List[str]) -> Optional[str]:
                if not isinstance(key_stats, list):
                    return None
                for item in key_stats:
                    if not isinstance(item, dict):
                        continue
                    name = (item.get("name") or item.get("title") or "").strip().lower()
                    value = item.get("value") or item.get("text") or item.get("data")
                    if any(n.lower() in name for n in names):
                        if isinstance(value, (str, int, float)):
                            return str(value)
                        if isinstance(value, dict):
                            return value.get("text") or value.get("value") or value.get("extracted_value")
                return None
            
            market_cap = find_stat(["market cap", "market capitalization"]) or None
            pe_ratio = read_number(find_stat(["p/e", "pe ratio", "price to earnings"]))
            dividend_yield = read_number(find_stat(["dividend yield"]))
            fifty_two_week = find_stat(["52-week range", "52 week range"]) or None
            fifty_two_week_high = None
            fifty_two_week_low = None
            if isinstance(fifty_two_week, str) and "-" in fifty_two_week:
                try:
                    lo, hi = [s.strip() for s in fifty_two_week.split("-")[:2]]
                    fifty_two_week_low = read_number(lo)
                    fifty_two_week_high = read_number(hi)
                except Exception:
                    pass
            beta = read_number(find_stat(["beta"]))
            eps = read_number(find_stat(["eps", "earnings per share"]))
            revenue = find_stat(["revenue"]) or None
            
            metrics = FinancialMetrics(
                symbol=symbol or "",
                company_name=company_name,
                current_price=current_price or 0.0,
                price_change=price_change or 0.0,
                price_change_percent=price_change_percent or 0.0,
                market_cap=market_cap,
                pe_ratio=pe_ratio,
                dividend_yield=dividend_yield,
                fifty_two_week_high=fifty_two_week_high,
                fifty_two_week_low=fifty_two_week_low,
                volume=None,
                avg_volume=None,
                beta=beta,
                eps=eps,
                revenue=revenue,
                timestamp=datetime.now().isoformat(),
                google_finance_url=data.get("search_metadata", {}).get("google_finance_url"),
            )
            
            # Debug which price source was used
            if price_source:
                print(f"🔎 Price source: {price_source}")
            print(
                f"✅ Extracted {company_name}: price=${metrics.current_price} change={metrics.price_change_percent or 0:.2f}%"
            )
            return metrics
        except Exception as e:
            print(f"❌ Error parsing financial metrics for {operator_name}: {e}")
            import traceback
            traceback.print_exc()
            return None

class NewsAnalyzer:
    """Analyzes news about data center operators using SerpAPI Google News API"""
    
    def __init__(self, serpapi_key: str = None):
        self.serpapi_key = serpapi_key
        self.serpapi_base = "https://serpapi.com/search"
        
    def search_news(self, query: str, days_back: int = 30) -> Optional[List[Dict]]:
        """Search for news using SerpAPI Google News"""
        
        if not self.serpapi_key:
            print("Warning: No SerpAPI key provided. Cannot fetch news data.")
            return None
        
        # Calculate date range
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days_back)
        
        params = {
            "engine": "google_news",
            "q": query,
            "api_key": self.serpapi_key,
            "hl": "en",
            "gl": "us",
            "tbm": "nws",
            "tbs": f"cdr:1,cd_min:{start_date.strftime('%m/%d/%Y')},cd_max:{end_date.strftime('%m/%d/%Y')}"
        }
        
        try:
            print(f"📰 Searching news for '{query}' (last {days_back} days)...")
            response = requests.get(self.serpapi_base, params=params, timeout=15)
            response.raise_for_status()
            
            data = response.json()
            
            if "error" in data:
                print(f"❌ SerpAPI Error: {data['error']}")
                return None
            
            return data.get("news_results", [])
            
        except Exception as e:
            print(f"❌ Error fetching news for '{query}': {e}")
            return None
    
    def parse_news_items(self, news_results: List[Dict], query: str) -> List[NewsItem]:
        """Parse news results into NewsItem objects"""
        
        news_items = []
        
        for result in news_results:
            try:
                title = result.get("title", "")
                snippet = result.get("snippet", "")
                source = result.get("source", "")
                date = result.get("date", "")
                url = result.get("link", "")
                
                news_item = NewsItem(
                    title=title,
                    source=source,
                    date=date,
                    snippet=snippet,
                    url=url
                )
                
                news_items.append(news_item)
                
            except Exception as e:
                print(f"⚠️  Error parsing news item: {e}")
                continue
        
        return news_items

class OperatorAnalyzer:
    """Comprehensive analysis of data center operators combining financial and news data"""
    
    def __init__(self, serpapi_key: str = None):
        self.financial_analyzer = FinancialAnalyzer(serpapi_key)
        self.news_analyzer = NewsAnalyzer(serpapi_key)
    
    def analyze_operator(self, operator_name: str, include_news: bool = True, news_days: int = 30) -> Dict:
        """Comprehensive analysis of a data center operator"""
        
        print(f"\n🏢 Analyzing operator: {operator_name}")
        print("=" * 50)
        
        result = {
            "operator_name": operator_name,
            "analysis_timestamp": datetime.now().isoformat(),
            "financial_data": None,
            "news_analysis": None,
            "overall_assessment": None,
            "errors": []
        }
        
        # Get financial data
        financial_data = self.financial_analyzer.search_financial_data(operator_name)
        if financial_data:
            financial_metrics = self.financial_analyzer.parse_financial_metrics(financial_data, operator_name)
            if financial_metrics:
                result["financial_data"] = {
                    "symbol": financial_metrics.symbol,
                    "company_name": financial_metrics.company_name,
                    "current_price": financial_metrics.current_price,
                    "price_change": financial_metrics.price_change,
                    "price_change_percent": financial_metrics.price_change_percent,
                    "market_cap": financial_metrics.market_cap,
                    "pe_ratio": financial_metrics.pe_ratio,
                    "dividend_yield": financial_metrics.dividend_yield,
                    "fifty_two_week_high": financial_metrics.fifty_two_week_high,
                    "fifty_two_week_low": financial_metrics.fifty_two_week_low,
                    "volume": financial_metrics.volume,
                    "avg_volume": financial_metrics.avg_volume,
                    "beta": financial_metrics.beta,
                    "eps": financial_metrics.eps,
                    "revenue": financial_metrics.revenue,
                    "timestamp": financial_metrics.timestamp,
                    "google_finance_url": financial_metrics.google_finance_url,
                }
                print(f"✅ Financial data retrieved successfully")
            else:
                result["errors"].append("Failed to parse financial data")
        else:
            result["errors"].append("Failed to fetch financial data")
        
        # Get news analysis
        if include_news:
            news_results = self.news_analyzer.search_news(f"{operator_name} data center", news_days)
            if news_results:
                news_items = self.news_analyzer.parse_news_items(news_results, operator_name)
                
                if news_items:
                    result["news_analysis"] = {
                        "total_articles": len(news_items),
                        "recent_headlines": [
                            {
                                "title": item.title,
                                "source": item.source,
                                "date": item.date,
                                "url": item.url
                            }
                            for item in news_items[:10]  # Top 10 most relevant
                        ],
                        "days_analyzed": news_days
                    }
                    print(f"✅ News analysis completed ({len(news_items)} articles)")
                else:
                    result["errors"].append("No relevant news articles found")
            else:
                result["errors"].append("Failed to fetch news data")
        
        # Generate overall assessment
        result["overall_assessment"] = self._generate_assessment(result)
        
        return result
    
    def _generate_assessment(self, analysis_result: Dict) -> Dict:
        """Generate overall assessment based on financial and news data"""
        
        assessment = {
            "financial_health": "unknown",
            "market_sentiment": "unknown", 
            "news_sentiment": "unknown",
            "overall_score": 0,
            "key_insights": [],
            "risk_factors": [],
            "opportunities": []
        }
        
        # Assess financial health
        financial_data = analysis_result.get("financial_data")
        if financial_data:
            price_change_percent = financial_data.get("price_change_percent", 0)
            pe_ratio = financial_data.get("pe_ratio")
            dividend_yield = financial_data.get("dividend_yield")
            
            # Financial health scoring
            financial_score = 0
            
            if price_change_percent > 5:
                assessment["financial_health"] = "strong"
                financial_score += 2
                assessment["key_insights"].append("Strong recent price performance")
            elif price_change_percent > 0:
                assessment["financial_health"] = "stable"
                financial_score += 1
            elif price_change_percent > -5:
                assessment["financial_health"] = "weak"
                financial_score -= 1
                assessment["risk_factors"].append("Recent price decline")
            else:
                assessment["financial_health"] = "poor"
                financial_score -= 2
                assessment["risk_factors"].append("Significant recent price decline")
            
            if pe_ratio and 10 <= pe_ratio <= 25:
                assessment["key_insights"].append("Reasonable P/E ratio indicates fair valuation")
                financial_score += 1
            elif pe_ratio and pe_ratio > 30:
                assessment["risk_factors"].append("High P/E ratio may indicate overvaluation")
            
            if dividend_yield and dividend_yield > 3:
                assessment["key_insights"].append("Attractive dividend yield")
                financial_score += 1
            
            assessment["overall_score"] += financial_score
        
        # Normalize overall score to 0-10 scale
        assessment["overall_score"] = max(0, min(10, assessment["overall_score"] + 5))
        
        return assessment

def main():
    """Test the OperatorAnalyzer with sample data"""
    import os
    from dotenv import load_dotenv
    
    # Load environment variables
    load_dotenv()
    
    # Get API token from environment
    api_token = os.getenv('SERPAPI_TOKEN')
    
    if not api_token:
        print("⚠️  No SERPAPI_TOKEN found in environment variables")
        print("   Add your token to .env file: SERPAPI_TOKEN=your_token_here")
        print("   Testing will continue but will show warnings about missing token\n")
    
    # Initialize analyzer
    analyzer = OperatorAnalyzer(serpapi_key=api_token)
    
    # Test operators - mix of public and private companies
    test_operators = [
        "Digital Realty",
        "Equinix", 
        "Vantage Data Centers"  # Private company
    ]
    
    print("🏢 Data Center Operator Analysis Test Suite")
    print("=" * 60)
    
    # Test 1: Stock symbol resolution
    print("\n📈 Testing Stock Symbol Resolution:")
    print("-" * 40)
    
    for operator in test_operators:
        symbol = analyzer.financial_analyzer.get_stock_symbol(operator)
        if symbol:
            print(f"  ✅ {operator} → {symbol}")
        else:
            print(f"  ❌ {operator} → No symbol found (likely private)")
    
    # Test 2: Financial data retrieval
    print("\n💰 Testing Financial Data Retrieval:")
    print("-" * 40)
    
    # Test with a few known public companies
    test_operators = ["Equinix", "Digital Realty", "American Tower"]
    
    for operator in test_operators:
        print(f"\n📊 Testing {operator}:")
        financial_data = analyzer.financial_analyzer.search_financial_data(operator)
        
        if financial_data:
            metrics = analyzer.financial_analyzer.parse_financial_metrics(financial_data, operator)
            if metrics:
                print(f"  ✅ Company: {metrics.company_name}")
                print(f"  💵 Price: ${metrics.current_price}")
                print(f"  📈 Change: {metrics.price_change_percent:+.2f}%")
                print(f"  🏢 Market Cap: {metrics.market_cap or 'N/A'}")
                print(f"  📊 P/E Ratio: {metrics.pe_ratio or 'N/A'}")
                print(f"  💰 Dividend Yield: {metrics.dividend_yield or 'N/A'}%")
                print(f"  📈 52W High: ${metrics.fifty_two_week_high or 'N/A'}")
                print(f"  📉 52W Low: ${metrics.fifty_two_week_low or 'N/A'}")
                print(f"  📊 Beta: {metrics.beta or 'N/A'}")
                print(f"  💼 EPS: ${metrics.eps or 'N/A'}")
            else:
                print(f"  ❌ Failed to parse financial data")
        else:
            print(f"  ❌ Failed to fetch financial data")
    
    # Test 3: News analysis
    print("\n📰 Testing News Analysis:")
    print("-" * 30)
    
    test_news_queries = ["Equinix data center", "Digital Realty expansion"]
    
    for query in test_news_queries:
        print(f"\n🔍 Testing news search: '{query}'")
        news_results = analyzer.news_analyzer.search_news(query, days_back=7)
        
        if news_results:
            news_items = analyzer.news_analyzer.parse_news_items(news_results, query.split()[0])
            print(f"  ✅ Found {len(news_items)} articles")
            
            if news_items:
                # Show top 3 articles
                for i, item in enumerate(news_items[:3], 1):
                    print(f"  {i}. {item.title[:60]}...")
                    print(f"     Source: {item.source} | Date: {item.date}")
        else:
            print(f"  ❌ No news results found")
    
    # Test 4: Complete operator analysis
    print("\n🎯 Testing Complete Operator Analysis:")
    print("-" * 45)
    
    # Test with 2-3 operators for comprehensive analysis
    detailed_test_operators = ["Equinix", "Digital Realty", "Vantage Data Centers"]
    
    for operator in detailed_test_operators:
        print(f"\n{'='*60}")
        print(f"🏢 COMPREHENSIVE ANALYSIS: {operator}")
        print(f"{'='*60}")
        
        analysis = analyzer.analyze_operator(operator, include_news=True, news_days=14)
        
        # Display results
        print(f"\n📊 ANALYSIS RESULTS:")
        print(f"  🏢 Operator: {analysis['operator_name']}")
        print(f"  ⏰ Timestamp: {analysis['analysis_timestamp']}")
        
        # Financial data
        if analysis['financial_data']:
            fd = analysis['financial_data']
            print(f"\n💰 FINANCIAL DATA:")
            print(f"  📈 Symbol: {fd['symbol']}")
            print(f"  🏢 Company: {fd['company_name']}")
            print(f"  💵 Current Price: ${fd['current_price']}")
            print(f"  📈 Change: {fd['price_change_percent']:+.2f}%")
            print(f"  🏢 Market Cap: {fd['market_cap'] or 'N/A'}")
            print(f"  📊 P/E Ratio: {fd['pe_ratio'] or 'N/A'}")
            print(f"  💰 Dividend Yield: {fd['dividend_yield'] or 'N/A'}%")
            print(f"  📈 52W High: ${fd['fifty_two_week_high'] or 'N/A'}")
            print(f"  📉 52W Low: ${fd['fifty_two_week_low'] or 'N/A'}")
            print(f"  📊 Beta: {fd['beta'] or 'N/A'}")
            print(f"  💼 EPS: ${fd['eps'] or 'N/A'}")
        else:
            print(f"\n💰 FINANCIAL DATA: Not available (likely private company)")
        
        # News analysis
        if analysis['news_analysis']:
            na = analysis['news_analysis']
            print(f"\n📰 NEWS ANALYSIS:")
            print(f"  📊 Total Articles: {na['total_articles']}")
            print(f"  📰 Recent Headlines:")
            for i, headline in enumerate(na['recent_headlines'][:5], 1):
                print(f"  {i}. {headline['title'][:80]}...")
                print(f"     Source: {headline['source']} | Date: {headline['date']}")
            
            print(f"  📆 Days Analyzed: {na['days_analyzed']}")
        else:
            print(f"\n📰 NEWS ANALYSIS: Not available")
        
        # Overall assessment
        if analysis['overall_assessment']:
            oa = analysis['overall_assessment']
            print(f"\n🎯 OVERALL ASSESSMENT:")
            print(f"  💰 Financial Health: {oa['financial_health'].upper()}")
            print(f"  📊 Overall Score: {oa['overall_score']}/10")
            
            if oa['key_insights']:
                print(f"  ✅ Key Insights:")
                for insight in oa['key_insights']:
                    print(f"    • {insight}")
            
            if oa['opportunities']:
                print(f"  🚀 Opportunities:")
                for opportunity in oa['opportunities']:
                    print(f"    • {opportunity}")
            
            if oa['risk_factors']:
                print(f"  ⚠️  Risk Factors:")
                for risk in oa['risk_factors']:
                    print(f"    • {risk}")
        
        # Errors
        if analysis['errors']:
            print(f"\n❌ ERRORS:")
            for error in analysis['errors']:
                print(f"  • {error}")
        
        print(f"\n{'='*60}")
    
    # Test 5: Error handling
    print(f"\n🚨 Testing Error Handling:")
    print("-" * 30)
    
    # Test with non-existent operator
    print(f"\n🔍 Testing non-existent operator:")
    fake_analysis = analyzer.analyze_operator("NonExistentDataCenterOperator", include_news=False)
    if fake_analysis['errors']:
        print(f"  ✅ Correctly handled non-existent operator")
        for error in fake_analysis['errors']:
            print(f"    • {error}")
    
    print(f"\n" + "=" * 60)
    print("🎉 Operator Analysis Test Suite Complete!")
    
    if api_token:
        print("✅ All tests ran with real SerpAPI data")
    else:
        print("⚠️  Tests ran without API token - add SERPAPI_TOKEN to .env for real data")
    
    print(f"\n💡 Usage Tips:")
    print("  - Set SERPAPI_TOKEN in your .env file")
    print("  - Use exact operator names for best results")
    print("  - Financial data only available for publicly traded companies")
    print("  - News analysis works for both public and private companies")
    print("  - Adjust news_days parameter to get more/less recent news")
    print("  - Check 'errors' field in results for issues")

if __name__ == "__main__":
    # Run the comprehensive test suite
    main()

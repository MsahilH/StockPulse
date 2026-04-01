from fastapi import FastAPI, APIRouter, HTTPException
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime, timezone, timedelta
import httpx
import asyncio
from contextlib import asynccontextmanager

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')



# Create the main app without a prefix
app = FastAPI()

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# NIFTY50 Stock Symbols
NIFTY50_SYMBOLS = [
    "RELIANCE", "TCS", "HDFCBANK", "INFY", "ICICIBANK",
    "HINDUNILVR", "SBIN", "BHARTIARTL", "ITC", "KOTAKBANK",
    "LT", "HCLTECH", "AXISBANK", "ASIANPAINT", "MARUTI",
    "SUNPHARMA", "TITAN", "BAJFINANCE", "DMART", "ULTRACEMCO",
    "NTPC", "ONGC", "WIPRO", "POWERGRID", "M&M",
    "JSWSTEEL", "TATASTEEL", "ADANIENT", "ADANIPORTS", "COALINDIA",
    "TECHM", "INDUSINDBK", "HINDALCO", "GRASIM", "BAJAJFINSV",
    "DRREDDY", "CIPLA", "NESTLEIND", "BRITANNIA", "HEROMOTOCO",
    "EICHERMOT", "DIVISLAB", "APOLLOHOSP", "BPCL", "TATACONSUM",
    "SBILIFE", "HDFCLIFE", "UPL", "SHREECEM", "TATAMOTORS"
]

# External Indian Stock API configuration
# Using Yahoo Finance API (Free and fast) with Redundancy
YAHOO_FINANCE_HOSTS = [
    "https://query1.finance.yahoo.com",
    "https://query2.finance.yahoo.com"
]
YAHOO_FINANCE_PATH = "/v8/finance/chart"

# Multiple GNews queries to construct a larger feed while bypassing max=10 per request
NEWS_API_ENDPOINTS = [
    "https://gnews.io/api/v4/top-headlines?category=business&lang=en&country=in&max=10&apikey=", # Business News
    "https://gnews.io/api/v4/top-headlines?category=technology&lang=en&country=in&max=10&apikey=", # Tech News
    "https://gnews.io/api/v4/top-headlines?category=general&lang=en&country=in&max=10&apikey=" # General News
]

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Define Models


class StockQuote(BaseModel):
    symbol: str
    name: str
    price: float
    change: float
    changePercent: float
    open: float
    high: float
    low: float
    volume: int
    previousClose: float
    dayHigh: float
    dayLow: float
    fiftyTwoWeekHigh: Optional[float] = None
    fiftyTwoWeekLow: Optional[float] = None
    lastUpdated: str

class StockHistoryPoint(BaseModel):
    date: str
    price: float

# Cache for stock data to avoid repeated API calls
stock_cache: Dict[str, Dict[str, Any]] = {}
cache_timestamp: Dict[str, datetime] = {}
news_cache: Dict[str, Any] = {"news": [], "timestamp": None}
CACHE_DURATION = 60  # seconds - cache for 1 minute

# Background task to refresh cache
async def refresh_all_stocks_background():
    """Periodically refresh all stocks in the background for zero-latency user access"""
    while True:
        try:
            logger.info("⚡ Background Cache Refresh: Started")
            semaphore = asyncio.Semaphore(1) # Reduced concurrency to 1 to avoid 429 Too Many Requests
            
            async def limited_fetch(symbol):
                async with semaphore:
                    data = await fetch_external_stock_data(symbol)
                    if data:
                        stock_cache[symbol] = data
                        cache_timestamp[symbol] = datetime.now(timezone.utc)
                    await asyncio.sleep(2.0) # Respect rate limits strictly to avoid 429
            
            await asyncio.gather(*[limited_fetch(symbol) for symbol in NIFTY50_SYMBOLS])
            
            logger.info("✅ Background Stocks Cache Refresh: Completed")
        except Exception as e:
            logger.error(f"❌ Background Cache error: {e}")
        
        await asyncio.sleep(300) # Refresh every 5 minutes instead of 1 minute to avoid rate limits

async def refresh_news_loop():
    """Independent loop to fetch news every 30 minutes to respect API rate limits."""
    # Run once immediately, then loop
    while True:
        try:
            await refresh_news_background()
        except Exception as e:
            logger.error(f"❌ Background News error: {e}")
        
        await asyncio.sleep(1800) # Sleep for 30 minutes (respects 100/day GNews free limit)

async def refresh_news_background():
    """Aggregates news from multiple category requests"""
    all_articles = []
    
    for endpoint in NEWS_API_ENDPOINTS:
        try:
            # Use a free GNews API key as default for demonstration
            api_key = ""
            if "newsapi.org" in endpoint:
                api_key = os.environ.get("NEWS_API_KEY", "f77e3479d26b4d4eb138c1ae26b5b258")
                if not api_key: continue
            elif "gnews.io" in endpoint:
                api_key = os.environ.get("GNEWS_API_KEY", "b44da312ccbcf8cdd4f00b201d120a1c") 
                
            actual_url = endpoint + api_key
            
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(actual_url)
                if response.status_code == 200:
                    data = response.json()
                    articles = data.get('articles', [])
                    if articles:
                        # Map GNews fields to expected NewsAPI format
                        for article in articles:
                            if 'image' in article and 'urlToImage' not in article:
                                article['urlToImage'] = article['image']
                        all_articles.extend(articles)
                elif response.status_code == 429:
                    logger.warning(f"⚠️ Rate limited (429) by news provider: {endpoint}")
        except Exception as e:
            logger.warning(f"⚠️ Failed to fetch news from {endpoint}: {e}")
            continue
            
    if all_articles:
        # Deduplicate and sort by publication date
        seen_urls = set()
        unique_articles = []
        for a in all_articles:
            url = a.get('url')
            if url and url not in seen_urls:
                seen_urls.add(url)
                unique_articles.append(a)
        
        # Sort by latest published (assuming ISO8601 strings)
        unique_articles.sort(key=lambda x: str(x.get('publishedAt', '')), reverse=True)
        
        news_cache["news"] = unique_articles[:30] # Limit to 30 items
        news_cache["timestamp"] = datetime.now(timezone.utc).isoformat()
        logger.info(f"✅ Aggregated {len(news_cache['news'])} News Articles Successfully")
    elif not news_cache["news"]:
        # Emergency Fallback: If ALL APIs fail, provide mock news so UI isn't empty
        news_cache["news"] = generate_mock_news()
        news_cache["timestamp"] = datetime.now(timezone.utc).isoformat()
        logger.info("ℹ️ Using Mock News fallback")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Start background tasks independently
    stock_task = asyncio.create_task(refresh_all_stocks_background())
    news_task = asyncio.create_task(refresh_news_loop())
    yield
    # Cleanup
    stock_task.cancel()
    news_task.cancel()
    try:
        await stock_task
        await news_task
    except asyncio.CancelledError:
        pass

# Create the main app with lifespan management
app = FastAPI(lifespan=lifespan)
async def fetch_external_stock_data(symbol: str) -> Optional[Dict[str, Any]]:
    """Internal helper to fetch data from external APIs"""
    # Try multiple hosts in order
    for host in YAHOO_FINANCE_HOSTS:
        try:
            ticker = f"{symbol}.NS"
            async with httpx.AsyncClient(timeout=5.0) as client: # Fast timeout for background
                response = await client.get(
                    f"{host}{YAHOO_FINANCE_PATH}/{ticker}?interval=1d&range=1d"
                )
                if response.status_code == 200:
                    data = response.json()
                    if 'chart' in data and 'result' in data['chart'] and data['chart']['result']:
                        result = data['chart']['result'][0]
                        meta = result.get('meta', {})
                        
                        price = meta.get('regularMarketPrice', 0)
                        prev_close = meta.get('previousClose', price)
                        
                        change = price - prev_close
                        change_percent = (change / prev_close) * 100 if prev_close else 0
                        
                        return {
                            "symbol": symbol,
                            "name": get_stock_name(symbol),
                            "price": round(price, 2),
                            "change": round(change, 2),
                            "changePercent": round(change_percent, 2),
                            "open": meta.get('regularMarketDayOpen', price),
                            "high": meta.get('regularMarketDayHigh', price),
                            "low": meta.get('regularMarketDayLow', price),
                            "volume": result.get('indicators', {}).get('quote', [{}])[0].get('volume', [0])[0] or 0,
                            "previousClose": round(prev_close, 2),
                            "lastUpdated": datetime.now(timezone.utc).isoformat()
                        }
        except Exception:
            continue
    return None

async def fetch_stock_data(symbol: str) -> Optional[Dict[str, Any]]:
    """Serve data from high-speed cache or fallback to mock instantly"""
    # If in cache, return immediately
    if symbol in stock_cache:
        return stock_cache[symbol]
    
    # Otherwise, return mock data instantly so the UI never waits
    return generate_mock_stock(symbol)

async def fetch_stock_history(symbol: str) -> List[Dict[str, Any]]:
    """Fetch historical data for sparkline charts with redundancy"""
    for host in YAHOO_FINANCE_HOSTS:
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                ticker = f"{symbol}.NS"
                response = await client.get(f"{host}{YAHOO_FINANCE_PATH}/{ticker}?interval=1d&range=1mo")
                if response.status_code == 200:
                    data = response.json()
                    # Format history to match our model
                    result = data['chart']['result'][0]
                    timestamps = result['timestamp']
                    prices = result['indicators']['adjclose'][0]['adjclose']
                    
                    history = []
                    for t, p in zip(timestamps, prices):
                        if p is not None:
                            history.append({
                                "date": datetime.fromtimestamp(t).strftime('%Y-%m-%d'),
                                "price": round(p, 2)
                            })
                    return history[-30:] if history else []
        except Exception as e:
            logger.warning(f"Error fetching history for {symbol} from host {host}: {e}")
            continue
    return []

# Add your routes to the router
@api_router.get("/")
async def root():
    return {"message": "Indian Stock Dashboard API"}

@api_router.get("/nifty50-symbols")
async def get_nifty50_symbols():
    """Get list of all NIFTY50 symbols"""
    return {"symbols": NIFTY50_SYMBOLS}

@api_router.get("/stock/{symbol}")
async def get_stock_quote(symbol: str):
    """Get real-time quote for a single stock"""
    data = await fetch_stock_data(symbol.upper())
    
    if data:
        return data
    
    # Return mock data if API fails
    return generate_mock_stock(symbol.upper())

@api_router.get("/stocks")
async def get_all_stocks():
    """INSTANT Endpoint: Returns the entire cached NIFTY 50 list immediately"""
    stocks = []
    for symbol in NIFTY50_SYMBOLS:
        if symbol in stock_cache:
            stocks.append(stock_cache[symbol])
        else:
            stocks.append(generate_mock_stock(symbol))
    
    return {"stocks": list(stocks), "timestamp": datetime.now(timezone.utc).isoformat()}

@api_router.get("/stocks/batch")
async def get_stocks_batch(symbols: str = ""):
    """Get quotes for specified stocks (comma-separated)"""
    if not symbols:
        symbols = ",".join(NIFTY50_SYMBOLS[:10])  # Default to first 10
    
    symbol_list = [s.strip().upper() for s in symbols.split(",")]
    stocks = []
    
    for symbol in symbol_list:
        data = await fetch_stock_data(symbol)
        if data:
            stocks.append({
                "symbol": symbol,
                "name": data.get("name", symbol),
                "price": data.get("price", 0),
                "change": data.get("change", 0),
                "changePercent": data.get("changePercent", 0),
                "open": data.get("open", 0),
                "high": data.get("dayHigh", data.get("high", 0)),
                "low": data.get("dayLow", data.get("low", 0)),
                "volume": data.get("volume", 0),
                "previousClose": data.get("previousClose", 0),
                "lastUpdated": datetime.now(timezone.utc).isoformat()
            })
        else:
            stocks.append(generate_mock_stock(symbol))
    
    return {"stocks": stocks, "timestamp": datetime.now(timezone.utc).isoformat()}

@api_router.get("/stock/{symbol}/history")
async def get_stock_history(symbol: str):
    """Get historical price data for charts"""
    history = await fetch_stock_history(symbol.upper())
    
    if history:
        return {"symbol": symbol.upper(), "history": history}
    
    # Generate mock history if API fails
    return {"symbol": symbol.upper(), "history": generate_mock_history()}

@api_router.get("/news")
async def get_market_news():
    """INSTANT Endpoint: Returns the cached headlines immediately"""
    if news_cache["news"]:
        return news_cache
    
    return {"news": [], "error": "News cache warming up..."}

@api_router.get("/search")
async def search_stocks(q: str = ""):
    """Search stocks by name or symbol"""
    if not q:
        return {"results": []}
    
    query = q.upper()
    results = []
    
    # Search in NIFTY50 symbols
    for symbol in NIFTY50_SYMBOLS:
        if query in symbol:
            results.append({"symbol": symbol, "name": get_stock_name(symbol)})
    
    # Also search by common names
    stock_names = get_all_stock_names()
    for symbol, name in stock_names.items():
        if query in name.upper() and symbol not in [r["symbol"] for r in results]:
            results.append({"symbol": symbol, "name": name})
    
    return {"results": results[:20]}  # Limit to 20 results

@api_router.get("/market-status")
async def get_market_status():
    """Get current market status"""
    now = datetime.now(timezone.utc)
    # NSE trading hours: 9:15 AM - 3:30 PM IST (UTC+5:30)
    # Convert to IST
    ist_hour = (now.hour + 5) % 24 + (1 if now.minute >= 30 else 0)
    
    is_weekend = now.weekday() >= 5
    is_trading_hours = 9 <= ist_hour < 16 and not is_weekend
    
    return {
        "isOpen": is_trading_hours,
        "status": "Market Open" if is_trading_hours else "Market Closed",
        "nextOpen": "9:15 AM IST" if not is_trading_hours else None,
        "timestamp": now.isoformat()
    }


# Helper functions
# Realistic NIFTY50 base prices (approx real prices)
STOCK_BASE_PRICES = {
    "RELIANCE": 2450, "TCS": 3800, "HDFCBANK": 1650, "INFY": 1450, "ICICIBANK": 1050,
    "HINDUNILVR": 2350, "SBIN": 620, "BHARTIARTL": 1180, "ITC": 430, "KOTAKBANK": 1780,
    "LT": 3450, "HCLTECH": 1580, "AXISBANK": 1100, "ASIANPAINT": 2850, "MARUTI": 10500,
    "SUNPHARMA": 1650, "TITAN": 3250, "BAJFINANCE": 6800, "DMART": 3650, "ULTRACEMCO": 10200,
    "NTPC": 350, "ONGC": 265, "WIPRO": 480, "POWERGRID": 305, "M&M": 2750,
    "JSWSTEEL": 850, "TATASTEEL": 145, "ADANIENT": 2400, "ADANIPORTS": 1180, "COALINDIA": 395,
    "TECHM": 1550, "INDUSINDBK": 1420, "HINDALCO": 620, "GRASIM": 2550, "BAJAJFINSV": 1680,
    "DRREDDY": 6200, "CIPLA": 1480, "NESTLEIND": 22500, "BRITANNIA": 5100, "HEROMOTOCO": 4250,
    "EICHERMOT": 4650, "DIVISLAB": 5850, "APOLLOHOSP": 6750, "BPCL": 585, "TATACONSUM": 1050,
    "SBILIFE": 1520, "HDFCLIFE": 640, "UPL": 520, "SHREECEM": 25800, "TATAMOTORS": 785
}

def generate_mock_news() -> List[Dict[str, Any]]:
    return [
        {
            "title": "Indian Markets Hit Record Highs Following Policy Announcements",
            "description": "The BSE Sensex and Nifty 50 surged to new all-time highs today, driven by strong buying in banking, IT, and consumer durable sectors...",
            "url": "#",
            "urlToImage": "https://images.unsplash.com/photo-1611974789855-9c2a0a7236a3?w=800&auto=format&fit=crop",
            "source": {"name": "Market Insider"},
            "publishedAt": datetime.now(timezone.utc).isoformat()
        },
        {
            "title": "Tech Giants in India Announce New AI Initiatives",
            "description": "Leading technology companies operating in India have announced multi-billion dollar investments in building AI infrastructure and training programs.",
            "url": "#",
            "urlToImage": "https://images.unsplash.com/photo-1518770660439-4636190af475?w=800&auto=format&fit=crop",
            "source": {"name": "Tech Daily"},
            "publishedAt": (datetime.now(timezone.utc) - timedelta(hours=2)).isoformat()
        },
        {
            "title": "Reserve Bank of India Keeps Repo Rate Unchanged",
            "description": "In a widely expected move, the RBI's Monetary Policy Committee decided to maintain the policy repo rate at its current level, focusing on inflation control.",
            "url": "#",
            "urlToImage": "https://images.unsplash.com/photo-1541354329998-f4d9a9f929d4?w=800&auto=format&fit=crop",
            "source": {"name": "Finance Today"},
            "publishedAt": (datetime.now(timezone.utc) - timedelta(hours=5)).isoformat()
        }
    ]

def generate_mock_stock(symbol: str) -> Dict[str, Any]:
    """Generate realistic mock stock data"""
    import random
    import hashlib
    
    # Use symbol hash to get consistent random seed for the same symbol
    seed = int(hashlib.md5(f"{symbol}{datetime.now(timezone.utc).strftime('%Y-%m-%d-%H')}".encode()).hexdigest()[:8], 16)
    random.seed(seed)
    
    base_price = STOCK_BASE_PRICES.get(symbol, random.uniform(500, 3000))
    
    # Add some variance (±3% from base)
    price_variance = base_price * random.uniform(-0.03, 0.03)
    current_price = base_price + price_variance
    
    # Generate realistic change (-2% to +2%)
    change_percent = random.uniform(-2, 2)
    change = current_price * (change_percent / 100)
    previous_close = current_price - change
    
    # Generate intraday high/low
    day_range = current_price * random.uniform(0.005, 0.015)
    
    return {
        "symbol": symbol,
        "name": get_stock_name(symbol),
        "price": round(current_price, 2),
        "change": round(change, 2),
        "changePercent": round(change_percent, 2),
        "open": round(previous_close + random.uniform(-day_range, day_range), 2),
        "high": round(current_price + day_range, 2),
        "low": round(current_price - day_range, 2),
        "volume": random.randint(500000, 15000000),
        "previousClose": round(previous_close, 2),
        "lastUpdated": datetime.now(timezone.utc).isoformat()
    }

def generate_mock_history() -> List[Dict[str, Any]]:
    """Generate realistic mock historical data"""
    import random
    history = []
    base_price = random.uniform(1000, 3000)
    
    for i in range(30):
        day = datetime.now(timezone.utc) - timedelta(days=30-i)
        base_price += random.uniform(-30, 35)  # Slight upward bias
        base_price = max(100, base_price)  # Floor at 100
        history.append({
            "date": day.strftime("%Y-%m-%d"),
            "price": round(base_price, 2)
        })
    
    return history

def get_stock_name(symbol: str) -> str:
    """Get company name from symbol"""
    names = get_all_stock_names()
    return names.get(symbol, symbol)

def get_all_stock_names() -> Dict[str, str]:
    """Get all stock names mapping"""
    return {
        "RELIANCE": "Reliance Industries",
        "TCS": "Tata Consultancy Services",
        "HDFCBANK": "HDFC Bank",
        "INFY": "Infosys",
        "ICICIBANK": "ICICI Bank",
        "HINDUNILVR": "Hindustan Unilever",
        "SBIN": "State Bank of India",
        "BHARTIARTL": "Bharti Airtel",
        "ITC": "ITC Limited",
        "KOTAKBANK": "Kotak Mahindra Bank",
        "LT": "Larsen & Toubro",
        "HCLTECH": "HCL Technologies",
        "AXISBANK": "Axis Bank",
        "ASIANPAINT": "Asian Paints",
        "MARUTI": "Maruti Suzuki",
        "SUNPHARMA": "Sun Pharma",
        "TITAN": "Titan Company",
        "BAJFINANCE": "Bajaj Finance",
        "DMART": "Avenue Supermarts",
        "ULTRACEMCO": "UltraTech Cement",
        "NTPC": "NTPC Limited",
        "ONGC": "Oil & Natural Gas Corp",
        "WIPRO": "Wipro",
        "POWERGRID": "Power Grid Corp",
        "M&M": "Mahindra & Mahindra",
        "JSWSTEEL": "JSW Steel",
        "TATASTEEL": "Tata Steel",
        "ADANIENT": "Adani Enterprises",
        "ADANIPORTS": "Adani Ports",
        "COALINDIA": "Coal India",
        "TECHM": "Tech Mahindra",
        "INDUSINDBK": "IndusInd Bank",
        "HINDALCO": "Hindalco Industries",
        "GRASIM": "Grasim Industries",
        "BAJAJFINSV": "Bajaj Finserv",
        "DRREDDY": "Dr. Reddy's Labs",
        "CIPLA": "Cipla",
        "NESTLEIND": "Nestle India",
        "BRITANNIA": "Britannia Industries",
        "HEROMOTOCO": "Hero MotoCorp",
        "EICHERMOT": "Eicher Motors",
        "DIVISLAB": "Divi's Laboratories",
        "APOLLOHOSP": "Apollo Hospitals",
        "BPCL": "Bharat Petroleum",
        "TATACONSUM": "Tata Consumer Products",
        "SBILIFE": "SBI Life Insurance",
        "HDFCLIFE": "HDFC Life Insurance",
        "UPL": "UPL Limited",
        "SHREECEM": "Shree Cement",
        "TATAMOTORS": "Tata Motors"
    }

# Include the router in the main app
app.include_router(api_router)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_credentials=False,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

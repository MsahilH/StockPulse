from fastapi import FastAPI, APIRouter, HTTPException
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime, timezone, timedelta
import httpx

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

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
INDIAN_STOCK_API_BASE = "https://stock.indianapi.in"
INDIAN_STOCK_API_KEY = os.environ.get('INDIAN_STOCK_API_KEY', '')

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Define Models
class StatusCheck(BaseModel):
    model_config = ConfigDict(extra="ignore")
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    client_name: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class StatusCheckCreate(BaseModel):
    client_name: str

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
CACHE_DURATION = 60  # seconds - cache for 1 minute to reduce API calls

# HTTP client for external API calls
async def fetch_stock_data(symbol: str) -> Optional[Dict[str, Any]]:
    """Fetch stock data from Indian Stock API"""
    # Check cache first
    if symbol in stock_cache:
        cache_time = cache_timestamp.get(symbol)
        if cache_time and (datetime.now(timezone.utc) - cache_time).seconds < CACHE_DURATION:
            return stock_cache[symbol]
    
    try:
        headers = {"X-Api-Key": INDIAN_STOCK_API_KEY}
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.get(
                f"{INDIAN_STOCK_API_BASE}/stock",
                params={"name": symbol},
                headers=headers
            )
            if response.status_code == 200:
                data = response.json()
                if data and 'currentPrice' in data:
                    # Parse the API response
                    nse_price = float(data.get('currentPrice', {}).get('NSE', '0').replace(',', ''))
                    percent_change = float(data.get('percentChange', '0').replace(',', ''))
                    year_high = float(data.get('yearHigh', '0').replace(',', '')) if data.get('yearHigh') else None
                    year_low = float(data.get('yearLow', '0').replace(',', '')) if data.get('yearLow') else None
                    
                    # Calculate change amount
                    change = nse_price * (percent_change / 100)
                    previous_close = nse_price - change
                    
                    parsed_data = {
                        "symbol": symbol,
                        "name": data.get('companyName', symbol),
                        "price": nse_price,
                        "change": round(change, 2),
                        "changePercent": percent_change,
                        "open": previous_close,  # Approximate
                        "high": nse_price * 1.01,  # Approximate
                        "low": nse_price * 0.99,  # Approximate  
                        "volume": 0,  # Not provided
                        "previousClose": round(previous_close, 2),
                        "fiftyTwoWeekHigh": year_high,
                        "fiftyTwoWeekLow": year_low,
                        "industry": data.get('industry', ''),
                        "lastUpdated": datetime.now(timezone.utc).isoformat()
                    }
                    
                    stock_cache[symbol] = parsed_data
                    cache_timestamp[symbol] = datetime.now(timezone.utc)
                    return parsed_data
    except Exception as e:
        logger.error(f"Error fetching stock {symbol}: {e}")
    
    return None

async def fetch_stock_history(symbol: str) -> List[Dict[str, Any]]:
    """Fetch historical data for sparkline charts"""
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.get(f"{NSE_API_BASE}/history?symbol={symbol}.NS&range=1mo")
            if response.status_code == 200:
                data = response.json()
                if isinstance(data, list):
                    return data[-30:]  # Last 30 data points
    except Exception as e:
        logger.error(f"Error fetching history for {symbol}: {e}")
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
    """Get quotes for all NIFTY50 stocks"""
    import asyncio
    
    async def get_stock_with_fallback(symbol: str) -> Dict[str, Any]:
        data = await fetch_stock_data(symbol)
        if data:
            return data
        return generate_mock_stock(symbol)
    
    # Fetch all stocks concurrently with a semaphore to limit concurrent requests
    semaphore = asyncio.Semaphore(3)  # Limit to 3 concurrent requests to avoid rate limits
    
    async def limited_fetch(symbol: str):
        async with semaphore:
            result = await get_stock_with_fallback(symbol)
            await asyncio.sleep(0.2)  # Small delay to avoid rate limiting
            return result
    
    stocks = await asyncio.gather(*[limited_fetch(symbol) for symbol in NIFTY50_SYMBOLS])
    
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

@api_router.post("/status", response_model=StatusCheck)
async def create_status_check(input: StatusCheckCreate):
    status_dict = input.model_dump()
    status_obj = StatusCheck(**status_dict)
    
    doc = status_obj.model_dump()
    doc['timestamp'] = doc['timestamp'].isoformat()
    
    _ = await db.status_checks.insert_one(doc)
    return status_obj

@api_router.get("/status", response_model=List[StatusCheck])
async def get_status_checks():
    status_checks = await db.status_checks.find({}, {"_id": 0}).to_list(1000)
    
    for check in status_checks:
        if isinstance(check['timestamp'], str):
            check['timestamp'] = datetime.fromisoformat(check['timestamp'])
    
    return status_checks

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

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()

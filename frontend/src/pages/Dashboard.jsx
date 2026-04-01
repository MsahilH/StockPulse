import { useState, useEffect, useCallback } from "react";
import { useNavigate, Link } from "react-router-dom";
import axios from "axios";
import { Search, RefreshCw, TrendingUp, TrendingDown, Clock, Activity } from "lucide-react";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { toast } from "sonner";
import StockCard from "@/components/StockCard";
import AdBanner from "@/components/AdBanner";

const BACKEND_URL = "http://localhost:8000"
// console.log(process, 'process')
const API = `${BACKEND_URL}/api`;

const Dashboard = () => {
  const navigate = useNavigate();
  const [stocks, setStocks] = useState([]);
  const [filteredStocks, setFilteredStocks] = useState([]);
  const [searchQuery, setSearchQuery] = useState("");
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [marketStatus, setMarketStatus] = useState({ isOpen: false, status: "Loading..." });
  const [lastUpdated, setLastUpdated] = useState(null);
  const [autoRefresh, setAutoRefresh] = useState(true);

  const fetchStocks = useCallback(async (showToast = false) => {
    try {
      if (!loading) setRefreshing(true);
      const response = await axios.get(`${API}/stocks`);
      
      if (response.data?.stocks) {
        setStocks(response.data.stocks);
        setFilteredStocks(response.data.stocks);
        setLastUpdated(new Date());
        if (showToast) {
          toast.success("Prices updated successfully");
        }
      }
    } catch (error) {
      console.error("Error fetching stocks:", error);
      toast.error("Failed to fetch stock data");
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, [loading]);

  const fetchMarketStatus = useCallback(async () => {
    try {
      const response = await axios.get(`${API}/market-status`);
      setMarketStatus(response.data);
    } catch (error) {
      console.error("Error fetching market status:", error);
    }
  }, []);

  useEffect(() => {
    fetchStocks();
    fetchMarketStatus();
  }, [fetchStocks, fetchMarketStatus]);

  // Auto-refresh every 30 seconds
  useEffect(() => {
    if (!autoRefresh) return;
    
    const interval = setInterval(() => {
      fetchStocks();
    }, 30000);

    return () => clearInterval(interval);
  }, [autoRefresh, fetchStocks]);

  // Search filter
  useEffect(() => {
    if (!searchQuery.trim()) {
      setFilteredStocks(stocks);
      return;
    }

    const query = searchQuery.toLowerCase();
    const filtered = stocks.filter(
      (stock) =>
        stock.symbol.toLowerCase().includes(query) ||
        stock.name.toLowerCase().includes(query)
    );
    setFilteredStocks(filtered);
  }, [searchQuery, stocks]);

  const handleManualRefresh = () => {
    fetchStocks(true);
  };

  const handleStockClick = (symbol) => {
    navigate(`/stock/${symbol}`);
  };

  // Calculate market summary
  const gainers = stocks.filter((s) => s.changePercent > 0).length;
  const losers = stocks.filter((s) => s.changePercent < 0).length;
  const unchanged = stocks.filter((s) => s.changePercent === 0).length;

  return (
    <div className="min-h-screen bg-[#0A0A0A]">
      {/* Header */}
      <header className="sticky top-0 z-50 bg-[#121212] border-b border-white/10" data-testid="main-header">
        <div className="container mx-auto px-4 md:px-6 py-4">
          <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
            {/* Logo & Title */}
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-[#00C805] to-[#007AFF] flex items-center justify-center">
                <Activity className="w-6 h-6 text-white" />
              </div>
              <div>
                <h1 className="text-xl md:text-2xl font-bold tracking-tight font-['Manrope']" data-testid="app-title">
                  StockPulse
                </h1>
                <p className="text-xs text-[#666666]">NIFTY 50 Live Tracker</p>
              </div>
            
            {/* Quick Links */}
            <nav className="flex items-center gap-6 ml-4 hidden md:flex">
              <Link to="/" className="text-sm font-medium text-white hover:text-[#00C805] transition-colors">Market</Link>
              <Link to="/news" className="text-sm font-medium text-[#A0A0A0] hover:text-[#00C805] transition-colors flex items-center gap-2">
                News
                <Badge variant="secondary" className="scale-75 bg-[#007AFF]/10 text-[#007AFF] border-none font-bold">LIVE</Badge>
              </Link>
            </nav>
            </div>

            {/* Search Bar */}
            <div className="relative flex-1 max-w-md" data-testid="search-container">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-[#666666]" />
              <Input
                type="text"
                placeholder="Search stocks by name or symbol..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="pl-10 bg-[#1E1E1E] border-white/10 text-white placeholder:text-[#666666] focus:border-white/30"
                data-testid="search-input"
              />
            </div>

            {/* Market Status & Refresh */}
            <div className="flex items-center gap-3">
              <Badge
                variant="outline"
                className={`${
                  marketStatus.isOpen
                    ? "bg-[#00C805]/15 text-[#00C805] border-[#00C805]/30"
                    : "bg-[#FF3B30]/15 text-[#FF3B30] border-[#FF3B30]/30"
                }`}
                data-testid="market-status-badge"
              >
                <span className={`w-2 h-2 rounded-full mr-2 ${marketStatus.isOpen ? "bg-[#00C805]" : "bg-[#FF3B30]"}`} />
                {marketStatus.status}
              </Badge>

              <Button
                variant="outline"
                size="sm"
                onClick={handleManualRefresh}
                disabled={refreshing}
                className="border-white/10 hover:border-white/20 hover:bg-white/5"
                data-testid="refresh-button"
              >
                <RefreshCw className={`w-4 h-4 mr-2 ${refreshing ? "animate-spin" : ""}`} />
                Refresh
              </Button>
            </div>
          </div>
        </div>
      </header>

      {/* Header Ad Banner */}
      <div className="container mx-auto px-4 md:px-6 py-4">
        <AdBanner
          type="header"
          adSlot="5524130932"
          imageUrl="https://images.pexels.com/photos/11194747/pexels-photo-11194747.jpeg"
          data-testid="header-ad-banner"
        />
      </div>

      <div className="container mx-auto px-4 md:px-6 pb-8">
        <div className="flex flex-col lg:flex-row gap-6">
          {/* Main Content */}
          <main className="flex-1" data-testid="main-content">
            {/* Market Summary */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
              <Card className="bg-[#121212] border-white/10">
                <CardContent className="p-4">
                  <div className="flex items-center gap-2 text-[#A0A0A0] text-sm mb-1">
                    <TrendingUp className="w-4 h-4 text-[#00C805]" />
                    Gainers
                  </div>
                  <p className="text-2xl font-bold text-[#00C805]" data-testid="gainers-count">{gainers}</p>
                </CardContent>
              </Card>
              <Card className="bg-[#121212] border-white/10">
                <CardContent className="p-4">
                  <div className="flex items-center gap-2 text-[#A0A0A0] text-sm mb-1">
                    <TrendingDown className="w-4 h-4 text-[#FF3B30]" />
                    Losers
                  </div>
                  <p className="text-2xl font-bold text-[#FF3B30]" data-testid="losers-count">{losers}</p>
                </CardContent>
              </Card>
              <Card className="bg-[#121212] border-white/10">
                <CardContent className="p-4">
                  <div className="flex items-center gap-2 text-[#A0A0A0] text-sm mb-1">
                    <Activity className="w-4 h-4 text-[#007AFF]" />
                    Total
                  </div>
                  <p className="text-2xl font-bold text-white" data-testid="total-count">{stocks.length}</p>
                </CardContent>
              </Card>
              <Card className="bg-[#121212] border-white/10">
                <CardContent className="p-4">
                  <div className="flex items-center gap-2 text-[#A0A0A0] text-sm mb-1">
                    <Clock className="w-4 h-4" />
                    Updated
                  </div>
                  <p className="text-sm font-medium text-white" data-testid="last-updated">
                    {lastUpdated ? lastUpdated.toLocaleTimeString() : "--:--:--"}
                  </p>
                </CardContent>
              </Card>
            </div>

            {/* Stock Grid */}
            <div className="mb-4 flex items-center justify-between">
              <h2 className="text-lg font-semibold font-['Manrope']" data-testid="section-title">
                NIFTY 50 Stocks
                {searchQuery && ` (${filteredStocks.length} results)`}
              </h2>
              <label className="flex items-center gap-2 text-sm text-[#A0A0A0]">
                <input
                  type="checkbox"
                  checked={autoRefresh}
                  onChange={(e) => setAutoRefresh(e.target.checked)}
                  className="rounded border-white/20 bg-[#1E1E1E]"
                  data-testid="auto-refresh-toggle"
                />
                Auto-refresh (30s)
              </label>
            </div>

            {loading ? (
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4" data-testid="loading-grid">
                {Array.from({ length: 12 }).map((_, i) => (
                  <Card key={i} className="bg-[#121212] border-white/10">
                    <CardContent className="p-4">
                      <Skeleton className="h-4 w-20 mb-2 bg-[#1E1E1E]" />
                      <Skeleton className="h-6 w-32 mb-4 bg-[#1E1E1E]" />
                      <Skeleton className="h-10 w-full bg-[#1E1E1E]" />
                    </CardContent>
                  </Card>
                ))}
              </div>
            ) : filteredStocks.length === 0 ? (
              <div className="text-center py-12 text-[#666666]" data-testid="no-results">
                <Search className="w-12 h-12 mx-auto mb-4 opacity-50" />
                <p>No stocks found matching "{searchQuery}"</p>
              </div>
            ) : (
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4" data-testid="stock-grid">
                {filteredStocks.map((stock, index) => (
                  <div key={stock.symbol}>
                    <StockCard
                      stock={stock}
                      onClick={() => handleStockClick(stock.symbol)}
                      data-testid={`stock-card-${stock.symbol}`}
                    />
                    {/* Insert content ad after every 8 cards */}
                    {(index + 1) % 8 === 0 && index < filteredStocks.length - 1 && (
                      <div className="col-span-1 sm:col-span-2 mt-4">
                        <AdBanner
                          type="content"
                          adSlot="3220132308"
                          imageUrl="https://images.pexels.com/photos/10414975/pexels-photo-10414975.jpeg"
                          data-testid="content-ad-banner"
                        />
                      </div>
                    )}
                  </div>
                ))}
              </div>
            )}
          </main>

          {/* Sidebar */}
          <aside className="w-full lg:w-72 space-y-6" data-testid="sidebar">
            {/* Sidebar Ad */}
            <AdBanner
              type="sidebar"
              adSlot="3220132308"
              imageUrl="https://images.unsplash.com/photo-1633869699811-cd4f63049b36"
              data-testid="sidebar-ad-banner"
            />

            {/* Top Gainers */}
            <Card className="bg-[#121212] border-white/10">
              <CardContent className="p-4">
                <h3 className="text-sm font-semibold text-[#A0A0A0] mb-3 flex items-center gap-2">
                  <TrendingUp className="w-4 h-4 text-[#00C805]" />
                  Top Gainers
                </h3>
                <div className="space-y-2">
                  {stocks
                    .sort((a, b) => b.changePercent - a.changePercent)
                    .slice(0, 5)
                    .map((stock) => (
                      <div
                        key={stock.symbol}
                        className="flex justify-between items-center py-2 px-2 rounded-lg hover:bg-white/5 cursor-pointer transition-colors"
                        onClick={() => handleStockClick(stock.symbol)}
                        data-testid={`top-gainer-${stock.symbol}`}
                      >
                        <span className="font-medium text-sm">{stock.symbol}</span>
                        <span className="text-[#00C805] text-sm font-semibold">
                          +{stock.changePercent.toFixed(2)}%
                        </span>
                      </div>
                    ))}
                </div>
              </CardContent>
            </Card>

            {/* Top Losers */}
            <Card className="bg-[#121212] border-white/10">
              <CardContent className="p-4">
                <h3 className="text-sm font-semibold text-[#A0A0A0] mb-3 flex items-center gap-2">
                  <TrendingDown className="w-4 h-4 text-[#FF3B30]" />
                  Top Losers
                </h3>
                <div className="space-y-2">
                  {stocks
                    .sort((a, b) => a.changePercent - b.changePercent)
                    .slice(0, 5)
                    .map((stock) => (
                      <div
                        key={stock.symbol}
                        className="flex justify-between items-center py-2 px-2 rounded-lg hover:bg-white/5 cursor-pointer transition-colors"
                        onClick={() => handleStockClick(stock.symbol)}
                        data-testid={`top-loser-${stock.symbol}`}
                      >
                        <span className="font-medium text-sm">{stock.symbol}</span>
                        <span className="text-[#FF3B30] text-sm font-semibold">
                          {stock.changePercent.toFixed(2)}%
                        </span>
                      </div>
                    ))}
                </div>
              </CardContent>
            </Card>
          </aside>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;

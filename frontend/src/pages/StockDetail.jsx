import { useState, useEffect, useCallback } from "react";
import { useParams, useNavigate } from "react-router-dom";
import axios from "axios";
import { ArrowLeft, RefreshCw, TrendingUp, TrendingDown, Activity, Clock, ArrowUpRight, ArrowDownRight } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { toast } from "sonner";
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Area, AreaChart } from "recharts";
import AdBanner from "@/components/AdBanner";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || "https://stockpulse-uwym.onrender.com";
const API = `${BACKEND_URL}/api`;

const StockDetail = () => {
  const { symbol } = useParams();
  const navigate = useNavigate();
  const [stock, setStock] = useState(null);
  const [history, setHistory] = useState([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  const fetchStockData = useCallback(async (showToast = false) => {
    try {
      if (!loading) setRefreshing(true);
      
      const [stockRes, historyRes] = await Promise.all([
        axios.get(`${API}/stock/${symbol}`),
        axios.get(`${API}/stock/${symbol}/history`),
      ]);

      setStock(stockRes.data);
      setHistory(historyRes.data.history || []);

      if (showToast) {
        toast.success("Stock data updated");
      }
    } catch (error) {
      console.error("Error fetching stock data:", error);
      toast.error("Failed to fetch stock data");
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, [symbol, loading]);

  useEffect(() => {
    fetchStockData();
  }, [symbol, fetchStockData]);

  // Auto-refresh every 30 seconds
  useEffect(() => {
    const interval = setInterval(() => {
      fetchStockData();
    }, 30000);

    return () => clearInterval(interval);
  }, [fetchStockData]);

  const handleRefresh = () => {
    fetchStockData(true);
  };

  const isPositive = stock?.changePercent >= 0;
  const priceColor = isPositive ? "#00C805" : "#FF3B30";

  const CustomTooltip = ({ active, payload, label }) => {
    if (active && payload && payload.length) {
      return (
        <div className="bg-[#1E1E1E] border border-white/10 rounded-lg p-3">
          <p className="text-[#A0A0A0] text-xs mb-1">{label}</p>
          <p className="text-white font-semibold">₹{payload[0].value?.toLocaleString()}</p>
        </div>
      );
    }
    return null;
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-[#0A0A0A] p-6">
        <div className="container mx-auto max-w-6xl">
          <Skeleton className="h-10 w-32 mb-6 bg-[#1E1E1E]" />
          <Skeleton className="h-48 w-full mb-6 bg-[#1E1E1E]" />
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {Array.from({ length: 8 }).map((_, i) => (
              <Skeleton key={i} className="h-24 bg-[#1E1E1E]" />
            ))}
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[#0A0A0A]">
      {/* Header */}
      <header className="sticky top-0 z-50 bg-[#121212] border-b border-white/10">
        <div className="container mx-auto max-w-6xl px-4 md:px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <Button
                variant="ghost"
                size="sm"
                onClick={() => navigate("/")}
                className="hover:bg-white/5"
                data-testid="back-button"
              >
                <ArrowLeft className="w-4 h-4 mr-2" />
                Back
              </Button>
              <div className="h-6 w-px bg-white/10" />
              <div>
                <h1 className="text-xl font-bold font-['Manrope'] flex items-center gap-2" data-testid="stock-symbol">
                  {stock?.symbol}
                  <Badge
                    variant="outline"
                    className={`${
                      isPositive
                        ? "bg-[#00C805]/15 text-[#00C805] border-[#00C805]/30"
                        : "bg-[#FF3B30]/15 text-[#FF3B30] border-[#FF3B30]/30"
                    }`}
                  >
                    {isPositive ? <ArrowUpRight className="w-3 h-3 mr-1" /> : <ArrowDownRight className="w-3 h-3 mr-1" />}
                    {isPositive ? "+" : ""}{stock?.changePercent?.toFixed(2)}%
                  </Badge>
                </h1>
                <p className="text-sm text-[#A0A0A0]" data-testid="stock-name">{stock?.name}</p>
              </div>
            </div>
            <Button
              variant="outline"
              size="sm"
              onClick={handleRefresh}
              disabled={refreshing}
              className="border-white/10 hover:border-white/20 hover:bg-white/5"
              data-testid="detail-refresh-button"
            >
              <RefreshCw className={`w-4 h-4 mr-2 ${refreshing ? "animate-spin" : ""}`} />
              Refresh
            </Button>
          </div>
        </div>
      </header>

      <div className="container mx-auto max-w-6xl px-4 md:px-6 py-6">
        {/* Price Section */}
        <Card className="bg-[#121212] border-white/10 mb-6">
          <CardContent className="p-6">
            <div className="flex flex-col md:flex-row md:items-end md:justify-between gap-4 mb-6">
              <div>
                <p className="text-[#A0A0A0] text-sm mb-1">Current Price</p>
                <p className="text-4xl md:text-5xl font-bold font-['Manrope']" style={{ color: priceColor }} data-testid="current-price">
                  ₹{stock?.price?.toLocaleString()}
                </p>
                <div className="flex items-center gap-2 mt-2">
                  {isPositive ? (
                    <TrendingUp className="w-5 h-5 text-[#00C805]" />
                  ) : (
                    <TrendingDown className="w-5 h-5 text-[#FF3B30]" />
                  )}
                  <span style={{ color: priceColor }} className="font-semibold" data-testid="price-change">
                    {isPositive ? "+" : ""}₹{stock?.change?.toFixed(2)} ({isPositive ? "+" : ""}{stock?.changePercent?.toFixed(2)}%)
                  </span>
                </div>
              </div>
              <div className="text-right text-sm text-[#A0A0A0]">
                <div className="flex items-center gap-1 justify-end">
                  <Clock className="w-4 h-4" />
                  Last updated: {new Date(stock?.lastUpdated).toLocaleTimeString()}
                </div>
              </div>
            </div>

            {/* Price Chart */}
            <div className="h-64 md:h-80" data-testid="price-chart">
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={history}>
                  <defs>
                    <linearGradient id="colorPrice" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor={priceColor} stopOpacity={0.3} />
                      <stop offset="95%" stopColor={priceColor} stopOpacity={0} />
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
                  <XAxis
                    dataKey="date"
                    stroke="#666666"
                    fontSize={12}
                    tickFormatter={(value) => {
                      const date = new Date(value);
                      return `${date.getDate()}/${date.getMonth() + 1}`;
                    }}
                  />
                  <YAxis
                    stroke="#666666"
                    fontSize={12}
                    domain={["auto", "auto"]}
                    tickFormatter={(value) => `₹${value}`}
                  />
                  <Tooltip content={<CustomTooltip />} />
                  <Area
                    type="monotone"
                    dataKey="price"
                    stroke={priceColor}
                    strokeWidth={2}
                    fillOpacity={1}
                    fill="url(#colorPrice)"
                  />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          </CardContent>
        </Card>

        {/* Ad Banner */}
        <div className="mb-6">
          <AdBanner
            type="header"
            imageUrl="https://images.pexels.com/photos/11194747/pexels-photo-11194747.jpeg"
            data-testid="detail-ad-banner"
          />
        </div>

        {/* Stock Details Grid */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
          <Card className="bg-[#121212] border-white/10">
            <CardContent className="p-4">
              <p className="text-[#A0A0A0] text-sm mb-1">Open</p>
              <p className="text-lg font-semibold" data-testid="open-price">₹{stock?.open?.toLocaleString()}</p>
            </CardContent>
          </Card>
          <Card className="bg-[#121212] border-white/10">
            <CardContent className="p-4">
              <p className="text-[#A0A0A0] text-sm mb-1">Previous Close</p>
              <p className="text-lg font-semibold" data-testid="prev-close">₹{stock?.previousClose?.toLocaleString()}</p>
            </CardContent>
          </Card>
          <Card className="bg-[#121212] border-white/10">
            <CardContent className="p-4">
              <p className="text-[#A0A0A0] text-sm mb-1">Day High</p>
              <p className="text-lg font-semibold text-[#00C805]" data-testid="day-high">₹{stock?.high?.toLocaleString()}</p>
            </CardContent>
          </Card>
          <Card className="bg-[#121212] border-white/10">
            <CardContent className="p-4">
              <p className="text-[#A0A0A0] text-sm mb-1">Day Low</p>
              <p className="text-lg font-semibold text-[#FF3B30]" data-testid="day-low">₹{stock?.low?.toLocaleString()}</p>
            </CardContent>
          </Card>
          <Card className="bg-[#121212] border-white/10">
            <CardContent className="p-4">
              <p className="text-[#A0A0A0] text-sm mb-1">Volume</p>
              <p className="text-lg font-semibold" data-testid="volume">
                {stock?.volume >= 1000000
                  ? `${(stock.volume / 1000000).toFixed(2)}M`
                  : stock?.volume >= 1000
                  ? `${(stock.volume / 1000).toFixed(2)}K`
                  : stock?.volume}
              </p>
            </CardContent>
          </Card>
          <Card className="bg-[#121212] border-white/10">
            <CardContent className="p-4">
              <p className="text-[#A0A0A0] text-sm mb-1">52W High</p>
              <p className="text-lg font-semibold" data-testid="52w-high">
                {stock?.fiftyTwoWeekHigh ? `₹${stock.fiftyTwoWeekHigh.toLocaleString()}` : "N/A"}
              </p>
            </CardContent>
          </Card>
          <Card className="bg-[#121212] border-white/10">
            <CardContent className="p-4">
              <p className="text-[#A0A0A0] text-sm mb-1">52W Low</p>
              <p className="text-lg font-semibold" data-testid="52w-low">
                {stock?.fiftyTwoWeekLow ? `₹${stock.fiftyTwoWeekLow.toLocaleString()}` : "N/A"}
              </p>
            </CardContent>
          </Card>
          <Card className="bg-[#121212] border-white/10">
            <CardContent className="p-4">
              <p className="text-[#A0A0A0] text-sm mb-1">Change</p>
              <p className={`text-lg font-semibold ${isPositive ? "text-[#00C805]" : "text-[#FF3B30]"}`} data-testid="change">
                {isPositive ? "+" : ""}₹{stock?.change?.toFixed(2)}
              </p>
            </CardContent>
          </Card>
        </div>

        {/* Sidebar Ad */}
        <div className="max-w-sm mx-auto">
          <AdBanner
            type="sidebar"
            imageUrl="https://images.unsplash.com/photo-1633869699811-cd4f63049b36"
            data-testid="detail-sidebar-ad"
          />
        </div>
      </div>
    </div>
  );
};

export default StockDetail;

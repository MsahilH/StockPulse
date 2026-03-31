import { useState, useEffect } from "react";
import { TrendingUp, TrendingDown } from "lucide-react";
import { Card, CardContent } from "@/components/ui/card";
import { LineChart, Line, ResponsiveContainer } from "recharts";

const StockCard = ({ stock, onClick }) => {
  const [prevPrice, setPrevPrice] = useState(stock.price);
  const [flashClass, setFlashClass] = useState("");

  useEffect(() => {
    if (stock.price !== prevPrice) {
      setFlashClass(stock.price > prevPrice ? "flash-green" : "flash-red");
      setPrevPrice(stock.price);
      
      const timer = setTimeout(() => {
        setFlashClass("");
      }, 500);

      return () => clearTimeout(timer);
    }
  }, [stock.price, prevPrice]);

  const isPositive = stock.changePercent >= 0;
  const priceColor = isPositive ? "#00C805" : "#FF3B30";

  // Generate mock sparkline data based on current price
  const generateSparklineData = () => {
    const data = [];
    let price = stock.price * 0.98;
    
    for (let i = 0; i < 20; i++) {
      price += (Math.random() - 0.5) * (stock.price * 0.01);
      data.push({ value: price });
    }
    
    // End with current price
    data.push({ value: stock.price });
    return data;
  };

  const sparklineData = generateSparklineData();

  return (
    <Card
      className={`bg-[#121212] border-white/10 hover:border-white/20 transition-all duration-200 cursor-pointer hover:-translate-y-1 ${flashClass}`}
      onClick={onClick}
      data-testid={`stock-card-${stock.symbol}`}
    >
      <CardContent className="p-4">
        {/* Header */}
        <div className="flex items-start justify-between mb-3">
          <div>
            <h3 className="font-semibold text-white font-['Manrope']" data-testid={`stock-symbol-${stock.symbol}`}>
              {stock.symbol}
            </h3>
            <p className="text-xs text-[#666666] truncate max-w-[140px]" data-testid={`stock-name-${stock.symbol}`}>
              {stock.name}
            </p>
          </div>
          <div className={`flex items-center gap-1 text-xs font-medium px-2 py-1 rounded-full ${
            isPositive 
              ? "bg-[#00C805]/15 text-[#00C805]" 
              : "bg-[#FF3B30]/15 text-[#FF3B30]"
          }`}>
            {isPositive ? (
              <TrendingUp className="w-3 h-3" />
            ) : (
              <TrendingDown className="w-3 h-3" />
            )}
            <span data-testid={`stock-change-percent-${stock.symbol}`}>
              {isPositive ? "+" : ""}{stock.changePercent?.toFixed(2)}%
            </span>
          </div>
        </div>

        {/* Price */}
        <div className="mb-2">
          <p className="text-2xl font-bold font-['Manrope']" style={{ color: priceColor }} data-testid={`stock-price-${stock.symbol}`}>
            ₹{stock.price?.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
          </p>
          <p className="text-xs text-[#A0A0A0]" data-testid={`stock-change-${stock.symbol}`}>
            {isPositive ? "+" : ""}₹{stock.change?.toFixed(2)}
          </p>
        </div>

        {/* Sparkline */}
        <div className="h-10 mt-2" data-testid={`stock-sparkline-${stock.symbol}`}>
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={sparklineData}>
              <Line
                type="monotone"
                dataKey="value"
                stroke={priceColor}
                strokeWidth={1.5}
                dot={false}
              />
            </LineChart>
          </ResponsiveContainer>
        </div>

        {/* Volume */}
        <div className="flex items-center justify-between mt-2 pt-2 border-t border-white/5">
          <span className="text-xs text-[#666666]">Volume</span>
          <span className="text-xs text-[#A0A0A0] font-medium" data-testid={`stock-volume-${stock.symbol}`}>
            {stock.volume >= 1000000
              ? `${(stock.volume / 1000000).toFixed(2)}M`
              : stock.volume >= 1000
              ? `${(stock.volume / 1000).toFixed(2)}K`
              : stock.volume}
          </span>
        </div>
      </CardContent>
    </Card>
  );
};

export default StockCard;

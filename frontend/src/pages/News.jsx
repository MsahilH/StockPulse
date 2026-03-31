import { useState, useEffect } from "react";
import { Link } from "react-router-dom";
import axios from "axios";
import { ArrowLeft, Clock, ExternalLink, Activity, Newspaper } from "lucide-react";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { toast } from "sonner";
import AdSensePlaceholder from "@/components/AdSensePlaceholder";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || "http://localhost:8000";
const API = `${BACKEND_URL}/api`;

const News = () => {
  const [news, setNews] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchNews = async () => {
      try {
        const response = await axios.get(`${API}/news`);
        if (response.data?.news) {
          setNews(response.data.news);
        }
      } catch (error) {
        console.error("Error fetching news:", error);
        toast.error("Failed to load market news");
      } finally {
        setLoading(false);
      }
    };

    fetchNews();
  }, []);

  return (
    <div className="min-h-screen bg-[#0A0A0A] text-white">
      {/* Header */}
      <header className="sticky top-0 z-50 bg-[#121212]/80 backdrop-blur-md border-b border-white/5">
        <div className="container mx-auto px-4 md:px-6 py-4 flex items-center justify-between">
          <Link 
            to="/" 
            className="flex items-center gap-2 text-[#666666] hover:text-white transition-colors group"
          >
            <ArrowLeft className="w-4 h-4 group-hover:-translate-x-1 transition-transform" />
            <span className="text-sm font-medium">Back to Dashboard</span>
          </Link>
          <div className="flex items-center gap-3">
             <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-[#00C805] to-[#007AFF] flex items-center justify-center">
                <Newspaper className="w-4 h-4 text-white" />
              </div>
              <h1 className="text-lg font-bold font-['Manrope']">Market News</h1>
          </div>
          <div className="w-24"></div> {/* Spacer */}
        </div>
      </header>

      <main className="container mx-auto px-4 md:px-6 py-8">
        <div className="max-w-4xl mx-auto">
          <div className="mb-8">
            <h2 className="text-3xl font-extrabold mb-2 tracking-tight">Financial & Business News</h2>
            <p className="text-[#666666]">Stay updated with the latest market trends and business developments in India.</p>
          </div>

          {/* Top Banner Ad */}
          <AdSensePlaceholder slot="news_top_banner" format="horizontal" className="mb-10" />

          {loading ? (
            <div className="space-y-6">
              {[1, 2, 3, 4].map((i) => (
                <div key={i} className="flex flex-col md:flex-row gap-4 p-4 border border-white/5 rounded-2xl">
                  <Skeleton className="w-full md:w-48 h-32 bg-white/5 rounded-xl" />
                  <div className="flex-1 space-y-3">
                    <Skeleton className="h-6 w-3/4 bg-white/5" />
                    <Skeleton className="h-4 w-full bg-white/5" />
                    <Skeleton className="h-4 w-1/4 bg-white/5" />
                  </div>
                </div>
              ))}
            </div>
          ) : news.length === 0 ? (
            <div className="text-center py-20 text-[#666666]">
              <Activity className="w-12 h-12 mx-auto mb-4 opacity-20" />
              <p>No news articles available at the moment.</p>
            </div>
          ) : (
            <div className="space-y-8">
              {news.map((item, index) => (
                <div key={index}>
                  <article className="group relative">
                    <a 
                      href={item.url} 
                      target="_blank" 
                      rel="noopener noreferrer"
                      className="flex flex-col md:flex-row gap-6 p-4 rounded-2xl hover:bg-white/[0.03] transition-all border border-transparent hover:border-white/5"
                    >
                      <div className="w-full md:w-56 h-40 overflow-hidden rounded-xl bg-white/5 border border-white/5">
                        {item.urlToImage ? (
                          <img 
                            src={item.urlToImage} 
                            alt={item.title} 
                            className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500"
                            onError={(e) => {
                              e.target.style.display = 'none';
                              e.target.parentElement.classList.add('flex', 'items-center', 'justify-center');
                              e.target.parentElement.innerHTML = '<span class="text-white/20 text-xs text-center p-2">Image not available</span>';
                            }}
                          />
                        ) : (
                           <div className="w-full h-full flex items-center justify-center">
                              <Newspaper className="w-8 h-8 text-white/10" />
                           </div>
                        )}
                      </div>
                      
                      <div className="flex-1 flex flex-col justify-between py-1">
                        <div>
                          <div className="flex items-center gap-3 mb-2">
                             <Badge variant="outline" className="bg-[#007AFF]/10 text-[#007AFF] border-[#007AFF]/20 hover:bg-[#007AFF]/20">
                               Business
                             </Badge>
                             <div className="flex items-center gap-1.5 text-xs text-[#666666]">
                                <Clock className="w-3 h-3" />
                                {item.publishedAt ? new Date(item.publishedAt).toLocaleDateString() : 'Recent'}
                             </div>
                          </div>
                          <h3 className="text-xl font-bold mb-2 group-hover:text-[#007AFF] transition-colors line-clamp-2">
                            {item.title}
                          </h3>
                          <p className="text-[#A0A0A0] text-sm line-clamp-2 mb-4 leading-relaxed">
                            {item.description}
                          </p>
                        </div>
                        
                        <div className="flex items-center justify-between text-[#666666] text-xs">
                          <span className="font-semibold uppercase tracking-wider">{item.source?.name || 'News Source'}</span>
                          <span className="flex items-center gap-1 text-[#007AFF] font-medium opacity-0 group-hover:opacity-100 transition-all">
                             Read full article <ExternalLink className="w-3 h-3" />
                          </span>
                        </div>
                      </div>
                    </a>
                  </article>

                  {/* Interspersed Ads after every 3 articles */}
                  {(index + 1) % 4 === 0 && (
                     <AdSensePlaceholder 
                        slot={`news_feed_${index}`} 
                        format="rectangle" 
                        className="my-10" 
                     />
                  )}
                </div>
              ))}
            </div>
          )}

          {/* Bottom Banner Ad */}
          <AdSensePlaceholder slot="news_footer_banner" format="horizontal" className="mt-12" />
        </div>
      </main>

      <footer className="border-t border-white/5 py-12 bg-[#050505]">
          <div className="container mx-auto px-4 text-center">
              <div className="flex items-center justify-center gap-2 mb-6">
                <div className="w-6 h-6 rounded bg-gradient-to-br from-[#00C805] to-[#007AFF] flex items-center justify-center">
                  <Activity className="w-3 h-3 text-white" />
                </div>
                <span className="font-bold text-sm tracking-tight">StockPulse</span>
              </div>
              <p className="text-[#666666] text-xs max-w-md mx-auto">
                StockPulse provides real-time market data and insights. Always coordinate with a financial advisor before making investment decisions.
              </p>
          </div>
      </footer>
    </div>
  );
};

export default News;

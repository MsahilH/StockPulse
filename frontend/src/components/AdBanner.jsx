import React, { useEffect } from 'react';

const AdBanner = ({ type = "header", adClient = "ca-pub-9105340754982447", adSlot, imageUrl, className = "" }) => {
  const getContainerStyles = () => {
    switch (type) {
      case "header":
        return "h-24 md:h-28";
      case "sidebar":
        return "h-64";
      case "content":
        return "h-32";
      default:
        return "h-24";
    }
  };

  useEffect(() => {
    try {
      // Initialize the Google AdSense ad on mount
      if (window) {
        (window.adsbygoogle = window.adsbygoogle || []).push({});
      }
    } catch (e) {
      console.error("AdSense error:", e);
    }
  }, []);

  return (
    <div
      className={`relative bg-[#121212] border border-white/10 rounded-lg overflow-hidden flex items-center justify-center ${getContainerStyles()} ${className}`}
      data-testid={`ad-banner-${type}`}
    >
      {/* Advertisement Label */}
      <div className="absolute top-2 left-2 z-10 pointer-events-none">
        <span className="text-[10px] text-[#666666] uppercase tracking-wider bg-[#121212]/80 px-2 py-1 rounded">
          Advertisement
        </span>
      </div>

      {/* Google AdSense Unit */}
      <ins 
        className="adsbygoogle w-full h-full block"
        style={{ display: "block" }}
        data-ad-client={adClient}
        data-ad-slot={adSlot}
        data-ad-format="auto"
        data-full-width-responsive="true"
      ></ins>
    </div>
  );
};

export default AdBanner;

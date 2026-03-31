const AdBanner = ({ type = "header", imageUrl, className = "" }) => {
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

  return (
    <div
      className={`relative bg-[#121212] border border-white/10 rounded-lg overflow-hidden ${getContainerStyles()} ${className}`}
      data-testid={`ad-banner-${type}`}
    >
      {/* Advertisement Label */}
      <div className="absolute top-2 left-2 z-10">
        <span className="text-[10px] text-[#666666] uppercase tracking-wider bg-[#121212]/80 px-2 py-1 rounded">
          Advertisement
        </span>
      </div>

      {/* Ad Image */}
      <img
        src={imageUrl}
        alt="Advertisement"
        className="w-full h-full object-cover opacity-80 hover:opacity-100 transition-opacity duration-300"
        loading="lazy"
      />

      {/* Overlay gradient for better text readability if needed */}
      <div className="absolute inset-0 bg-gradient-to-t from-black/30 to-transparent pointer-events-none" />

      {/* Dummy AdSense placeholder script comment */}
      {/* 
        <ins className="adsbygoogle"
          style={{ display: "block" }}
          data-ad-client="ca-pub-XXXXXXXXXXXXXXXX"
          data-ad-slot="XXXXXXXXXX"
          data-ad-format="auto"
          data-full-width-responsive="true">
        </ins>
      */}
    </div>
  );
};

export default AdBanner;

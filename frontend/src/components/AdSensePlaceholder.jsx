import React from 'react';

const AdSensePlaceholder = ({ slot, format = 'auto', className = "" }) => (
  <div className={`w-full bg-[#121212] border border-dashed border-white/10 rounded-xl p-8 flex flex-col items-center justify-center text-[#666666] my-6 transition-all hover:border-white/20 ${className}`}>
    <div className="w-12 h-12 rounded-full bg-white/5 flex items-center justify-center mb-4">
      <span className="text-xl font-bold font-serif opacity-40">Ad</span>
    </div>
    <p className="text-[10px] font-mono uppercase tracking-[0.2em] mb-1 font-semibold">Google AdSense Placeholder</p>
    <div className="flex gap-2 items-center opacity-40">
      <span className="text-[9px] px-1.5 py-0.5 rounded border border-white/10">SLOT: {slot}</span>
      <span className="text-[9px] px-1.5 py-0.5 rounded border border-white/10">FORMAT: {format}</span>
    </div>
    <div className="mt-6 w-1/3 h-px bg-gradient-to-r from-transparent via-white/10 to-transparent"></div>
  </div>
);

export default AdSensePlaceholder;

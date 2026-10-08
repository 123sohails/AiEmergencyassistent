import { Bell, Wifi, ChevronDown } from 'lucide-react';

export default function Header() {
  return (
    <div className="h-20 w-full bg-[#0b161e] border-b border-[#233743] flex items-center justify-between px-8 shrink-0">
      <div className="flex flex-col">
        <div className="flex items-center gap-2 mb-1">
          <div className="w-2 h-2 rounded-full bg-ns-teal animate-pulse"></div>
          <span className="text-[10px] font-bold text-ns-teal tracking-widest uppercase">Live Operations</span>
        </div>
        <h1 className="text-xl font-bold text-white tracking-wide">Urban response dashboard</h1>
      </div>
      
      <div className="flex items-center gap-6">
        <div className="flex items-center gap-2 px-4 py-1.5 rounded-full border border-[#233743] bg-[#13232c] text-xs text-muted">
          <Wifi size={14} className="text-ns-teal" />
          <span>Connected to field network</span>
        </div>
        
        <div className="relative cursor-pointer">
          <Bell size={20} className="text-muted hover:text-white transition-colors" />
          <div className="absolute -top-1 -right-1 w-2.5 h-2.5 bg-ns-red rounded-full border-2 border-[#0b161e]"></div>
        </div>
        
        <div className="w-px h-8 bg-[#233743] mx-2"></div>
        
        <div className="flex items-center gap-3 cursor-pointer group">
          <div className="w-9 h-9 rounded-full bg-[#cfa862] text-[#0b161e] font-bold flex items-center justify-center text-sm">
            AR
          </div>
          <div className="flex flex-col hidden sm:flex">
            <span className="text-sm font-bold text-white leading-tight">A. Rahman</span>
            <span className="text-[10px] text-muted">Desk operator</span>
          </div>
          <ChevronDown size={14} className="text-muted group-hover:text-white transition-colors" />
        </div>
      </div>
    </div>
  );
}

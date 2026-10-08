import { Send } from 'lucide-react';

export default function AITriage({ selectedIncident }: { selectedIncident: any }) {
  if (!selectedIncident) return <div className="h-48"></div>;

  return (
    <div className="flex gap-4">
      {/* Donut Chart Panel */}
      <div className="bg-[#13232c] border border-[#233743] rounded-2xl p-6 flex-1 flex flex-col">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-2">
            <span className="text-ns-yellow">✨</span>
            <span className="font-bold text-white">AI triage activity</span>
          </div>
          <span className="text-muted cursor-pointer">•••</span>
        </div>
        <p className="text-xs text-muted mb-6">How incoming reports are being understood right now.</p>
        
        <div className="flex items-center gap-8">
          <div className="relative w-32 h-32 shrink-0">
            {/* Fake Donut SVG for UI */}
            <svg viewBox="0 0 100 100" className="w-full h-full transform -rotate-90">
              <circle cx="50" cy="50" r="40" fill="none" stroke="#233743" strokeWidth="12" />
              <circle cx="50" cy="50" r="40" fill="none" stroke="#e75e50" strokeWidth="12" strokeDasharray="251.2" strokeDashoffset="80.3" strokeLinecap="round" />
              <circle cx="50" cy="50" r="40" fill="none" stroke="#cfa862" strokeWidth="12" strokeDasharray="251.2" strokeDashoffset="210" strokeLinecap="round" className="origin-center rotate-[245deg]" />
            </svg>
            <div className="absolute inset-0 flex flex-col items-center justify-center">
              <span className="text-2xl font-bold text-white">86%</span>
              <span className="text-[10px] text-muted">confidence</span>
            </div>
          </div>
          
          <div className="flex flex-col gap-3 flex-1">
            <div className="flex items-center justify-between text-sm">
              <div className="flex items-center gap-2">
                <div className="w-2 h-2 rounded-full bg-ns-red"></div>
                <span className="text-white font-medium">Emergency signals</span>
              </div>
              <span className="text-muted">68%</span>
            </div>
            <div className="h-1 bg-[#233743] rounded-full overflow-hidden"><div className="h-full bg-ns-red w-[68%]"></div></div>
            
            <div className="flex items-center justify-between text-sm mt-1">
              <div className="flex items-center gap-2">
                <div className="w-2 h-2 rounded-full bg-ns-yellow"></div>
                <span className="text-white font-medium">Needs confirmation</span>
              </div>
              <span className="text-muted">21%</span>
            </div>
            <div className="h-1 bg-[#233743] rounded-full overflow-hidden"><div className="h-full bg-ns-yellow w-[21%]"></div></div>
            
            <div className="flex items-center justify-between text-sm mt-1">
              <div className="flex items-center gap-2">
                <div className="w-2 h-2 rounded-full bg-ns-teal"></div>
                <span className="text-white font-medium">Filtered noise</span>
              </div>
              <span className="text-muted">11%</span>
            </div>
            <div className="h-1 bg-[#233743] rounded-full overflow-hidden"><div className="h-full bg-ns-teal w-[11%]"></div></div>
          </div>
        </div>
      </div>

      {/* Selected Incident Detail */}
      <div className="bg-[#13232c] border border-[#233743] rounded-2xl p-6 flex-1 flex flex-col justify-between">
        <div>
          <div className="flex justify-between items-start mb-2">
            <div className="text-[10px] font-bold text-muted tracking-widest uppercase">SELECTED INCIDENT</div>
            <span className="bg-ns-red/20 text-ns-red border border-ns-red/30 px-2 py-0.5 rounded text-xs font-bold">Needs review</span>
          </div>
          <h3 className="text-lg font-bold text-white mb-1">{selectedIncident.id}</h3>
          <h4 className="text-sm font-semibold text-white mb-2">{selectedIncident.summary?.split('.')[0]}</h4>
          <p className="text-xs text-muted leading-relaxed line-clamp-3 mb-4">
            {selectedIncident.summary}
          </p>
          
          <div className="flex gap-4 mb-4">
            <div className="bg-[#1a2f3b] rounded-lg p-3 flex-1">
              <div className="text-[10px] text-muted mb-1">Source</div>
              <div className="text-xs text-white">Voice note</div>
            </div>
            <div className="bg-[#1a2f3b] rounded-lg p-3 flex-1">
              <div className="text-[10px] text-muted mb-1">Affected</div>
              <div className="text-xs text-white">{selectedIncident.people_latest || 0} people</div>
            </div>
          </div>
        </div>
        
        <button className="w-full bg-[#1e4a4b] hover:bg-ns-teal transition-colors text-white font-semibold py-3 rounded-xl flex items-center justify-center gap-2 shadow-lg shadow-ns-teal/10">
          <Send size={16} />
          <span>Create dispatch note</span>
        </button>
      </div>
    </div>
  );
}

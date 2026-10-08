import { Flame, MapPin, Clock, Users, Mic, Image, Navigation } from 'lucide-react';
import axios from 'axios';
import { useRef } from 'react';

export default function IncidentFeed({ incidents, refresh }: { incidents: any[], refresh: () => void }) {
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    if (!e.target.files || e.target.files.length === 0) return;
    const formData = new FormData();
    formData.append('file', e.target.files[0]);
    try {
      await axios.post('http://localhost:8000/api/upload', formData);
      refresh();
    } catch (error) {
      console.error("Upload failed", error);
    } finally {
      if (fileInputRef.current) fileInputRef.current.value = '';
    }
  };

  return (
    <div className="flex flex-col gap-4">
      <div className="flex items-end justify-between mb-2">
        <div className="flex flex-col">
          <span className="text-[10px] font-bold text-muted tracking-widest uppercase mb-1">Situation Overview</span>
          <h2 className="text-2xl font-bold text-white tracking-wide">Live incident picture</h2>
          <span className="text-sm text-muted mt-1">AI-organized reports from every incoming channel.</span>
        </div>
        <div className="flex items-center gap-3">
          <button className="flex items-center gap-2 px-4 py-2 rounded-xl bg-transparent border border-[#233743] text-white hover:bg-[#13232c] transition-colors">
            <span className="font-semibold text-sm">Filters</span>
          </button>
          
          <input type="file" ref={fileInputRef} onChange={handleUpload} className="hidden" accept=".csv,.json,.txt,.mp3,.wav" />
          <button onClick={() => fileInputRef.current?.click()} className="flex items-center gap-2 px-4 py-2 rounded-xl bg-ns-red hover:bg-ns-red/80 text-white shadow-lg shadow-ns-red/20 transition-colors">
            <span className="font-semibold text-sm">Upload Dataset</span>
          </button>
        </div>
      </div>

      <div className="bg-[#13232c] border border-[#233743] rounded-2xl overflow-hidden flex flex-col h-[500px]">
        {/* Feed Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-[#233743]">
          <div className="flex items-center gap-3">
            <ActivityIcon />
            <span className="font-bold text-white">Incident feed</span>
            <span className="text-[10px] bg-ns-teal/20 text-ns-teal font-bold px-2 py-0.5 rounded border border-ns-teal/30">Live</span>
          </div>
          <div className="flex items-center gap-2 bg-[#0b161e] p-1 rounded-xl">
            <button className="px-4 py-1 rounded-lg bg-[#233743] text-white text-xs font-bold">All</button>
            <button className="px-4 py-1 rounded-lg text-muted hover:text-white text-xs font-bold">Critical</button>
            <button className="px-4 py-1 rounded-lg text-muted hover:text-white text-xs font-bold">High</button>
            <button className="px-4 py-1 rounded-lg text-muted hover:text-white text-xs font-bold">Medium</button>
          </div>
        </div>

        {/* Feed List */}
        <div className="flex-1 overflow-y-auto">
          {incidents.length === 0 ? (
            <div className="p-8 text-center text-muted">No active incidents.</div>
          ) : (
            incidents.map((inc, i) => (
              <div key={inc.id} className="flex gap-4 p-5 border-b border-[#233743] hover:bg-[#1a2f3b] transition-colors cursor-pointer relative group">
                {inc.urgency === 'critical' && <div className="absolute left-0 top-0 bottom-0 w-1 bg-ns-red"></div>}
                {inc.urgency === 'high' && <div className="absolute left-0 top-0 bottom-0 w-1 bg-ns-yellow"></div>}
                
                <div className="w-10 h-10 rounded-full bg-[#0b161e] border border-[#233743] flex items-center justify-center shrink-0">
                  {inc.urgency === 'critical' ? <Flame size={18} className="text-ns-red" /> : <Navigation size={18} className="text-ns-yellow" />}
                </div>
                
                <div className="flex flex-col flex-1">
                  <div className="flex items-center justify-between mb-1">
                    <div className="flex items-center gap-3">
                      <span className="font-bold text-white text-base">{inc.summary?.split('.')[0] || inc.id}</span>
                      <span className={`text-[10px] font-bold px-2 py-0.5 rounded ${inc.urgency === 'critical' ? 'bg-ns-red/20 text-ns-red border border-ns-red/30' : 'bg-ns-yellow/20 text-ns-yellow border border-ns-yellow/30'}`}>
                        {inc.urgency?.toUpperCase()}
                      </span>
                    </div>
                  </div>
                  
                  <div className="flex items-center gap-1.5 text-xs text-muted mb-2">
                    <MapPin size={12} />
                    <span>{inc.location_text || 'Unknown Location'}</span>
                  </div>
                  
                  <p className="text-sm text-[#8ba3b2] mb-3 leading-relaxed">
                    {inc.summary}
                  </p>
                  
                  <div className="flex items-center gap-4 text-xs font-medium text-muted">
                    {inc.status === 'pending' ? (
                      <span className="bg-ns-red/20 text-ns-red px-2 py-1 rounded">Needs review</span>
                    ) : (
                      <span className="bg-ns-teal/20 text-ns-teal px-2 py-1 rounded">In progress</span>
                    )}
                    <div className="flex items-center gap-1.5"><Clock size={12} /> 14:22:10</div>
                    <div className="flex items-center gap-1.5"><Users size={12} /> {inc.people_latest || 0} affected</div>
                    <div className="flex items-center gap-1.5"><Mic size={12} /> Text note</div>
                  </div>
                </div>
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  );
}

function ActivityIcon() {
  return (
    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className="text-ns-teal">
      <path d="M22 12h-4l-3 9L9 3l-3 9H2" />
    </svg>
  );
}

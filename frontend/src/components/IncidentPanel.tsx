"use client";
import { useState, useEffect } from 'react';
import axios from 'axios';

export default function IncidentPanel({ incidents }: { incidents: any[] }) {
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [details, setDetails] = useState<any>(null);
  const [tab, setTab] = useState<'details' | 'explainability' | 'evidence'>('details');
  const [searchTerm, setSearchTerm] = useState('');

  useEffect(() => {
    if (incidents.length > 0 && !selectedId) {
      setSelectedId(incidents[0].id);
    }
  }, [incidents]);

  useEffect(() => {
    if (selectedId) {
      axios.get(`http://localhost:8000/api/incidents/${selectedId}/details`)
        .then(res => setDetails(res.data))
        .catch(console.error);
    }
  }, [selectedId]);

  const filteredIncidents = incidents.filter(i => 
    i.id.toLowerCase().includes(searchTerm.toLowerCase()) || 
    (i.location_text || '').toLowerCase().includes(searchTerm.toLowerCase()) ||
    (i.summary || '').toLowerCase().includes(searchTerm.toLowerCase())
  );

  const getUrgencyIcon = (urgency: string) => {
    if (urgency === 'critical') return '🔥';
    if (urgency === 'high') return '⚠️';
    if (urgency === 'medium') return '⚡';
    return 'ℹ️';
  };

  const inc = incidents.find(i => i.id === selectedId);

  return (
    <div className="bg-slate-900/40 border border-slate-800 rounded-xl p-4 flex flex-col h-full overflow-hidden">
      <h3 className="text-white font-bold mb-4">Incident Console</h3>
      
      {incidents.length === 0 ? (
        <div className="text-slate-500 text-sm">No active incidents.</div>
      ) : (
        <>
          <input 
            type="text" 
            placeholder="Search incidents..." 
            className="w-full bg-slate-800 border border-slate-700 text-white rounded p-2 text-sm mb-2 outline-none"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
          />
          <select 
            className="w-full bg-slate-800 border border-slate-700 text-white rounded p-2 text-sm mb-4 outline-none"
            value={selectedId || ''}
            onChange={(e) => setSelectedId(e.target.value)}
          >
            {filteredIncidents.map(i => (
              <option key={i.id} value={i.id}>
                {getUrgencyIcon(i.urgency)} {i.id} - {i.location_text}
              </option>
            ))}
          </select>

          {inc && (
            <>
              <div className="flex border-b border-slate-800 mb-4">
                <button className={`flex-1 pb-2 text-xs font-bold ${tab === 'details' ? 'text-cyan-400 border-b-2 border-cyan-400' : 'text-slate-500'}`} onClick={() => setTab('details')}>Details</button>
                <button className={`flex-1 pb-2 text-xs font-bold ${tab === 'explainability' ? 'text-cyan-400 border-b-2 border-cyan-400' : 'text-slate-500'}`} onClick={() => setTab('explainability')}>AI Logic</button>
                <button className={`flex-1 pb-2 text-xs font-bold ${tab === 'evidence' ? 'text-cyan-400 border-b-2 border-cyan-400' : 'text-slate-500'}`} onClick={() => setTab('evidence')}>Evidence</button>
              </div>

              <div className="flex-grow overflow-y-auto pr-2 text-sm text-slate-300 space-y-3 max-h-96">
                {tab === 'details' && (
                  <>
                    <div><strong className="text-slate-500">Status:</strong> <span className="text-cyan-400">{inc.status.replace(/_/g, ' ').toUpperCase()}</span></div>
                    <div><strong className="text-slate-500">Priority:</strong> <span className="text-red-400">{getUrgencyIcon(inc.urgency)} {inc.urgency.toUpperCase()}</span></div>
                    <div><strong className="text-slate-500">Last Updated:</strong> {inc.last_updated.split('.')[0]}</div>
                    <div><strong className="text-slate-500">Location:</strong> {inc.location_text}</div>
                    <div><strong className="text-slate-500">Coords:</strong> {inc.lat}, {inc.lng}</div>
                    <div><strong className="text-slate-500">Needs:</strong> {inc.resource}</div>
                    <div><strong className="text-slate-500">People:</strong> {inc.people_latest}</div>
                    {inc.vulnerable && inc.vulnerable.length > 0 && (
                      <div><strong className="text-slate-500">Vulnerable:</strong> {inc.vulnerable.join(', ')}</div>
                    )}
                    <div className="mt-4"><strong className="text-slate-500">Summary:</strong><br/>{inc.summary}</div>
                  </>
                )}

                {tab === 'explainability' && details && (
                  <>
                    <div className="font-bold text-white mb-2">AI Clustering Events ({details.events.length})</div>
                    {details.events.map((ev: any, idx: number) => (
                      <div key={idx} className="border-l-2 border-slate-700 pl-3 py-1">
                        <div className="text-xs text-slate-500">{ev.time.split(' ')[1]}</div>
                        <div className="text-cyan-400 text-xs font-bold">{ev.event_type}</div>
                        <div className="text-xs mt-1">{ev.detail}</div>
                      </div>
                    ))}
                  </>
                )}

                {tab === 'evidence' && details && (
                  <>
                    <div className="font-bold text-white mb-2">Raw Intel Sources ({details.reports.length})</div>
                    {details.reports.map((rep: any, idx: number) => (
                      <div key={idx} className="bg-slate-800/50 p-2 rounded border border-slate-700/50 mb-2">
                        <div className="text-cyan-400 text-xs font-bold mb-1">[{rep.source.toUpperCase()}] {rep.received_at.split(' ')[1]}</div>
                        <div className="text-xs">{rep.raw_text}</div>
                      </div>
                    ))}
                  </>
                )}
              </div>
            </>
          )}
        </>
      )}
    </div>
  );
}

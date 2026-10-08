"use client";
import { useEffect, useState } from 'react';

export default function TopBar() {
  const [timeStr, setTimeStr] = useState("Loading...");

  useEffect(() => {
    const updateTime = () => setTimeStr(new Date().toLocaleString('en-IN', { dateStyle: 'medium', timeStyle: 'short' }));
    updateTime();
    const timer = setInterval(updateTime, 60000);
    return () => clearInterval(timer);
  }, []);

  const steps = [
    { num: 1, title: 'INGEST', sub: 'Real-time Feeds', active: true },
    { num: 2, title: 'FILTER', sub: 'Classify & Prioritize', active: true },
    { num: 3, title: 'EXTRACT', sub: 'Entities & Locations', active: true },
    { num: 4, title: 'CLUSTER', sub: 'Group Similar Events', active: true },
    { num: 5, title: 'DISPATCH', sub: 'Teams & Resources', active: false },
  ];

  return (
    <div className="w-full flex items-center justify-between mb-6">
      <div className="flex flex-col">
        <h1 className="text-2xl font-bold text-white tracking-wide flex items-center gap-2">
          NDRF <span className="text-slate-400 font-light text-xl">| Urban Incident Response & Risk Monitoring</span>
        </h1>
      </div>
      
      <div className="flex-grow max-w-4xl mx-8">
        <div className="flex items-center justify-between bg-slate-900/50 backdrop-blur-md border border-slate-800 rounded-xl px-8 py-3">
          {steps.map((step, i) => (
            <div key={i} className="flex items-center gap-4">
              <div className={`flex items-center gap-3 ${step.active ? 'opacity-100' : 'opacity-40'}`}>
                <div className={`w-8 h-8 rounded-full flex items-center justify-center font-bold border ${step.active ? 'border-cyan-400 text-cyan-400 shadow-[0_0_10px_rgba(0,240,255,0.3)]' : 'border-slate-600 text-slate-500'}`}>
                  {step.num}
                </div>
                <div className="flex flex-col">
                  <span className={`text-xs font-bold tracking-wider ${step.active ? 'text-white' : 'text-slate-500'}`}>{step.title}</span>
                  <span className="text-[10px] text-slate-500">{step.sub}</span>
                </div>
              </div>
              {i < steps.length - 1 && (
                <div className="text-slate-700 mx-2">→</div>
              )}
            </div>
          ))}
        </div>
      </div>

      <div className="flex flex-col text-right text-slate-400 text-sm">
        <span>{timeStr}</span>
        <div className="flex items-center gap-2 justify-end mt-1">
          <span>Mumbai, MH</span>
          <span className="bg-emerald-500/20 text-emerald-400 border border-emerald-500/50 rounded px-2 py-0.5 text-xs flex items-center gap-1">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse"></span>
            Live Feed
          </span>
        </div>
      </div>
    </div>
  );
}

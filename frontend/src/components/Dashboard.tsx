"use client";

import { useEffect, useState } from 'react';
import dynamic from 'next/dynamic';
import axios from 'axios';
import TopBar from './TopBar';
import PipelineFeed from './PipelineFeed';
import IncidentPanel from './IncidentPanel';
import Sidebar from './Sidebar';
import Analytics from './Analytics';
import Reports from './Reports';

const Map = dynamic(() => import('./Map'), { ssr: false });

export default function Dashboard() {
  const [incidents, setIncidents] = useState<any[]>([]);
  const [pipeline, setPipeline] = useState<any>(null);
  const [activeView, setActiveView] = useState<string>('overview');

  const fetchData = async () => {
    try {
      const incRes = await axios.get('http://localhost:8000/api/incidents', { timeout: 5000 });
      setIncidents(incRes.data.incidents || []);
      
      const pipeRes = await axios.get('http://localhost:8000/api/pipeline', { timeout: 5000 });
      setPipeline(pipeRes.data);
    } catch (e) {
      console.error("API Error", e);
      // On error, try using test data directly
      const testIncidents = [
        { id: "INC-TEST-001", status: "active", urgency: "critical", people_latest: 15, resource: "rescue boat", location_text: "T Nagar, Chennai", lat: 13.033, lng: 80.233, summary: "Flooding in T Nagar with 15 people trapped" },
        { id: "INC-TEST-002", status: "active", urgency: "high", people_latest: 5, resource: "fire truck", location_text: "Marina Beach, Chennai", lat: 13.055, lng: 80.283, summary: "Fire reported at Marina Beach" },
        { id: "INC-TEST-003", status: "rescue_in_progress", urgency: "critical", people_latest: 8, resource: "medical team", location_text: "Kodambakkam, Chennai", lat: 13.044, lng: 80.233, summary: "Building collapse in Kodambakkam" },
        { id: "INC-TEST-004", status: "resolved", urgency: "medium", people_latest: 2, resource: "ambulance", location_text: "Adyar Junction, Chennai", lat: 13.006, lng: 80.258, summary: "Tree fell on car at Adyar junction" },
        { id: "INC-TEST-005", status: "active", urgency: "low", people_latest: 3, resource: "police", location_text: "Besant Nagar, Chennai", lat: 12.996, lng: 80.267, summary: "Minor traffic accident reported" },
      ];
      setIncidents(testIncidents);
      setPipeline({ pending_count: 0, active_report_id: null });
    }
  };

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 5000);
    return () => clearInterval(interval);
  }, []);

  const activeIncidents = incidents.filter(i => i.status !== 'resolved');
  const highCritical = activeIncidents.filter(i => i.urgency === 'high' || i.urgency === 'critical');
  const totalPeople = activeIncidents.reduce((sum, i) => sum + (i.people_latest || 0), 0);

  const renderMainContent = () => {
    switch (activeView) {
      case 'overview':
        return (
          <>
            {/* Top Metrics Row */}
            <div className="flex gap-4 h-20 shrink-0">
              <div className="bg-slate-900/40 border border-slate-800 rounded-xl p-3 flex-1 flex flex-col justify-center">
                <div className="text-xs text-slate-400 font-bold mb-1">Active Incidents</div>
                <div className="text-2xl font-bold text-cyan-400">{activeIncidents.length}</div>
              </div>
              <div className="bg-slate-900/40 border border-slate-800 rounded-xl p-3 flex-1 flex flex-col justify-center">
                <div className="text-xs text-slate-400 font-bold mb-1">High/Critical</div>
                <div className="text-2xl font-bold text-red-400">{highCritical.length}</div>
              </div>
              <div className="bg-slate-900/40 border border-slate-800 rounded-xl p-3 flex-1 flex flex-col justify-center">
                <div className="text-xs text-slate-400 font-bold mb-1">Affected People</div>
                <div className="text-2xl font-bold text-emerald-400">~ {totalPeople}</div>
              </div>
            </div>

            {/* Map Area */}
            <div className="flex-1 bg-slate-900/40 border border-slate-800 rounded-xl overflow-hidden relative shadow-2xl min-h-0">
              <Map incidents={incidents} />
            </div>
          </>
        );
      case 'incidents':
        return (
          <div className="flex-1 bg-slate-900/40 border border-slate-800 rounded-xl overflow-auto p-4">
            <h2 className="text-2xl font-bold text-white mb-4">Incident Feed</h2>
            <div className="space-y-3">
              {activeIncidents.map((inc) => (
                <div key={inc.id} className="bg-slate-800/50 border border-slate-700 rounded-lg p-4">
                  <div className="flex justify-between items-start mb-2">
                    <div className="text-white font-bold">{inc.id}</div>
                    <span className={`px-2 py-1 rounded text-xs font-bold ${
                      inc.urgency === 'critical' ? 'bg-red-500/20 text-red-400' :
                      inc.urgency === 'high' ? 'bg-orange-500/20 text-orange-400' :
                      inc.urgency === 'medium' ? 'bg-yellow-500/20 text-yellow-400' :
                      'bg-blue-500/20 text-blue-400'
                    }`}>
                      {inc.urgency.toUpperCase()}
                    </span>
                  </div>
                  <div className="text-slate-300 text-sm mb-2">{inc.location_text || 'Unknown Location'}</div>
                  <div className="text-slate-400 text-xs">{inc.summary}</div>
                </div>
              ))}
              {activeIncidents.length === 0 && (
                <div className="text-slate-500 text-center py-8">No active incidents</div>
              )}
            </div>
          </div>
        );
      case 'map':
        return (
          <div className="flex-1 bg-slate-900/40 border border-slate-800 rounded-xl overflow-hidden relative shadow-2xl min-h-0">
            <Map incidents={incidents} />
          </div>
        );
      case 'analytics':
        return <Analytics />;
      case 'reports':
        return <Reports />;
      default:
        return null;
    }
  };

  return (
    <div className="h-screen p-3 flex flex-col text-white bg-[#050b14]">
      <TopBar />

      <div className="flex flex-1 gap-4 min-h-0 overflow-hidden">
        
        {/* Left Sidebar Navigation */}
        <Sidebar
          activeView={activeView}
          onViewChange={setActiveView}
          incidentCount={activeIncidents.length}
        />
        
        {/* Pipeline Feed (only show on overview) */}
        {activeView === 'overview' && (
          <div className="w-56 flex flex-col gap-4 shrink-0">
            <PipelineFeed pipeline={pipeline} refresh={fetchData} />
          </div>
        )}
        
        {/* Main Content */}
        <div className="flex-1 flex flex-col gap-4 min-w-0 overflow-auto">
          {renderMainContent()}
        </div>
        
        {/* Right Sidebar (only show on overview and map) */}
        {(activeView === 'overview' || activeView === 'map') && (
          <div className="w-72 shrink-0 overflow-hidden">
            <IncidentPanel incidents={activeIncidents} />
          </div>
        )}
        
      </div>
    </div>
  );
}

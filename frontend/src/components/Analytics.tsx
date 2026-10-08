"use client";

import { useState, useEffect } from 'react';
import axios from 'axios';

export default function Analytics() {
  const [incidents, setIncidents] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  const fetchIncidents = async () => {
    try {
      const res = await axios.get('http://localhost:8000/api/incidents');
      setIncidents(res.data.incidents || []);
      setLoading(false);
    } catch (e) {
      console.error("Error fetching incidents", e);
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchIncidents();
    const interval = setInterval(fetchIncidents, 2000);
    return () => clearInterval(interval);
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="text-slate-400">Loading analytics...</div>
      </div>
    );
  }

  const activeIncidents = incidents.filter(i => i.status !== 'resolved');
  const resolvedIncidents = incidents.filter(i => i.status === 'resolved');

  // Calculate statistics
  const urgencyStats = {
    critical: activeIncidents.filter(i => i.urgency === 'critical').length,
    high: activeIncidents.filter(i => i.urgency === 'high').length,
    medium: activeIncidents.filter(i => i.urgency === 'medium').length,
    low: activeIncidents.filter(i => i.urgency === 'low').length,
  };

  const resourceStats = activeIncidents.reduce((acc, inc) => {
    const resource = inc.resource || 'unknown';
    acc[resource] = (acc[resource] || 0) + 1;
    return acc;
  }, {} as Record<string, number>);

  const totalPeople = activeIncidents.reduce((sum, i) => sum + (i.people_latest || 0), 0);
  const totalVulnerable = activeIncidents.reduce((sum, i) => {
    const vuln = i.vulnerable || [];
    return sum + vuln.length;
  }, 0);

  const getBarWidth = (value: number, max: number) => {
    return max > 0 ? `${(value / max) * 100}%` : '0%';
  };

  const maxUrgency = Math.max(...Object.values(urgencyStats));
  const maxResource = Math.max(...Object.values(resourceStats));

  return (
    <div className="p-6 space-y-6 overflow-auto">
      <h2 className="text-2xl font-bold text-white mb-6">Analytics Dashboard</h2>

      {/* Top Metrics */}
      <div className="grid grid-cols-4 gap-4">
        <div className="bg-slate-900/40 border border-slate-800 rounded-xl p-4">
          <div className="text-slate-400 text-sm font-bold mb-1">Total Incidents</div>
          <div className="text-3xl font-bold text-cyan-400">{incidents.length}</div>
        </div>
        <div className="bg-slate-900/40 border border-slate-800 rounded-xl p-4">
          <div className="text-slate-400 text-sm font-bold mb-1">Active</div>
          <div className="text-3xl font-bold text-red-400">{activeIncidents.length}</div>
        </div>
        <div className="bg-slate-900/40 border border-slate-800 rounded-xl p-4">
          <div className="text-slate-400 text-sm font-bold mb-1">Resolved</div>
          <div className="text-3xl font-bold text-green-400">{resolvedIncidents.length}</div>
        </div>
        <div className="bg-slate-900/40 border border-slate-800 rounded-xl p-4">
          <div className="text-slate-400 text-sm font-bold mb-1">Resolution Rate</div>
          <div className="text-3xl font-bold text-emerald-400">
            {incidents.length > 0 ? `${Math.round((resolvedIncidents.length / incidents.length) * 100)}%` : '0%'}
          </div>
        </div>
      </div>

      {/* Urgency Distribution */}
      <div className="bg-slate-900/40 border border-slate-800 rounded-xl p-6">
        <h3 className="text-lg font-bold text-white mb-4">Urgency Distribution (Active Incidents)</h3>
        <div className="space-y-3">
          {Object.entries(urgencyStats).map(([urgency, count]) => (
            <div key={urgency} className="flex items-center gap-3">
              <div className="w-24 text-sm font-bold text-slate-400 uppercase">{urgency}</div>
              <div className="flex-1 bg-slate-800 rounded-full h-6 overflow-hidden">
                <div
                  className={`h-full ${
                    urgency === 'critical' ? 'bg-red-500' :
                    urgency === 'high' ? 'bg-orange-500' :
                    urgency === 'medium' ? 'bg-yellow-500' : 'bg-blue-500'
                  }`}
                  style={{ width: getBarWidth(count, maxUrgency) }}
                />
              </div>
              <div className="w-12 text-sm font-bold text-white text-right">{count}</div>
            </div>
          ))}
        </div>
      </div>

      {/* Resource Types */}
      <div className="bg-slate-900/40 border border-slate-800 rounded-xl p-6">
        <h3 className="text-lg font-bold text-white mb-4">Resource Types Needed</h3>
        <div className="space-y-3">
          {Object.entries(resourceStats).sort((a, b) => b[1] - a[1]).map(([resource, count]) => (
            <div key={resource} className="flex items-center gap-3">
              <div className="w-32 text-sm font-bold text-slate-400 capitalize">{resource}</div>
              <div className="flex-1 bg-slate-800 rounded-full h-6 overflow-hidden">
                <div
                  className="h-full bg-cyan-500"
                  style={{ width: getBarWidth(count, maxResource) }}
                />
              </div>
              <div className="w-12 text-sm font-bold text-white text-right">{count}</div>
            </div>
          ))}
        </div>
      </div>

      {/* People Statistics */}
      <div className="grid grid-cols-2 gap-4">
        <div className="bg-slate-900/40 border border-slate-800 rounded-xl p-6">
          <h3 className="text-lg font-bold text-white mb-4">People Affected</h3>
          <div className="text-4xl font-bold text-cyan-400 mb-2">{totalPeople}</div>
          <div className="text-slate-400 text-sm">Total people across all active incidents</div>
        </div>
        <div className="bg-slate-900/40 border border-slate-800 rounded-xl p-6">
          <h3 className="text-lg font-bold text-white mb-4">Vulnerable People</h3>
          <div className="text-4xl font-bold text-red-400 mb-2">{totalVulnerable}</div>
          <div className="text-slate-400 text-sm">Total vulnerable individuals identified</div>
        </div>
      </div>

      {/* Recent Activity Timeline */}
      <div className="bg-slate-900/40 border border-slate-800 rounded-xl p-6">
        <h3 className="text-lg font-bold text-white mb-4">Recent Incidents</h3>
        <div className="space-y-2">
          {incidents.slice(0, 10).map((inc) => (
            <div key={inc.id} className="flex items-center gap-4 p-3 bg-slate-800/50 rounded-lg">
              <div className={`w-3 h-3 rounded-full ${
                inc.status === 'resolved' ? 'bg-green-500' :
                inc.urgency === 'critical' ? 'bg-red-500' :
                inc.urgency === 'high' ? 'bg-orange-500' :
                inc.urgency === 'medium' ? 'bg-yellow-500' : 'bg-blue-500'
              }`} />
              <div className="flex-1">
                <div className="text-white font-semibold text-sm">{inc.location_text || 'Unknown Location'}</div>
                <div className="text-slate-400 text-xs">{inc.resource || 'Assessing'}</div>
              </div>
              <div className="text-slate-500 text-xs">{inc.last_updated?.split('T')[0] || 'N/A'}</div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

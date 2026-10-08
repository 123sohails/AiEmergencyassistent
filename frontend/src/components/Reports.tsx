"use client";

import { useState, useEffect } from 'react';
import axios from 'axios';

export default function Reports() {
  const [incidents, setIncidents] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [filterStatus, setFilterStatus] = useState<string>('all');
  const [filterUrgency, setFilterUrgency] = useState<string>('all');

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

  const filteredIncidents = incidents.filter(inc => {
    if (filterStatus !== 'all' && inc.status !== filterStatus) return false;
    if (filterUrgency !== 'all' && inc.urgency !== filterUrgency) return false;
    return true;
  });

  const exportToCSV = () => {
    const headers = ['ID', 'Status', 'Urgency', 'Location', 'Resource', 'People', 'Vulnerable', 'First Seen', 'Last Updated', 'Summary'];
    const rows = filteredIncidents.map(inc => [
      inc.id,
      inc.status,
      inc.urgency,
      inc.location_text || 'Unknown',
      inc.resource || 'Assessing',
      inc.people_latest || 0,
      Array.isArray(inc.vulnerable) ? inc.vulnerable.join('; ') : inc.vulnerable || '',
      inc.first_seen || '',
      inc.last_updated || '',
      inc.summary || ''
    ]);

    const csvContent = [headers, ...rows]
      .map(row => row.map(cell => `"${cell}"`).join(','))
      .join('\n');

    const blob = new Blob([csvContent], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `incident_report_${new Date().toISOString().split('T')[0]}.csv`;
    a.click();
    window.URL.revokeObjectURL(url);
  };

  const exportToJSON = () => {
    const data = filteredIncidents.map(inc => ({
      id: inc.id,
      status: inc.status,
      urgency: inc.urgency,
      location: inc.location_text,
      coordinates: { lat: inc.lat, lng: inc.lng },
      resource: inc.resource,
      people_affected: inc.people_latest,
      vulnerable: inc.vulnerable,
      timeline: {
        first_seen: inc.first_seen,
        last_updated: inc.last_updated
      },
      summary: inc.summary
    }));

    const jsonContent = JSON.stringify(data, null, 2);
    const blob = new Blob([jsonContent], { type: 'application/json' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `incident_report_${new Date().toISOString().split('T')[0]}.json`;
    a.click();
    window.URL.revokeObjectURL(url);
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="text-slate-400">Loading reports...</div>
      </div>
    );
  }

  const getStatusBadge = (status: string) => {
    const colors = {
      active: 'bg-red-500/20 text-red-400 border-red-500',
      rescue_in_progress: 'bg-yellow-500/20 text-yellow-400 border-yellow-500',
      resolved: 'bg-green-500/20 text-green-400 border-green-500'
    };
    return colors[status as keyof typeof colors] || colors.active;
  };

  const getUrgencyBadge = (urgency: string) => {
    const colors = {
      critical: 'bg-red-500/20 text-red-400 border-red-500',
      high: 'bg-orange-500/20 text-orange-400 border-orange-500',
      medium: 'bg-yellow-500/20 text-yellow-400 border-yellow-500',
      low: 'bg-blue-500/20 text-blue-400 border-blue-500'
    };
    return colors[urgency as keyof typeof colors] || colors.low;
  };

  return (
    <div className="p-6 space-y-6 overflow-auto">
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-bold text-white">Incident Reports</h2>
        <div className="flex gap-2">
          <button
            onClick={exportToCSV}
            className="px-4 py-2 bg-cyan-500 hover:bg-cyan-600 text-slate-900 font-bold rounded-lg transition-colors"
          >
            Export CSV
          </button>
          <button
            onClick={exportToJSON}
            className="px-4 py-2 bg-slate-700 hover:bg-slate-600 text-white font-bold rounded-lg transition-colors"
          >
            Export JSON
          </button>
        </div>
      </div>

      {/* Filters */}
      <div className="bg-slate-900/40 border border-slate-800 rounded-xl p-4 flex gap-4">
        <div className="flex-1">
          <label className="text-slate-400 text-sm font-bold mb-2 block">Status</label>
          <select
            value={filterStatus}
            onChange={(e) => setFilterStatus(e.target.value)}
            className="w-full bg-slate-800 border border-slate-700 text-white rounded p-2 outline-none"
          >
            <option value="all">All Statuses</option>
            <option value="active">Active</option>
            <option value="rescue_in_progress">Rescue in Progress</option>
            <option value="resolved">Resolved</option>
          </select>
        </div>
        <div className="flex-1">
          <label className="text-slate-400 text-sm font-bold mb-2 block">Urgency</label>
          <select
            value={filterUrgency}
            onChange={(e) => setFilterUrgency(e.target.value)}
            className="w-full bg-slate-800 border border-slate-700 text-white rounded p-2 outline-none"
          >
            <option value="all">All Urgencies</option>
            <option value="critical">Critical</option>
            <option value="high">High</option>
            <option value="medium">Medium</option>
            <option value="low">Low</option>
          </select>
        </div>
        <div className="flex-1">
          <label className="text-slate-400 text-sm font-bold mb-2 block">Results</label>
          <div className="w-full bg-slate-800 border border-slate-700 text-white rounded p-2">
            {filteredIncidents.length} incidents
          </div>
        </div>
      </div>

      {/* Summary Stats */}
      <div className="grid grid-cols-4 gap-4">
        <div className="bg-slate-900/40 border border-slate-800 rounded-xl p-4">
          <div className="text-slate-400 text-sm font-bold mb-1">Total Records</div>
          <div className="text-2xl font-bold text-cyan-400">{filteredIncidents.length}</div>
        </div>
        <div className="bg-slate-900/40 border border-slate-800 rounded-xl p-4">
          <div className="text-slate-400 text-sm font-bold mb-1">Active</div>
          <div className="text-2xl font-bold text-red-400">{filteredIncidents.filter(i => i.status === 'active').length}</div>
        </div>
        <div className="bg-slate-900/40 border border-slate-800 rounded-xl p-4">
          <div className="text-slate-400 text-sm font-bold mb-1">Critical</div>
          <div className="text-2xl font-bold text-orange-400">{filteredIncidents.filter(i => i.urgency === 'critical').length}</div>
        </div>
        <div className="bg-slate-900/40 border border-slate-800 rounded-xl p-4">
          <div className="text-slate-400 text-sm font-bold mb-1">Resolved</div>
          <div className="text-2xl font-bold text-green-400">{filteredIncidents.filter(i => i.status === 'resolved').length}</div>
        </div>
      </div>

      {/* Incident Table */}
      <div className="bg-slate-900/40 border border-slate-800 rounded-xl overflow-hidden">
        <table className="w-full">
          <thead className="bg-slate-800/50">
            <tr>
              <th className="text-left p-4 text-slate-400 font-bold text-sm">ID</th>
              <th className="text-left p-4 text-slate-400 font-bold text-sm">Status</th>
              <th className="text-left p-4 text-slate-400 font-bold text-sm">Urgency</th>
              <th className="text-left p-4 text-slate-400 font-bold text-sm">Location</th>
              <th className="text-left p-4 text-slate-400 font-bold text-sm">Resource</th>
              <th className="text-left p-4 text-slate-400 font-bold text-sm">People</th>
              <th className="text-left p-4 text-slate-400 font-bold text-sm">First Seen</th>
              <th className="text-left p-4 text-slate-400 font-bold text-sm">Last Updated</th>
            </tr>
          </thead>
          <tbody>
            {filteredIncidents.map((inc) => (
              <tr key={inc.id} className="border-t border-slate-800 hover:bg-slate-800/30">
                <td className="p-4 text-white font-mono text-sm">{inc.id}</td>
                <td className="p-4">
                  <span className={`px-2 py-1 rounded text-xs font-bold border ${getStatusBadge(inc.status)}`}>
                    {inc.status.replace(/_/g, ' ').toUpperCase()}
                  </span>
                </td>
                <td className="p-4">
                  <span className={`px-2 py-1 rounded text-xs font-bold border ${getUrgencyBadge(inc.urgency)}`}>
                    {inc.urgency.toUpperCase()}
                  </span>
                </td>
                <td className="p-4 text-white text-sm">{inc.location_text || 'Unknown'}</td>
                <td className="p-4 text-slate-300 text-sm">{inc.resource || 'Assessing'}</td>
                <td className="p-4 text-white text-sm">{inc.people_latest || 0}</td>
                <td className="p-4 text-slate-400 text-sm">{inc.first_seen?.split('T')[0] || 'N/A'}</td>
                <td className="p-4 text-slate-400 text-sm">{inc.last_updated?.split('T')[0] || 'N/A'}</td>
              </tr>
            ))}
          </tbody>
        </table>
        {filteredIncidents.length === 0 && (
          <div className="p-8 text-center text-slate-500">No incidents match the current filters</div>
        )}
      </div>
    </div>
  );
}

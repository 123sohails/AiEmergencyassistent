import { AlertTriangle, Clock, Users, Flame } from 'lucide-react';

export default function TopMetrics({ activeCount, criticalCount, peopleCount }: { activeCount: number, criticalCount: number, peopleCount: number }) {
  return (
    <div className="grid grid-cols-4 gap-4 mb-8">
      {/* Active Incidents */}
      <div className="bg-[#13232c] border border-[#233743] rounded-2xl p-5 flex flex-col justify-between">
        <div className="flex justify-between items-start mb-4">
          <span className="text-sm font-semibold text-muted">Active incidents</span>
          <div className="w-8 h-8 rounded-full bg-ns-red/20 flex items-center justify-center">
            <AlertTriangle size={16} className="text-ns-red" />
          </div>
        </div>
        <div>
          <div className="text-4xl font-bold text-white mb-2">{activeCount.toString().padStart(2, '0')}</div>
          <div className="text-xs text-muted">+3 today</div>
        </div>
      </div>

      {/* Critical Alerts */}
      <div className="bg-[#13232c] border border-[#233743] rounded-2xl p-5 flex flex-col justify-between">
        <div className="flex justify-between items-start mb-4">
          <span className="text-sm font-semibold text-muted">Critical alerts</span>
          <div className="w-8 h-8 rounded-full bg-ns-yellow/20 flex items-center justify-center">
            <Flame size={16} className="text-ns-yellow" />
          </div>
        </div>
        <div>
          <div className="text-4xl font-bold text-white mb-2">{criticalCount.toString().padStart(2, '0')}</div>
          <div className="text-xs text-muted">Needs attention</div>
        </div>
      </div>

      {/* People Affected */}
      <div className="bg-[#13232c] border border-[#233743] rounded-2xl p-5 flex flex-col justify-between">
        <div className="flex justify-between items-start mb-4">
          <span className="text-sm font-semibold text-muted">People affected</span>
          <div className="w-8 h-8 rounded-full bg-ns-teal/20 flex items-center justify-center">
            <Users size={16} className="text-ns-teal" />
          </div>
        </div>
        <div>
          <div className="text-4xl font-bold text-white mb-2">{peopleCount}</div>
          <div className="text-xs text-muted">+8 in last hour</div>
        </div>
      </div>

      {/* Avg Response */}
      <div className="bg-[#13232c] border border-[#233743] rounded-2xl p-5 flex flex-col justify-between">
        <div className="flex justify-between items-start mb-4">
          <span className="text-sm font-semibold text-muted">Avg. response time</span>
          <div className="w-8 h-8 rounded-full bg-[#3d5a6c]/30 flex items-center justify-center">
            <Clock size={16} className="text-[#8ba3b2]" />
          </div>
        </div>
        <div>
          <div className="text-4xl font-bold text-white mb-2">04:18</div>
          <div className="text-xs text-ns-teal">12% faster today</div>
        </div>
      </div>
    </div>
  );
}

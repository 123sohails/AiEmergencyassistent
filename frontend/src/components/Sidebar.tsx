import { LayoutGrid, AlertTriangle, Map as MapIcon, Activity, FileText, ShieldAlert } from 'lucide-react';

interface SidebarProps {
  activeView: string;
  onViewChange: (view: string) => void;
  incidentCount?: number;
}

export default function Sidebar({ activeView, onViewChange, incidentCount = 0 }: SidebarProps) {
  const navItems = [
    { id: 'overview', label: 'Overview', icon: LayoutGrid },
    { id: 'incidents', label: 'Incidents', icon: AlertTriangle, badge: incidentCount },
    { id: 'map', label: 'Map', icon: MapIcon },
    { id: 'analytics', label: 'Analytics', icon: Activity },
    { id: 'reports', label: 'Reports', icon: FileText },
  ];

  return (
    <div className="w-64 h-full bg-[#0b161e] border-r border-[#233743] flex flex-col shrink-0 overflow-hidden">
      <div className="h-20 px-6 flex items-center gap-3 border-b border-[#233743] shrink-0">
        <div className="w-10 h-10 rounded-xl bg-ns-red flex items-center justify-center shrink-0">
          <ShieldAlert className="text-white" size={20} />
        </div>
        <div className="flex flex-col">
          <span className="font-bold text-white tracking-wide text-sm leading-tight">NORTHSTAR</span>
          <span className="text-[10px] text-muted font-semibold tracking-widest uppercase">Response Command</span>
        </div>
      </div>
      
      <div className="p-4 flex-1 flex flex-col gap-2 overflow-auto">
        <div className="text-[10px] font-bold text-[#718096] tracking-widest uppercase mb-2 px-2">Command Center</div>

        {navItems.map((item) => {
          const Icon = item.icon;
          const isActive = activeView === item.id;

          return (
            <button
              key={item.id}
              onClick={() => onViewChange(item.id)}
              className={`flex items-center gap-3 px-4 py-3 rounded-xl w-full transition-colors group ${
                isActive
                  ? 'bg-[#13232c] border border-[#00f0ff]/30 text-white'
                  : 'hover:bg-[#13232c]/50 text-[#718096] hover:text-white'
              }`}
            >
              <Icon
                className={isActive ? 'text-[#00f0ff]' : 'group-hover:text-[#ff4444] transition-colors'}
                size={18}
              />
              <span className="font-semibold text-sm">{item.label}</span>
              {item.badge !== undefined && item.badge > 0 && (
                <span className="ml-auto bg-[#1a2f3b] text-xs px-2 py-0.5 rounded-full text-[#718096]">
                  {item.badge}
                </span>
              )}
            </button>
          );
        })}
      </div>
    </div>
  );
}

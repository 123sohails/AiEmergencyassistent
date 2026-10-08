import { Home, AlertTriangle, Map as MapIcon, BarChart2, FileText } from 'lucide-react';

interface SidebarProps {
  activeView: string;
  onViewChange: (view: string) => void;
  incidentCount?: number;
}

export default function Sidebar({ activeView, onViewChange, incidentCount = 0 }: SidebarProps) {
  const navItems = [
    { id: 'overview', label: 'Overview', icon: Home },
    { id: 'incidents', label: 'Incidents', icon: AlertTriangle },
    { id: 'map', label: 'Map', icon: MapIcon },
    { id: 'analytics', label: 'Analytics', icon: BarChart2 },
    { id: 'reports', label: 'Reports', icon: FileText },
  ];

  return (
    <div className="w-48 bg-[#0a121e] border-r border-[#1a365d] flex flex-col pt-6 shrink-0 z-50 rounded-l-xl">
      {navItems.map((item) => {
        const Icon = item.icon;
        const isActive = activeView === item.id;

        return (
          <button
            key={item.id}
            onClick={() => onViewChange(item.id)}
            className={`flex items-center gap-4 px-6 py-4 w-full transition-colors relative ${
              isActive
                ? 'bg-[#10243e] text-[#00f0ff]'
                : 'text-slate-400 hover:bg-[#10243e]/50 hover:text-slate-200'
            }`}
          >
            {isActive && (
              <div className="absolute left-0 top-0 bottom-0 w-1.5 bg-[#00f0ff]"></div>
            )}
            <Icon size={20} className={isActive ? 'text-[#00f0ff]' : ''} />
            <span className="font-semibold text-sm">{item.label}</span>
          </button>
        );
      })}
    </div>
  );
}

import { Home, AlertTriangle, Map, BarChart2, FileText } from 'lucide-react';

export default function NavSidebar({ activeTab, setActiveTab }: { activeTab: string, setActiveTab: (t: string) => void }) {
  const tabs = [
    { id: 'overview', icon: <Home size={20} />, label: 'Overview' },
    { id: 'incidents', icon: <AlertTriangle size={20} />, label: 'Incidents' },
    { id: 'map', icon: <Map size={20} />, label: 'Map' },
    { id: 'analytics', icon: <BarChart2 size={20} />, label: 'Analytics' },
    { id: 'reports', icon: <FileText size={20} />, label: 'Reports' },
  ];

  return (
    <div className="w-48 bg-[#0a121e] border-r border-[#1a365d] flex flex-col pt-6 shrink-0 z-50">
      {tabs.map(tab => (
        <button
          key={tab.id}
          onClick={() => setActiveTab(tab.id)}
          className={`flex items-center gap-3 px-6 py-4 w-full transition-colors relative ${
            activeTab === tab.id 
              ? 'bg-[#10243e] text-[#00f0ff]' 
              : 'text-slate-400 hover:bg-[#10243e]/50 hover:text-slate-200'
          }`}
        >
          {activeTab === tab.id && (
            <div className="absolute left-0 top-0 bottom-0 w-1 bg-[#00f0ff]"></div>
          )}
          {tab.icon}
          <span className="font-semibold text-sm">{tab.label}</span>
        </button>
      ))}
    </div>
  );
}

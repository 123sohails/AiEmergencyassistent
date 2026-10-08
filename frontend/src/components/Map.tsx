"use client";

import { useEffect, useState } from 'react';
import { MapContainer, TileLayer, Marker, Popup, Tooltip, useMap } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';
import L from 'leaflet';

// Fix Leaflet icons in Next.js
delete (L.Icon.Default.prototype as any)._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon-2x.png',
  iconUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon.png',
  shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-shadow.png',
});

// Custom colored icons
const createIcon = (color: string) => {
  return new L.Icon({
    iconUrl: `https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-${color}.png`,
    shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-shadow.png',
    iconSize: [25, 41],
    iconAnchor: [12, 41],
    popupAnchor: [1, -34],
    shadowSize: [41, 41]
  });
};

const icons = {
  critical: createIcon('red'),
  high: createIcon('red'),
  medium: createIcon('orange'),
  low: createIcon('blue'),
  resolved: createIcon('green')
};

// Component to dynamically recenter the map when incidents arrive
function MapRecenter({ incidents }: { incidents: any[] }) {
  const map = useMap();
  useEffect(() => {
    if (incidents.length > 0) {
      const firstValid = incidents.find(i => i.lat && i.lng);
      if (firstValid) {
        map.setView([firstValid.lat, firstValid.lng], 12, { animate: true });
      }
    }
  }, [incidents, map]);
  return null;
}

export default function Map({ incidents }: { incidents: any[] }) {
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  if (!mounted) return <div className="w-full h-full bg-slate-900 rounded-xl animate-pulse"></div>;

  return (
    <MapContainer 
      center={[19.0760, 72.8777]} // Default to Mumbai roughly, but it will auto-center
      zoom={11} 
      className="w-full h-full rounded-xl z-0"
    >
      <MapRecenter incidents={incidents} />
      <TileLayer
        url="https://server.arcgisonline.com/ArcGIS/rest/services/Canvas/World_Dark_Gray_Base/MapServer/tile/{z}/{y}/{x}"
        attribution='&copy; <a href="https://www.esri.com/">Esri</a>'
      />
      
      {incidents.map((inc) => {
        if (!inc.lat || !inc.lng) return null;
        const icon = inc.status === 'resolved' ? icons.resolved : icons[inc.urgency as keyof typeof icons] || icons.low;
        
        const getUrgencyIcon = (urgency: string) => {
          if (urgency === 'critical') return '🔥';
          if (urgency === 'high') return '⚠️';
          if (urgency === 'medium') return '⚡';
          return 'ℹ️';
        };
        
        return (
          <Marker key={inc.id} position={[inc.lat, inc.lng]} icon={icon}>
            <Tooltip direction="top" offset={[0, -40]} opacity={1} className="custom-tooltip">
              <div className="bg-slate-900 text-white p-2 border border-slate-700 rounded shadow-xl text-xs font-sans">
                <div className="font-bold mb-1">{getUrgencyIcon(inc.urgency)} {inc.location_text || 'Unknown Location'}</div>
                <div className="text-slate-400">{inc.resource || 'Assessing'}</div>
              </div>
            </Tooltip>
            <Popup>
              <div className="text-sm font-sans">
                <strong>{inc.id}</strong><br/>
                {inc.summary}
              </div>
            </Popup>
          </Marker>
        );
      })}
    </MapContainer>
  );
}

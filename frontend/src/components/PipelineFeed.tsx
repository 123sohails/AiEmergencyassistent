"use client";
import { Upload, RefreshCw, Trash2 } from 'lucide-react';
import axios from 'axios';
import { useRef, useState } from 'react';

export default function PipelineFeed({ pipeline, refresh }: { pipeline: any, refresh: () => void }) {
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [uploading, setUploading] = useState(false);

  const handleUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    if (!e.target.files || e.target.files.length === 0) return;
    setUploading(true);
    
    const formData = new FormData();
    formData.append('file', e.target.files[0]);
    
    try {
      await axios.post('http://localhost:8000/api/upload', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        }
      });
      refresh();
    } catch (error) {
      console.error("Upload failed", error);
      // Silent fail - upload is optional
    } finally {
      setUploading(false);
      if (fileInputRef.current) fileInputRef.current.value = '';
    }
  };

  const handleReset = async () => {
    await axios.post('http://localhost:8000/api/reset');
    refresh();
  };

  return (
    <div className="bg-slate-900/40 border border-slate-800 rounded-xl p-4 flex flex-col gap-4">
      <h3 className="text-white font-bold flex items-center gap-2">
        <span className="text-cyan-400">⛑️</span> Control Panel
      </h3>
      
      <div className="bg-slate-800/50 p-3 rounded-lg border border-slate-700 flex flex-col gap-3">
        <div className="text-sm text-slate-300 font-bold mb-1">Upload Intel</div>
        <input 
          type="file" 
          ref={fileInputRef} 
          onChange={handleUpload} 
          className="hidden" 
          accept=".csv,.json,.txt,.mp3,.wav"
        />
        <button 
          onClick={() => fileInputRef.current?.click()}
          disabled={uploading}
          className="bg-cyan-500 hover:bg-cyan-400 text-slate-900 font-bold py-2 px-4 rounded w-full flex items-center justify-center gap-2 transition-colors disabled:opacity-50"
        >
          <Upload size={16} />
          {uploading ? 'Uploading...' : 'Queue Dataset'}
        </button>
      </div>

      <div className="flex gap-2">
        <button onClick={refresh} className="bg-slate-800 hover:bg-slate-700 text-white font-bold py-2 px-3 rounded flex-1 flex items-center justify-center gap-2 border border-slate-700 text-sm">
          <RefreshCw size={14} /> Refresh
        </button>
        <button onClick={handleReset} className="bg-red-900/30 hover:bg-red-900/50 text-red-400 font-bold py-2 px-3 rounded flex-1 flex items-center justify-center gap-2 border border-red-900/50 text-sm">
          <Trash2 size={14} /> Reset
        </button>
      </div>

      <div className="mt-4">
        <h4 className="text-slate-400 text-sm font-bold mb-3 border-b border-slate-800 pb-2">Live AI Pipeline Feed</h4>
        {pipeline?.pending_count > 0 ? (
          <div className="text-cyan-400 text-xs flex items-center gap-2 bg-cyan-900/20 p-2 rounded border border-cyan-900/50">
            <span className="w-2 h-2 rounded-full bg-cyan-400 animate-pulse"></span>
            Processing {pipeline.active_report_id}...
            <span className="ml-auto bg-slate-800 px-2 py-0.5 rounded text-[10px]">{pipeline.pending_count} left</span>
          </div>
        ) : (
          <div className="text-emerald-400 text-xs flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-emerald-400"></span>
            Pipeline Idle (Awaiting Intel)
          </div>
        )}
      </div>

      <div className="mt-auto pt-4 border-t border-slate-800">
        <h4 className="text-yellow-500/80 text-xs font-bold mb-2 flex items-center gap-1">
          <span>⚠️</span> AI Limitations & Warnings
        </h4>
        <ul className="text-[10px] text-slate-500 space-y-2 list-disc pl-3">
          <li>Location geocoding relies on LLM landmark resolution and may be approximate.</li>
          <li>Conflicting casualty reports prioritize the highest reported number (worst-case scenario).</li>
          <li>Audio transcripts may contain hallucinated entities in highly noisy environments.</li>
        </ul>
      </div>
    </div>
  );
}

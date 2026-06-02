'use client';

import React, { useEffect, useState } from 'react';
import { BA_API } from '../utils/api';

export default function Header() {
  const [isOnline, setIsOnline] = useState(false);
  const [dbType, setDbType] = useState('');

  useEffect(() => {
    const checkConnection = async () => {
      try {
        const res = await fetch(BA_API.getApiUrl() + '/');
        if (res.ok) {
          const data = await res.json();
          setIsOnline(true);
          setDbType(data.database || 'SQLite (Local)');
        } else {
          setIsOnline(false);
        }
      } catch (e) {
        setIsOnline(false);
      }
    };
    checkConnection();
    const interval = setInterval(checkConnection, 15000);
    return () => clearInterval(interval);
  }, []);

  return (
    <header className="h-16 border-b border-slate-200 bg-white px-8 flex items-center justify-between shrink-0 shadow-sm">
      {/* Workspace breadcrumbs */}
      <div className="flex items-center gap-2">
        <span className="text-slate-400 text-xs font-semibold uppercase tracking-wider">
          Workspace
        </span>
        <span className="text-slate-300">/</span>
        <span className="text-slate-800 text-sm font-bold flex items-center gap-2">
          Đặc tả màn hình thiết kế
          <span className="w-1.5 h-1.5 rounded-full bg-cyan-500 animate-ping"></span>
        </span>
      </div>

      {/* Right controls */}
      <div className="flex items-center gap-6">
        {/* API connection indicator */}
        <div className="flex items-center gap-2 bg-slate-50 border border-slate-100 px-3.5 py-1.5 rounded-xl">
          <div className="flex items-center gap-1.5">
            <span className={`w-2.5 h-2.5 rounded-full ${
              isOnline ? 'bg-emerald-500 shadow-md shadow-emerald-500/20' : 'bg-rose-500 shadow-md shadow-rose-500/20'
            }`}></span>
            <span className="text-xs font-bold text-slate-600">
              {isOnline ? 'Backend Online' : 'Backend Offline'}
            </span>
          </div>
          {isOnline && dbType && (
            <>
              <span className="text-slate-300">|</span>
              <span className="text-[10px] text-slate-500 font-bold font-mono">
                {dbType}
              </span>
            </>
          )}
        </div>

        {/* Profile Avatar */}
        <div className="flex items-center gap-2.5 border-l border-slate-200 pl-6">
          <div className="text-right">
            <p className="text-xs font-bold text-slate-800">Business Analyst</p>
            <p className="text-[9px] text-slate-400 font-semibold">User Account</p>
          </div>
          <div className="w-9 h-9 rounded-xl bg-gradient-to-tr from-cyan-500 to-indigo-500 p-[1.5px] shadow-sm">
            <div className="w-full h-full rounded-[10px] bg-white flex items-center justify-center font-bold text-xs text-slate-700 font-mono">
              BA
            </div>
          </div>
        </div>
      </div>
    </header>
  );
}

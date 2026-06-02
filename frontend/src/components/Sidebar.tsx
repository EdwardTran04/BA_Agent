'use client';

import React, { useEffect, useState } from 'react';
import { BA_API, SessionResponse } from '../utils/api';

interface SidebarProps {
  currentSessionId: string | null;
  onSelectSession: (id: string) => void;
  onNewSession: () => void;
}

export default function Sidebar({
  currentSessionId,
  onSelectSession,
  onNewSession,
}: SidebarProps) {
  const [sessions, setSessions] = useState<SessionResponse[]>([]);
  const [loading, setLoading] = useState(true);

  const [isCollapsed, setIsCollapsed] = useState(false);

  const fetchSessions = async () => {
    try {
      const data = await BA_API.listSessions();
      setSessions(data);
    } catch (e) {
      console.error('Failed to load session history:', e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchSessions();
    // Poll sessions list every 10 seconds to keep history fresh
    const interval = setInterval(fetchSessions, 10000);
    return () => clearInterval(interval);
  }, [currentSessionId]);

  const getStatusBadge = (status: SessionResponse['status']) => {
    switch (status) {
      case 'completed':
      case 'docx_generated':
        return (
          <span className="text-[10px] px-2 py-0.5 rounded-full font-medium bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
            Hoàn thành
          </span>
        );
      case 'awaiting_answers':
      case 'waiting_user_answer':
        return (
          <span className="text-[10px] px-2 py-0.5 rounded-full font-medium bg-amber-500/10 text-amber-400 border border-amber-500/20">
            Chờ trả lời
          </span>
        );
      case 'analyzing':
      case 'uploaded':
        return (
          <span className="text-[10px] px-2 py-0.5 rounded-full font-medium bg-blue-500/10 text-blue-400 border border-blue-500/20 animate-pulse">
            Đang phân tích
          </span>
        );
      default:
        return (
          <span className="text-[10px] px-2 py-0.5 rounded-full font-medium bg-rose-500/10 text-rose-400 border border-rose-500/20">
            Lỗi
          </span>
        );
    }
  };

  return (
    <aside className={`bg-slate-900 border-r border-slate-800 text-slate-100 flex flex-col h-screen shrink-0 transition-all duration-300 ${
      isCollapsed ? 'w-20' : 'w-80'
    }`}>
      {/* Brand Header */}
      <div className={`border-b border-slate-800 flex items-center justify-between gap-3 ${
        isCollapsed ? 'p-4 justify-center' : 'p-6'
      }`}>
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-cyan-500 to-indigo-600 flex items-center justify-center shadow-lg shadow-cyan-500/20 animate-pulse shrink-0">
            <svg className="w-5 h-5 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
            </svg>
          </div>
          {!isCollapsed && (
            <div>
              <h1 className="font-bold text-sm leading-tight bg-gradient-to-r from-cyan-400 to-indigo-400 bg-clip-text text-transparent">
                BA Agent AI
              </h1>
              <p className="text-[10px] text-slate-400 font-medium">Screen-to-Spec MVP</p>
            </div>
          )}
        </div>
        <button
          onClick={() => setIsCollapsed(!isCollapsed)}
          className="p-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 transition-colors"
          title={isCollapsed ? "Mở rộng Sidebar" : "Thu nhỏ Sidebar"}
        >
          <svg className="w-3.5 h-3.5 text-slate-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            {isCollapsed ? (
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M9 5l7 7-7 7" />
            ) : (
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M15 19l-7-7 7-7" />
            )}
          </svg>
        </button>
      </div>

      {/* Main Actions */}
      <div className="p-4 flex justify-center">
        {isCollapsed ? (
          <button
            onClick={onNewSession}
            className="w-10 h-10 rounded-full bg-gradient-to-r from-cyan-500 to-indigo-500 hover:from-cyan-600 hover:to-indigo-600 flex items-center justify-center transition-all duration-300 shadow-lg shadow-cyan-500/10 hover:shadow-cyan-500/20 hover:-translate-y-0.5"
            title="Phân tích màn hình mới"
          >
            <svg className="w-5 h-5 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M12 4v16m8-8H4" />
            </svg>
          </button>
        ) : (
          <button
            onClick={onNewSession}
            className="w-full flex items-center justify-center gap-2 py-3 px-4 rounded-xl bg-gradient-to-r from-cyan-500 to-indigo-500 hover:from-cyan-600 hover:to-indigo-600 font-semibold text-sm transition-all duration-300 shadow-lg shadow-cyan-500/10 hover:shadow-cyan-500/20 hover:-translate-y-0.5 active:translate-y-0"
          >
            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
            </svg>
            Phân tích màn hình mới
          </button>
        )}
      </div>

      {/* History List */}
      <div className="flex-1 overflow-y-auto px-3 py-2 scrollbar-thin scrollbar-thumb-slate-800">
        <div className="px-3 mb-2 flex items-center justify-between">
          {!isCollapsed && (
            <h2 className="text-[11px] font-bold text-slate-400 uppercase tracking-wider">
              Lịch sử phân tích
            </h2>
          )}
          <button 
            onClick={fetchSessions}
            className="text-slate-400 hover:text-white transition-colors duration-150 mx-auto"
            title="Tải lại lịch sử"
          >
            <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 1121.21 15H19" />
            </svg>
          </button>
        </div>

        {loading ? (
          <div className="py-8 text-center text-xs text-slate-500 animate-pulse">
            {!isCollapsed ? 'Đang tải lịch sử...' : '...'}
          </div>
        ) : sessions.length === 0 ? (
          <div className={`p-4 text-center rounded-xl bg-slate-950/30 border border-dashed border-slate-800 ${isCollapsed ? 'hidden' : ''}`}>
            <svg className="w-8 h-8 text-slate-600 mx-auto mb-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
            </svg>
            <p className="text-xs text-slate-500">Chưa có lịch sử.</p>
          </div>
        ) : (
          <div className="space-y-1.5">
            {sessions.map((sess) => {
              const isSelected = sess.id === currentSessionId;
              const dateObj = new Date(sess.created_at);
              const formattedDate = `${String(dateObj.getDate()).padStart(2, '0')}/${String(dateObj.getMonth() + 1).padStart(2, '0')} ${String(dateObj.getHours()).padStart(2, '0')}:${String(dateObj.getMinutes()).padStart(2, '0')}`;
              
              return (
                <button
                  key={sess.id}
                  onClick={() => onSelectSession(sess.id)}
                  className={`w-full text-left rounded-xl border transition-all duration-200 group flex flex-col gap-1.5 ${
                    isCollapsed ? 'p-2.5 items-center justify-center' : 'p-3.5'
                  } ${
                    isSelected
                      ? 'bg-slate-800/80 border-slate-700 shadow-md ring-1 ring-cyan-500/30'
                      : 'bg-slate-900/40 border-transparent hover:bg-slate-800/40 hover:border-slate-800'
                  }`}
                  title={sess.screen_name || sess.context || `Màn hình phân tích`}
                >
                  {isCollapsed ? (
                    <div className="relative">
                      <div className={`w-8 h-8 rounded-lg flex items-center justify-center font-bold text-xs border ${
                        isSelected ? 'bg-cyan-500/10 text-cyan-400 border-cyan-500/20' : 'bg-slate-800 text-slate-400 border-slate-700'
                      }`}>
                        {(sess.screen_name || sess.context || 'M').charAt(0).toUpperCase()}
                      </div>
                      <span className={`absolute -bottom-0.5 -right-0.5 w-2.5 h-2.5 rounded-full border border-slate-900 ${
                        sess.status === 'docx_generated' || sess.status === 'completed'
                          ? 'bg-emerald-500'
                          : sess.status === 'waiting_user_answer' || sess.status === 'awaiting_answers'
                          ? 'bg-amber-500'
                          : sess.status === 'uploaded' || sess.status === 'analyzing'
                          ? 'bg-blue-500 animate-pulse'
                          : 'bg-rose-500'
                      }`} />
                    </div>
                  ) : (
                    <>
                      <div className="flex items-start justify-between gap-2 w-full">
                        <span className={`text-xs font-semibold truncate flex-1 group-hover:text-cyan-400 transition-colors ${
                          isSelected ? 'text-cyan-400' : 'text-slate-200'
                        }`}>
                          {sess.screen_name || sess.context || `Màn hình phân tích`}
                        </span>
                        <span className="text-[10px] text-slate-500 shrink-0 font-medium font-mono">
                          {formattedDate}
                        </span>
                      </div>
                      
                      <div className="flex items-center justify-between w-full">
                        <span className="text-[10px] text-slate-500 font-mono truncate max-w-[120px]">
                          ID: {sess.id.slice(0, 8)}...
                        </span>
                        {getStatusBadge(sess.status)}
                      </div>
                    </>
                  )}
                </button>
              );
            })}
          </div>
        )}
      </div>

      {/* Footer Info */}
      <div className="p-4 border-t border-slate-800 bg-slate-950/40 text-center text-[10px] text-slate-500 flex flex-col gap-0.5 shrink-0">
        {isCollapsed ? (
          <p className="font-semibold text-cyan-400">BA</p>
        ) : (
          <>
            <p className="font-semibold">BA Agent Vision MVP v1.0</p>
            <p>© 2026 Advanced Agentic Coding</p>
          </>
        )}
      </div>
    </aside>
  );
}

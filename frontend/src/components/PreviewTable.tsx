'use client';

import React, { useState } from 'react';
import { ControlSpec, BA_API } from '../utils/api';

interface PreviewTableProps {
  sessionId: string;
  controls: ControlSpec[];
  docxPath: string | null;
  onDocxGenerated: (updatedSession: any) => void;
}

export default function PreviewTable({
  sessionId,
  controls,
  docxPath,
  onDocxGenerated,
}: PreviewTableProps) {
  const [exporting, setExporting] = useState(false);

  const handleExportDocx = async () => {
    setExporting(true);
    try {
      const updatedSession = await BA_API.generateDocx(sessionId);
      onDocxGenerated(updatedSession);
    } catch (e) {
      alert('Tạo file Word thất bại. Vui lòng kiểm tra kết nối API.');
      console.error(e);
    } finally {
      setExporting(false);
    }
  };

  const downloadUrl = BA_API.getDownloadUrl(sessionId);

  return (
    <div className="bg-white border border-slate-200 rounded-2xl shadow-sm overflow-hidden flex flex-col">
      {/* Table Action Bar */}
      <div className="px-6 py-4 border-b border-slate-100 bg-slate-50/50 flex items-center justify-between gap-4">
        <div>
          <h3 className="font-bold text-slate-800 text-sm flex items-center gap-2">
            Đặc tả chi tiết thành phần & Control
            <span className="text-xs font-semibold px-2.5 py-0.5 rounded-full bg-cyan-50 text-cyan-600 border border-cyan-100 font-mono">
              {controls.length} Controls
            </span>
          </h3>
          <p className="text-[11px] text-slate-400 mt-0.5">
            Bản xem trước bảng đặc tả UI chuẩn bị kết xuất tài liệu đặc tả kỹ thuật.
          </p>
        </div>

        {/* Word Document Generation Trigger */}
        <div className="flex items-center gap-3">
          {docxPath ? (
            <a
              href={downloadUrl}
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center gap-2 py-2 px-4 rounded-xl bg-gradient-to-r from-emerald-500 to-teal-500 hover:from-emerald-600 hover:to-teal-600 font-bold text-xs text-white shadow-md shadow-emerald-500/10 hover:shadow-emerald-500/20 hover:-translate-y-0.5 active:translate-y-0 transition-all duration-300 animate-fade-in"
            >
              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
              </svg>
              Tải file Word (.docx)
            </a>
          ) : (
            <button
              onClick={handleExportDocx}
              disabled={exporting || controls.length === 0}
              className={`flex items-center gap-2 py-2.5 px-4 rounded-xl font-bold text-xs shadow-md transition-all duration-300 ${
                exporting
                  ? 'bg-slate-100 text-slate-400 cursor-not-allowed border border-slate-100 shadow-none'
                  : 'bg-gradient-to-r from-cyan-500 to-indigo-500 hover:from-cyan-600 hover:to-indigo-600 text-white hover:shadow-cyan-500/10 hover:-translate-y-0.5 active:translate-y-0'
              }`}
            >
              {exporting ? (
                <>
                  <svg className="animate-spin h-3.5 w-3.5 text-slate-400" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                  </svg>
                  <span>Đang kết xuất file Word...</span>
                </>
              ) : (
                <>
                  <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                  </svg>
                  <span>Xuất báo cáo DOCX</span>
                </>
              )}
            </button>
          )}
        </div>
      </div>

      {/* Main Grid View */}
      {controls.length === 0 ? (
        <div className="p-12 text-center">
          <svg className="w-12 h-12 text-slate-300 mx-auto mb-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M3 10h18M3 14h18m-9-4v8m-7 0h14a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z" />
          </svg>
          <p className="text-sm font-bold text-slate-800">Chưa có bảng đặc tả điều khiển</p>
          <p className="text-xs text-slate-400 mt-1">
            Bảng đặc tả tự động hiển thị sau khi AI hoàn thành phân tích màn hình của bạn.
          </p>
        </div>
      ) : (
        <div className="overflow-x-auto max-h-[520px] overflow-y-auto scrollbar-thin">
          <table className="w-full text-left border-collapse relative">
            <thead className="sticky top-0 z-10 bg-slate-100/95 backdrop-blur shadow-sm">
              <tr className="border-b border-slate-200">
                <th className="py-3 px-4 text-xs font-bold text-slate-600 text-center w-14">STT</th>
                <th className="py-3 px-4 text-xs font-bold text-slate-600 w-44">Thành phần/ Control</th>
                <th className="py-3 px-4 text-xs font-bold text-slate-600 text-center w-28">Kiểu dữ liệu</th>
                <th className="py-3 px-4 text-xs font-bold text-slate-600 text-center w-28">Input/ Output</th>
                <th className="py-3 px-4 text-xs font-bold text-slate-600 w-32">Giá trị khởi tạo</th>
                <th className="py-3 px-4 text-xs font-bold text-slate-600">Mô tả chi tiết</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 text-xs text-slate-700">
              {controls.map((ctrl, index) => {
                const isEven = index % 2 === 0;
                
                return (
                  <tr
                    key={ctrl.STT}
                    className={`hover:bg-cyan-50/25 transition-colors duration-150 ${
                      isEven ? 'bg-white' : 'bg-slate-50/30'
                    }`}
                  >
                    {/* STT Column */}
                    <td className="py-3.5 px-4 font-mono font-bold text-slate-500 text-center">
                      {ctrl.STT}
                    </td>
                    
                    {/* Control Name Column */}
                    <td className="py-3.5 px-4 font-bold text-slate-900 group">
                      {ctrl.control_name}
                    </td>

                    {/* Data Type Column */}
                    <td className="py-3.5 px-4 text-center">
                      <span className="px-2 py-0.5 rounded bg-slate-100 text-slate-600 border border-slate-200 font-semibold text-[10px]">
                        {ctrl.data_type}
                      </span>
                    </td>

                    {/* Input Output Column */}
                    <td className="py-3.5 px-4 text-center">
                      <span className={`px-2 py-0.5 rounded font-semibold text-[10px] border ${
                        ctrl.io === 'Input'
                          ? 'bg-blue-50 text-blue-600 border-blue-100'
                          : ctrl.io === 'Output'
                          ? 'bg-teal-50 text-teal-600 border-teal-100'
                          : 'bg-indigo-50 text-indigo-600 border-indigo-100'
                      }`}>
                        {ctrl.io}
                      </span>
                    </td>

                    {/* Initial Value Column */}
                    <td className="py-3.5 px-4 italic text-slate-500 break-words font-medium">
                      {ctrl.initial_value || 'Rỗng'}
                    </td>

                    {/* Detailed Description Column */}
                    <td className="py-3.5 px-4 text-slate-600 leading-relaxed font-normal break-words max-w-sm whitespace-pre-line">
                      {ctrl.description}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

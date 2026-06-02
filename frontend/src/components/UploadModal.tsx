'use client';

import React, { useState, useEffect, useRef } from 'react';

interface UploadModalProps {
  isOpen: boolean;
  onClose: () => void;
  onUpload: (file: File, context: string) => void;
}

export default function UploadModal({ isOpen, onClose, onUpload }: UploadModalProps) {
  const [file, setFile] = useState<File | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [context, setContext] = useState('');
  const [dragOver, setDragOver] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Handle Clipboard Paste Event (Ctrl+V / Cmd+V)
  useEffect(() => {
    if (!isOpen) return;

    const handlePaste = (e: ClipboardEvent) => {
      const items = e.clipboardData?.items;
      if (!items) return;

      for (let i = 0; i < items.length; i++) {
        if (items[i].type.indexOf('image') !== -1) {
          const blob = items[i].getAsFile();
          if (blob) {
            const pastedFile = new File([blob], `pasted_screen_${Date.now()}.png`, {
              type: blob.type,
            });
            handleFileSelect(pastedFile);
            break;
          }
        }
      }
    };

    window.addEventListener('paste', handlePaste);
    return () => window.removeEventListener('paste', handlePaste);
  }, [isOpen]);

  const handleFileSelect = (selectedFile: File) => {
    if (!selectedFile.type.startsWith('image/')) {
      alert('Vui lòng chọn hoặc dán tệp ảnh hợp lệ (PNG, JPG, JPEG, WEBP).');
      return;
    }
    setFile(selectedFile);
    const url = URL.createObjectURL(selectedFile);
    setPreviewUrl(url);
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      handleFileSelect(e.target.files[0]);
    }
  };

  // Drag & Drop Handlers
  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setDragOver(true);
  };

  const handleDragLeave = () => {
    setDragOver(false);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setDragOver(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFileSelect(e.dataTransfer.files[0]);
    }
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!file) return;
    onUpload(file, context);
  };

  const clearSelection = () => {
    setFile(null);
    if (previewUrl) {
      URL.revokeObjectURL(previewUrl);
      setPreviewUrl(null);
    }
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/60 backdrop-blur-sm p-4 animate-fade-in">
      <div className="w-full max-w-2xl bg-white rounded-2xl border border-slate-100 shadow-2xl overflow-hidden flex flex-col max-h-[90vh]">
        
        {/* Modal Header */}
        <div className="p-6 border-b border-slate-100 flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-lg bg-cyan-50 flex items-center justify-center text-cyan-600">
              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
              </svg>
            </div>
            <h2 className="font-bold text-slate-800 text-base">
              Tải ảnh màn hình lên để AI BA phân tích
            </h2>
          </div>
          <button
            onClick={onClose}
            className="text-slate-400 hover:text-slate-600 transition-colors p-1.5 hover:bg-slate-50 rounded-lg"
          >
            <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        <form onSubmit={handleSubmit} className="flex-1 overflow-y-auto p-6 space-y-5">
          {/* Upload Drop Zone & Clipboard paste listener */}
          {!previewUrl ? (
            <div
              onDragOver={handleDragOver}
              onDragLeave={handleDragLeave}
              onDrop={handleDrop}
              onClick={() => fileInputRef.current?.click()}
              className={`border-2 border-dashed rounded-xl p-8 text-center cursor-pointer flex flex-col items-center justify-center gap-4 transition-all duration-300 min-h-[220px] ${
                dragOver
                  ? 'border-cyan-500 bg-cyan-50/45 scale-[0.99]'
                  : 'border-slate-200 hover:border-cyan-400 hover:bg-slate-50/50'
              }`}
            >
              <input
                type="file"
                ref={fileInputRef}
                onChange={handleFileChange}
                accept="image/*"
                className="hidden"
              />
              
              <div className="w-14 h-14 rounded-full bg-slate-50 flex items-center justify-center shadow-inner group-hover:scale-105 transition-transform duration-200">
                <svg className="w-6 h-6 text-slate-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
                </svg>
              </div>

              <div>
                <p className="text-sm font-bold text-slate-800">
                  Kéo thả file ảnh hoặc Click để chọn tệp tin
                </p>
                <p className="text-xs text-slate-400 mt-1">
                  Mẹo: Nhấp vào đây rồi ấn <kbd className="px-1.5 py-0.5 rounded border bg-slate-100 font-mono text-[10px] text-slate-600 font-bold">Ctrl+V</kbd> để dán ảnh chụp trực tiếp từ Clipboard
                </p>
              </div>
              <span className="text-[10px] uppercase font-bold text-slate-400 bg-slate-50 border border-slate-100 px-2 py-0.5 rounded">
                PNG, JPG, JPEG, WEBP (Tối đa 10MB)
              </span>
            </div>
          ) : (
            <div className="border border-slate-200 rounded-xl overflow-hidden bg-slate-50 relative flex flex-col items-center justify-center p-4 min-h-[220px]">
              {/* Image Preview */}
              <img
                src={previewUrl}
                alt="Selected Screen"
                className="max-h-[240px] max-w-full rounded-lg object-contain shadow-sm border border-slate-100"
              />
              
              {/* File Info Overlay */}
              <div className="w-full flex items-center justify-between gap-3 mt-3 bg-white border border-slate-100 p-2.5 rounded-lg">
                <div className="flex items-center gap-2 truncate">
                  <svg className="w-4 h-4 text-emerald-500 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                  <span className="text-xs font-bold text-slate-700 truncate">
                    {file?.name}
                  </span>
                  <span className="text-[10px] font-mono text-slate-400">
                    ({file ? (file.size / 1024).toFixed(1) : 0} KB)
                  </span>
                </div>
                
                <button
                  type="button"
                  onClick={clearSelection}
                  className="text-xs font-semibold text-rose-500 hover:text-rose-700 hover:bg-rose-50 px-2.5 py-1.5 rounded-lg transition-all duration-150"
                >
                  Chọn ảnh khác
                </button>
              </div>
            </div>
          )}

          {/* Context / Business Rules input */}
          <div className="space-y-2">
            <label className="text-xs font-bold text-slate-700 flex items-center justify-between">
              <span>Bối cảnh nghiệp vụ / Quy tắc bổ sung (Tùy chọn)</span>
              <span className="text-[10px] text-slate-400 font-normal">Đặc tả sẽ chính xác hơn nếu có context</span>
            </label>
            <textarea
              value={context}
              onChange={(e) => setContext(e.target.value)}
              placeholder="Ví dụ: Màn hình này dùng để thêm mới hồ sơ nhân viên trong phân hệ Quản lý nhân sự HR. Nút Lưu sẽ validate độ dài và gọi API tạo mới, Nút Hủy quay lại màn hình danh sách..."
              className="w-full min-h-[90px] border border-slate-200 rounded-xl p-3.5 text-xs text-slate-800 placeholder-slate-400 focus:outline-none focus:border-cyan-500 focus:ring-1 focus:ring-cyan-500/50 resize-none transition-all duration-150"
            />
          </div>

          {/* Action buttons */}
          <div className="pt-3 border-t border-slate-100 flex items-center justify-end gap-3">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2.5 text-xs font-bold text-slate-600 hover:text-slate-800 hover:bg-slate-50 rounded-xl border border-slate-200 transition-all duration-150"
            >
              Hủy bỏ
            </button>
            <button
              type="submit"
              disabled={!file}
              className={`px-5 py-2.5 rounded-xl font-bold text-xs shadow-md transition-all duration-300 ${
                file
                  ? 'bg-gradient-to-r from-cyan-500 to-indigo-500 text-white hover:from-cyan-600 hover:to-indigo-600 hover:shadow-lg hover:shadow-cyan-500/10 hover:-translate-y-0.5'
                  : 'bg-slate-100 text-slate-400 cursor-not-allowed border border-slate-100 shadow-none'
              }`}
            >
              Bắt đầu phân tích
            </button>
          </div>
        </form>

      </div>
    </div>
  );
}

'use client';

import React, { useState, useEffect } from 'react';
import Sidebar from '../components/Sidebar';
import Header from '../components/Header';
import UploadModal from '../components/UploadModal';
import QuestionPanel from '../components/QuestionPanel';
import PreviewTable from '../components/PreviewTable';
import { BA_API, SessionResponse } from '../utils/api';

export default function Home() {
  const [currentSession, setCurrentSession] = useState<SessionResponse | null>(null);
  const [isUploadOpen, setIsUploadOpen] = useState(false);
  const [analyzing, setAnalyzing] = useState(false);
  const [submittingAnswers, setSubmittingAnswers] = useState(false);
  const [loaderPhase, setLoaderPhase] = useState('Khởi động AI Vision...');

  // Automatically update loading phrases to give an interactive, polished experience
  useEffect(() => {
    if (!analyzing) return;
    const phases = [
      'Đang tải tệp ảnh lên server...',
      'Đang xử lý hình ảnh qua AI Vision...',
      'Đang quét các thành phần giao diện (UI controls)...',
      'Đang xác định kiểu dữ liệu và giá trị khởi tạo...',
      'Đang phân tích các điểm chưa rõ để soạn câu hỏi BA...'
    ];
    let idx = 0;
    setLoaderPhase(phases[0]);
    const timer = setInterval(() => {
      idx = (idx + 1) % phases.length;
      setLoaderPhase(phases[idx]);
    }, 4000);
    return () => clearInterval(timer);
  }, [analyzing]);

  const handleUpload = async (file: File, context: string) => {
    setIsUploadOpen(false);
    setAnalyzing(true);
    try {
      const session = await BA_API.analyzeScreen(file, context);
      setCurrentSession(session);
    } catch (e: any) {
      alert(e.message || 'Phân tích thất bại. Vui lòng kiểm tra lại cấu hình.');
    } finally {
      setAnalyzing(false);
    }
  };

  const handleAnswersSubmit = async (answers: { id: string; answer: string }[], autoGenerate: boolean) => {
    if (!currentSession) return;
    setSubmittingAnswers(true);
    try {
      const refinedSession = await BA_API.submitAnswers(currentSession.id, answers, autoGenerate);
      setCurrentSession(refinedSession);
    } catch (e: any) {
      alert(e.message || 'Lỗi khi gửi câu trả lời.');
    } finally {
      setSubmittingAnswers(false);
    }
  };

  const handleSelectSession = async (id: string) => {
    try {
      const session = await BA_API.getSession(id);
      setCurrentSession(session);
    } catch (e) {
      console.error(e);
      alert('Không thể tải thông tin phiên phân tích này.');
    }
  };

  const handleNewSession = () => {
    setCurrentSession(null);
    setIsUploadOpen(true);
  };

  const handleDocxUpdate = (updatedSession: SessionResponse) => {
    setCurrentSession(updatedSession);
  };

  const getImageUrl = (path: string) => {
    const filename = path.replace(/\\/g, '/').split('/').pop();
    return `${BA_API.getApiUrl()}/static/${filename}`;
  };

  return (
    <div className="flex h-screen w-screen overflow-hidden bg-slate-50 font-sans">
      {/* Sidebar history */}
      <Sidebar
        currentSessionId={currentSession?.id || null}
        onSelectSession={handleSelectSession}
        onNewSession={handleNewSession}
      />

      {/* Main Container */}
      <div className="flex-1 flex flex-col h-full overflow-hidden">
        {/* Header toolbar */}
        <Header />

        {/* Work Area */}
        <main className="flex-1 overflow-y-auto p-8 scrollbar-thin">
          {analyzing ? (
            /* Premium Loading Screen */
            <div className="h-full min-h-[450px] flex flex-col items-center justify-center gap-6 animate-fade-in bg-white border border-slate-200 rounded-2xl p-12 max-w-3xl mx-auto shadow-sm">
              <div className="relative w-20 h-20">
                <div className="absolute inset-0 rounded-full border-4 border-cyan-100 animate-pulse"></div>
                <div className="absolute inset-0 rounded-full border-4 border-transparent border-t-cyan-500 animate-spin"></div>
              </div>
              <div className="text-center space-y-2">
                <h3 className="font-bold text-slate-800 text-base">
                  AI BA đang xử lý thiết kế màn hình
                </h3>
                <p className="text-sm font-bold text-cyan-600 font-mono animate-pulse">
                  {loaderPhase}
                </p>
                <p className="text-xs text-slate-400 max-w-sm mx-auto leading-relaxed">
                  Vui lòng không đóng tab này. AI đang nhìn sâu vào giao diện để nhận diện nút bấm, bảng dữ liệu, và các trường thông tin.
                </p>
              </div>
            </div>
          ) : !currentSession ? (
            /* Welcome / Hero State */
            <div className="max-w-4xl mx-auto py-12 space-y-12 animate-fade-in">
              <div className="text-center space-y-4">
                <span className="text-xs font-bold uppercase tracking-widest px-3 py-1 bg-cyan-50 text-cyan-600 border border-cyan-100 rounded-full">
                  AI-Powered BA Agent
                </span>
                <h2 className="text-3xl font-extrabold text-slate-900 tracking-tight leading-tight">
                  Tự Động Hóa Đặc Tả Màn Hình UI <br />
                  Thành Tài Liệu Word Chuẩn Nghiệp Vụ
                </h2>
                <p className="text-sm text-slate-500 max-w-xl mx-auto leading-relaxed">
                  Chỉ cần tải lên ảnh chụp màn hình thiết kế hoặc wireframe. AI BA Agent sẽ tự động review, phát hiện tất cả các control, hỗ trợ bạn bổ sung logic qua Q&A và xuất bản file đặc tả DOCX trong 10 giây.
                </p>

                {/* Central Call-to-action */}
                <div className="pt-6">
                  <button
                    onClick={() => setIsUploadOpen(true)}
                    className="group relative inline-flex items-center gap-3.5 py-4 px-8 rounded-2xl bg-gradient-to-r from-cyan-500 to-indigo-600 hover:from-cyan-600 hover:to-indigo-700 text-white font-bold text-sm shadow-xl shadow-cyan-500/10 hover:shadow-cyan-500/20 transition-all duration-300 hover:-translate-y-1 active:translate-y-0"
                  >
                    <svg className="w-5 h-5 group-hover:scale-110 transition-transform duration-200" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
                    </svg>
                    Tải ảnh màn hình lên để bắt đầu
                    <div className="absolute inset-0 rounded-2xl bg-white/20 opacity-0 group-hover:opacity-100 transition-opacity duration-300"></div>
                  </button>
                </div>
              </div>

              {/* Step Process Display */}
              <div className="grid grid-cols-1 md:grid-cols-4 gap-6 pt-6">
                {[
                  {
                    step: '01',
                    title: 'Tải Ảnh Lên',
                    desc: 'Chọn file ảnh giao diện thiết kế từ local hoặc dán nhanh bằng Ctrl+V.',
                    color: 'border-cyan-100 text-cyan-500 bg-cyan-50/50'
                  },
                  {
                    step: '02',
                    title: 'AI Nhận Diện',
                    desc: 'AI quét thiết kế, phân loại các control và chuẩn hóa các kiểu dữ liệu sơ bộ.',
                    color: 'border-indigo-100 text-indigo-500 bg-indigo-50/50'
                  },
                  {
                    step: '03',
                    title: 'Làm Rõ Nghiệp Vụ',
                    desc: 'Trả lời các câu hỏi gợi ý từ AI để hoàn thiện quy tắc logic thực tế.',
                    color: 'border-amber-100 text-amber-500 bg-amber-50/50'
                  },
                  {
                    step: '04',
                    title: 'Tải Tài Liệu DOCX',
                    desc: 'Nhận bảng mô tả 6 cột chi tiết kết xuất dưới dạng file Word chuyên nghiệp.',
                    color: 'border-emerald-100 text-emerald-500 bg-emerald-50/50'
                  }
                ].map((s) => (
                  <div key={s.step} className="bg-white border border-slate-100 p-6 rounded-2xl shadow-sm space-y-4">
                    <span className={`w-8 h-8 rounded-lg flex items-center justify-center font-bold text-xs border ${s.color}`}>
                      {s.step}
                    </span>
                    <h4 className="font-bold text-slate-800 text-xs">{s.title}</h4>
                    <p className="text-[11px] text-slate-400 leading-normal">{s.desc}</p>
                  </div>
                ))}
              </div>
            </div>
          ) : (
            /* Active Analysis Session View */
            <div className="space-y-6 animate-fade-in max-w-6xl mx-auto">
              
              {/* Back to welcome */}
              <div className="flex items-center justify-between">
                <button
                  onClick={handleNewSession}
                  className="flex items-center gap-1.5 text-xs font-bold text-slate-400 hover:text-slate-600 transition-colors"
                >
                  <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 19l-7-7m0 0l7-7m-7 7h18" />
                  </svg>
                  Quay lại Trang chủ
                </button>
                <div className="flex items-center gap-2">
                  <span className="text-[10px] uppercase font-bold text-slate-400 font-mono bg-white border border-slate-200 px-2 py-0.5 rounded">
                    Session ID: {currentSession.id.slice(0, 18)}...
                  </span>
                </div>
              </div>

              {/* Side-by-side design layout */}
              <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
                
                {/* Left Side: Uploaded Image Visualizer */}
                <div className="lg:col-span-5 space-y-4">
                  <div className="bg-white border border-slate-200 rounded-2xl p-4 shadow-sm space-y-3">
                    <h3 className="text-xs font-bold text-slate-700 flex items-center gap-1.5 border-b border-slate-100 pb-2">
                      <svg className="w-4 h-4 text-cyan-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
                      </svg>
                      Ảnh UI Mockup Đang Phân Tích
                    </h3>
                    <div className="rounded-lg overflow-hidden border border-slate-100 bg-slate-50 flex items-center justify-center p-2 min-h-[220px]">
                      <img
                        src={getImageUrl(currentSession.image_path)}
                        alt="Workspace Screenshot"
                        className="max-h-[380px] w-auto object-contain rounded-md shadow-sm border border-slate-150/40 hover:scale-[1.02] transition-transform duration-300"
                        onError={(e) => {
                          // Fallback if local server static files URL format needs fallback
                          console.log("Image loading error fallback path triggered");
                        }}
                      />
                    </div>
                    {currentSession.context && (
                      <div className="bg-slate-50 border border-slate-100 p-3 rounded-xl">
                        <p className="text-[10px] font-bold text-slate-400 uppercase tracking-wide">Bối cảnh nghiệp vụ:</p>
                        <p className="text-xs text-slate-600 mt-1 leading-normal font-medium">{currentSession.context}</p>
                      </div>
                    )}
                  </div>
                </div>

                {/* Right Side: Interactive AI Panel */}
                <div className="lg:col-span-7 space-y-6">
                  {(currentSession.status === 'awaiting_answers' || currentSession.status === 'waiting_user_answer') ? (
                    <QuestionPanel
                      questions={currentSession.questions || []}
                      onSubmit={handleAnswersSubmit}
                      submitting={submittingAnswers}
                    />
                  ) : (
                    <PreviewTable
                      sessionId={currentSession.id}
                      controls={currentSession.specification || []}
                      docxPath={currentSession.docx_path}
                      onDocxGenerated={handleDocxUpdate}
                    />
                  )}
                </div>

              </div>
            </div>
          )}
        </main>
      </div>

      {/* Screenshot paste and select overlay */}
      <UploadModal
        isOpen={isUploadOpen}
        onClose={() => setIsUploadOpen(false)}
        onUpload={handleUpload}
      />
    </div>
  );
}

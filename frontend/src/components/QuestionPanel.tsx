'use client';

import React, { useState, useEffect } from 'react';
import { QuestionItem } from '../utils/api';

interface QuestionPanelProps {
  questions: QuestionItem[];
  onSubmit: (answers: { id: string; answer: string }[], autoGenerate: boolean) => void;
  submitting: boolean;
}

export default function QuestionPanel({ questions, onSubmit, submitting }: QuestionPanelProps) {
  const [answers, setAnswers] = useState<Record<string, string>>({});
  const [autoGenerate, setAutoGenerate] = useState(false);

  // Initialize/reset answers when questions change
  useEffect(() => {
    const initialAnswers: Record<string, string> = {};
    questions.forEach((q) => {
      initialAnswers[q.id] = q.answer || '';
    });
    setAnswers(initialAnswers);
  }, [questions]);

  const handleAnswerChange = (id: string, value: string) => {
    setAnswers((prev) => ({
      ...prev,
      [id]: value,
    }));
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    
    // Package answers
    const answersList = Object.entries(answers)
      .filter(([_, val]) => val.trim() !== '')
      .map(([id, val]) => ({
        id,
        answer: val.trim(),
      }));

    // If autoGenerate is false, and some questions are empty, warn or enforce answers
    const totalQuestions = questions.length;
    const answeredCount = answersList.length;

    if (!autoGenerate && answeredCount < totalQuestions) {
      const confirmProceed = window.confirm(
        `Bạn mới chỉ trả lời ${answeredCount}/${totalQuestions} câu hỏi. ` +
        `Bạn có muốn tiếp tục gửi không? Những câu hỏi chưa trả lời sẽ không được tinh chỉnh đặc tả.`
      );
      if (!confirmProceed) return;
    }

    onSubmit(answersList, autoGenerate);
  };

  if (!questions || questions.length === 0) return null;

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 shadow-xl text-slate-100 space-y-6">
      {/* Panel Header */}
      <div className="flex items-start gap-3 pb-4 border-b border-slate-800">
        <div className="w-10 h-10 rounded-xl bg-amber-500/10 text-amber-400 border border-amber-500/20 flex items-center justify-center shrink-0">
          <svg className="w-5 h-5 animate-bounce" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8.228 9c.549-1.165 2.03-2 3.772-2 2.21 0 4 1.343 4 3 0 1.4-1.278 2.575-3.006 2.907-.542.104-.994.54-.994 1.093m0 3h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
        </div>
        <div>
          <h3 className="font-bold text-slate-100 text-sm">
            AI BA đang làm rõ một số điểm thiết kế màn hình
          </h3>
          <p className="text-[11px] text-slate-400 mt-0.5">
            Hãy trả lời các câu hỏi sau để AI hoàn thiện bảng đặc tả chi tiết nhất.
          </p>
        </div>
      </div>

      <form onSubmit={handleSubmit} className="space-y-4">
        {/* Questions list */}
        <div className="space-y-4 max-h-[380px] overflow-y-auto pr-1 scrollbar-thin scrollbar-thumb-slate-800">
          {questions.map((q, idx) => {
            const hasAnswer = (answers[q.id] || '').trim() !== '';
            
            return (
              <div
                key={q.id}
                className={`p-4 rounded-xl border transition-all duration-200 ${
                  hasAnswer
                    ? 'bg-slate-800/40 border-slate-700/80 shadow-inner'
                    : 'bg-slate-900/60 border-slate-800 hover:border-slate-700/60'
                }`}
              >
                {/* Question Label */}
                <div className="flex items-start gap-2.5 mb-2.5">
                  <span className={`text-[10px] uppercase font-mono font-bold px-2 py-0.5 rounded ${
                    hasAnswer
                      ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20'
                      : 'bg-amber-500/10 text-amber-400 border border-amber-500/20'
                  }`}>
                    Câu hỏi {idx + 1}
                  </span>
                  <p className="text-xs text-slate-200 font-bold leading-relaxed">
                    {q.question}
                  </p>
                </div>

                {/* Answer Area */}
                <textarea
                  value={answers[q.id] || ''}
                  onChange={(e) => handleAnswerChange(q.id, e.target.value)}
                  disabled={submitting}
                  placeholder="Ví dụ: Tối đa 255 ký tự, bắt buộc nhập, nếu bỏ trống báo lỗi 'Vui lòng điền thông tin...'"
                  className="w-full min-h-[64px] bg-slate-950 border border-slate-800 rounded-lg p-2.5 text-xs text-slate-300 placeholder-slate-600 focus:outline-none focus:border-cyan-500 focus:ring-1 focus:ring-cyan-500/30 resize-none transition-all duration-150"
                />
              </div>
            );
          })}
        </div>

        {/* AI Assumption Checkbox */}
        <div className="bg-slate-950/40 border border-slate-800/80 p-3.5 rounded-xl flex items-start gap-3 select-none">
          <input
            type="checkbox"
            id="chkAuto"
            checked={autoGenerate}
            onChange={(e) => setAutoGenerate(e.target.checked)}
            disabled={submitting}
            className="mt-1 h-4 w-4 rounded border-slate-800 bg-slate-950 text-cyan-500 focus:ring-cyan-500 focus:ring-offset-slate-900"
          />
          <label htmlFor="chkAuto" className="text-xs cursor-pointer">
            <p className="font-bold text-slate-200">
              Xác nhận tự động tạo theo giả định tối ưu của AI
            </p>
            <p className="text-[10px] text-slate-500 mt-0.5 leading-normal">
              Các câu hỏi bạn bỏ trống sẽ được AI tự đưa ra giả thiết nghiệp vụ tối ưu nhất (ví dụ: các ràng buộc mặc định, thông điệp lỗi tiêu chuẩn) và đưa vào bảng đặc tả.
            </p>
          </label>
        </div>

        {/* Submit Actions */}
        <div className="pt-2 flex items-center justify-end">
          <button
            type="submit"
            disabled={submitting}
            className={`w-full py-3 rounded-xl font-bold text-xs shadow-lg transition-all duration-300 flex items-center justify-center gap-2 ${
              submitting
                ? 'bg-slate-800 text-slate-500 cursor-not-allowed border border-slate-700/50 shadow-none'
                : 'bg-gradient-to-r from-amber-500 to-orange-500 hover:from-amber-600 hover:to-orange-600 text-white hover:shadow-orange-500/10 hover:-translate-y-0.5'
            }`}
          >
            {submitting ? (
              <>
                <svg className="animate-spin h-4 w-4 text-slate-500" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                </svg>
                <span>AI BA đang hoàn thiện bảng đặc tả...</span>
              </>
            ) : (
              <>
                <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                </svg>
                <span>Gửi câu trả lời & Cập nhật đặc tả</span>
              </>
            )}
          </button>
        </div>
      </form>
    </div>
  );
}

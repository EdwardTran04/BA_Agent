export interface QuestionItem {
  id: string;
  question: string;
  answer: string | null;
  answered: boolean;
}

export interface ControlSpec {
  STT: number;
  control_name: string;
  data_type: string;
  io: string;
  initial_value: string;
  description: string;
}

export interface SessionResponse {
  id: string;
  image_path: string;
  context: string | null;
  status: 'uploaded' | 'analyzing' | 'waiting_user_answer' | 'ready_to_generate' | 'docx_generated' | 'failed' | 'awaiting_answers' | 'completed';
  screen_name: string | null;
  module: string | null;
  screen_type: string | null;
  role: string | null;
  screen_summary: string | null;
  assumptions: Array<{ content: string; risk_level: 'high' | 'medium' | 'low' }> | null;
  ready_to_generate_docx: boolean;
  questions: QuestionItem[];
  specification: ControlSpec[];
  docx_path: string | null;
  created_at: string;
  updated_at: string;
}

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export const BA_API = {
  getApiUrl: () => API_BASE_URL,

  // 1. Analyze: upload screenshot + context
  analyzeScreen: async (file: File, context?: string): Promise<SessionResponse> => {
    const formData = new FormData();
    formData.append('file', file);
    if (context) {
      formData.append('context', context);
    }

    const response = await fetch(`${API_BASE_URL}/api/screen/analyze`, {
      method: 'POST',
      body: formData,
    });

    if (!response.ok) {
      const err = await response.json().catch(() => ({ detail: 'Failed to analyze screenshot' }));
      throw new Error(err.detail || 'Failed to analyze screenshot');
    }

    return response.json();
  },

  // 2. Answer Questions: submit user answers
  submitAnswers: async (
    sessionId: string,
    answers: { id: string; answer: string }[],
    autoGenerate = false
  ): Promise<SessionResponse> => {
    const response = await fetch(`${API_BASE_URL}/api/screen/answer-questions/${sessionId}`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ answers, auto_generate: autoGenerate }),
    });

    if (!response.ok) {
      const err = await response.json().catch(() => ({ detail: 'Failed to submit answers' }));
      throw new Error(err.detail || 'Failed to submit answers');
    }

    return response.json();
  },

  // 3. Preview: get current specifications table
  previewSpec: async (sessionId: string): Promise<ControlSpec[]> => {
    const response = await fetch(`${API_BASE_URL}/api/screen/preview/${sessionId}`);
    if (!response.ok) {
      throw new Error('Failed to load preview specifications');
    }
    return response.json();
  },

  // 4. Generate Word Document
  generateDocx: async (sessionId: string): Promise<SessionResponse> => {
    const response = await fetch(`${API_BASE_URL}/api/screen/generate-docx/${sessionId}`, {
      method: 'POST',
    });

    if (!response.ok) {
      throw new Error('Failed to generate Word document');
    }

    return response.json();
  },

  // 5. Download URL endpoint helper
  getDownloadUrl: (sessionId: string): string => {
    return `${API_BASE_URL}/api/screen/download/${sessionId}`;
  },

  // 6. View Single Session details
  getSession: async (sessionId: string): Promise<SessionResponse> => {
    const response = await fetch(`${API_BASE_URL}/api/screen/sessions/${sessionId}`);
    if (!response.ok) {
      throw new Error('Failed to load session details');
    }
    return response.json();
  },

  // 7. List History of all sessions
  listSessions: async (): Promise<SessionResponse[]> => {
    const response = await fetch(`${API_BASE_URL}/api/screen/sessions`);
    if (!response.ok) {
      throw new Error('Failed to fetch session history');
    }
    return response.json();
  },
};

# BA Agent AI - Screen-to-Spec MVP

**BA Agent AI** là hệ sinh thái thông minh giúp tự động hóa quy trình phân tích và viết tài liệu đặc tả màn hình. 

- **Dự án dùng để làm gì?**: Nhận diện ảnh chụp màn hình UI thiết kế, phân loại các control thành phần, làm rõ nghiệp vụ chưa rõ ràng bằng Q&A tương tác và xuất ra file Word đặc tả chuẩn kỹ thuật.
- **Giải quyết vấn đề gì?**: Khắc phục việc tốn hàng giờ của Business Analyst (BA) để nhập liệu thủ công danh sách điều khiển, tránh bỏ sót các trường dữ liệu và tự động làm giàu các ràng buộc nghiệp vụ (validation rules, default values).
- **Đối tượng sử dụng là ai?**: Business Analysts (BAs), Product Owners (POs), Developers, QAs, và Project Managers cần tài liệu hóa màn hình thiết kế nhanh chóng để bàn giao.

---

## 📋 Mục lục
- [Giới thiệu](#-giới-thiệu)
- [Tính năng](#-tính-năng)
- [Công nghệ sử dụng](#-công-nghệ-sử-dụng)
- [Cài đặt](#-cài-đặt)
- [Hướng dẫn sử dụng](#-hướng-dẫn-sử-dụng)
- [Cấu trúc dự án](#-cấu-trúc-dự-án)
- [API Documentation](#-api-documentation)
- [Roadmap](#-roadmap)
- [Đóng góp](#-đóng-góp)
- [License](#-license)
- [Liên hệ](#-liên-hệ)

---

## 🚀 Giới thiệu

Trong phát triển phần mềm, việc viết đặc tả giao diện (Screen Specification Document) là một nhiệm vụ lặp đi lặp lại và tốn nhiều công sức của BA. **BA Agent AI** giải quyết vấn đề này bằng cách tận dụng sức mạnh của AI Vision để "nhìn" bản vẽ thiết kế UI, tự động bóc tách các control, hỏi người dùng những logic chưa rõ (ví dụ: công thức lương, validation số điện thoại) và xuất ra file Word hoàn chỉnh.

> Hệ thống cung cấp cơ chế **Offline Mock Simulator** chạy ngay lập tức mà không cần điền API Key, giúp các lập trình viên có thể kiểm thử toàn bộ luồng nghiệp vụ cục bộ một cách dễ dàng trước khi tích hợp mô hình OpenAI hoặc Gemini thực tế.

---

## ✨ Tính năng

- **Tải ảnh linh hoạt**: Kéo thả tệp tin ảnh hoặc **dán ảnh trực tiếp từ Clipboard (`Ctrl+V`)** vào giao diện ứng dụng.
- **AI BA Vision Analyzer**: Nhận dạng thông minh các điều khiển tương tác (Textbox, Button, Table, Combobox, Toggle, v.v.).
- **Tương tác Q&A (Clarifying Questions)**: AI tự phát hiện các vùng nghiệp vụ mập mờ và đặt từ 3-5 câu hỏi trực quan để người dùng trả lời nhằm tinh chỉnh tài liệu.
- **Chuẩn hóa & Tự động Làm giàu Đặc tả**:
  - Tự động sắp xếp lại số thứ tự `STT` tuần tự từ 1.
  - Tự động đổi tên các control bị trùng lặp.
  - Tự động thêm logic nghiệp vụ mặc định nếu mô tả của AI quá ngắn (dưới 20 ký tự).
- **Xuất file DOCX Chuyên nghiệp**: Bảng đặc tả 6 cột gồm (*STT, Thành phần/ Control, Kiểu dữ liệu, Input/ Output, Giá trị khởi tạo, Mô tả chi tiết*) được định dạng với tone màu xanh teal hiện đại, hàng xen kẽ đổ bóng và căn lề rộng rãi.
- **Quản lý lịch sử**: Xem và tiếp tục xử lý các phiên phân tích cũ ngay trên Sidebar.

---

## 🛠 Công nghệ sử dụng

### Backend
- **Python / FastAPI**: Xây dựng API non-blocking hiệu năng cao.
- **SQLAlchemy ORM**: Giao tiếp database, tương thích tốt với SQLite và PostgreSQL.
- **Pydantic**: Xác thực và làm sạch dữ liệu đầu vào/đầu ra.
- **python-docx**: Tạo và định dạng nâng cao tệp Word (.docx) ở mức cấu trúc XML.
- **OpenAI SDK / Gemini REST API**: Tích hợp các mô hình ngôn ngữ lớn xử lý đa phương tiện.

### Frontend
- **React / Next.js (App Router)**: Framework xây dựng giao diện phía Client.
- **TypeScript**: Tăng tính an toàn và giảm lỗi trong quá trình phát triển.
- **Tailwind CSS**: Thiết kế giao diện responsive sang trọng, hỗ trợ micro-animations và tùy chỉnh scrollbar.

### Database
- **SQLite** (mặc định để chạy local nhanh chóng).
- **PostgreSQL** (chỉ cần đổi cấu hình `DATABASE_URL` để triển khai sản xuất).

---

## ⚙️ Cài đặt

### Yêu cầu hệ thống
- **Python** >= 3.10
- **Node.js** >= 18.0
- **NPM** >= 9.0

### Clone source
```bash
git clone https://github.com/your-username/ba-agent.git
cd ba-agent
```

### 1. Cấu hình & Chạy Backend (FastAPI)
Di chuyển vào thư mục backend:
```bash
cd backend
```

Cài đặt các thư viện Python:
```bash
pip install -r requirements.txt
```

Cấu hình môi trường (Tạo file `.env` trong thư mục `backend/`):
```env
# URL Kết nối Database (Mặc định SQLite local)
DATABASE_URL=sqlite:///./ba_agent.db

# Cấu hình AI Provider (Lựa chọn: openai / gemini)
AI_PROVIDER=openai

# Điền key để kích hoạt AI thực tế (Bỏ trống nếu muốn chạy Mock Simulator cục bộ)
OPENAI_API_KEY=your-openai-key
OPENAI_MODEL=gpt-4o

GEMINI_API_KEY=your-gemini-key
GEMINI_MODEL=gemini-1.5-flash
```

Khởi chạy server FastAPI:
```bash
fastapi dev app/main.py
```
*API sẽ chạy tại địa chỉ: `http://localhost:8000`*

### 2. Cấu hình & Chạy Frontend (Next.js)
Mở một terminal mới và di chuyển vào thư mục frontend:
```bash
cd frontend
```

Cài đặt các gói npm:
```bash
npm install
```

Cấu hình môi trường (Tạo file `.env.local` trong thư mục `frontend/`):
```env
# Địa chỉ kết nối đến Backend FastAPI
NEXT_PUBLIC_API_URL=http://localhost:8000
```

Khởi chạy ứng dụng Next.js:
```bash
npm run dev
```
*Giao diện người dùng sẽ chạy tại địa chỉ: `http://localhost:3000`*

---

## 🖥️ Hướng dẫn sử dụng

1. **Truy cập Giao diện**: Mở trình duyệt truy cập `http://localhost:3000`. Bạn sẽ thấy thông báo trạng thái "Backend Online" ở góc trên bên phải.
2. **Tải lên Thiết kế**: 
   - Click nút **Phân tích màn hình mới**.
   - Kéo thả tệp ảnh thiết kế vào vùng tải lên, hoặc click chọn ảnh, hoặc copy ảnh và nhấn `Ctrl+V` để dán.
   - Nhập bối cảnh nghiệp vụ của màn hình này (nếu có) vào ô văn bản bên dưới và bấm **Bắt đầu phân tích**.
3. **Trả lời câu hỏi BA**:
   - Hệ thống hiển thị ảnh thiết kế ở bên trái và danh sách câu hỏi nghiệp vụ do AI tạo ở bên phải.
   - Nhập câu trả lời làm rõ nghiệp vụ cho từng câu hỏi.
   - (Tùy chọn) Chọn ô **Xác nhận tự động tạo theo giả định tối ưu của AI** để tự động hoàn thiện các trường bỏ trống.
   - Bấm **Gửi câu trả lời & Cập nhật đặc tả**.
4. **Xem trước & Tải báo cáo**:
   - Hệ thống sẽ trả về bảng đặc tả 6 cột hoàn chỉnh.
   - Rà soát bảng dữ liệu và bấm **Xuất báo cáo DOCX**.
   - Bấm **Tải file Word (.docx)** để lưu tài liệu đặc tả được định dạng chuyên nghiệp về máy.

---

## 📂 Cấu trúc dự án

```
project-root/
├── backend/                  # Mã nguồn Python Backend
│   ├── app/
│   │   ├── services/
│   │   │   ├── ai_service.py # Xử lý tích hợp OpenAI/Gemini/Mock
│   │   │   ├── validator.py  # Chuẩn hóa & làm giàu dữ liệu đặc tả
│   │   │   └── docx_gen.py   # Xuất và định dạng bảng tài liệu Word XML
│   │   ├── config.py         # Đọc cấu hình từ .env
│   │   ├── database.py       # Cấu hình DB ORM và model sessions
│   │   ├── main.py           # Định nghĩa router và static mounts
│   │   └── schemas.py        # Định nghĩa các kiểu dữ liệu Pydantic
│   ├── uploads/              # Nơi lưu trữ ảnh tải lên và file DOCX kết xuất
│   ├── requirements.txt      # Khai báo thư viện Python
│   └── test_backend.py       # Kịch bản chạy thử nghiệm backend cục bộ
│
└── frontend/                 # Mã nguồn React/Next.js Frontend
    ├── src/
    │   ├── app/              # Các routes và cấu hình CSS
    │   │   ├── globals.css   # Tùy chỉnh scrollbar và hiệu ứng chuyển động
    │   │   └── page.tsx      # Giao diện chính của Dashboard
    │   ├── components/       # Các React components tái sử dụng
    │   │   ├── Sidebar.tsx   # Thanh điều hướng và lịch sử phân tích
    │   │   ├── Header.tsx    # Header trạng thái kết nối backend
    │   │   ├── UploadModal.tsx# Hộp thoại tải ảnh, kéo thả, paste clipboard
    │   │   ├── QuestionPanel.tsx# Khối nhập câu trả lời nghiệp vụ
    │   │   └── PreviewTable.tsx# Bảng đặc tả và nút download DOCX
    │   └── utils/
    │       └── api.ts        # Client kết nối API Backend
```

---

## 🔌 API Documentation

### 1. Phân tích ảnh lần đầu
- **Endpoint**: `POST /api/screen/analyze`
- **Content-Type**: `multipart/form-data`
- **Request Body**:
  - `file`: Tệp ảnh dạng binary (PNG, JPG, JPEG, WEBP)
  - `context`: Chuỗi text nghiệp vụ bổ sung (Tùy chọn)
- **Response**: Trả về thông tin Session mới tạo kèm danh sách câu hỏi làm rõ.

### 2. Gửi câu trả lời tinh chỉnh đặc tả
- **Endpoint**: `POST /api/screen/answer-questions/{session_id}`
- **Request Body**:
  ```json
  {
    "answers": [
      {
        "id": "q1",
        "answer": "Mức lương tối thiểu là 5,000,000đ"
      }
    ],
    "auto_generate": true
  }
  ```
- **Response**: Trả về dữ liệu đặc tả chi tiết đã tinh chỉnh của Session.

### 3. Xuất báo cáo tài liệu Word
- **Endpoint**: `POST /api/screen/generate-docx/{session_id}`
- **Response**: Tạo file `.docx` vật lý trên server và trả về thông tin đường dẫn.

### 4. Tải file Word về máy
- **Endpoint**: `GET /api/screen/download/{session_id}`
- **Response**: Trả về file tải xuống trực tiếp dạng attachment binary.

---

## 📸 Demo

### Luồng Nghiệp Vụ Chính
```
[Tải ảnh UI lên & Ghi Context] ──> [AI phân tích & sinh Câu hỏi]
                                                │
[Tải file DOCX đặc tả 6 cột]  <── [Người dùng trả lời Q&A]
```

*(Hình ảnh Demo giao diện Dashboard và file Word đặc tả sẽ được cập nhật tại đây)*

---

## 🗺️ Roadmap

- **Version 1.0 (MVP - Hiện tại)**
  - [x] Đăng tải thiết kế bằng cách Chọn file / Dán ảnh Clipboard.
  - [x] Tích hợp AI Vision (OpenAI, Gemini) nhận diện control.
  - [x] Hệ thống Q&A tương tác tinh chỉnh tài liệu đặc tả.
  - [x] Tự động chuẩn hóa dữ liệu đầu vào.
  - [x] Kết xuất tệp Word (.docx) định dạng chuyên nghiệp.
- **Version 2.0 (Kế hoạch)**
  - Cải tiến việc đặt câu hỏi (như thế nào là hợp lí và đúng trọng tâm)
  - Tích hợp thêm Stitch hỗ trợ tạo giao diện
  - Tích hợp thêm Skill nhằm hỗ trợ việc list danh sách Usecase tổng hợp vấn đề


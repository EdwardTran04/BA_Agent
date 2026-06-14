from pydantic import BaseModel, Field
from typing import List, Optional, Any
from datetime import datetime
from enum import Enum


# ──────────────────────────────────────────────
# Enums
# ──────────────────────────────────────────────

class ScreenType(str, Enum):
    CREATE = "Create"
    EDIT = "Edit"
    VIEW = "View"
    SEARCH = "Search"
    APPROVAL = "Approval"
    REPORT = "Report"
    UNKNOWN = "Unknown"


class QuestionPriority(str, Enum):
    CRITICAL = "critical"
    IMPORTANT = "important"
    OPTIONAL = "optional"


class RiskLevel(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class ControlSource(str, Enum):
    VISIBLE = "visible"
    INFERRED = "inferred"
    USER_CONFIRMED = "user_confirmed"


# ──────────────────────────────────────────────
# Clarifying Question Schema
# ──────────────────────────────────────────────

class ClarifyingQuestion(BaseModel):
    id: str
    priority: str = "important"  # critical | important | optional
    question: str
    reason: Optional[str] = None
    affected_controls: Optional[List[str]] = []
    answer: Optional[str] = None
    answered: bool = False


# ──────────────────────────────────────────────
# Assumption Schema
# ──────────────────────────────────────────────

class Assumption(BaseModel):
    content: str
    risk_level: str = "medium"  # high | medium | low


# ──────────────────────────────────────────────
# Control Row Schema (extended with quality fields)
# ──────────────────────────────────────────────

class ControlRow(BaseModel):
    STT: int = Field(..., description="Số thứ tự")
    control_name: str = Field(..., description="Thành phần/ Control")
    data_type: str = Field(..., description="Kiểu dữ liệu")
    io: str = Field(..., description="Input/ Output")
    initial_value: str = Field(..., description="Giá trị khởi tạo")
    description: str = Field(..., description="Mô tả chi tiết")
    control_type: Optional[str] = Field(None, description="Loại control nghiệp vụ")
    confidence: Optional[float] = Field(None, description="Độ tin cậy (0.0 - 1.0)")
    source: Optional[str] = Field("visible", description="visible | inferred | user_confirmed")

    class Config:
        populate_by_name = True


# ──────────────────────────────────────────────
# Request Schemas
# ──────────────────────────────────────────────

class QuestionAnswer(BaseModel):
    id: str
    answer: str


class AnswerQuestionsRequest(BaseModel):
    answers: List[QuestionAnswer]
    auto_generate: Optional[bool] = False  # If true, auto-fills unanswered with AI assumptions


# ──────────────────────────────────────────────
# Session Response Schema
# ──────────────────────────────────────────────

class SessionResponse(BaseModel):
    id: str
    image_path: str
    screen_name: Optional[str] = None
    module: Optional[str] = None
    screen_type: Optional[str] = None
    role: Optional[str] = None
    context: Optional[str] = None
    screen_summary: Optional[str] = None
    status: str
    ready_to_generate_docx: bool = False
    questions: Optional[List[ClarifyingQuestion]] = []
    assumptions: Optional[List[Assumption]] = []
    specification: Optional[List[ControlRow]] = []
    docx_path: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

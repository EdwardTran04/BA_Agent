import logging
from typing import Tuple

logger = logging.getLogger("ba_agent.validator")


class SpecValidator:
    """
    Validates the full AI-generated spec JSON according to the plan's rules:
    - Schema completeness
    - STT sequential from 1
    - No duplicate controls
    - IO must be Input/Output/Input/Output
    - Data type not empty
    - Initial value not meaninglessly empty
    - Description not too short
    - Critical questions check
    """

    VALID_IO_VALUES = {"Input", "Output", "Input/Output"}
    VALID_SCREEN_TYPES = {"Create", "Edit", "View", "Search", "Approval", "Report", "Unknown"}
    VALID_PRIORITIES = {"critical", "important", "optional"}
    VALID_RISK_LEVELS = {"high", "medium", "low"}
    VALID_SOURCES = {"visible", "inferred", "user_confirmed"}

    @classmethod
    def validate_full_spec(cls, spec: dict) -> Tuple[dict, list]:
        """
        Validates and cleans the full spec JSON.
        Returns: (cleaned_spec, list_of_warnings)
        """
        warnings = []

        if not spec or not isinstance(spec, dict):
            logger.warning("Empty or invalid spec received for validation.")
            return {}, ["Spec JSON rỗng hoặc không hợp lệ."]

        # ── Validate top-level fields ──
        if not spec.get("screen_name"):
            spec["screen_name"] = "[Chưa xác định]"
            warnings.append("screen_name trống, đã gán mặc định.")

        screen_type = spec.get("screen_type", "Unknown")
        if screen_type not in cls.VALID_SCREEN_TYPES:
            spec["screen_type"] = "Unknown"
            warnings.append(f"screen_type '{screen_type}' không hợp lệ, đã gán Unknown.")

        if not spec.get("screen_summary"):
            spec["screen_summary"] = "[Chưa có tóm tắt]"
            warnings.append("screen_summary trống.")

        # ── Validate clarifying_questions ──
        questions = spec.get("clarifying_questions", [])
        if not isinstance(questions, list):
            questions = []
        cleaned_questions = []
        for q in questions:
            if not isinstance(q, dict):
                continue
            cq = {
                "id": q.get("id", f"Q{len(cleaned_questions) + 1}"),
                "priority": q.get("priority", "important"),
                "question": q.get("question", ""),
                "reason": q.get("reason", ""),
                "affected_controls": q.get("affected_controls", []),
                "answer": q.get("answer"),
                "answered": q.get("answered", False),
            }
            if cq["priority"] not in cls.VALID_PRIORITIES:
                cq["priority"] = "important"
            if cq["question"]:
                cleaned_questions.append(cq)
        spec["clarifying_questions"] = cleaned_questions

        # ── Validate assumptions ──
        assumptions = spec.get("assumptions", [])
        if not isinstance(assumptions, list):
            assumptions = []
        cleaned_assumptions = []
        for a in assumptions:
            if not isinstance(a, dict):
                continue
            ca = {
                "content": a.get("content", ""),
                "risk_level": a.get("risk_level", "medium"),
            }
            if ca["risk_level"] not in cls.VALID_RISK_LEVELS:
                ca["risk_level"] = "medium"
            if ca["content"]:
                cleaned_assumptions.append(ca)
        spec["assumptions"] = cleaned_assumptions

        # ── Validate and clean rows (controls) ──
        raw_rows = spec.get("rows", [])
        if not isinstance(raw_rows, list):
            raw_rows = []
        cleaned_rows = cls.validate_and_clean_rows(raw_rows, warnings)
        spec["rows"] = cleaned_rows

        # ── Determine ready_to_generate_docx ──
        has_critical_unanswered = any(
            q.get("priority") == "critical" and not q.get("answered", False)
            for q in spec.get("clarifying_questions", [])
        )
        if has_critical_unanswered:
            spec["ready_to_generate_docx"] = False

        logger.info(f"Validation complete: {len(cleaned_rows)} rows, {len(warnings)} warnings.")
        return spec, warnings

    @classmethod
    def validate_and_clean_rows(cls, raw_rows: list, warnings: list = None) -> list:
        """
        Validates the control rows list and cleans up data:
        1. Ensures 6+2 fields exist.
        2. Sequential STT starting from 1.
        3. De-duplicates control names.
        4. Normalizes IO values.
        5. Validates data_type not empty.
        6. Marks unclear initial_value with [Cần xác nhận].
        7. Enriches descriptions that are too sparse.
        """
        if warnings is None:
            warnings = []

        if not raw_rows or not isinstance(raw_rows, list):
            return []

        cleaned = []
        seen_names = {}

        for index, item in enumerate(raw_rows):
            if not isinstance(item, dict):
                continue

            stt = index + 1

            # ── Control name ──
            raw_name = (
                item.get("control_name")
                or item.get("thanh_phan_control")
                or item.get("Thành phần/ Control")
                or item.get("name")
                or f"Control_{stt}"
            )
            raw_name = str(raw_name).strip()

            if raw_name in seen_names:
                seen_names[raw_name] += 1
                control_name = f"{raw_name} ({seen_names[raw_name]})"
                warnings.append(f"Control trùng tên '{raw_name}', đã thêm suffix.")
            else:
                seen_names[raw_name] = 1
                control_name = raw_name

            # ── Data type ──
            data_type = (
                item.get("data_type")
                or item.get("kieu_du_lieu")
                or item.get("Kiểu dữ liệu")
                or ""
            )
            data_type = str(data_type).strip()
            if not data_type:
                data_type = "String"
                warnings.append(f"STT {stt} '{control_name}': data_type trống, gán mặc định 'String'.")

            # ── IO ──
            io = (
                item.get("io")
                or item.get("input_output")
                or item.get("Input/ Output")
                or "Input"
            )
            io = str(io).strip()
            io_map = {
                "i": "Input", "input": "Input", "in": "Input",
                "o": "Output", "output": "Output", "out": "Output",
                "io": "Input/Output", "input/output": "Input/Output",
                "i/o": "Input/Output", "input / output": "Input/Output",
            }
            io = io_map.get(io.lower(), io)
            if io not in cls.VALID_IO_VALUES:
                warnings.append(f"STT {stt} '{control_name}': io '{io}' không hợp lệ, gán 'Input'.")
                io = "Input"

            # ── Initial value ──
            initial_value = (
                item.get("initial_value")
                or item.get("gia_tri_khoi_tao")
                or item.get("Giá trị khởi tạo")
                or ""
            )
            initial_value = str(initial_value).strip()
            if not initial_value or initial_value.lower() in ["none", "null", "n/a", ""]:
                initial_value = "Rỗng"

            # ── Description ──
            description = (
                item.get("description")
                or item.get("mo_ta_chi_tiet")
                or item.get("Mô tả chi tiết")
                or ""
            )
            description = str(description).strip()

            if len(description) < 30:
                ctrl_lower = data_type.lower()
                if "button" in ctrl_lower or "nút" in control_name.lower():
                    description = (
                        f"{description or 'Nút thao tác.'} "
                        "Khi click, validate dữ liệu đầu vào, hiển thị loading chặn click đúp, "
                        "gửi request lên backend. [Cần xác nhận] hành vi chi tiết."
                    )
                elif any(k in ctrl_lower for k in ["string", "text", "input"]):
                    description = (
                        f"{description or 'Trường nhập liệu.'} "
                        "Độ dài tối đa 255 ký tự. Trim khoảng trắng thừa. "
                        "[Cần xác nhận] độ dài tối đa và validation rules."
                    )
                elif any(k in ctrl_lower for k in ["date", "ngày"]):
                    description = (
                        f"{description or 'Chọn ngày tháng.'} "
                        "Định dạng DD/MM/YYYY. Chọn qua lịch popup hoặc gõ tay. "
                        "[Cần xác nhận] ràng buộc ngày."
                    )
                elif any(k in ctrl_lower for k in ["dropdown", "option", "select"]):
                    description = (
                        f"{description or 'Lựa chọn giá trị.'} "
                        "Chọn 1 giá trị từ danh sách. Hỗ trợ tìm kiếm nhanh nếu > 10 phần tử. "
                        "[Cần xác nhận] data source."
                    )
                else:
                    description = (
                        f"{description or 'Mô tả chi tiết.'} "
                        "[Cần xác nhận] behavior và validation rules chi tiết."
                    )
                warnings.append(f"STT {stt} '{control_name}': description quá ngắn, đã bổ sung.")

            # ── Control type ──
            control_type = item.get("control_type") or item.get("loai_control") or item.get("Loại control") or None
            if control_type:
                control_type = str(control_type).strip()

            # ── Confidence & Source ──
            confidence = item.get("confidence")
            if confidence is not None:
                try:
                    confidence = float(confidence)
                    confidence = max(0.0, min(1.0, confidence))
                except (ValueError, TypeError):
                    confidence = 0.5

            source = item.get("source", "visible")
            if source not in cls.VALID_SOURCES:
                source = "visible"

            cleaned.append({
                "STT": stt,
                "control_name": control_name,
                "data_type": data_type,
                "io": io,
                "initial_value": initial_value,
                "description": description,
                "control_type": control_type,
                "confidence": confidence,
                "source": source,
            })

        logger.info(f"Validated and cleaned {len(cleaned)} control rows.")
        return cleaned

    @classmethod
    def can_generate_official_docx(cls, spec: dict) -> Tuple[bool, str]:
        """
        Checks if the spec is ready for official DOCX generation.
        Returns (can_generate, reason).
        """
        questions = spec.get("clarifying_questions", [])
        critical_unanswered = [
            q for q in questions
            if q.get("priority") == "critical" and not q.get("answered", False)
        ]

        if critical_unanswered:
            return False, (
                f"Còn {len(critical_unanswered)} câu hỏi critical chưa được trả lời. "
                "Chỉ có thể tạo bản nháp (draft)."
            )

        rows = spec.get("rows", [])
        if not rows:
            return False, "Chưa có control nào được nhận diện."

        return True, "Đặc tả đủ điều kiện tạo DOCX chính thức."

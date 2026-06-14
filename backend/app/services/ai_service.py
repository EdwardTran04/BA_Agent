import base64
import json
import logging
import httpx
from app.config import config

logger = logging.getLogger("ba_agent.ai_service")


class AIService:

    @staticmethod
    def encode_image(image_path: str) -> str:
        """Encodes a local image to base64 string."""
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode("utf-8")

    # ──────────────────────────────────────────────
    # Stage 1: Initial Screenshot Analysis
    # ──────────────────────────────────────────────

    @classmethod
    def analyze_screenshot(cls, image_path: str, context: str = "",
                           screen_name: str = "", module: str = "",
                           screen_type: str = "", role: str = "") -> dict:
        """
        Stage 1: Analyzes screenshot, detects controls, generates clarifying questions.
        Returns the full extended spec JSON.
        """
        base64_image = cls.encode_image(image_path)

        system_prompt = cls._build_stage1_prompt()

        context_parts = []
        if screen_name:
            context_parts.append(f"Tên màn hình: {screen_name}")
        if module:
            context_parts.append(f"Module: {module}")
        if screen_type and screen_type != "Unknown":
            context_parts.append(f"Loại màn hình: {screen_type}")
        if role:
            context_parts.append(f"Role người dùng: {role}")
        if context:
            context_parts.append(f"Bối cảnh nghiệp vụ bổ sung: {context}")

        context_str = "\n".join(context_parts) if context_parts else "Không có thông tin bổ sung."

        user_prompt = f"Phân tích thiết kế màn hình này.\n\nThông tin bổ sung từ User:\n{context_str}"

        logger.info(f"Stage 1: Calling AI Vision for initial analysis...")

        if config.AI_PROVIDER == "gemini" and config.GEMINI_API_KEY:
            try:
                return cls._call_gemini_vision(system_prompt, user_prompt, base64_image)
            except Exception as gemini_err:
                if config.OPENROUTER_API_KEY_STAGE2:
                    logger.warning(
                        f"Native Gemini API failed with: {str(gemini_err)}. "
                        "Attempting automatic fallback to OpenRouter Stage 2 model..."
                    )
                    try:
                        # Fallback to the same gemini model on OpenRouter using Stage 2 key
                        return cls._call_openrouter_api(
                            api_key=config.OPENROUTER_API_KEY_STAGE2,
                            model="google/gemini-2.5-flash",
                            system_prompt=system_prompt,
                            user_prompt=user_prompt,
                            base64_image=base64_image
                        )
                    except Exception as or_err:
                        logger.error(f"OpenRouter Stage 2 fallback also failed: {str(or_err)}")
                        raise gemini_err
                else:
                    raise gemini_err
        elif config.AI_PROVIDER == "openai" and config.OPENAI_API_KEY:
            return cls._call_openai_vision(system_prompt, user_prompt, base64_image)
        else:
            logger.warning("No API key configured. Falling back to offline mock service.")
            return cls._generate_mock_analysis(context)

    # ──────────────────────────────────────────────
    # Stage 2: Refine Specification After User Answers
    # ──────────────────────────────────────────────

    @classmethod
    def refine_specification(cls, image_path: str, previous_spec: dict, user_answers: list) -> dict:
        """
        Stage 2: Receives previous spec + user answers, returns updated spec.
        May return new clarifying questions if critical gaps remain.
        """
        base64_image = cls.encode_image(image_path)

        system_prompt = cls._build_stage2_prompt()

        answers_str = "\n".join([
            f"- Câu hỏi (ID: {item['id']}): {item['question']}\n  Trả lời từ User: {item['answer']}"
            for item in user_answers
        ])

        user_prompt = (
            f"Dưới đây là kết quả phân tích trước đó:\n"
            f"```json\n{json.dumps(previous_spec, ensure_ascii=False, indent=2)}\n```\n\n"
            f"Dưới đây là câu trả lời của User:\n{answers_str}\n\n"
            f"Hãy cập nhật lại đặc tả màn hình theo hướng dẫn trong system prompt."
        )

        logger.info(f"Stage 2: Calling AI Vision for spec refinement...")

        if config.OPENROUTER_API_KEY_STAGE2:
            return cls._call_openrouter_api(
                api_key=config.OPENROUTER_API_KEY_STAGE2,
                model=config.OPENROUTER_MODEL_STAGE2,
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                base64_image=base64_image
            )
        elif config.AI_PROVIDER == "gemini" and config.GEMINI_API_KEY:
            return cls._call_gemini_vision(system_prompt, user_prompt, base64_image)
        elif config.AI_PROVIDER == "openai" and config.OPENAI_API_KEY:
            return cls._call_openai_vision(system_prompt, user_prompt, base64_image)
        else:
            logger.warning("No API key configured. Falling back to offline mock refinement.")
            return cls._generate_mock_refinement(previous_spec, user_answers)

    # ──────────────────────────────────────────────
    # Stage 3: QA Validation Before DOCX
    # ──────────────────────────────────────────────

    @classmethod
    def qa_check_specification(cls, image_path: str, spec: dict) -> dict:
        """
        Stage 3: QA review of the spec before generating DOCX.
        Returns corrected spec JSON.
        """
        base64_image = cls.encode_image(image_path)

        system_prompt = cls._build_stage3_prompt()

        user_prompt = (
            f"Hãy kiểm tra lại bảng mô tả control trước khi tạo DOCX:\n\n"
            f"```json\n{json.dumps(spec, ensure_ascii=False, indent=2)}\n```\n\n"
            f"Trả về JSON đã chỉnh sửa theo hướng dẫn trong system prompt."
        )

        logger.info(f"Stage 3: Calling AI for QA validation...")

        if config.OPENROUTER_API_KEY_STAGE3:
            return cls._call_openrouter_api(
                api_key=config.OPENROUTER_API_KEY_STAGE3,
                model=config.OPENROUTER_MODEL_STAGE3,
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                base64_image=base64_image
            )
        elif config.AI_PROVIDER == "gemini" and config.GEMINI_API_KEY:
            return cls._call_gemini_vision(system_prompt, user_prompt, base64_image)
        elif config.AI_PROVIDER == "openai" and config.OPENAI_API_KEY:
            return cls._call_openai_vision(system_prompt, user_prompt, base64_image)
        else:
            logger.warning("No API key configured. Skipping QA check.")
            return spec

    # ══════════════════════════════════════════════
    # PROMPT BUILDERS
    # ══════════════════════════════════════════════

    @staticmethod
    def _build_common_ba_control_rules() -> str:
        """Common BA rules for screen specification."""
        return (
            "Bạn là Senior Business Analyst chuyên phân tích thiết kế màn hình phần mềm "
            "và viết đặc tả chi tiết để Dev, QA, UI/UX Designer có thể triển khai mà hạn chế phải hỏi lại BA.\n\n"

            "## Mục tiêu chính:\n"
            "Từ ảnh thiết kế màn hình và context người dùng cung cấp, hãy tạo đặc tả màn hình theo từng "
            "THÀNH PHẦN NGHIỆP VỤ / LOGICAL BUSINESS CONTROL, không mô tả theo từng UI element vật lý rời rạc.\n\n"

            "## Nguyên tắc cực kỳ quan trọng về cách tách control:\n"
            "1. Một dòng trong bảng mô tả phải tương ứng với một logical business control.\n"
            "2. Không được tách label, input, placeholder, icon, đơn vị tính, dấu hai chấm, helper text thành các control riêng "
            "nếu chúng thuộc cùng một field nghiệp vụ.\n"
            "3. Label chỉ là một thuộc tính của control chính, không phải một control riêng, trừ khi label/text đó là thành phần độc lập.\n\n"

            "Ví dụ đúng:\n"
            "- Màn hình hiển thị 'Tên người dùng: [input]' thì chỉ tạo 1 dòng: 'Trường nhập Tên người dùng'.\n"
            "- Màn hình hiển thị 'Email: [input]' thì chỉ tạo 1 dòng: 'Trường nhập Email'.\n"
            "- Màn hình hiển thị 'Trạng thái: [dropdown]' thì chỉ tạo 1 dòng: 'Dropdown Trạng thái'.\n"
            "- Màn hình hiển thị 'Ngày sinh: [date picker]' thì chỉ tạo 1 dòng: 'Date picker Ngày sinh'.\n"
            "- Màn hình hiển thị checkbox kèm nhãn 'Đồng ý điều khoản' thì chỉ tạo 1 dòng: 'Checkbox Đồng ý điều khoản'.\n"
            "- Màn hình hiển thị 'Tổng tiền: 1.000.000 VND' ở dạng chỉ đọc thì chỉ tạo 1 dòng: 'Trường hiển thị Tổng tiền'.\n\n"

            "Ví dụ sai:\n"
            "- Label Tên người dùng\n"
            "- Input Tên người dùng\n"
            "- Placeholder Tên người dùng\n"
            "- Icon calendar\n"
            "- Dấu hai chấm\n\n"

            "## Khi nào text/label được coi là control riêng:\n"
            "Chỉ tạo dòng riêng cho text/label nếu nó là thành phần độc lập, ví dụ:\n"
            "- Tiêu đề màn hình.\n"
            "- Tiêu đề section hoặc group box.\n"
            "- Tab name.\n"
            "- Breadcrumb.\n"
            "- Alert, warning, success message, error banner.\n"
            "- Text hướng dẫn độc lập không gắn trực tiếp với một field cụ thể.\n"
            "- Badge trạng thái nghiệp vụ độc lập.\n"
            "- Link điều hướng độc lập.\n\n"

            "## Quy tắc phân loại Input/Output:\n"
            "- Input: control cho phép người dùng nhập, chọn, upload, tick, search, click để thực hiện hành động.\n"
            "- Output: control chỉ hiển thị dữ liệu, trạng thái, kết quả tính toán, kết quả truy vấn hoặc thông tin read-only.\n"
            "- Input/Output: control vừa hiển thị dữ liệu vừa cho phép thao tác, ví dụ editable grid, file upload list có xóa file, table có inline edit.\n\n"

            "## Nguyên tắc mô tả chi tiết:\n"
            "1. Với control dạng Input hoặc Input/Output, phần mô tả chi tiết phải rất kỹ.\n"
            "2. Với control dạng Output thuần túy, không cần mô tả các rule chỉ dành cho nhập liệu như min length, max length, required input, ký tự đặc biệt, trim space, v.v. "
            "Thay vào đó hãy mô tả nguồn dữ liệu, format hiển thị, điều kiện hiển thị, thời điểm cập nhật, trạng thái empty/error nếu có.\n"
            "3. Không được tự bịa rule nghiệp vụ nếu ảnh hoặc câu trả lời của user không cung cấp.\n"
            "4. Nếu không chắc chắn, ghi rõ [Cần xác nhận: ...] trong mô tả chi tiết hoặc đưa vào clarifying_questions nếu là điểm quan trọng.\n"
            "5. Các rule đã được user xác nhận thì được coi là thông tin chính thức.\n\n"

            "## Checklist chung cho mọi control:\n"
            "Mỗi control nên được mô tả theo các nhóm thông tin sau, tùy loại control mà áp dụng:\n"
            "- Mục đích nghiệp vụ: control tồn tại để làm gì.\n"
            "- Business Rule: quy tắc nghiệp vụ liên quan.\n"
            "- Validation Rule: điều kiện hợp lệ và điều kiện lỗi.\n"
            "- Permission: ai được xem, ai được nhập/sửa/xóa/thực hiện.\n"
            "- UI State: normal, disabled, loading, empty, error, readonly nếu có.\n"
            "- API Mapping: field frontend, field backend, data type, required nếu biết.\n"
            "- Acceptance Criteria: Given/When/Then cho các hành vi quan trọng.\n\n"

            "## Cách viết mô tả chi tiết trong một dòng control:\n"
            "Phần mô tả chi tiết nên viết có cấu trúc, không viết một câu chung chung. "
            "Ưu tiên format dạng nhiều ý ngắn như sau:\n"
            "- Mục đích: ...\n"
            "- Hiển thị: Label = ..., Placeholder = ...\n"
            "- Dữ liệu: Kiểu dữ liệu = ..., Giá trị mặc định = ...\n"
            "- Validation: ...\n"
            "- Business rule: ...\n"
            "- Permission: ...\n"
            "- UI state: ...\n"
            "- API mapping: FE field = ..., BE field = ...\n"
            "- Acceptance criteria: AC01 ..., AC02 ...\n"
            "- Cần xác nhận: ...\n\n"

            "## Quy tắc mô tả theo từng loại control nghiệp vụ:\n\n"

            "### 1. Textbox / Input Field\n"
            "Áp dụng cho các field như: Họ tên, Email, Số điện thoại, Mã khách hàng, Tên đăng nhập.\n"
            "Cần làm rõ:\n"
            "- Label hiển thị.\n"
            "- Placeholder.\n"
            "- Kiểu dữ liệu: Text, Number, Email, Password, Phone, Code, Currency nếu áp dụng.\n"
            "- Độ dài tối thiểu.\n"
            "- Độ dài tối đa.\n"
            "- Bắt buộc hay không.\n"
            "- Giá trị mặc định.\n"
            "- Validation format.\n"
            "- Ký tự đặc biệt được phép hoặc không được phép.\n"
            "- Khoảng trắng đầu/cuối xử lý thế nào: giữ nguyên, tự trim, hay báo lỗi.\n"
            "- Duplicate rule nếu có.\n"
            "- Error message khi validation thất bại.\n"
            "- Read-only hay editable.\n"
            "- Khi nào disable.\n"
            "- API mapping nếu biết.\n"
            "- Acceptance criteria cho required, invalid format, duplicate, submit thành công nếu có.\n\n"

            "Ví dụ mô tả tốt cho Textbox:\n"
            "Mục đích: Cho phép người dùng nhập Email để định danh tài khoản. "
            "Hiển thị: Label = Email, Placeholder = Nhập email. "
            "Dữ liệu: Kiểu Email/String, Max length = 255, Required = Yes. "
            "Validation: phải đúng định dạng abc@domain.com; không được trùng email đã tồn tại; tự trim khoảng trắng đầu/cuối. "
            "Error: 'Email không đúng định dạng', 'Email đã tồn tại', 'Email là bắt buộc'. "
            "Permission: user có quyền tạo/sửa tài khoản được nhập. "
            "UI state: disabled khi đang loading hoặc user không có quyền chỉnh sửa. "
            "API mapping: FE field = email, BE field = email. "
            "Acceptance criteria: AC01 Given user chưa nhập Email When click Submit Then hiển thị 'Email là bắt buộc'. "
            "AC02 Given Email sai định dạng When rời khỏi field hoặc Submit Then hiển thị 'Email không đúng định dạng'.\n\n"

            "### 2. Text Area\n"
            "Áp dụng cho các field nhập nhiều dòng như: Mô tả sản phẩm, Ghi chú, Lý do từ chối.\n"
            "Cần làm rõ:\n"
            "- Label hiển thị.\n"
            "- Placeholder.\n"
            "- Số dòng hiển thị mặc định.\n"
            "- Min ký tự.\n"
            "- Max ký tự.\n"
            "- Có cho xuống dòng không.\n"
            "- Có hỗ trợ HTML không.\n"
            "- Có hỗ trợ emoji không.\n"
            "- Có bộ đếm ký tự không, ví dụ 1500/2000.\n"
            "- Required hay optional.\n"
            "- Error message.\n"
            "- Read-only/editable/disabled.\n"
            "- API mapping.\n"
            "- Acceptance criteria.\n\n"

            "### 3. Dropdown - Single Select\n"
            "Áp dụng cho các field chọn một giá trị như: Trạng thái đơn hàng, Loại khách hàng, Tỉnh/Thành phố.\n"
            "Cần làm rõ:\n"
            "- Label hiển thị.\n"
            "- Placeholder.\n"
            "- Danh sách option gồm Display và Value nếu biết.\n"
            "- Thứ tự hiển thị option.\n"
            "- Giá trị mặc định.\n"
            "- Có search trong dropdown không.\n"
            "- Có cho nhập custom value không.\n"
            "- Dữ liệu lấy từ đâu: hardcode, master data, API, config, enum.\n"
            "- Khi thay đổi giá trị thì ảnh hưởng field nào hoặc logic nào.\n"
            "- Required hay optional.\n"
            "- Error message.\n"
            "- Disabled condition.\n"
            "- API mapping.\n"
            "- Acceptance criteria.\n\n"

            "Ví dụ option:\n"
            "Display = Mới, Value = NEW; Display = Đang xử lý, Value = PROCESSING; Display = Hoàn thành, Value = DONE.\n\n"

            "### 4. Multi Select\n"
            "Áp dụng cho các field chọn nhiều giá trị như: Tags, Nhóm quyền, Danh mục sản phẩm.\n"
            "Cần làm rõ:\n"
            "- Label hiển thị.\n"
            "- Placeholder.\n"
            "- Danh sách option Display/Value nếu biết.\n"
            "- Chọn tối thiểu bao nhiêu.\n"
            "- Chọn tối đa bao nhiêu.\n"
            "- Có search không.\n"
            "- Có Select All không.\n"
            "- Có bỏ chọn hàng loạt không.\n"
            "- Cách hiển thị khi chọn nhiều: chip, comma-separated, count summary.\n"
            "- Required hay optional.\n"
            "- Error message khi vượt quá giới hạn hoặc thiếu lựa chọn bắt buộc.\n"
            "- API mapping: gửi array string, array id, hay object array.\n"
            "- Acceptance criteria.\n\n"

            "### 5. Radio Button / Radio Group\n"
            "Áp dụng cho nhóm lựa chọn một giá trị như: Giới tính, Loại khách hàng, Phương thức thanh toán.\n"
            "Cần làm rõ:\n"
            "- Label nhóm.\n"
            "- Danh sách giá trị Display/Value.\n"
            "- Giá trị mặc định.\n"
            "- Có bắt buộc chọn không.\n"
            "- Logic khi đổi lựa chọn.\n"
            "- Field nào bị enable/disable/ẩn/hiện theo lựa chọn.\n"
            "- Error message nếu bắt buộc nhưng chưa chọn.\n"
            "- API mapping.\n"
            "- Acceptance criteria.\n\n"

            "### 6. Checkbox\n"
            "Áp dụng cho các lựa chọn true/false hoặc xác nhận như: Đồng ý điều khoản, Nhận email thông báo.\n"
            "Cần làm rõ:\n"
            "- Label hiển thị.\n"
            "- Mặc định checked hay unchecked.\n"
            "- Required hay optional.\n"
            "- Ý nghĩa checked/unchecked.\n"
            "- Khi chọn hoặc bỏ chọn ảnh hưởng gì.\n"
            "- Có disable trong trường hợp nào không.\n"
            "- Error message nếu required mà chưa tick.\n"
            "- API mapping: boolean, Y/N, 1/0 hay enum.\n"
            "- Acceptance criteria.\n\n"

            "Ví dụ: Checkbox 'Đồng ý điều khoản' mặc định unchecked. Nếu chưa tick thì không cho Submit và hiển thị lỗi 'Vui lòng đồng ý điều khoản'.\n\n"

            "### 7. Date Picker\n"
            "Áp dụng cho các field ngày như: Ngày sinh, Ngày hiệu lực, Ngày hết hạn.\n"
            "Cần làm rõ:\n"
            "- Label hiển thị.\n"
            "- Placeholder.\n"
            "- Format ngày, ví dụ dd/MM/yyyy.\n"
            "- Timezone nếu có liên quan.\n"
            "- Có cho chọn ngày quá khứ không.\n"
            "- Có cho chọn ngày tương lai không.\n"
            "- Min date.\n"
            "- Max date.\n"
            "- Default date.\n"
            "- Required hay optional.\n"
            "- Có cho nhập tay không hay chỉ chọn từ calendar.\n"
            "- Error message khi sai format hoặc ngoài khoảng hợp lệ.\n"
            "- API mapping: string date, ISO date, timestamp.\n"
            "- Acceptance criteria.\n\n"

            "### 8. Date Time Picker\n"
            "Áp dụng cho các field ngày giờ như: Thời gian họp, Thời gian giao hàng, Thời điểm hiệu lực.\n"
            "Cần làm rõ:\n"
            "- Label hiển thị.\n"
            "- Format ngày giờ.\n"
            "- Timezone.\n"
            "- Bước nhảy thời gian, ví dụ 15 phút/lần.\n"
            "- Có chọn giây không.\n"
            "- Min datetime.\n"
            "- Max datetime.\n"
            "- Default datetime.\n"
            "- Required hay optional.\n"
            "- Error message.\n"
            "- API mapping.\n"
            "- Acceptance criteria.\n\n"

            "### 9. Time Picker\n"
            "Áp dụng cho các field giờ như: Giờ mở cửa, Giờ đóng cửa, Thời gian bắt đầu.\n"
            "Cần làm rõ:\n"
            "- Label hiển thị.\n"
            "- Format 12h hay 24h.\n"
            "- Min time.\n"
            "- Max time.\n"
            "- Interval/bước nhảy thời gian.\n"
            "- Default time.\n"
            "- Required hay optional.\n"
            "- Error message.\n"
            "- API mapping.\n"
            "- Acceptance criteria.\n\n"

            "### 10. Upload File\n"
            "Áp dụng cho các control upload như: Upload CV, Upload hợp đồng, Upload ảnh đại diện.\n"
            "Cần làm rõ:\n"
            "- Label hiển thị.\n"
            "- Định dạng file được phép, ví dụ PDF, DOCX, PNG, JPG.\n"
            "- Kích thước tối đa mỗi file.\n"
            "- Số file tối đa.\n"
            "- Có upload nhiều file hay không.\n"
            "- Lưu file ở đâu nếu biết.\n"
            "- Quy tắc đặt tên file nếu có.\n"
            "- Có preview không.\n"
            "- Có download lại được không.\n"
            "- Có xóa/thay thế file sau upload không.\n"
            "- Required hay optional.\n"
            "- Error message khi sai định dạng, vượt dung lượng, vượt số lượng.\n"
            "- Loading/progress state.\n"
            "- API mapping.\n"
            "- Acceptance criteria.\n\n"

            "### 11. Button\n"
            "Áp dụng cho các nút hành động như: Lưu, Submit, Tìm kiếm, Hủy, Xóa, Xuất Excel.\n"
            "Cần làm rõ:\n"
            "- Label button.\n"
            "- Mục đích hành động.\n"
            "- Khi nào enable.\n"
            "- Khi nào disable.\n"
            "- Khi click thì thực hiện logic gì.\n"
            "- Có gọi API nào không.\n"
            "- Có validate form trước khi xử lý không.\n"
            "- Double click xử lý thế nào.\n"
            "- Loading state khi đang xử lý.\n"
            "- Kết quả thành công.\n"
            "- Kết quả thất bại.\n"
            "- Message thành công/lỗi.\n"
            "- Điều hướng sau khi xử lý nếu có.\n"
            "- Permission: role nào được thấy/click.\n"
            "- Acceptance criteria.\n\n"

            "Ví dụ: Click Submit → validate form → gọi API Create Order → disable button trong lúc loading → "
            "thành công thì hiển thị message và điều hướng sang màn chi tiết.\n\n"

            "### 12. Search Box\n"
            "Áp dụng cho ô tìm kiếm nhanh như: Tìm khách hàng, Tìm đơn hàng, Tìm sản phẩm.\n"
            "Cần làm rõ:\n"
            "- Label hoặc placeholder.\n"
            "- Search theo trường nào.\n"
            "- Tìm gần đúng hay chính xác.\n"
            "- Có phân biệt hoa thường không.\n"
            "- Có bỏ dấu tiếng Việt không.\n"
            "- Delay search/debounce bao nhiêu ms.\n"
            "- Min ký tự để search.\n"
            "- Search khi nhập, khi Enter, hay khi click button.\n"
            "- Clear search hoạt động thế nào.\n"
            "- Empty result hiển thị gì.\n"
            "- API mapping/query parameter.\n"
            "- Acceptance criteria.\n\n"

            "Ví dụ: Nhập từ 3 ký tự mới search; debounce 500ms; tìm gần đúng theo tên khách hàng, email, số điện thoại.\n\n"

            "### 13. Table / Grid / Data Grid\n"
            "Áp dụng cho bảng dữ liệu như: Danh sách đơn hàng, Danh sách khách hàng, Lịch sử giao dịch.\n"
            "Cần làm rõ:\n"
            "- Mục đích bảng.\n"
            "- Nguồn dữ liệu.\n"
            "- Danh sách cột.\n"
            "- Tên cột.\n"
            "- Kiểu dữ liệu từng cột.\n"
            "- Width từng cột nếu biết.\n"
            "- Format hiển thị từng cột.\n"
            "- Cột nào được sort.\n"
            "- Sort mặc định.\n"
            "- Cột nào được filter.\n"
            "- Filter theo điều kiện gì.\n"
            "- Pagination có hay không.\n"
            "- Page size mặc định.\n"
            "- Danh sách page size được chọn nếu có.\n"
            "- Empty state khi không có dữ liệu.\n"
            "- Loading state.\n"
            "- Error state khi tải dữ liệu thất bại.\n"
            "- Row action: xem, sửa, xóa, duyệt, tải xuống.\n"
            "- Permission cho từng action nếu biết.\n"
            "- API mapping: request filter, response field.\n"
            "- Acceptance criteria.\n\n"

            "Quy tắc mô tả Table/Grid:\n"
            "- Tạo một dòng chính cho bảng, ví dụ 'Bảng Danh sách đơn hàng'.\n"
            "- Không tách từng header cột thành label riêng.\n"
            "- Trong mô tả chi tiết của bảng, liệt kê column spec dạng: Column = Order ID, Type = Text, Format = ..., Sort = Yes/No.\n"
            "- Chỉ tạo dòng riêng cho một cột nếu cột đó có control/hành vi phức tạp riêng, ví dụ cột Action có nhiều button, cột Status là badge có rule màu/trạng thái, cột Amount là calculated field quan trọng.\n\n"

            "### 14. Modal / Popup / Dialog\n"
            "Áp dụng cho popup xác nhận, popup nhập liệu, popup xem chi tiết.\n"
            "Cần làm rõ:\n"
            "- Trigger mở popup.\n"
            "- Tiêu đề popup.\n"
            "- Nội dung popup.\n"
            "- Danh sách field hoặc control bên trong popup.\n"
            "- Nút hành động.\n"
            "- Nút mặc định/focus mặc định.\n"
            "- Đóng bằng ESC được không.\n"
            "- Click outside có đóng không.\n"
            "- Có icon close không.\n"
            "- Có validate dữ liệu trong popup không.\n"
            "- Loading state khi submit popup.\n"
            "- Permission.\n"
            "- Acceptance criteria.\n\n"

            "### 15. Tab\n"
            "Áp dụng cho nhóm tab như: Thông tin chung, Lịch sử, Cấu hình, Tài liệu.\n"
            "Cần làm rõ:\n"
            "- Danh sách tab.\n"
            "- Tab mặc định.\n"
            "- Có lưu tab cuối user đã mở không.\n"
            "- Chuyển tab có reload dữ liệu không.\n"
            "- Tab nào bị disable theo trạng thái/permission.\n"
            "- Có lazy load nội dung tab không.\n"
            "- URL có thay đổi theo tab không.\n"
            "- Acceptance criteria.\n\n"

            "### 16. Toggle Switch\n"
            "Áp dụng cho bật/tắt trạng thái như: Kích hoạt tài khoản, Bật thông báo.\n"
            "Cần làm rõ:\n"
            "- Label hiển thị.\n"
            "- ON tương ứng giá trị gì.\n"
            "- OFF tương ứng giá trị gì.\n"
            "- Giá trị mặc định.\n"
            "- Có confirm khi đổi trạng thái không.\n"
            "- Có gọi API ngay khi đổi không hay lưu sau.\n"
            "- Error handling nếu đổi trạng thái thất bại.\n"
            "- Permission.\n"
            "- API mapping: boolean, enum, 1/0, Y/N.\n"
            "- Acceptance criteria.\n\n"

            "Ví dụ: ON = Active, OFF = Inactive. Khi chuyển từ OFF sang ON, hiển thị popup xác nhận trước khi gọi API cập nhật trạng thái.\n\n"

            "### 17. Link\n"
            "Áp dụng cho link điều hướng như: Xem chi tiết, Quên mật khẩu, Tải tài liệu.\n"
            "Cần làm rõ:\n"
            "- Text hiển thị.\n"
            "- Điều hướng tới đâu.\n"
            "- Mở cùng tab hay tab mới.\n"
            "- Có truyền parameter nào không.\n"
            "- Quyền truy cập.\n"
            "- Trạng thái disabled/hidden nếu không có quyền.\n"
            "- Error handling nếu route không tồn tại hoặc không có quyền.\n"
            "- Acceptance criteria.\n\n"

            "### 18. Card\n"
            "Áp dụng cho card hiển thị dữ liệu như: Product Card, Summary Card, Customer Card, Dashboard Card.\n"
            "Cần làm rõ:\n"
            "- Mục đích card.\n"
            "- Dữ liệu hiển thị trên card.\n"
            "- Thứ tự hiển thị các thông tin.\n"
            "- Format từng thông tin.\n"
            "- Responsive behavior nếu biết.\n"
            "- Click card làm gì.\n"
            "- Có action button/menu trên card không.\n"
            "- Empty/loading/error state.\n"
            "- Permission.\n"
            "- API mapping.\n"
            "- Acceptance criteria.\n\n"

            "### 19. Read-only Field / Output Field\n"
            "Áp dụng cho field chỉ hiển thị như: Mã hồ sơ tự sinh, Tổng tiền, Trạng thái xử lý, Người tạo, Ngày tạo.\n"
            "Vì đây là output nên KHÔNG cần mô tả min length, max length, required nhập liệu, ký tự đặc biệt. "
            "Cần làm rõ:\n"
            "- Label hiển thị.\n"
            "- Dữ liệu hiển thị là gì.\n"
            "- Nguồn dữ liệu: API, database, hệ thống tự sinh, kết quả tính toán.\n"
            "- Format hiển thị.\n"
            "- Giá trị khi rỗng/null.\n"
            "- Khi nào dữ liệu được cập nhật.\n"
            "- Có copy được không.\n"
            "- Có tooltip không.\n"
            "- Permission xem dữ liệu.\n"
            "- API mapping nếu biết.\n"
            "- Acceptance criteria nếu có rule quan trọng.\n\n"

            "### 20. Calculated Field\n"
            "Áp dụng cho field tính toán như: Tổng tiền, VAT, Thành tiền, Tuổi, Số ngày còn lại.\n"
            "Cần làm rõ:\n"
            "- Label hiển thị.\n"
            "- Công thức tính.\n"
            "- Field đầu vào dùng để tính.\n"
            "- Thời điểm tính lại: khi nhập, khi blur, khi submit, khi tải dữ liệu.\n"
            "- Quy tắc làm tròn.\n"
            "- Format hiển thị.\n"
            "- Xử lý khi thiếu dữ liệu đầu vào.\n"
            "- Có cho sửa tay không.\n"
            "- API mapping nếu backend trả về hay frontend tự tính.\n"
            "- Acceptance criteria.\n\n"

            "## Quy tắc hỏi lại user:\n"
            "Trước khi tạo DOCX chính thức, nếu còn thông tin quan trọng chưa rõ thì phải đặt clarifying_questions.\n"
            "Tuy nhiên không đặt quá nhiều câu hỏi nhỏ lẻ gây rối. Hãy nhóm câu hỏi theo control hoặc theo nhóm rule.\n\n"

            "Nên hỏi lại khi thiếu các thông tin sau:\n"
            "- Field nào bắt buộc.\n"
            "- Max length/min length của các input quan trọng.\n"
            "- Format dữ liệu quan trọng như Email, SĐT, Mã, Ngày, Tiền tệ.\n"
            "- Source dữ liệu của dropdown/multi-select/radio.\n"
            "- Công thức tính của calculated field.\n"
            "- Button click sẽ gọi hành động/API nào.\n"
            "- Điều kiện enable/disable/hidden quan trọng.\n"
            "- Quyền thao tác theo role.\n"
            "- API mapping nếu tài liệu yêu cầu Dev triển khai trực tiếp.\n"
            "- Message lỗi/thành công nếu ảnh không thể hiện.\n\n"

            "Không cần hỏi lại các chi tiết thuần UI nhỏ nếu không ảnh hưởng nghiệp vụ, ví dụ màu sắc, font, spacing, icon style, trừ khi user yêu cầu.\n\n"

            "## Quy tắc về confidence và source:\n"
            "- source = 'visible' nếu thông tin nhìn thấy trực tiếp trên ảnh.\n"
            "- source = 'inferred' nếu thông tin được suy luận hợp lý nhưng chưa được xác nhận.\n"
            "- source = 'user_confirmed' nếu thông tin đã được user trả lời/xác nhận.\n"
            "- confidence cao khi thông tin nhìn thấy rõ hoặc được user xác nhận.\n"
            "- confidence thấp hơn nếu thông tin chỉ suy luận từ ảnh.\n\n"

            "## Quy tắc về assumptions:\n"
            "- Chỉ đưa vào assumptions các giả định thực sự cần thiết.\n"
            "- Nếu assumption đã được user xác nhận thì loại khỏi assumptions và cập nhật vào mô tả control tương ứng.\n"
            "- Assumption có rủi ro cao thì nên chuyển thành clarifying_question priority = 'critical'.\n\n"

            "## Quy tắc sắp xếp rows:\n"
            "- Sắp xếp theo thứ tự xuất hiện trên màn hình: từ trên xuống dưới, từ trái sang phải.\n"
            "- Các control trong cùng một section nên đứng liền nhau.\n"
            "- Button/action chính thường đặt sau các input liên quan.\n"
            "- Table/Grid đặt sau vùng filter/search nếu màn hình có tìm kiếm.\n"
            "- STT phải bắt đầu từ 1 và tăng liên tục.\n"
            "- Không được trùng lặp control.\n\n"

            "## Quy tắc output:\n"
            "Output cuối cùng phải là JSON đúng schema đã định nghĩa. "
            "Trong rows, mỗi dòng phải đủ các thông tin để tạo bảng DOCX gồm các cột:\n"
            "- STT\n"
            "- control_name\n"
            "- control_type\n"
            "- data_type\n"
            "- io\n"
            "- initial_value\n"
            "- description\n"
            "- confidence\n"
            "- source\n"
        )

    @staticmethod
    def _build_stage1_prompt() -> str:
        """Stage 1 prompt: Analyze screenshot and ask clarification questions."""
        return (
            AIService._build_common_ba_control_rules()
            + "\n\n"
            "## Stage 1 - Phân tích ảnh màn hình lần đầu\n\n"
            "Bạn đang nhận một ảnh chụp màn hình thiết kế UI. "
            "Hãy nhìn thật kỹ toàn bộ ảnh trước khi đưa ra đặc tả.\n\n"

            "## Nhiệm vụ Stage 1:\n"
            "1. Review tổng thể màn hình.\n"
            "2. Xác định tên màn hình nếu có thể nhìn thấy hoặc suy luận từ context.\n"
            "3. Xác định loại màn hình: Create, Edit, View, Search, Approval, Report hoặc Unknown.\n"
            "4. Chia màn hình thành các vùng chức năng nếu có: header, filter/search area, form input, action area, table/grid, popup, footer.\n"
            "5. Nhận diện toàn bộ logical business control trên màn hình.\n"
            "6. Không tách label và input/dropdown/date picker/value thành các dòng riêng nếu chúng thuộc cùng một field nghiệp vụ.\n"
            "7. Với mỗi logical control, xác định đúng loại control nghiệp vụ (control_type): Textbox, Text Area, Dropdown, Multi Select, Radio, Checkbox, Date Picker, Date Time Picker, Time Picker, Upload File, Button, Search Box, Table/Grid, Modal, Tab, Toggle Switch, Link, Card, Read-only Field, Calculated Field.\n"
            "8. Với control dạng Input hoặc Input/Output, mô tả chi tiết theo checklist của từng loại control.\n"
            "9. Với control dạng Output, chỉ mô tả nguồn dữ liệu, format, trạng thái hiển thị, permission, API mapping nếu biết; không mô tả các rule nhập liệu không liên quan.\n"
            "10. Nếu thông tin không nhìn thấy trên ảnh và chưa có context, không được tự bịa. Hãy ghi [Cần xác nhận: ...].\n"
            "11. Đặt clarifying_questions cho các thông tin quan trọng còn thiếu trước khi tạo DOCX chính thức.\n"
            "12. Nếu còn câu hỏi priority = 'critical', set ready_to_generate_docx = false.\n"
            "13. Nếu không còn câu hỏi priority = 'critical', có thể set ready_to_generate_docx = true.\n\n"

            "## Cách đặt câu hỏi làm rõ:\n"
            "Câu hỏi phải cụ thể, có nêu control bị ảnh hưởng và lý do cần hỏi. "
            "Không hỏi chung chung kiểu 'Bạn có yêu cầu gì thêm không?'.\n\n"

            "## JSON Schema bắt buộc:\n"
            "```json\n"
            "{\n"
            '  "screen_name": "Tên màn hình",\n'
            '  "screen_type": "Create | Edit | View | Search | Approval | Report | Unknown",\n'
            '  "screen_summary": "Tóm tắt màn hình",\n'
            '  "ready_to_generate_docx": false,\n'
            '  "clarifying_questions": [\n'
            '    {\n'
            '      "id": "Q1",\n'
            '      "priority": "critical | important | optional",\n'
            '      "question": "Nội dung câu hỏi",\n'
            '      "reason": "Lý do cần hỏi",\n'
            '      "affected_controls": ["Tên control liên quan"]\n'
            '    }\n'
            '  ],\n'
            '  "assumptions": [\n'
            '    {\n'
            '      "content": "Nội dung giả định",\n'
            '      "risk_level": "high | medium | low"\n'
            '    }\n'
            '  ],\n'
            '  "rows": [\n'
            '    {\n'
            '      "stt": 1,\n'
            '      "control_name": "Tên logical control",\n'
            '      "control_type": "Textbox | Dropdown | Button | Table/Grid | etc.",\n'
            '      "data_type": "Kiểu dữ liệu",\n'
            '      "io": "Input | Output | Input/Output",\n'
            '      "initial_value": "Giá trị khởi tạo",\n'
            '      "description": "Mô tả chi tiết cực kỳ kỹ theo format",\n'
            '      "confidence": 0.9,\n'
            '      "source": "visible | inferred | user_confirmed"\n'
            '    }\n'
            '  ]\n'
            "}\n"
            "```\n\n"
            "Nhắc lại: rows phải mô tả theo logical business control, không theo UI element vật lý."
        )

    @staticmethod
    def _build_stage2_prompt() -> str:
        """Stage 2 prompt: Refine after user answers."""
        return (
            AIService._build_common_ba_control_rules()
            + "\n\n"
            "## Stage 2 - Cập nhật đặc tả sau khi User trả lời câu hỏi làm rõ\n\n"
            "Bạn đã phân tích ảnh chụp màn hình trước đó và đưa ra đặc tả sơ bộ. "
            "Người dùng đã trả lời các câu hỏi làm rõ. "
            "Nhiệm vụ của bạn là cập nhật, chuẩn hóa và hoàn thiện đặc tả để có thể tạo DOCX.\n\n"

            "## Nhiệm vụ Stage 2:\n"
            "1. Dựa vào câu trả lời của User, ảnh thiết kế màn hình và đặc tả sơ bộ trước đó, hãy cập nhật lại toàn bộ đặc tả.\n"
            "2. Các thông tin đã được User xác nhận thì set source = 'user_confirmed' và tăng confidence phù hợp.\n"
            "3. Điều chỉnh lại chính xác loại control (control_type), kiểu dữ liệu, giá trị khởi tạo, validation, business rule, permission, UI state, API mapping và acceptance criteria dựa trên câu trả lời của User.\n"
            "4. Chuẩn hóa rows theo logical business control, không theo UI element vật lý.\n"
            "5. Nếu bản phân tích trước đang tách Label và Input/Dropdown/Date Picker/Value thành nhiều dòng, phải gộp lại thành một dòng control nghiệp vụ duy nhất.\n"
            "6. Xóa các dòng label rời rạc để tránh trùng lặp.\n"
            "7. Không được bỏ sót control đã có trong bản phân tích trước, trừ trường hợp control đó chỉ là label/helper/icon/placeholder đã được gộp vào control chính.\n"
            "8. Với các control dạng Input hoặc Input/Output, phần mô tả chi tiết phải cực kỳ kỹ lượng theo checklist riêng của từng loại control.\n"
            "9. Với các control dạng Output, không thêm các rule nhập liệu không liên quan; chỉ mô tả nguồn dữ liệu, format, tính toán, permission, UI state, API mapping nếu biết.\n"
            "10. Nếu vẫn còn điểm chưa rõ quan trọng, tiếp tục đặt clarifying_questions mới.\n"
            "11. Nếu không còn câu hỏi priority = 'critical', set ready_to_generate_docx = true.\n"
            "12. Nếu còn câu hỏi priority = 'critical', set ready_to_generate_docx = false.\n"
            "13. Đảm bảo STT tuần tự từ 1 đến hết sau khi đã gộp control.\n"
            "14. Không được trùng lặp control.\n"
            "15. Cập nhật lại assumptions: loại bỏ assumption nào đã được User xác nhận.\n\n"

            "## Quy tắc gộp control từ bản phân tích trước:\n"
            "If bản phân tích trước đang có:\n"
            "- Label A\n"
            "- Input A\n"
            "thì phải gộp thành một dòng duy nhất: 'Trường nhập A'.\n\n"

            "Nếu bản phân tích trước đang có:\n"
            "- Label B\n"
            "- Dropdown B\n"
            "thì phải gộp thành một dòng duy nhất: 'Dropdown B'.\n\n"

            "Nếu bản phân tích trước đang có:\n"
            "- Label C\n"
            "- Date picker C\n"
            "thì phải gộp thành một dòng duy nhất: 'Date picker C'.\n\n"

            "Nếu bản phân tích trước đang có:\n"
            "- Label D\n"
            "- Giá trị D\n"
            "và giá trị này chỉ hiển thị/read-only, thì phải gộp thành một dòng duy nhất: 'Trường hiển thị D'.\n\n"

            "Nếu bản phân tích trước đang có:\n"
            "- Placeholder của field E\n"
            "- Icon search/calendar/dropdown của field E\n"
            "- Input E\n"
            "thì chỉ giữ một dòng control chính và đưa placeholder/icon vào mô tả chi tiết của control đó.\n\n"

            "## Cách đặt tên tại cột 'control_name':\n"
            "Tên control phải thể hiện rõ loại control + tên nghiệp vụ.\n\n"

            "Ví dụ đúng:\n"
            "- Trường nhập Họ tên\n"
            "- Trường nhập Email\n"
            "- Trường nhập Số điện thoại\n"
            "- Text Area Mô tả sản phẩm\n"
            "- Dropdown Trạng thái đơn hàng\n"
            "- Multi Select Tags\n"
            "- Radio Group Giới tính\n"
            "- Checkbox Đồng ý điều khoản\n"
            "- Date Picker Ngày sinh\n"
            "- Date Time Picker Thời gian họp\n"
            "- Time Picker Giờ mở cửa\n"
            "- Upload File CV\n"
            "- Search Box Tìm khách hàng\n"
            "- Button Submit\n"
            "- Bảng Danh sách đơn hàng\n"
            "- Modal Xác nhận xóa\n"
            "- Tab Thông tin chung\n"
            "- Toggle Switch Kích hoạt tài khoản\n"
            "- Link Xem chi tiết\n"
            "- Card Sản phẩm\n"
            "- Trường hiển thị Tổng tiền\n"
            "- Trường tính toán VAT\n\n"

            "Ví dụ sai:\n"
            "- Label Email\n"
            "- Text Email\n"
            "- Input\n"
            "- Ô nhập\n"
            "- Icon lịch\n"
            "- Placeholder nhập email\n\n"

            "## Yêu cầu bắt buộc cho mô tả chi tiết của Input control:\n"
            "Với mọi control có io = 'Input' hoặc 'Input/Output', phần mô tả chi tiết (description) phải cố gắng bao gồm:\n"
            "- Label hiển thị.\n"
            "- Placeholder nếu có.\n"
            "- Kiểu dữ liệu.\n"
            "- Giá trị khởi tạo/mặc định.\n"
            "- Required hay optional.\n"
            "- Min/max length hoặc min/max value nếu áp dụng.\n"
            "- Format dữ liệu nếu áp dụng.\n"
            "- Validation rule.\n"
            "- Error message.\n"
            "- Business rule.\n"
            "- Permission.\n"
            "- UI state: normal, disabled, loading, error, readonly nếu áp dụng.\n"
            "- API mapping nếu biết.\n"
            "- Acceptance criteria cho các hành vi quan trọng.\n"
            "- Các điểm còn [Cần xác nhận].\n\n"

            "## Yêu cầu bắt buộc cho Output control:\n"
            "Với control có io = 'Output', phần mô tả chi tiết (description) chỉ cần tập trung vào:\n"
            "- Label hiển thị.\n"
            "- Dữ liệu hiển thị là gì.\n"
            "- Nguồn dữ liệu.\n"
            "- Format hiển thị.\n"
            "- Giá trị khi null/empty.\n"
            "- Thời điểm cập nhật dữ liệu.\n"
            "- Permission xem dữ liệu.\n"
            "- UI state: loading, empty, error nếu áp dụng.\n"
            "- API mapping nếu biết.\n"
            "- Công thức tính nếu là calculated field.\n\n"

            "## JSON Schema bắt buộc:\n"
            "Trả về JSON đúng schema đã định nghĩa ở Stage 1 (screen_name, screen_type, screen_summary, ready_to_generate_docx, clarifying_questions, assumptions, rows)."
        )

    @staticmethod
    def _build_stage3_prompt() -> str:
        """Stage 3 prompt: QA validation before DOCX."""
        return (
            AIService._build_common_ba_control_rules()
            + "\n\n"
            "## Pre-DOCX QA\n\n"
            "Bạn đang kiểm tra lại đặc tả màn hình ngay trước khi tạo file DOCX.\n\n"

            "## Nhiệm vụ QA:\n"
            "1. Kiểm tra toàn bộ rows có đang mô tả theo logical business control không.\n"
            "2. Nếu còn dòng Label/Input bị tách rời, hãy gộp lại.\n"
            "3. Nếu còn dòng placeholder/icon/helper text bị tạo thành control riêng, hãy gộp vào control chính.\n"
            "4. Kiểm tra STT có tuần tự từ 1 đến hết không. Nếu sai, đánh lại STT.\n"
            "5. Kiểm tra có control trùng lặp không. Nếu có, gộp hoặc xóa dòng trùng.\n"
            "6. Kiểm tra mỗi control Input/Input-Output đã có mô tả đủ sâu chưa.\n"
            "7. Kiểm tra mỗi Output control không bị mô tả thừa rule nhập liệu không liên quan.\n"
            "8. Kiểm tra các thông tin không chắc chắn đã được ghi [Cần xác nhận] chưa.\n"
            "9. Kiểm tra nếu còn câu hỏi critical thì ready_to_generate_docx phải là false.\n"
            "10. Nếu không còn câu hỏi critical thì ready_to_generate_docx có thể là true.\n\n"

            "## Checklist QA cho Input/Input-Output control:\n"
            "Mỗi control Input/Input-Output nên có các nội dung sau trong mô tả chi tiết (description) nếu áp dụng:\n"
            "- Label.\n"
            "- Placeholder.\n"
            "- Kiểu dữ liệu.\n"
            "- Default value.\n"
            "- Required/optional.\n"
            "- Min/max length hoặc min/max value.\n"
            "- Format.\n"
            "- Validation.\n"
            "- Error message.\n"
            "- Business rule.\n"
            "- Permission.\n"
            "- UI state.\n"
            "- API mapping.\n"
            "- Acceptance criteria.\n"
            "- [Cần xác nhận] với thông tin còn thiếu.\n\n"

            "## Checklist QA cho Output control:\n"
            "Mỗi control Output nên có các nội dung sau trong mô tả chi tiết (description) nếu áp dụng:\n"
            "- Label.\n"
            "- Dữ liệu hiển thị.\n"
            "- Nguồn dữ liệu.\n"
            "- Format.\n"
            "- Giá trị khi empty/null.\n"
            "- Thời điểm cập nhật.\n"
            "- Permission xem.\n"
            "- UI state.\n"
            "- API mapping.\n"
            "- Công thức tính nếu là calculated field.\n\n"

            "## Output:\n"
            "Trả về JSON đã được chỉnh sửa, đúng schema đã định nghĩa ở Stage 1 (screen_name, screen_type, screen_summary, ready_to_generate_docx, clarifying_questions, assumptions, rows), sẵn sàng tạo DOCX."
        )

    # ══════════════════════════════════════════════
    # AI API CALLERS
    # ══════════════════════════════════════════════

    @classmethod
    def _call_openai_vision(cls, system_prompt: str, user_prompt: str, base64_image: str) -> dict:
        try:
            from openai import OpenAI
            client = OpenAI(api_key=config.OPENAI_API_KEY)

            response = client.chat.completions.create(
                model=config.OPENAI_MODEL,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": user_prompt},
                            {
                                "type": "image_url",
                                "image_url": {"url": f"data:image/png;base64,{base64_image}"}
                            }
                        ]
                    }
                ],
                response_format={"type": "json_object"},
                temperature=0.2
            )

            content = response.choices[0].message.content
            logger.info(f"OpenAI response length: {len(content)} chars")
            return json.loads(content)
        except Exception as e:
            logger.error(f"Error calling OpenAI Vision API: {str(e)}")
            raise e

    @classmethod
    def _call_gemini_vision(cls, system_prompt: str, user_prompt: str, base64_image: str) -> dict:
        import time
        max_retries = 3
        delay = 2.0
        
        for attempt in range(max_retries):
            try:
                url = (
                    f"https://generativelanguage.googleapis.com/v1beta/models/"
                    f"{config.GEMINI_MODEL}:generateContent?key={config.GEMINI_API_KEY}"
                )

                payload = {
                    "contents": [
                        {
                            "role": "user",
                            "parts": [
                                {"text": f"{system_prompt}\n\n{user_prompt}"},
                                {
                                    "inlineData": {
                                        "mimeType": "image/png",
                                        "data": base64_image
                                    }
                                }
                            ]
                        }
                    ],
                    "generationConfig": {
                        "responseMimeType": "application/json",
                        "temperature": 0.2
                    }
                }

                with httpx.Client(timeout=120.0) as client:
                    r = client.post(url, json=payload)
                    r.raise_for_status()
                    result = r.json()

                    text = result["candidates"][0]["content"]["parts"][0]["text"]
                    logger.info(f"Gemini response length: {len(text)} chars")
                    return json.loads(text)
            except Exception as e:
                is_status_error = isinstance(e, httpx.HTTPStatusError)
                is_503_or_429 = is_status_error and e.response.status_code in (503, 429)
                
                if (is_503_or_429 or "503" in str(e) or "429" in str(e)) and attempt < max_retries - 1:
                    logger.warning(f"Gemini API temporarily rate-limited or busy (status: 503/429). Attempt {attempt + 1}/{max_retries}. Retrying in {delay}s...")
                    time.sleep(delay)
                    delay *= 2
                else:
                    logger.error(f"Error calling Gemini Vision API after {attempt + 1} attempts: {str(e)}")
                    raise e

    @classmethod
    def _call_openrouter_api(cls, api_key: str, model: str, system_prompt: str, user_prompt: str, base64_image: str = None) -> dict:
        import time
        max_retries = 3
        delay = 2.0
        
        for attempt in range(max_retries):
            try:
                url = "https://openrouter.ai/api/v1/chat/completions"
                headers = {
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                    "HTTP-Referer": "https://github.com/google-deepmind/antigravity",
                    "X-Title": "Antigravity BA Agent"
                }
                
                messages = [
                    {"role": "system", "content": system_prompt}
                ]
                
                # Check if the OpenRouter model supports vision
                is_vision_model = any(k in model.lower() for k in ["vision", "gemini", "claude", "gpt-4o", "pixtral", "llava"])
                
                if base64_image and is_vision_model:
                    user_content = [
                        {"type": "text", "text": user_prompt},
                        {
                            "type": "image_url",
                            "image_url": {"url": f"data:image/png;base64,{base64_image}"}
                        }
                    ]
                else:
                    # Text-only model or no image provided: send prompt as plain text
                    user_content = user_prompt
                    
                messages.append({"role": "user", "content": user_content})
                
                payload = {
                    "model": model,
                    "messages": messages,
                    "temperature": 0.2,
                    "response_format": {"type": "json_object"}
                }
                
                logger.info(f"Calling OpenRouter API for model {model} (attempt {attempt + 1}/{max_retries})...")
                
                with httpx.Client(timeout=120.0) as client:
                    r = client.post(url, json=payload, headers=headers)
                    r.raise_for_status()
                    result = r.json()
                    
                    if "choices" not in result or not result["choices"]:
                        raise ValueError(f"Invalid response structure from OpenRouter: {result}")
                        
                    text = result["choices"][0]["message"]["content"]
                    logger.info(f"OpenRouter response length: {len(text)} chars")
                    
                    # Clean up any potential markdown JSON wrappers
                    text = text.strip()
                    if text.startswith("```json"):
                        text = text[7:]
                    elif text.startswith("```"):
                        text = text[3:]
                    if text.endswith("```"):
                        text = text[:-3]
                    text = text.strip()
                    
                    return json.loads(text)
            except Exception as e:
                is_status_error = isinstance(e, httpx.HTTPStatusError)
                is_503_or_429 = is_status_error and e.response.status_code in (503, 429)
                
                if (is_503_or_429 or "503" in str(e) or "429" in str(e)) and attempt < max_retries - 1:
                    logger.warning(
                        f"OpenRouter API temporarily rate-limited or busy (status: 503/429). "
                        f"Attempt {attempt + 1}/{max_retries}. Retrying in {delay}s..."
                    )
                    time.sleep(delay)
                    delay *= 2
                else:
                    logger.error(f"Error calling OpenRouter API after {attempt + 1} attempts: {str(e)}")
                    raise e

    # ══════════════════════════════════════════════
    # MOCK FALLBACKS (for offline testing only)
    # ══════════════════════════════════════════════

    @classmethod
    def _generate_mock_analysis(cls, context: str) -> dict:
        """Generates rich mock data matching the extended schema. For offline testing only."""
        return {
            "screen_name": "Thêm mới nhân viên",
            "screen_type": "Create",
            "screen_summary": (
                "Màn hình thêm mới nhân viên gồm form nhập liệu các trường thông tin cá nhân "
                "(họ tên, ngày sinh, giới tính, email, SĐT, địa chỉ), thông tin công việc "
                "(phòng ban, chức vụ, ngày vào làm, mức lương) và 2 nút thao tác Lưu/Hủy."
            ),
            "ready_to_generate_docx": False,
            "clarifying_questions": [
                {
                    "id": "Q1",
                    "priority": "critical",
                    "question": "Mức lương cơ bản có giới hạn trần tối đa hoặc mức lương tối thiểu vùng hay không?",
                    "reason": "Ảnh chỉ hiển thị trường nhập lương, không thể xác định ràng buộc min/max.",
                    "affected_controls": ["Mức lương cơ bản"]
                },
                {
                    "id": "Q2",
                    "priority": "critical",
                    "question": "Dropdown 'Phòng ban' lấy danh sách từ master data cố định hay lọc theo chi nhánh?",
                    "reason": "Ảnh chỉ thể hiện control dropdown, không xác định được data source.",
                    "affected_controls": ["Phòng ban"]
                },
                {
                    "id": "Q3",
                    "priority": "important",
                    "question": "Khi ấn Hủy khi đang nhập dữ liệu, có cần hiển thị popup cảnh báo xác nhận không?",
                    "reason": "Cần xác định hành vi UX khi user hủy giữa chừng.",
                    "affected_controls": ["Nút Hủy"]
                }
            ],
            "assumptions": [
                {"content": "Mã nhân viên được hệ thống tự sinh, user không nhập.", "risk_level": "low"},
                {"content": "Email phải là duy nhất trong hệ thống.", "risk_level": "medium"},
                {"content": "Nhân viên phải đủ 18 tuổi tại thời điểm tạo.", "risk_level": "low"}
            ],
            "rows": [
                {"stt": 1, "control_name": "Tiêu đề trang", "data_type": "Label", "io": "Output", "initial_value": "Thêm mới nhân viên", "description": "Hiển thị tiêu đề trang, căn giữa, cỡ chữ 24px bold.", "confidence": 1.0, "source": "visible"},
                {"stt": 2, "control_name": "Mã nhân viên", "data_type": "String", "io": "Output", "initial_value": "Tự động sinh", "description": "Mã định danh duy nhất. Tự sinh theo định dạng NV + 6 chữ số tăng dần (NV000123). Read-only.", "confidence": 0.7, "source": "inferred"},
                {"stt": 3, "control_name": "Họ và tên", "data_type": "String", "io": "Input", "initial_value": "Rỗng", "description": "Nhập đầy đủ họ tên tiếng Việt có dấu. Tối đa 100 ký tự. Bắt buộc nhập. [Cần xác nhận] độ dài tối thiểu.", "confidence": 0.85, "source": "visible"},
                {"stt": 4, "control_name": "Ngày sinh", "data_type": "Date", "io": "Input", "initial_value": "Rỗng", "description": "DatePicker chọn ngày sinh. DD/MM/YYYY. Ràng buộc: tuổi >= 18.", "confidence": 0.9, "source": "visible"},
                {"stt": 5, "control_name": "Phòng ban", "data_type": "Option", "io": "Input", "initial_value": "Chọn phòng ban", "description": "Dropdown lấy danh sách phòng ban. [Cần xác nhận] data source.", "confidence": 0.6, "source": "visible"},
                {"stt": 6, "control_name": "Mức lương cơ bản", "data_type": "Number", "io": "Input", "initial_value": "0", "description": "Nhập mức lương cơ bản. Số dương. Định dạng phân tách hàng nghìn. [Cần xác nhận] min/max.", "confidence": 0.6, "source": "visible"},
                {"stt": 7, "control_name": "Nút Lưu", "data_type": "Button", "io": "Input", "initial_value": "Hoạt động", "description": "Lưu thông tin nhân viên. Validate toàn bộ trường bắt buộc trước khi submit. Hiển thị loading khi xử lý.", "confidence": 0.95, "source": "visible"},
                {"stt": 8, "control_name": "Nút Hủy", "data_type": "Button", "io": "Input", "initial_value": "Hoạt động", "description": "Hủy thao tác và quay về danh sách. [Cần xác nhận] có cần confirm modal không.", "confidence": 0.7, "source": "visible"},
            ]
        }

    @classmethod
    def _generate_mock_refinement(cls, previous_spec: dict, user_answers: list) -> dict:
        """Enriches existing spec with user answers. For offline testing only."""
        spec = previous_spec.copy()

        answers_map = {item["id"]: item["answer"] for item in user_answers}

        # Update rows based on answers
        rows = spec.get("rows", [])
        for row in rows:
            name = row.get("control_name", "").lower()
            desc = row.get("description", "")

            if "lương" in name and "Q1" in answers_map:
                row["description"] = f"{desc} Ràng buộc bổ sung: {answers_map['Q1']}."
                row["source"] = "user_confirmed"
                row["confidence"] = 1.0
                row["description"] = row["description"].replace("[Cần xác nhận]", "")
            elif "phòng ban" in name and "Q2" in answers_map:
                row["description"] = f"{desc} Data source: {answers_map['Q2']}."
                row["source"] = "user_confirmed"
                row["confidence"] = 1.0
                row["description"] = row["description"].replace("[Cần xác nhận]", "")
            elif "hủy" in name and "Q3" in answers_map:
                row["description"] = f"{desc} Hành vi xác nhận: {answers_map['Q3']}."
                row["source"] = "user_confirmed"
                row["confidence"] = 1.0
                row["description"] = row["description"].replace("[Cần xác nhận]", "")

        spec["rows"] = rows
        spec["ready_to_generate_docx"] = True
        spec["clarifying_questions"] = []  # All answered
        # Remove confirmed assumptions
        spec["assumptions"] = [a for a in spec.get("assumptions", []) if a.get("risk_level") == "high"]

        return spec

import os
import shutil
from app.config import config
from app.database import init_db, get_db, AnalysisSession
from app.services.ai_service import AIService
from app.services.validator import SpecValidator
from app.services.docx_gen import DOCXGenerator

def run_backend_test():
    print("========================================")
    print("STARTING BACKEND SERVICE DRY-RUN VERIFICATION")
    print("========================================")

    # 1. Initialize DB
    print("\n[Step 1] Initializing SQLite Database...")
    init_db()
    print("-> Database and tables initialized successfully.")

    # 2. Setup testing mockup directories and files
    print("\n[Step 2] Creating temporary test image...")
    os.makedirs(config.UPLOAD_DIR, exist_ok=True)
    temp_img_path = os.path.join(config.UPLOAD_DIR, "test_mock_screen.png")
    
    # Write a dummy byte array representing a minimal valid PNG or just text
    # A tiny 1x1 black pixel PNG base64
    tiny_png_base64 = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNkYP8DAA0bAP0yG64FAAAAAElFTkSuQmCC"
    import base64
    with open(temp_img_path, "wb") as f:
        f.write(base64.b64decode(tiny_png_base64))
    print(f"-> Mock image created at: {temp_img_path}")

    # 3. Simulate Stage 1: AI Vision Scan
    print("\n[Step 3] Running Stage 1 AI vision analysis...")
    context = "Đặc tả màn hình thêm mới nhân viên có chức năng lưu và hủy"
    analysis_res = AIService.analyze_screenshot(temp_img_path, context)
    
    print("\n-> Extracted Questions:")
    for q in analysis_res["questions"]:
        print(f"   * ID: {q['id']} - Question: {q['question']}")
        
    print("\n-> Extracted Controls:")
    for c in analysis_res["controls"]:
        print(f"   * STT: {c.get('STT')} | Control: {c.get('control_name')} | Type: {c.get('data_type')} | IO: {c.get('io')}")

    # 4. Validate and Clean Controls
    print("\n[Step 4] Running Spec Validation Service...")
    validated_controls = SpecValidator.validate_and_clean_spec(analysis_res["controls"])
    print(f"-> Validated and sanitized {len(validated_controls)} controls.")

    # 5. Simulate Stage 2: User answers and Spec Refinement
    print("\n[Step 5] Simulating user answering questions and refining spec...")
    mock_qna = [
        {"id": "q1", "question": "Mức lương cơ bản của nhân viên có giới hạn trần tối đa hoặc mức lương tối thiểu vùng hay không?", "answer": "Mức lương tối thiểu là 5,000,000đ và tối đa là 150,000,000đ"},
        {"id": "q2", "question": "Dropdown 'Phòng ban' có cần hỗ trợ phân quyền lọc theo chi nhánh không?", "answer": "Có lọc theo chi nhánh của user đăng nhập"},
        {"id": "q3", "question": "Khi người dùng ấn 'Hủy' khi đang nhập dữ liệu có cần cảnh báo không?", "answer": "Có, cần hiển thị Confirm modal xác nhận hủy bỏ."}
    ]
    
    refined_controls = AIService.refine_specification(
        image_path=temp_img_path,
        context=context,
        original_controls=validated_controls,
        qna_list=mock_qna
    )
    
    final_validated_controls = SpecValidator.validate_and_clean_spec(refined_controls)
    print("-> Refined Controls specifications:")
    for c in final_validated_controls:
        print(f"   * STT: {c['STT']} | Control: {c['control_name']} | Initial Value: {c['initial_value']}")
        print(f"     Description: {c['description']}")

    # 6. Generate DOCX
    print("\n[Step 6] Running DOCX Generator service...")
    session_id = "test-session-12345"
    docx_file = DOCXGenerator.generate_docx(
        session_id=session_id,
        context=context,
        controls=final_validated_controls,
        output_dir=config.UPLOAD_DIR
    )
    print(f"-> DOCX Document generated successfully! Saved at:\n   {docx_file}")

    print("\n========================================")
    print("BACKEND SERVICE DRY-RUN PASSED SUCCESSFULLY!")
    print("========================================")

if __name__ == "__main__":
    run_backend_test()

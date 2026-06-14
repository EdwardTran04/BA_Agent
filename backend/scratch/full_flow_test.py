import time
import os
import sys
import logging

# Set stdout to UTF-8
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.config import config
from app.services.ai_service import AIService
from app.services.validator import SpecValidator

logging.basicConfig(level=logging.INFO)

def run_full_flow():
    image_path = os.path.join("uploads", "3e902244-9fb2-48ac-bd89-89397ce7572f.png")
    if not os.path.exists(image_path):
        print(f"Image not found at {image_path}")
        return
        
    print(f"--- Running full flow on {image_path} ---")
    print("AI Provider:", config.AI_PROVIDER)
    print("Gemini Model:", config.GEMINI_MODEL)
    print("OpenRouter Stage 2 Key configured:", bool(config.OPENROUTER_API_KEY_STAGE2))
    print("OpenRouter Stage 2 Model:", config.OPENROUTER_MODEL_STAGE2)
    print("OpenRouter Stage 3 Key configured:", bool(config.OPENROUTER_API_KEY_STAGE3))
    print("OpenRouter Stage 3 Model:", config.OPENROUTER_MODEL_STAGE3)

    # 1. Stage 1
    t0 = time.time()
    try:
        stage1_res = AIService.analyze_screenshot(
            image_path=image_path,
            context="Đặc tả màn hình quản lý kho",
            screen_name="Quản lý kho",
            module="Inventory",
            screen_type="Search",
            role="Warehouse Manager"
        )
        t1 = time.time()
        print(f"Stage 1 completed in {t1 - t0:.2f} seconds.")
    except Exception as e:
        print("Stage 1 failed:", e)
        return

    # Clean and validate
    cleaned_spec, _ = SpecValidator.validate_full_spec(stage1_res)
    
    # 2. Stage 2
    mock_answers = [
        {"id": "Q1", "question": "Mức lương cơ bản của nhân viên có giới hạn trần tối đa hoặc mức lương tối thiểu vùng hay không?", "answer": "Không áp dụng", "answered": True}
    ]
    t2 = time.time()
    try:
        stage2_res = AIService.refine_specification(
            image_path=image_path,
            previous_spec=cleaned_spec,
            user_answers=mock_answers
        )
        t3 = time.time()
        print(f"Stage 2 completed in {t3 - t2:.2f} seconds.")
    except Exception as e:
        print("Stage 2 failed:", e)
        return
        
    # Clean and validate
    cleaned_spec2, _ = SpecValidator.validate_full_spec(stage2_res)
    
    # 3. Stage 3
    t4 = time.time()
    try:
        stage3_res = AIService.qa_check_specification(
            image_path=image_path,
            spec=cleaned_spec2
        )
        t5 = time.time()
        print(f"Stage 3 completed in {t5 - t4:.2f} seconds.")
    except Exception as e:
        print("Stage 3 failed:", e)
        return
        
    print(f"Total time for all 3 stages: {t5 - t0:.2f} seconds.")

if __name__ == "__main__":
    run_full_flow()

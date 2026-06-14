import time
import os
import sys
import logging
import httpx
import json

# Set stdout to UTF-8
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.config import config
from app.services.ai_service import AIService
from app.services.validator import SpecValidator

logging.basicConfig(level=logging.INFO)

# A modified call helper that doesn't send the image
def call_gemini_text_only(system_prompt: str, user_prompt: str) -> dict:
    url = (
        f"https://generativelanguage.googleapis.com/v1beta/models/"
        f"{config.GEMINI_MODEL}:generateContent?key={config.GEMINI_API_KEY}"
    )

    payload = {
        "contents": [
            {
                "role": "user",
                "parts": [
                    {"text": f"{system_prompt}\n\n{user_prompt}"}
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
        return json.loads(text)

def run_test():
    image_path = os.path.join("uploads", "3e902244-9fb2-48ac-bd89-89397ce7572f.png")
    if not os.path.exists(image_path):
        print(f"Image not found at {image_path}")
        return
        
    print("Running Stage 1 first to get spec...")
    stage1_res = AIService.analyze_screenshot(
        image_path=image_path,
        context="Đặc tả màn hình quản lý kho",
        screen_name="Quản lý kho",
        module="Inventory",
        screen_type="Search",
        role="Warehouse Manager"
    )
    cleaned_spec, _ = SpecValidator.validate_full_spec(stage1_res)
    
    # Test Stage 2 text-only
    system_prompt_s2 = AIService._build_stage2_prompt()
    mock_answers = [
        {"id": "Q1", "question": "Mức lương cơ bản của nhân viên có giới hạn trần tối đa hoặc mức lương tối thiểu vùng hay không?", "answer": "Không áp dụng", "answered": True}
    ]
    answers_str = "\n".join([
        f"- Câu hỏi (ID: {item['id']}): {item['question']}\n  Trả lời từ User: {item['answer']}"
        for item in mock_answers
    ])
    user_prompt_s2 = (
        f"Dưới đây là kết quả phân tích trước đó:\n"
        f"```json\n{json.dumps(cleaned_spec, ensure_ascii=False, indent=2)}\n```\n\n"
        f"Dưới đây là câu trả lời của User:\n{answers_str}\n\n"
        f"Hãy cập nhật lại đặc tả màn hình theo hướng dẫn trong system prompt."
    )
    
    print("\nCalling Stage 2 (Text-Only)...")
    t0 = time.time()
    try:
        stage2_res = call_gemini_text_only(system_prompt_s2, user_prompt_s2)
        t1 = time.time()
        print(f"Stage 2 (Text-Only) completed in {t1 - t0:.2f} seconds!")
    except Exception as e:
        print("Stage 2 failed:", e)
        return

    # Test Stage 3 text-only
    system_prompt_s3 = AIService._build_stage3_prompt()
    user_prompt_s3 = (
        f"Hãy kiểm tra lại bảng mô tả control trước khi tạo DOCX:\n\n"
        f"```json\n{json.dumps(stage2_res, ensure_ascii=False, indent=2)}\n```\n\n"
        f"Trả về JSON đã chỉnh sửa theo hướng dẫn trong system prompt."
    )
    
    print("\nCalling Stage 3 (Text-Only)...")
    t2 = time.time()
    try:
        stage3_res = call_gemini_text_only(system_prompt_s3, user_prompt_s3)
        t3 = time.time()
        print(f"Stage 3 (Text-Only) completed in {t3 - t2:.2f} seconds!")
    except Exception as e:
        print("Stage 3 failed:", e)
        return
        
    print(f"Total time for Stage 2 & 3 (Text-Only): {t3 - t0:.2f} seconds.")

if __name__ == "__main__":
    run_test()

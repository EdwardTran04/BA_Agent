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

logging.basicConfig(level=logging.INFO)

def test_real_image():
    image_path = os.path.join("uploads", "3e902244-9fb2-48ac-bd89-89397ce7572f.png")
    if not os.path.exists(image_path):
        print(f"Image not found at {image_path}")
        return
        
    print(f"Testing real image: {image_path} ({os.path.getsize(image_path)} bytes)")
    print("AI Provider:", config.AI_PROVIDER)
    print("Gemini Model:", config.GEMINI_MODEL)
    
    start_time = time.time()
    try:
        res = AIService.analyze_screenshot(
            image_path=image_path,
            context="Đặc tả màn hình quản lý kho",
            screen_name="Quản lý kho",
            module="Inventory",
            screen_type="Search",
            role="Warehouse Manager"
        )
        end_time = time.time()
        print(f"Real Stage 1 call succeeded in {end_time - start_time:.2f} seconds!")
        print("Screen name:", res.get("screen_name"))
        print("Ready to generate:", res.get("ready_to_generate_docx"))
        print("Questions count:", len(res.get("clarifying_questions", [])))
        print("Rows count:", len(res.get("rows", [])))
    except Exception as e:
        end_time = time.time()
        print(f"Real Stage 1 call failed after {end_time - start_time:.2f} seconds.")
        print("Error:", e)

if __name__ == "__main__":
    test_real_image()

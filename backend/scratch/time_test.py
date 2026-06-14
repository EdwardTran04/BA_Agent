import time
import os
import sys
import logging

# Add backend to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.config import config
from app.services.ai_service import AIService

logging.basicConfig(level=logging.INFO)

def test_api():
    print("AI Provider:", config.AI_PROVIDER)
    print("Gemini Key:", config.GEMINI_API_KEY[:10] + "..." if config.GEMINI_API_KEY else "None")
    print("Gemini Model:", config.GEMINI_MODEL)
    
    # Create a dummy small image
    tiny_png_base64 = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNkYP8DAA0bAP0yG64FAAAAAElFTkSuQmCC"
    import base64
    temp_img_path = "test_temp_image.png"
    with open(temp_img_path, "wb") as f:
        f.write(base64.b64decode(tiny_png_base64))
        
    print("\nStarting Stage 1 analysis call...")
    start_time = time.time()
    try:
        res = AIService.analyze_screenshot(
            image_path=temp_img_path,
            context="Đặc tả màn hình thêm mới nhân viên có chức năng lưu và hủy",
            screen_name="Thêm mới nhân viên",
            module="HR",
            screen_type="Create",
            role="HR Admin"
        )
        end_time = time.time()
        print(f"Stage 1 call succeeded in {end_time - start_time:.2f} seconds!")
        print("Screen name from result:", res.get("screen_name"))
        print("Ready to generate DOCX:", res.get("ready_to_generate_docx"))
        print("Number of questions:", len(res.get("clarifying_questions", [])))
        print("Number of rows:", len(res.get("rows", [])))
    except Exception as e:
        end_time = time.time()
        print(f"Stage 1 call failed after {end_time - start_time:.2f} seconds.")
        print("Error:", e)
        
    if os.path.exists(temp_img_path):
        os.remove(temp_img_path)

if __name__ == "__main__":
    test_api()

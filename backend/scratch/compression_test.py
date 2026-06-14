import time
import os
import sys
import logging
from PIL import Image
import io
import base64

# Set stdout to UTF-8
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.config import config
from app.services.ai_service import AIService

logging.basicConfig(level=logging.INFO)

def compress_image_to_base64(image_path: str, max_size=(1200, 1200), quality=80) -> str:
    start_time = time.time()
    with Image.open(image_path) as img:
        # Convert RGBA to RGB if necessary
        if img.mode in ('RGBA', 'LA') or (img.mode == 'P' and 'transparency' in img.info):
            # Create a white background
            bg = Image.new('RGB', img.size, (255, 255, 255))
            bg.paste(img, mask=img.convert('RGBA').split()[3])
            img = bg
        elif img.mode != 'RGB':
            img = img.convert('RGB')
            
        # Resize if larger than max_size
        img.thumbnail(max_size, Image.Resampling.LANCZOS)
        
        # Save to buffer
        buffer = io.BytesIO()
        img.save(buffer, format="JPEG", quality=quality, optimize=True)
        base64_str = base64.b64encode(buffer.getvalue()).decode("utf-8")
        
    print(f"Compression completed in {time.time() - start_time:.4f}s. Size reduced from {os.path.getsize(image_path)} bytes to {len(buffer.getvalue())} bytes.")
    return base64_str

def test_comparison():
    image_path = os.path.join("uploads", "3e902244-9fb2-48ac-bd89-89397ce7572f.png")
    if not os.path.exists(image_path):
        print(f"Image not found at {image_path}")
        return
        
    # Test 1: Compress and call
    print("\n--- TEST 1: Compressed Image ---")
    compressed_base64 = compress_image_to_base64(image_path)
    
    system_prompt = AIService._build_stage1_prompt()
    user_prompt = "Phân tích thiết kế màn hình này.\n\nThông tin bổ sung từ User: Không có thông tin bổ sung."
    
    start_time = time.time()
    try:
        res = AIService._call_gemini_vision(system_prompt, user_prompt, compressed_base64)
        print(f"Compressed Stage 1 succeeded in {time.time() - start_time:.2f} seconds!")
        print("Rows count:", len(res.get("rows", [])))
    except Exception as e:
        print("Error in Compressed Test:", e)

if __name__ == "__main__":
    test_comparison()

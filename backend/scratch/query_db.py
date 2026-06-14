import sys
import os

# Set stdout to UTF-8 to prevent charmap encoding errors on Windows
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

# Add backend to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.database import engine, AnalysisSession
from sqlalchemy.orm import sessionmaker

SessionLocal = sessionmaker(bind=engine)
db = SessionLocal()

try:
    sessions = db.query(AnalysisSession).all()
    print(f"Total sessions: {len(sessions)}")
    for s in sessions:
        print(f"Session ID: {s.id}")
        print(f"  Screen Name: {s.screen_name}")
        print(f"  Status: {s.status}")
        print(f"  Created At: {s.created_at}")
        print(f"  Updated At: {s.updated_at}")
        duration = (s.updated_at - s.created_at).total_seconds() if s.updated_at and s.created_at else 0
        print(f"  Duration (seconds): {duration}")
        print(f"  Ready to Gen: {s.ready_to_generate_docx}")
        print(f"  Questions Count: {len(s.questions) if s.questions else 0}")
        print(f"  Specification Rows: {len(s.specification) if s.specification else 0}")
        print("-" * 50)
finally:
    db.close()

from sqlalchemy import create_engine, Column, String, Text, DateTime, JSON, Boolean, Integer, Float, ForeignKey, func
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from app.config import config
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from sqlalchemy.engine import make_url

# Create engine
# For SQLite: need check_same_thread=False
# For PostgreSQL (Neon.tech): need sslmode=require for cloud connections
def _build_connect_args():
    if config.DATABASE_URL.startswith("sqlite"):
        return {"check_same_thread": False}
    elif config.DATABASE_URL.startswith("postgresql") or config.DATABASE_URL.startswith("postgres"):
        # Neon.tech and other cloud PostgreSQL services require SSL
        return {"sslmode": "require"}
    return {}

engine = create_engine(
    config.DATABASE_URL,
    connect_args=_build_connect_args()
)

# Create sessionmaker
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Declarative Base
Base = declarative_base()


# ──────────────────────────────────────────────
# Main analysis session table
# ──────────────────────────────────────────────

class AnalysisSession(Base):
    __tablename__ = "analysis_sessions"

    id = Column(String(36), primary_key=True, index=True)

    # Screen metadata (provided by user at upload time)
    screen_name = Column(String(255), nullable=True)
    module = Column(String(100), nullable=True)
    screen_type = Column(String(50), nullable=True)  # Create | Edit | View | Search | Approval | Report | Unknown
    role = Column(String(100), nullable=True)
    context = Column(Text, nullable=True)

    # Image storage
    image_path = Column(String(500), nullable=False)

    # AI analysis results
    screen_summary = Column(Text, nullable=True)  # AI-generated summary of the screen
    ready_to_generate_docx = Column(Boolean, default=False, nullable=False)

    # Status: uploaded | analyzing | waiting_user_answer | ready_to_generate | docx_generated | failed
    status = Column(String(50), nullable=False, default="uploaded")

    # Clarifying questions from AI (extended format with priority/reason/affected_controls)
    # Format: [{"id": "Q1", "priority": "critical", "question": "...", "reason": "...", "affected_controls": [...], "answer": null, "answered": false}]
    questions = Column(JSON, nullable=True)

    # AI assumptions
    # Format: [{"content": "...", "risk_level": "high|medium|low"}]
    assumptions = Column(JSON, nullable=True)

    # Control specification rows (extended with confidence/source)
    # Format: [{"STT": 1, "control_name": "...", "data_type": "...", "io": "...", "initial_value": "...", "description": "...", "confidence": 0.9, "source": "visible"}]
    specification = Column(JSON, nullable=True)

    # Generated file reference
    docx_path = Column(String(500), nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    # Relationships
    spec_versions = relationship("ScreenSpec", back_populates="session", cascade="all, delete-orphan")
    generated_files = relationship("GeneratedFile", back_populates="session", cascade="all, delete-orphan")


# ──────────────────────────────────────────────
# Spec versioning table (tracks each AI iteration)
# ──────────────────────────────────────────────

class ScreenSpec(Base):
    __tablename__ = "screen_specs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(String(36), ForeignKey("analysis_sessions.id"), nullable=False, index=True)
    spec_json = Column(JSON, nullable=False)  # Full snapshot of the spec at this version
    version = Column(Integer, nullable=False, default=1)
    created_at = Column(DateTime, default=func.now())

    session = relationship("AnalysisSession", back_populates="spec_versions")


# ──────────────────────────────────────────────
# Generated files tracking table
# ──────────────────────────────────────────────

class GeneratedFile(Base):
    __tablename__ = "generated_files"

    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(String(36), ForeignKey("analysis_sessions.id"), nullable=False, index=True)
    file_name = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    file_type = Column(String(50), nullable=False, default="docx")  # docx | xlsx | pdf
    is_draft = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=func.now())

    session = relationship("AnalysisSession", back_populates="generated_files")


# ──────────────────────────────────────────────
# Database dependency helper
# ──────────────────────────────────────────────

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def create_database_if_not_exists():
    url = config.DATABASE_URL
    if not (url.startswith("postgresql") or url.startswith("postgres")):
        return
    
    try:
        parsed_url = make_url(url)
        db_name = parsed_url.database
        if not db_name:
            return
        
        # Check if database name is safe
        if not all(c.isalnum() or c in ('_', '-') for c in db_name):
            print(f"Invalid database name format: {db_name}")
            return
            
        # Connect to 'postgres' system database
        conn = psycopg2.connect(
            dbname="postgres",
            user=parsed_url.username or "postgres",
            password=parsed_url.password or "",
            host=parsed_url.host or "localhost",
            port=parsed_url.port or 5432
        )
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()
        
        # Check if target database exists
        cursor.execute("SELECT 1 FROM pg_catalog.pg_database WHERE datname = %s;", (db_name,))
        exists = cursor.fetchone()
        
        if not exists:
            from psycopg2.extensions import quote_ident
            safe_db_name = quote_ident(db_name, conn)
            cursor.execute(f"CREATE DATABASE {safe_db_name};")
            print(f"Database '{db_name}' successfully created.")
        else:
            print(f"Database '{db_name}' already exists.")
            
        cursor.close()
        conn.close()
    except Exception as e:
        print(f"Error checking/creating database: {e}")


# Helper to initialize the database (creates tables)
def init_db():
    create_database_if_not_exists()
    Base.metadata.create_all(bind=engine)

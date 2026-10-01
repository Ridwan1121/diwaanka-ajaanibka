"""
Diwaanka Ajaanibka - Database (PostgreSQL)
"""
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Boolean, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import os

# Database URL (Supabase ama Local)
raw_database_url = os.getenv("DATABASE_URL", "").strip()

if raw_database_url.startswith("3.12.0"):
    raw_database_url = raw_database_url[len("3.12.0"):]
    print("⚠️  DATABASE_URL waxa laga saaray '3.12.0' oo horay u qaatay URL-ka")

if not raw_database_url:
    DATABASE_URL = "sqlite:///./diwaanka_ajaanibka.db"
    print("⚠️  DATABASE_URL lama helin - SQLite ayaa la isticmaalayaa")
else:
    if raw_database_url.startswith("postgres://"):
        raw_database_url = raw_database_url.replace("postgres://", "postgresql://", 1)
    DATABASE_URL = raw_database_url
    print(f"✅ DATABASE_URL waa la helay: {DATABASE_URL[:30]}...")

engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class ImmigrantDB(Base):
    __tablename__ = "immigrants"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    country = Column(String)
    region = Column(String)
    entry_point = Column(String)
    district = Column(String)
    passport = Column(String, nullable=True)
    status = Column(String, default="registered")
    face_encoding = Column(Text, nullable=True)
    registered_at = Column(DateTime, default=datetime.utcnow)

class OfficerDB(Base):
    __tablename__ = "officers"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    office = Column(String)
    border = Column(String)
    country = Column(String)
    status = Column(String, default="active")
    created_at = Column(DateTime, default=datetime.utcnow)

class AdminDB(Base):
    __tablename__ = "admins"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    role = Column(String)
    office = Column(String)
    status = Column(String, default="active")
    created_at = Column(DateTime, default=datetime.utcnow)

class UserDB(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    full_name = Column(String)
    email = Column(String, unique=True)
    hashed_password = Column(String)
    role = Column(String, default="officer")
    disabled = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

class ScanHistoryDB(Base):
    __tablename__ = "scan_history"
    id = Column(Integer, primary_key=True, index=True)
    faces_detected = Column(Integer)
    scan_type = Column(String)
    scanned_by = Column(String, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow)

def init_db():
    Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

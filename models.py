from sqlalchemy import Column, Integer, String, Text,DateTime
from db import Base
from datetime import datetime


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    email = Column(String(100), unique=True)
    password = Column(String(100))


class Report(Base):
    __tablename__ = "reports"

    id = Column(Integer, primary_key=True)
    email = Column(String(100))
    score = Column(String(20))
    career = Column(String(100))
    missing_skills = Column(Text)

    created_at = Column(DateTime, default=datetime.utcnow)
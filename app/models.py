from sqlalchemy import Column, Integer, String, DateTime
from datetime import datetime
from .database import Base

class Support(Base):
    __tablename__ = "supports"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    description = Column(String)
    dify_model = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow) 
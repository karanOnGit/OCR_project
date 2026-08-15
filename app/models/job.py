import uuid
from datetime import datetime, timezone
import enum
from sqlalchemy import Column, String, Text, DateTime, Enum, Integer
from app.core.database import Base


class JobStatus(str, enum.Enum):
    UPLOADED = "uploaded"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class Job(Base):
    __tablename__ = "jobs"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    original_filename = Column(String(255), nullable=True)
    image_path = Column(String(500), nullable=False)
    file_size = Column(Integer, nullable=True)
    status = Column(Enum(JobStatus), default=JobStatus.UPLOADED, nullable=False, index=True)
    extracted_text = Column(Text, nullable=True)
    error = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    def to_dict(self):
        return {
            "id": self.id,
            "original_filename": self.original_filename,
            "image_path": self.image_path,
            "file_size": self.file_size,
            "status": self.status.value if isinstance(self.status, JobStatus) else self.status,
            "extracted_text": self.extracted_text,
            "error": self.error,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

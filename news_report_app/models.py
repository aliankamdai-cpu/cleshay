"""Data models for the news report application."""

from dataclasses import dataclass, field
from typing import Optional
from datetime import datetime
import uuid


@dataclass
class NewsItem:
    """Represents a single news item with all its properties."""
    
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    source: str = ""
    title: str = ""
    content: str = ""
    image_path: Optional[str] = None
    coordinates: Optional[str] = None
    recommendation: Optional[str] = None
    incident_time: Optional[str] = None  # Time of the incident/accident
    created_at: datetime = field(default_factory=datetime.now)
    
    def is_valid(self) -> bool:
        """Check if the news item has all required fields."""
        return bool(self.source.strip() and self.title.strip() and self.content.strip())
    
    def has_attachments(self) -> bool:
        """Check if the news item has any attachments."""
        return bool(self.image_path or self.coordinates or self.recommendation or self.incident_time)
    
    def get_attachments_summary(self) -> str:
        """Get a summary of attachments for display."""
        attachments = []
        if self.image_path:
            attachments.append("🖼")
        if self.coordinates:
            attachments.append("📍")
        if self.recommendation:
            attachments.append("💡")
        if self.incident_time:
            attachments.append("⏰")
        return " ".join(attachments) if attachments else "-"
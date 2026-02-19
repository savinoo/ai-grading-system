"""
Student Knowledge Base - Persistent Storage
Stores student profiles and submission history across sessions.
Uses JSON for simplicity (can be upgraded to SQLite/PostgreSQL later).
"""
import json
import logging
from pathlib import Path
from typing import Dict, Optional, List
from datetime import datetime

from src.domain.analytics_schemas import StudentProfile, SubmissionRecord

logger = logging.getLogger(__name__)


class StudentKnowledgeBase:
    """
    Persistent storage for student learning profiles.
    """
    
    def __init__(self, storage_path: str = "data/student_profiles.json"):
        self.storage_path = Path(storage_path)
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        self.profiles: Dict[str, StudentProfile] = {}
        self.load()
    
    def load(self):
        """Load all profiles from disk"""
        if not self.storage_path.exists():
            logger.info(f"No existing profile data at {self.storage_path}")
            return
        
        try:
            with open(self.storage_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Deserialize
            for student_id, profile_dict in data.items():
                self.profiles[student_id] = StudentProfile(**profile_dict)
            
            logger.info(f"Loaded {len(self.profiles)} student profiles")
        except Exception as e:
            logger.error(f"Failed to load profiles: {e}")
            self.profiles = {}
    
    def save(self):
        """Save all profiles to disk"""
        try:
            # Serialize with custom datetime handling
            data = {}
            for student_id, profile in self.profiles.items():
                data[student_id] = profile.model_dump(mode='json')
            
            with open(self.storage_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, default=str)
            
            logger.info(f"Saved {len(self.profiles)} student profiles")
        except Exception as e:
            logger.error(f"Failed to save profiles: {e}")
    
    def add_or_update(self, profile: StudentProfile):
        """Add new profile or update existing"""
        self.profiles[profile.student_id] = profile
        self.save()
    
    def get(self, student_id: str) -> Optional[StudentProfile]:
        """Retrieve student profile"""
        return self.profiles.get(student_id)
    
    def get_all(self) -> List[StudentProfile]:
        """Get all profiles"""
        return list(self.profiles.values())
    
    def delete(self, student_id: str):
        """Remove student profile (for GDPR compliance)"""
        if student_id in self.profiles:
            del self.profiles[student_id]
            self.save()
            logger.info(f"Deleted profile for {student_id}")
    
    def export_student_history(self, student_id: str, output_path: str):
        """Export single student's complete history as JSON"""
        profile = self.get(student_id)
        if not profile:
            logger.warning(f"No profile found for {student_id}")
            return
        
        output = Path(output_path)
        output.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output, 'w', encoding='utf-8') as f:
            json.dump(profile.model_dump(mode='json'), f, indent=2, default=str)
        
        logger.info(f"Exported {student_id} history to {output}")
    
    def clear_old_submissions(self, days_to_keep: int = 365):
        """
        Remove submissions older than specified days.
        For privacy compliance and storage management.
        """
        cutoff = datetime.now().timestamp() - (days_to_keep * 24 * 3600)
        removed_count = 0
        
        for profile in self.profiles.values():
            original_count = len(profile.submissions_history)
            profile.submissions_history = [
                sub for sub in profile.submissions_history
                if sub.timestamp.timestamp() > cutoff
            ]
            removed_count += original_count - len(profile.submissions_history)
        
        if removed_count > 0:
            self.save()
            logger.info(f"Removed {removed_count} old submissions")


# Global instance
_global_kb: Optional[StudentKnowledgeBase] = None

def get_knowledge_base() -> StudentKnowledgeBase:
    """Get or create global knowledge base instance"""
    global _global_kb
    if _global_kb is None:
        _global_kb = StudentKnowledgeBase()
    return _global_kb

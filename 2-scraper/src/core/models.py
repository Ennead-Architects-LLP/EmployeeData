"""
Employee data model for JSON serialization.
"""
from dataclasses import dataclass, asdict, field
from typing import Optional, Dict, Any, List
import json
from datetime import datetime


@dataclass
class EmployeeData:
    """
    Data class representing an employee's information.
    All fields are optional to handle missing data gracefully.
    """
    # Basic Information
    human_name: Optional[str] = None
    email: Optional[str] = None
    bio: Optional[str] = None
    
    # Contact Information
    phone: Optional[str] = None
    mobile: Optional[str] = None
    office_location: Optional[str] = None
    
    # Profile Information
    profile_url: Optional[str] = None
    image_url: Optional[str] = None
    image_local_path: Optional[str] = None
    
    # Professional information
    position: Optional[str] = None
    department: Optional[str] = None
    years_with_firm: Optional[int] = None
    

    # Professional memberships
    memberships: List[str] = field(default_factory=list)
    
    # Education
    education: List[Dict[str, str]] = field(default_factory=list)
    
    # Licenses and registrations
    licenses: List[Dict[str, str]] = field(default_factory=list)
    
    # Projects
    projects: Dict[str, Dict[str, str]] = field(default_factory=dict)
    
    # Recent posts/activity
    recent_posts: List[Dict[str, str]] = field(default_factory=list)
    
    # Contact information
    teams_url: Optional[str] = None
    
    # Social links
    linkedin_url: Optional[str] = None
    website_url: Optional[str] = None
    
    # Scraping metadata
    scraped_at: Optional[str] = None
    profile_id: Optional[str] = None
    
 
    
    def __post_init__(self):
        """Set default values after initialization."""
        if self.scraped_at is None:
            self.scraped_at = datetime.now().isoformat()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the employee data to a dictionary."""
        return asdict(self)
    
    def to_json(self, indent: int = 2) -> str:
        """Convert the employee data to a JSON string."""
        return json.dumps(self.to_dict(), indent=indent, ensure_ascii=False)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'EmployeeData':
        """Create an EmployeeData instance from a dictionary."""
        return cls(**data)
    
    @classmethod
    def from_json(cls, json_str: str) -> 'EmployeeData':
        """Create an EmployeeData instance from a JSON string."""
        data = json.loads(json_str)
        return cls.from_dict(data)
    
    def is_valid(self) -> bool:
        """Check if the employee data has at least basic information."""
        return bool(self.human_name or self.email)
    
    def get_display_name(self) -> str:
        """Get a display name for the employee."""
        if self.human_name:
            return self.human_name
        elif self.email:
            return self.email.split('@')[0]
        else:
            return f"Employee_{self.profile_id or 'unknown'}"
    
    def get_contact_summary(self) -> str:
        """Get a summary of contact information."""
        contacts = []
        if self.email:
            contacts.append(f"Email: {self.email}")
        if self.phone:
            contacts.append(f"Phone: {self.phone}")
        if self.mobile:
            contacts.append(f"Mobile: {self.mobile}")
        if self.office_location:
            contacts.append(f"Office: {self.office_location}")
        
        return " | ".join(contacts) if contacts else "No contact info available"
    
    def __str__(self) -> str:
        """String representation of the employee data."""
        return f"EmployeeData(name={self.get_display_name()}, email={self.email}, valid={self.is_valid()})"
    
    def __repr__(self) -> str:
        """Detailed representation of the employee data."""
        return f"EmployeeData(human_name='{self.human_name}', email='{self.email}', profile_url='{self.profile_url}')"

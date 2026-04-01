"""
models - SQLAlchemy database models.

Tables:
  - Internship:   all scraped job listings (url is UNIQUE)
  - User:         registered accounts (username + hashed password)
"""

from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()


class User(db.Model):
    """Stores registered user accounts."""
    __tablename__ = 'users'

    id            = db.Column(db.Integer, primary_key=True)
    username      = db.Column(db.String(80), unique=True, nullable=False)
    email         = db.Column(db.String(200), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)  # bcrypt hash, never plain text
    created_at    = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        """Safe public representation — never include password_hash."""
        return {
            'id':       self.id,
            'username': self.username,
            'email':    self.email,
        }


class UserProfile(db.Model):
    """Stores user profile preferences and profile metadata."""
    __tablename__ = 'user_profiles'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), unique=True, nullable=False)

    full_name = db.Column(db.String(120))
    university = db.Column(db.String(160))
    degree = db.Column(db.String(160))
    skills = db.Column(db.JSON, default=list)

    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    def to_dict(self):
        return {
            'user_id': self.user_id,
            'full_name': self.full_name,
            'university': self.university,
            'degree': self.degree,
            'skills': self.skills or [],
        }

class Internship(db.Model):
    """Database model for storing internship listings."""
    __tablename__ = 'internships'
    # PRIMARY KEY: Unique identifier for each internship
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    
    # BASIC INFORMATION
    title = db.Column(db.String(500), nullable=False)
    company = db.Column(db.String(200), nullable=False)
    location = db.Column(db.String(200)) # e.g: "London, UK" or "Remote"
    
    
    # JOB DETAILS
    description = db.Column(db.Text) # Full job description (can be very long, hence 'Text' type)
    salary_range = db.Column(db.String(100)) # Example: "£25,000 - £35,000" or "Competitive"
    
    # DATES
    date_posted = db.Column(db.Date) # When the company posted the job
    deadline = db.Column(db.Date) # Last day to apply
    
    # METADATA
    url = db.Column(db.String(1000), unique=True, nullable=False) # Direct link to the job posting
    # 'unique=True' prevents duplicate listings from same URL
    source_website = db.Column(db.String(200)) # e.g: "LinkedIn", "Indeed", "Glassdoor"
    scraped_at = db.Column(db.DateTime, default=datetime.utcnow) # Timestamp when we scraped this listing
    
    # NLP EXTRACTED DATA
    extracted_skills = db.Column(db.JSON) # List of skills found in description: ["Python", "SQL", "React"]
    
    # STATUS TRACKING
    is_active = db.Column(db.Boolean, default=True) # False if job posting is expired/removed
    
    def __repr__(self):
        """String representation for debugging"""
        return f'<Internship {self.company} - {self.title}>'
    
    def to_dict(self):
        """
        Convert database object to dictionary for JSON API responses.
        This is what your Flask API will send to the frontend.
        """
        return {
            'id': self.id,
            'title': self.title,
            'company': self.company,
            'location': self.location,
            'description': self.description,
            'salary_range': self.salary_range,
            'date_posted': self.date_posted.isoformat() if self.date_posted else None,
            'deadline': self.deadline.isoformat() if self.deadline else None,
            'url': self.url,
            'source_website': self.source_website,
            'scraped_at': self.scraped_at.isoformat() if self.scraped_at else None,
            'extracted_skills': self.extracted_skills,
            'is_active': self.is_active
        }


class TrackerEntry(db.Model):
    """User-managed application tracker entries."""
    __tablename__ = 'tracker'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    status = db.Column(db.String(100), nullable=False, default='Not Applied')
    company_name = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(300), nullable=False)
    opening_date = db.Column(db.Date)
    closing_date = db.Column(db.Date)
    link = db.Column(db.String(1000))
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'status': self.status,
            'company': self.company_name,
            'role': self.role,
            'opening_date': self.opening_date.isoformat() if self.opening_date else None,
            'closing_date': self.closing_date.isoformat() if self.closing_date else None,
            'link': self.link,
            'notes': self.notes,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }


class CommunityThread(db.Model):
    """Community threads for discussion and company ratings."""
    __tablename__ = 'community_threads'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    category = db.Column(db.String(50), nullable=False)  # discussion | company-ratings
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    rating = db.Column(db.Integer)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'category': self.category,
            'title': self.title,
            'content': self.content,
            'rating': self.rating,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }


class ThreadReply(db.Model):
    """Replies attached to community threads."""
    __tablename__ = 'thread_replies'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    thread_id = db.Column(db.Integer, db.ForeignKey('community_threads.id', ondelete='CASCADE'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    def to_dict(self):
        return {
            'id': self.id,
            'thread_id': self.thread_id,
            'user_id': self.user_id,
            'content': self.content,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }

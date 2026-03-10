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

class Internship(db.Model):
    """
    Database model for storing internship listings.
    """
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

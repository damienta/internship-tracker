"""
skills.py - Keyword-based skill extraction from job description text.

Scans a job's description for a predefined list of skills/technologies using
word-boundary regex matching. Results are stored in the `extracted_skills` JSON
column and can be used to filter jobs by technology (e.g. ?skills=python).

Usage:
    from skills import extract_skills
    skills = extract_skills("We need a Python developer with SQL and React experience.")
    # ["python", "react", "sql"]
"""

import re

# Skills keyword list
# Each entry is stored and searched in lowercase.
# Word-boundary matching is used so "java" won't match "javascript".

SKILLS: list[str] = [
    # Programming languages
    "python",
    "java",
    "javascript",
    "typescript",
    "c",
    "c++",
    "c#",
    "go",
    "golang",
    "rust",
    "ruby",
    "swift",
    "kotlin",
    "scala",
    "r",
    "matlab",
    "bash",
    "shell",
    "php",
    "perl",
    "haskell",
    "lua",
    "dart",
    # Web / frontend
    "react",
    "angular",
    "vue",
    "next.js",
    "html",
    "css",
    "sass",
    "tailwind",
    "webpack",
    "vite",
    # Backend / API
    "node.js",
    "django",
    "flask",
    "fastapi",
    "spring",
    "express",
    "graphql",
    "rest",
    "grpc",
    # Data / ML / AI
    "tensorflow",
    "pytorch",
    "keras",
    "scikit-learn",
    "pandas",
    "numpy",
    "spark",
    "hadoop",
    "tableau",
    "power bi",
    "excel",
    "machine learning",
    "deep learning",
    "data science",
    "computer vision",
    # Databases
    "sql",
    "postgresql",
    "mysql",
    "sqlite",
    "mongodb",
    "redis",
    "cassandra",
    "dynamodb",
    "bigquery",
    "snowflake",
    # Cloud / DevOps
    "aws",
    "azure",
    "gcp",
    "docker",
    "kubernetes",
    "terraform",
    "ansible",
    "jenkins",
    "github actions",
    "ci/cd",
    "linux",
    "unix",
    # Practices / methodologies
    "git",
    "agile",
    "scrum",
    "jira",
    "tdd",
    "oop",
    "functional programming",
    # Networking / security
    "networking",
    "tcp/ip",
    "cybersecurity",
    "penetration testing",
    "firewalls",
]

# Pre-compile a regex pattern for each skill using word boundaries.
# Multi-word skills (e.g "machine learning") are matched as exact phrases.
_PATTERNS: list[tuple[str, re.Pattern]] = [
    (skill, re.compile(r"\b" + re.escape(skill) + r"\b", re.IGNORECASE))
    for skill in SKILLS
]


def extract_skills(text: str | None) -> list[str]:
    """
    Return a sorted list of skills found in *text*.

    Args:
        text: Raw job description (HTML stripped or plain text). Can be None.

    Returns:
        Sorted list of matched skill strings (lowercase), e.g. ["java", "sql"].
        Returns an empty list if text is None or no skills are found.
    """
    if not text:
        return []

    found: set[str] = set()
    for skill, pattern in _PATTERNS:
        if pattern.search(text):
            found.add(skill)

    return sorted(found)

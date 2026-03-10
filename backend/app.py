"""
app.py - Flask application factory and REST API routes.

Exposes the internship data stored in PostgreSQL via a JSON API.

Endpoints:
    GET /api/jobs           - list jobs (filterable, paginated)
    GET /api/jobs/<id>      - single job by id
    GET /api/stats          - summary counts by source, company, role type
    GET /api/companies      - distinct list of companies in the database
    GET /api/sources        - distinct list of sources in the database
    GET /api/skills         - full list of recognised skill keywords
    POST /api/auth/register - create a new user account
    POST /api/auth/login    - log in and receive a JWT token

Query parameters for GET /api/jobs:
    company   - filter by company name (partial, case-insensitive)
    source    - filter by source_website (exact: lever, greenhouse, bt, hsbc, sap)
    location  - filter by location (partial, case-insensitive)
    keyword   - filter by job title keyword (partial, case-insensitive)
    role_type - filter by role type inferred from title:
                  intern / internship / graduate / grad / placement / apprentice
    skills    - filter by a skill stored in extracted_skills, e.g. ?skills=python
    page      - page number (default 1)
    per_page  - results per page (default 20, max 100)
"""

import os
import bcrypt
from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_jwt_extended import JWTManager, create_access_token
from sqlalchemy import func
from models import db, Internship, User
from scraper.skills import SKILLS
from dotenv import load_dotenv

load_dotenv()

# Keywords used to infer role type from job title
ROLE_TYPE_KEYWORDS = {
    "intern":      ["intern", "internship"],
    "graduate":    ["graduate", "grad"],
    "placement":   ["placement", "year in industry", "sandwich", "industrial"],
}


def title_role_type(title: str) -> str:
    """Return the role type from a job title, or 'other'."""
    t = title.lower()
    for rt, keywords in ROLE_TYPE_KEYWORDS.items():
        if any(kw in t for kw in keywords):
            return rt
    return "other"


def create_app(db_url: str = None) -> Flask:
    """
    Application factory.
    Creates Flask app, binds SQLAlchemy, creates all tables, registers routes.
    """
    app = Flask(__name__)
    CORS(app)  # Allow cross-origin requests from the frontend

    app.config["SQLALCHEMY_DATABASE_URI"] = (
        db_url
        or os.getenv("DATABASE_URL", "sqlite:///internships.db")
    )
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["SQLALCHEMY_ECHO"] = os.getenv("SQLALCHEMY_ECHO", "False") == "True"
    app.config["JWT_SECRET_KEY"] = os.getenv("JWT_SECRET_KEY")

    db.init_app(app)
    JWTManager(app)

    with app.app_context():
        db.create_all()

    # GET /api/jobs
    @app.route("/api/jobs", methods=["GET"])
    def get_jobs():
        """
        Return job listings with optional filters.

        Query params: company, source, location, keyword, role_type, page, per_page
        """
        query = Internship.query.filter_by(is_active=True)

        # --- Filters ---
        company = request.args.get("company", "").strip()
        if company:
            query = query.filter(Internship.company.ilike(f"%{company}%"))

        source = request.args.get("source", "").strip()
        if source:
            query = query.filter(Internship.source_website == source)

        location = request.args.get("location", "").strip()
        if location:
            query = query.filter(Internship.location.ilike(f"%{location}%"))

        keyword = request.args.get("keyword", "").strip()
        if keyword:
            query = query.filter(Internship.title.ilike(f"%{keyword}%"))

        # role_type is inferred from the title - match against known keywords
        role_type = request.args.get("role_type", "").strip().lower()
        if role_type and role_type in ROLE_TYPE_KEYWORDS:
            kws = ROLE_TYPE_KEYWORDS[role_type]
            # Build OR condition: title contains any of the role keywords
            from sqlalchemy import or_
            query = query.filter(
                or_(*[Internship.title.ilike(f"%{kw}%") for kw in kws])
            )

        # skills filter: match a specific skill stored in extracted_skills JSON array
        # e.g. ?skills=python  →  jobs where extracted_skills contains "python"
        skills_param = request.args.get("skills", "").strip().lower()
        if skills_param:
            query = query.filter(Internship.extracted_skills.contains([skills_param]))

        try:
            page     = max(1, int(request.args.get("page", 1)))
            per_page = min(100, max(1, int(request.args.get("per_page", 20))))
        except (ValueError, TypeError):
            page, per_page = 1, 20

        total = query.count()
        internships = (
            query
            .order_by(Internship.scraped_at.desc())
            .offset((page - 1) * per_page)
            .limit(per_page)
            .all()
        )

        return jsonify({
            "page":       page,
            "per_page":   per_page,
            "total":      total,
            "pages":      (total + per_page - 1) // per_page,
            "results":    [i.to_dict() for i in internships],
        })

    # GET /api/jobs/<id>
    @app.route("/api/jobs/<int:job_id>", methods=["GET"])
    def get_job(job_id: int):
        """Return a single job by id."""
        internship = db.get_or_404(Internship, job_id)
        return jsonify(internship.to_dict())
    
    # GET /api/stats
    @app.route("/api/stats", methods=["GET"])
    def get_stats():
        """Return summary statistics about the stored internships."""
        total         = Internship.query.count()
        active        = Internship.query.filter_by(is_active=True).count()
        company_count = db.session.query(func.count(func.distinct(Internship.company))).scalar()

        # Counts per source
        source_rows = (
            db.session.query(Internship.source_website, func.count(Internship.id))
            .group_by(Internship.source_website)
            .all()
        )
        by_source = {src: count for src, count in source_rows}

        # Counts per inferred role type (across active roles only)
        role_type_counts = {"intern": 0, "graduate": 0, "placement": 0, "apprentice": 0, "other": 0}
        all_titles = db.session.query(Internship.title).filter_by(is_active=True).all()
        for (title,) in all_titles:
            role_type_counts[title_role_type(title)] += 1

        return jsonify({
            "total":        total,
            "active":       active,
            "companies":    company_count,
            "by_source":    by_source,
            "by_role_type": role_type_counts,
        })

    # GET /api/companies
    @app.route("/api/companies", methods=["GET"])
    def get_companies():
        """Return a sorted list of all distinct companies in the database."""
        rows = (
            db.session.query(Internship.company)
            .distinct()
            .order_by(Internship.company)
            .all()
        )
        return jsonify([r[0] for r in rows])
    
    # GET /api/auth/register
    @app.route("/api/auth/register", methods=["POST"])
    def register():
        """
        Create a new user account.

        Request body (JSON):
            username  - unique display name
            email     - unique email address
            password  - plain-text password (hashed before storage)

        Returns 201 with the new user object and a JWT token on success.
        Returns 400 if any field is missing or the username/email already exists.
        """
        data = request.get_json(silent=True) or {}
        username = data.get("username", "").strip()
        email = data.get("email", "").strip().lower()
        password = data.get("password", "")

        if not username or not email or not password:
            return jsonify({"error": "username, email and password are required"}), 400

        if len(password) < 8:
            return jsonify({"error": "Password must be at least 8 characters"}), 400

        if User.query.filter_by(username=username).first():
            return jsonify({"error": "Username already taken"}), 400

        if User.query.filter_by(email=email).first():
            return jsonify({"error": "Email already registered"}), 400

        # Hash the password — bcrypt generates a random salt automatically
        password_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

        user = User(username=username, email=email, password_hash=password_hash)
        db.session.add(user)
        db.session.commit()

        token = create_access_token(identity=str(user.id))
        return jsonify({"user": user.to_dict(), "token": token}), 201

    # POST /api/auth/login
    @app.route("/api/auth/login", methods=["POST"])
    def login():
        """
        Log in with username and password.

        Request body (JSON):
            username  - registered username
            password  - plain-text password

        Returns 200 with the user object and a JWT token on success.
        Returns 401 for invalid credentials (deliberately vague to prevent enumeration).
        """
        data = request.get_json(silent=True) or {}
        username = data.get("username", "").strip()
        password = data.get("password", "")

        user = User.query.filter_by(username=username).first()

        # Check user exists and password matches the stored hash
        if not user or not bcrypt.checkpw(password.encode(), user.password_hash.encode()):
            return jsonify({"error": "Invalid username or password"}), 401

        token = create_access_token(identity=str(user.id))
        return jsonify({"user": user.to_dict(), "token": token}), 200

    return app


if __name__ == "__main__":
    flask_app = create_app()
    flask_app.run(debug=True)


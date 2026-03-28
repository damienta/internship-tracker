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
    GET /api/profile/<user_id> - fetch profile settings for one user
    PUT /api/profile/<user_id> - create/update user profile settings
    PATCH /api/account/id - change username/email
    POST /api/account/change-password - change account password
    DELETE /api/account/<user_id> - delete account
    POST /api/auth/register - create a new user account
    POST /api/auth/login    - log in and receive a JWT token

Query parameters for GET /api/jobs:
    company   - filter by company name (partial, case-insensitive)
    source    - filter by source_website (exact: lever, greenhouse, ashby, bt, hsbc, sap)
    location  - filter by location (partial, case-insensitive)
    keyword   - filter by job title keyword (partial, case-insensitive)
    role_type - filter by role type inferred from title:
                  intern / internship / graduate / grad / junior / placement / apprentice
    skills    - filter by a skill stored in extracted_skills, e.g. ?skills=python
    sort      - sorting mode: scraped (default), recent, or deadline
    page      - page number (default 1)
    per_page  - results per page (default 20, max 100)
"""

import os
import re
import bcrypt
from datetime import datetime, date
from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_jwt_extended import JWTManager, create_access_token
from sqlalchemy import func
from models import db, Internship, User, UserProfile, TrackerEntry
from scraper.skills import SKILLS
from dotenv import load_dotenv

load_dotenv()

# Keywords used to infer role type from job title
ROLE_TYPE_KEYWORDS = {
    "intern":      ["intern", "internship"],
    "graduate":    ["graduate", "grad"],
    "junior":      ["junior"],
    "placement":   ["placement", "year in industry", "sandwich", "industrial"],
}

TRACKER_STATUSES = {
    "Not Applied",
    "Applied",
    "Offer",
    "Unsuccessful",
    "First Interview",
    "Second Interview",
    "Final Interview",
    "Phone Screening",
    "Recruiter Call",
}


def title_role_type(title: str) -> str:
    """Return the role type from a job title, or 'other'."""
    t = title.lower()
    for rt, keywords in ROLE_TYPE_KEYWORDS.items():
        if any(kw in t for kw in keywords):
            return rt
    return "other"


def parse_iso_date(value):
    """Parse an ISO date string (YYYY-MM-DD) or return None."""
    if value is None:
        return None

    cleaned = str(value).strip()
    if not cleaned:
        return None

    try:
        return datetime.strptime(cleaned, "%Y-%m-%d").date()
    except ValueError:
        return None


def clean_list_of_strings(values):
    """Normalize an incoming list of strings and remove blanks/duplicates."""
    if not isinstance(values, list):
        return []

    normalized = []
    seen = set()
    for raw in values:
        item = str(raw).strip()
        if not item:
            continue
        key = item.lower()
        if key in seen:
            continue
        seen.add(key)
        normalized.append(item)
    return normalized


def ensure_user_profile(user_id: int) -> UserProfile:
    profile = UserProfile.query.filter_by(user_id=user_id).first()
    if profile:
        return profile

    profile = UserProfile(user_id=user_id)
    db.session.add(profile)
    db.session.commit()
    return profile


def is_valid_email(value: str) -> bool:
    return bool(re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", value))


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

        sort = request.args.get("sort", "scraped").strip().lower()

        try:
            page     = max(1, int(request.args.get("page", 1)))
            per_page = min(100, max(1, int(request.args.get("per_page", 20))))
        except (ValueError, TypeError):
            page, per_page = 1, 20

        if sort == "deadline":
            # Closest deadline first.
            query = query.order_by(
                Internship.deadline.is_(None),
                Internship.deadline.asc(),
                Internship.scraped_at.desc(),
            )
        elif sort in {"recent", "opened"}:
            # Most recently opened first (date_posted), then newest scrape as tie-breaker.
            query = query.order_by(
                Internship.date_posted.is_(None),
                Internship.date_posted.desc(),
                Internship.scraped_at.desc(),
            )
        else:
            # Original default behavior: newest scraped first.
            query = query.order_by(Internship.scraped_at.desc())

        total = query.count()
        internships = (
            query
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
    @app.route("/api/jobs/upcoming", methods=["GET"])
    def get_upcoming_jobs():
        """Return soonest active jobs with deadlines on or after today."""
        try:
            limit = min(25, max(1, int(request.args.get("limit", 3))))
        except (ValueError, TypeError):
            limit = 3

        today = date.today()
        jobs = (
            Internship.query
            .filter(Internship.is_active.is_(True))
            .filter(Internship.deadline.isnot(None))
            .filter(Internship.deadline >= today)
            .order_by(Internship.deadline.asc(), Internship.scraped_at.desc())
            .limit(limit)
            .all()
        )

        return jsonify({"results": [job.to_dict() for job in jobs]})

    # GET /api/jobs/<id>
    @app.route("/api/jobs/<int:job_id>", methods=["GET"])
    def get_job(job_id: int):
        """Return a single job by id."""
        internship = db.get_or_404(Internship, job_id)
        return jsonify(internship.to_dict())

    # GET /api/tracker
    @app.route("/api/tracker", methods=["GET"])
    def get_tracker_entries():
        """Return all tracker entries, newest first."""
        user_id = request.args.get("user_id", type=int)
        if not user_id:
            return jsonify({"error": "user_id is required"}), 400

        entries = (
            TrackerEntry.query
            .filter_by(user_id=user_id)
            .order_by(TrackerEntry.created_at.desc())
            .all()
        )
        return jsonify([entry.to_dict() for entry in entries])

    # POST /api/tracker
    @app.route("/api/tracker", methods=["POST"])
    def create_tracker_entry():
        """Create a tracker entry."""
        data = request.get_json(silent=True) or {}

        status = str(data.get("status", "Not Applied")).strip()
        company = str(data.get("company", "")).strip()
        role = str(data.get("role", "")).strip()
        user_id = data.get("user_id")

        try:
            user_id = int(user_id)
        except (TypeError, ValueError):
            return jsonify({"error": "user_id is required"}), 400

        if status not in TRACKER_STATUSES:
            return jsonify({"error": "Invalid status"}), 400

        if not company or not role:
            return jsonify({"error": "company and role are required"}), 400

        link = str(data.get("link", "")).strip()
        if not link:
            return jsonify({"error": "link is required"}), 400

        if not (link.startswith("http://") or link.startswith("https://")):
            return jsonify({"error": "Link must start with http:// or https://."}), 400

        opening_date = parse_iso_date(data.get("opening_date"))
        closing_date = parse_iso_date(data.get("closing_date"))

        if data.get("opening_date") not in (None, "") and opening_date is None:
            return jsonify({"error": "Dates must be valid."}), 400

        if data.get("closing_date") not in (None, "") and closing_date is None:
            return jsonify({"error": "Dates must be valid."}), 400

        if opening_date and closing_date and closing_date < opening_date:
            return jsonify({"error": "closing_date cannot be earlier than opening_date"}), 400

        entry = TrackerEntry(
            user_id=user_id,
            status=status,
            company_name=company,
            role=role,
            opening_date=opening_date,
            closing_date=closing_date,
            link=link,
            notes=str(data.get("notes", "")).strip() or None,
        )

        db.session.add(entry)
        db.session.commit()
        return jsonify(entry.to_dict()), 201

    # PATCH /api/tracker/<id>
    @app.route("/api/tracker/<int:entry_id>", methods=["PATCH"])
    def update_tracker_entry(entry_id: int):
        """Update editable fields on a tracker entry."""
        entry = db.get_or_404(TrackerEntry, entry_id)
        data = request.get_json(silent=True) or {}

        user_id = data.get("user_id")
        try:
            user_id = int(user_id)
        except (TypeError, ValueError):
            return jsonify({"error": "user_id is required"}), 400

        if entry.user_id != user_id:
            return jsonify({"error": "Forbidden"}), 403

        if "status" in data:
            status = str(data.get("status", "")).strip()
            if status not in TRACKER_STATUSES:
                return jsonify({"error": "Invalid status"}), 400
            entry.status = status

        if "company" in data:
            company = str(data.get("company", "")).strip()
            if not company:
                return jsonify({"error": "company cannot be empty"}), 400
            entry.company_name = company

        if "role" in data:
            role = str(data.get("role", "")).strip()
            if not role:
                return jsonify({"error": "role cannot be empty"}), 400
            entry.role = role

        if "opening_date" in data:
            if data.get("opening_date") not in (None, "") and parse_iso_date(data.get("opening_date")) is None:
                return jsonify({"error": "opening_date must be YYYY-MM-DD"}), 400
            entry.opening_date = parse_iso_date(data.get("opening_date"))

        if "closing_date" in data:
            if data.get("closing_date") not in (None, "") and parse_iso_date(data.get("closing_date")) is None:
                return jsonify({"error": "closing_date must be YYYY-MM-DD"}), 400
            entry.closing_date = parse_iso_date(data.get("closing_date"))

        if entry.opening_date and entry.closing_date and entry.closing_date < entry.opening_date:
            return jsonify({"error": "closing_date cannot be earlier than opening_date"}), 400

        if "link" in data:
            link = str(data.get("link", "")).strip()
            if not link:
                return jsonify({"error": "link is required"}), 400
            if not (link.startswith("http://") or link.startswith("https://")):
                return jsonify({"error": "Link must start with http:// or https://."}), 400
            entry.link = link

        if "notes" in data:
            entry.notes = str(data.get("notes", "")).strip() or None

        db.session.commit()
        return jsonify(entry.to_dict())

    # DELETE /api/tracker/<id>
    @app.route("/api/tracker/<int:entry_id>", methods=["DELETE"])
    def delete_tracker_entry(entry_id: int):
        """Delete a tracker entry for the requesting user."""
        entry = db.get_or_404(TrackerEntry, entry_id)
        user_id = request.args.get("user_id", type=int)

        if not user_id:
            return jsonify({"error": "user_id is required"}), 400

        if entry.user_id != user_id:
            return jsonify({"error": "Forbidden"}), 403

        db.session.delete(entry)
        db.session.commit()
        return jsonify({"ok": True}), 200
    
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
        role_type_counts = {"intern": 0, "graduate": 0, "junior": 0, "placement": 0, "apprentice": 0, "other": 0}
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

    # GET /api/skills
    @app.route("/api/skills", methods=["GET"])
    def get_skills():
        """Return a sorted list of recognised skills."""
        return jsonify(sorted(set(SKILLS)))

    # GET /api/profile/<user_id>
    @app.route("/api/profile/<int:user_id>", methods=["GET"])
    def get_profile(user_id: int):
        """Return profile settings for one user."""
        user = db.get_or_404(User, user_id)
        profile = ensure_user_profile(user.id)

        return jsonify({
            "username": user.username,
            "email": user.email,
            "profile": profile.to_dict(),
        })

    # PUT /api/profile/<user_id>
    @app.route("/api/profile/<int:user_id>", methods=["PUT"])
    def update_profile(user_id: int):
        """Create or update profile settings for one user."""
        user = db.get_or_404(User, user_id)
        profile = ensure_user_profile(user.id)
        data = request.get_json(silent=True) or {}

        profile.full_name = str(data.get("full_name", "")).strip() or None
        profile.university = str(data.get("university", "")).strip() or None
        profile.degree = str(data.get("degree", "")).strip() or None
        profile.skills = clean_list_of_strings(data.get("skills", []))

        db.session.commit()
        return jsonify({"profile": profile.to_dict()})

    # PATCH /api/account/id
    @app.route("/api/account/id", methods=["PATCH"])
    def update_account_identity():
        """Update username/email after confirming the current password."""
        data = request.get_json(silent=True) or {}

        try:
            user_id = int(data.get("user_id"))
        except (TypeError, ValueError):
            return jsonify({"error": "user_id is required"}), 400

        current_password = str(data.get("current_password", ""))
        new_username = str(data.get("username", "")).strip()
        new_email = str(data.get("email", "")).strip().lower()

        if not current_password:
            return jsonify({"error": "current_password is required"}), 400

        if not new_username and not new_email:
            return jsonify({"error": "Provide a new username and/or email"}), 400

        user = db.get_or_404(User, user_id)
        if not bcrypt.checkpw(current_password.encode(), user.password_hash.encode()):
            return jsonify({"error": "Current password is incorrect"}), 401

        if new_username and new_username != user.username:
            if User.query.filter(User.id != user.id, User.username == new_username).first():
                return jsonify({"error": "Username already taken"}), 400
            user.username = new_username

        if new_email and new_email != user.email:
            if not is_valid_email(new_email):
                return jsonify({"error": "Email format is invalid"}), 400
            if User.query.filter(User.id != user.id, User.email == new_email).first():
                return jsonify({"error": "Email already registered"}), 400
            user.email = new_email

        db.session.commit()
        return jsonify({"user": user.to_dict()})

    # POST /api/account/change-password
    @app.route("/api/account/change-password", methods=["POST"])
    def change_password():
        """Change password for a user after verifying the current password."""
        data = request.get_json(silent=True) or {}

        try:
            user_id = int(data.get("user_id"))
        except (TypeError, ValueError):
            return jsonify({"error": "user_id is required"}), 400

        current_password = str(data.get("current_password", ""))
        new_password = str(data.get("new_password", ""))

        if not current_password or not new_password:
            return jsonify({"error": "current_password and new_password are required"}), 400

        if len(new_password) < 8:
            return jsonify({"error": "New password must be at least 8 characters"}), 400

        user = db.get_or_404(User, user_id)
        if not bcrypt.checkpw(current_password.encode(), user.password_hash.encode()):
            return jsonify({"error": "Current password is incorrect"}), 401

        user.password_hash = bcrypt.hashpw(new_password.encode(), bcrypt.gensalt()).decode()
        db.session.commit()
        return jsonify({"ok": True})

    # DELETE /api/account/<user_id>
    @app.route("/api/account/<int:user_id>", methods=["DELETE"])
    def delete_account(user_id: int):
        """Delete account (and related profile/tracker data) after password confirmation."""
        data = request.get_json(silent=True) or {}
        password = str(data.get("password", ""))

        if not password:
            return jsonify({"error": "password is required"}), 400

        user = db.get_or_404(User, user_id)
        if not bcrypt.checkpw(password.encode(), user.password_hash.encode()):
            return jsonify({"error": "Invalid password"}), 401

        TrackerEntry.query.filter_by(user_id=user.id).delete()
        UserProfile.query.filter_by(user_id=user.id).delete()
        db.session.delete(user)
        db.session.commit()
        return jsonify({"ok": True})

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


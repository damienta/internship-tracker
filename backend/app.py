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
    sort      - sorting mode: scraped (default), recent, deadline, or match
    user_id   - required when sort=match to rank by the user's profile skills
    page      - page number (default 1)
    per_page  - results per page (default 20, max 100)
"""

import os
import re
import bcrypt
from datetime import datetime, date, timedelta
from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_jwt_extended import JWTManager, create_access_token
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
from models import db, Internship, User, UserProfile, TrackerEntry, CommunityThread, ThreadReply
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

THREAD_CATEGORIES = {"discussion", "company-ratings"}


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


def _normalize_skill_set(values):
    normalized = set()
    for raw in values or []:
        clean = str(raw).strip().lower()
        if clean:
            normalized.add(clean)
    return normalized


def get_relevant_jobs_for_user(user_id: int, jobs):
    """Return jobs sorted by skill relevance for a user, with match metadata."""
    profile = ensure_user_profile(user_id)
    user_skills = _normalize_skill_set(profile.skills)

    ranked = []
    for job in jobs or []:
        job_skills = _normalize_skill_set(job.extracted_skills)
        matched = sorted(user_skills.intersection(job_skills))
        matched_pretty = ", ".join(matched)
        why_match = (
            f"Matched skills: {matched_pretty} ({len(matched)} match(es))."
            if matched
            else "No direct skill overlap found."
        )
        ranked.append({
            "job": job,
            "match_count": len(matched),
            "matched_skills": matched,
            "why_match": why_match,
        })

    ranked.sort(
        key=lambda item: (item["match_count"], item["job"].scraped_at or datetime.min),
        reverse=True,
    )
    return ranked


def _build_weekly_digest_payload(user: User, profile: UserProfile):
    since = datetime.utcnow() - timedelta(days=7)
    recent_jobs = (
        Internship.query
        .filter(Internship.is_active.is_(True), Internship.scraped_at >= since)
        .order_by(Internship.scraped_at.desc())
        .limit(60)
        .all()
    )

    ranked = get_relevant_jobs_for_user(user.id, recent_jobs)

    newest_opportunities = [job.to_dict() for job in recent_jobs[:15]]
    top_matches = []
    for item in ranked[:10]:
        payload = item["job"].to_dict()
        payload["match_count"] = item["match_count"]
        payload["matched_skills"] = item["matched_skills"]
        payload["why_match"] = item["why_match"]
        top_matches.append(payload)

    return {
        "user_id": user.id,
        "email": user.email,
        "weekly_digest_enabled": bool(profile.weekly_digest_enabled),
        "digest_window_days": 7,
        "generated_at": datetime.utcnow().isoformat(),
        "newest_opportunities": newest_opportunities,
        "top_matches": top_matches,
    }


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
    Creates Flask app, binds SQLAlchemy, registers routes.
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

        if sort == "match":
            user_id = request.args.get("user_id", type=int)
            if not user_id:
                return jsonify({"error": "user_id is required for sort=match"}), 400

            user = db.session.get(User, user_id)
            if not user:
                return jsonify({"error": "User not found"}), 404

            ranked = get_relevant_jobs_for_user(user_id, query.all())
            total = len(ranked)
            page_items = ranked[(page - 1) * per_page : page * per_page]

            results = []
            for item in page_items:
                payload = item["job"].to_dict()
                payload["match_count"] = item["match_count"]
                payload["matched_skills"] = item["matched_skills"]
                payload["why_match"] = item["why_match"]
                results.append(payload)

            return jsonify({
                "page": page,
                "per_page": per_page,
                "total": total,
                "pages": (total + per_page - 1) // per_page,
                "results": results,
            })

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

        internship_id = data.get("internship_id")
        parsed_internship_id = None
        if internship_id not in (None, ""):
            try:
                parsed_internship_id = int(internship_id)
            except (TypeError, ValueError):
                return jsonify({"error": "internship_id must be an integer"}), 400

            if not db.session.get(Internship, parsed_internship_id):
                return jsonify({"error": "Internship not found"}), 404

            existing = TrackerEntry.query.filter_by(user_id=user_id, internship_id=parsed_internship_id).first()
            if existing:
                return jsonify({"error": "Opportunity already added to tracker", "entry": existing.to_dict()}), 409

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
            internship_id=parsed_internship_id,
            status=status,
            company_name=company,
            role=role,
            opening_date=opening_date,
            closing_date=closing_date,
            link=link,
            notes=str(data.get("notes", "")).strip() or None,
        )

        try:
            db.session.add(entry)
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            if parsed_internship_id is not None:
                existing = TrackerEntry.query.filter_by(user_id=user_id, internship_id=parsed_internship_id).first()
                return jsonify({"error": "Opportunity already added to tracker", "entry": existing.to_dict() if existing else None}), 409
            return jsonify({"error": "Failed to create tracker entry"}), 400

        return jsonify(entry.to_dict()), 201

    # POST /api/tracker/from-opportunity
    @app.route("/api/tracker/from-opportunity", methods=["POST"])
    def create_tracker_entry_from_opportunity():
        """Create a tracker entry from an existing opportunity only once per user."""
        data = request.get_json(silent=True) or {}

        try:
            user_id = int(data.get("user_id"))
        except (TypeError, ValueError):
            return jsonify({"error": "user_id is required"}), 400

        try:
            internship_id = int(data.get("internship_id"))
        except (TypeError, ValueError):
            return jsonify({"error": "internship_id is required"}), 400

        user = db.session.get(User, user_id)
        if not user:
            return jsonify({"error": "User not found"}), 404

        internship = db.session.get(Internship, internship_id)
        if not internship:
            return jsonify({"error": "Internship not found"}), 404

        existing = TrackerEntry.query.filter_by(user_id=user_id, internship_id=internship_id).first()
        if existing:
            return jsonify({"error": "Opportunity already added to tracker", "entry": existing.to_dict()}), 409

        entry = TrackerEntry(
            user_id=user_id,
            internship_id=internship.id,
            status="Not Applied",
            company_name=internship.company,
            role=internship.title,
            opening_date=internship.date_posted,
            closing_date=internship.deadline,
            link=internship.url,
            notes=str(data.get("notes", "")).strip() or None,
        )

        try:
            db.session.add(entry)
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            existing = TrackerEntry.query.filter_by(user_id=user_id, internship_id=internship_id).first()
            return jsonify({"error": "Opportunity already added to tracker", "entry": existing.to_dict() if existing else None}), 409

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

    # Turns thread into API-safe JSON with author username included
    def return_thread_author(thread: CommunityThread):
        author = db.session.get(User, thread.user_id)
        payload = thread.to_dict()
        payload["author_username"] = author.username if author else "Unknown"
        return payload

    # Looks up author
    def return_author(reply: ThreadReply):
        author = db.session.get(User, reply.user_id)
        payload = reply.to_dict()
        payload["author_username"] = author.username if author else "Unknown"
        return payload

    # Converts thread model object into plain dictionary
    @app.route("/api/community/threads", methods=["GET"])
    def get_community_threads():
        category = request.args.get("category", "discussion").strip().lower()
        if category not in THREAD_CATEGORIES:
            return jsonify({"error": "Invalid category"}), 400

        threads = (
            CommunityThread.query
            .filter_by(category=category)
            .order_by(CommunityThread.updated_at.desc(), CommunityThread.created_at.desc())
            .all()
        )
        return jsonify([return_thread_author(thread) for thread in threads])

    # Adds a new thread
    @app.route("/api/community/threads", methods=["POST"])
    def create_community_thread():
        data = request.get_json(silent=True) or {}

        try:
            user_id = int(data.get("user_id"))
        except (TypeError, ValueError):
            return jsonify({"error": "user_id is required"}), 400

        user = db.session.get(User, user_id)
        if not user:
            return jsonify({"error": "User not found"}), 404

        category = str(data.get("category", "")).strip().lower()
        if category not in THREAD_CATEGORIES:
            return jsonify({"error": "Invalid category"}), 400

        title = str(data.get("title", "")).strip()
        content = str(data.get("content", "")).strip()
        if not title or not content:
            return jsonify({"error": "title and content are required"}), 400

        rating = None
        if category == "company-ratings":
            try:
                rating = int(data.get("rating"))
            except (TypeError, ValueError):
                rating = None

            if rating is None or rating < 1 or rating > 5:
                return jsonify({"error": "rating must be between 1 and 5"}), 400

        thread = CommunityThread(
            user_id=user_id,
            category=category,
            title=title,
            content=content,
            rating=rating,
        )
        db.session.add(thread)
        db.session.commit()
        return jsonify(return_thread_author(thread)), 201

    # Returns a single thread with author name
    @app.route("/api/community/threads/<int:thread_id>", methods=["GET"])
    def get_community_thread(thread_id: int):
        thread = db.get_or_404(CommunityThread, thread_id)
        return jsonify(return_thread_author(thread))

    # Edit thread (owner only)
    @app.route("/api/community/threads/<int:thread_id>", methods=["PATCH"])
    def update_community_thread(thread_id: int):
        thread = db.get_or_404(CommunityThread, thread_id)
        data = request.get_json(silent=True) or {}

        try:
            user_id = int(data.get("user_id"))
        except (TypeError, ValueError):
            return jsonify({"error": "user_id is required"}), 400

        if thread.user_id != user_id:
            return jsonify({"error": "Only the thread owner can edit this thread"}), 403

        title = str(data.get("title", "")).strip()
        content = str(data.get("content", "")).strip()
        if not title or not content:
            return jsonify({"error": "title and content are required"}), 400

        thread.title = title
        thread.content = content
        thread.updated_at = datetime.utcnow()
        db.session.commit()
        return jsonify(return_thread_author(thread)), 200

    # Delete thread (owner only)
    @app.route("/api/community/threads/<int:thread_id>", methods=["DELETE"])
    def delete_community_thread(thread_id: int):
        thread = db.get_or_404(CommunityThread, thread_id)
        user_id = request.args.get("user_id", type=int)

        if not user_id:
            return jsonify({"error": "user_id is required"}), 400

        if thread.user_id != user_id:
            return jsonify({"error": "Only the thread owner can delete this thread"}), 403

        ThreadReply.query.filter_by(thread_id=thread.id).delete()
        db.session.delete(thread)
        db.session.commit()
        return jsonify({"ok": True}), 200


    # Retrieve replies for a thread
    @app.route("/api/community/threads/<int:thread_id>/replies", methods=["GET"])
    def get_thread_replies(thread_id: int):
        db.get_or_404(CommunityThread, thread_id)
        replies = (
            ThreadReply.query
            .filter_by(thread_id=thread_id)
            .order_by(ThreadReply.created_at.asc())
            .all()
        )
        return jsonify([return_author(reply) for reply in replies])

    # Send reply to a thread
    @app.route("/api/community/threads/<int:thread_id>/replies", methods=["POST"])
    def create_thread_reply(thread_id: int):
        thread = db.get_or_404(CommunityThread, thread_id)
        data = request.get_json(silent=True) or {}

        try:
            user_id = int(data.get("user_id"))
        except (TypeError, ValueError):
            return jsonify({"error": "user_id is required"}), 400

        user = db.session.get(User, user_id)
        if not user:
            return jsonify({"error": "User not found"}), 404

        content = str(data.get("content", "")).strip()
        if not content:
            return jsonify({"error": "content is required"}), 400

        reply = ThreadReply(thread_id=thread.id, user_id=user_id, content=content)
        db.session.add(reply)

        # Bump thread ordering so active threads surface first.
        thread.updated_at = datetime.utcnow()

        db.session.commit()
        return jsonify(return_author(reply)), 201

    # Edit reply (owner only)
    @app.route("/api/community/replies/<int:reply_id>", methods=["PATCH"])
    def update_thread_reply(reply_id: int):
        reply = db.get_or_404(ThreadReply, reply_id)
        data = request.get_json(silent=True) or {}

        try:
            user_id = int(data.get("user_id"))
        except (TypeError, ValueError):
            return jsonify({"error": "user_id is required"}), 400

        if reply.user_id != user_id:
            return jsonify({"error": "Only the reply owner can edit this reply"}), 403

        content = str(data.get("content", "")).strip()
        if not content:
            return jsonify({"error": "content is required"}), 400

        reply.content = content
        db.session.commit()
        return jsonify(return_author(reply)), 200

    # Delete reply (owner only)
    @app.route("/api/community/replies/<int:reply_id>", methods=["DELETE"])
    def delete_thread_reply(reply_id: int):
        reply = db.get_or_404(ThreadReply, reply_id)
        user_id = request.args.get("user_id", type=int)

        if not user_id:
            return jsonify({"error": "user_id is required"}), 400

        if reply.user_id != user_id:
            return jsonify({"error": "Only the reply owner can delete this reply"}), 403

        db.session.delete(reply)
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
        if "weekly_digest_enabled" in data:
            profile.weekly_digest_enabled = bool(data.get("weekly_digest_enabled"))

        db.session.commit()
        return jsonify({"profile": profile.to_dict()})

    # GET /api/digest/weekly/<user_id>
    @app.route("/api/digest/weekly/<int:user_id>", methods=["GET"])
    def get_weekly_digest(user_id: int):
        """Return a 7-day digest with newest opportunities and best skill matches."""
        user = db.get_or_404(User, user_id)
        profile = ensure_user_profile(user.id)
        return jsonify(_build_weekly_digest_payload(user, profile))

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

        user_thread_ids = [row[0] for row in db.session.query(CommunityThread.id).filter_by(user_id=user.id).all()]
        if user_thread_ids:
            ThreadReply.query.filter(ThreadReply.thread_id.in_(user_thread_ids)).delete(synchronize_session=False)
        ThreadReply.query.filter_by(user_id=user.id).delete()
        CommunityThread.query.filter_by(user_id=user.id).delete()
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


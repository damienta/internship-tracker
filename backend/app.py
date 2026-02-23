"""
app.py - Flask application factory and REST API routes.

Exposes the internship data stored in PostgreSQL via a JSON API.

Endpoints:
    GET /api/internships - list all internships (supports ?company= and ?source= filters)
    GET /api/internships/<id> - single internship by id
    GET /api/stats - summary counts by source and company
"""

import os
from flask import Flask, jsonify, request
from models import db, Internship
from dotenv import load_dotenv

load_dotenv()


def create_app(db_url: str = None) -> Flask:
    """
    Application factory.
    Creates Flask app, binds SQLAlchemy, creates all tables, registers routes.
    """
    app = Flask(__name__)

    app.config["SQLALCHEMY_DATABASE_URI"] = (
        db_url
        or os.getenv("DATABASE_URL", "sqlite:///internships.db")
    )
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["SQLALCHEMY_ECHO"] = os.getenv("SQLALCHEMY_ECHO", "False") == "True"

    db.init_app(app)

    with app.app_context():
        db.create_all()  # Creates the internships table if it doesn't exist

    # Routes
    @app.route("/api/internships", methods=["GET"])
    def get_internships():
        """Return all active internship listings. Supports ?company= and ?source= filters."""
        query = Internship.query.filter_by(is_active=True)

        company = request.args.get("company")
        if company:
            query = query.filter(Internship.company.ilike(f"%{company}%"))

        source = request.args.get("source")
        if source:
            query = query.filter(Internship.source_website == source)

        internships = query.order_by(Internship.scraped_at.desc()).all()
        return jsonify([i.to_dict() for i in internships])

    @app.route("/api/internships/<int:internship_id>", methods=["GET"])
    def get_internship(internship_id: int):
        """Return a single internship by id."""
        internship = db.get_or_404(Internship, internship_id)
        return jsonify(internship.to_dict())

    @app.route("/api/stats", methods=["GET"])
    def get_stats():
        """Return basic statistics about the database."""
        total   = Internship.query.count()
        active  = Internship.query.filter_by(is_active=True).count()
        companies = db.session.query(Internship.company).distinct().count()
        sources = db.session.query(Internship.source_website).distinct().count()
        return jsonify({
            "total": total,
            "active": active,
            "companies": companies,
            "sources": sources,
        })

    return app

if __name__ == "__main__":
    flask_app = create_app()
    flask_app.run(debug=True)

from datetime import datetime, timezone

import pytest

from app import create_app
from models import Internship, db


@pytest.fixture(scope="session")
def app():
	app = create_app(db_url="sqlite:///:memory:")
	app.config["TESTING"] = True
	app.config["JWT_SECRET_KEY"] = "test-secret"

	with app.app_context():
		db.create_all()
		db.session.add_all([
			Internship(
				title="Software Engineering Intern",
				company="Alpha Corp",
				location="London, UK",
				url="https://example.com/1",
				source_website="greenhouse",
				is_active=True,
				scraped_at=datetime.now(timezone.utc),
			),
			Internship(
				title="Graduate Software Engineer",
				company="Beta Ltd",
				location="London, UK",
				url="https://example.com/2",
				source_website="lever",
				is_active=True,
				scraped_at=datetime.now(timezone.utc),
			),
			Internship(
				title="Industrial Placement Engineer",
				company="Charlie Inc",
				location="Manchester, UK",
				url="https://example.com/3",
				source_website="lever",
				is_active=True,
				scraped_at=datetime.now(timezone.utc),
			),
			Internship(
				title="Technology Graduate Scheme",
				company="Delta Co",
				location="Birmingham, UK",
				url="https://example.com/4",
				source_website="bt",
				is_active=True,
				scraped_at=datetime.now(timezone.utc),
			),
			Internship(
				title="Expired Intern Role",
				company="Echo Ltd",
				location="London, UK",
				url="https://example.com/5",
				source_website="bt",
				is_active=False,
				scraped_at=datetime.now(timezone.utc),
			),
		])
		db.session.commit()

	yield app


@pytest.fixture(scope="function")
def client(app):
	return app.test_client()

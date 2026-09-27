# Tracker.dev

A full-stack platform for students hunting internships, placements and graduate roles. It pulls live listings from company career sites and job boards, lets you track every application in one place, and gives you a community space for CVs, cover letters and interview advice.

**Live demo:** [internship-tracker-ruby.vercel.app](https://internship-tracker-ruby.vercel.app)

Built as my dissertation project (Sep 2025 – Apr 2026).

![Tracker.dev home page](docs/screenshots/home.png)

## Features

### Opportunities
Browse every scraped role in one feed. Filter by keyword, company, location, source and role type (internship, placement, graduate, junior), or by a skill such as `python`. Sort by most recent, closest deadline, or **best match**, which ranks roles against the skills saved in your profile.

![Opportunities page](docs/screenshots/opportunities.png)

### Application tracker
Add any role to your tracker, straight from Opportunities or by hand, and move it through each stage: Not Applied, Applied, Phone Screening, Recruiter Call, First/Second/Final Interview, Offer or Unsuccessful. Each entry keeps its link, opening and closing dates, and your notes.

![Application tracker](docs/screenshots/tracker.png)

### Community
CV and cover letter templates and examples to download, how-to guides, a discussion board, and company ratings where students share what applying was really like.

![Community hub](docs/screenshots/community.png)

### Profile and settings
Save your university, course and skills (these power the best-match sort), manage notifications, and change your username, email or password.

![Settings page](docs/screenshots/settings.png)

## How it works

```
GitHub Actions (every 6 hours)
        │  run_scrapers.py
        ▼
 Scrapers ──► PostgreSQL (Neon) ◄── Flask REST API (Render) ◄── React frontend (Vercel)
```

- **Scrapers** (`backend/scraper/`) collect roles from three kinds of source: company career pages (BT, HSBC, SAP), and the Greenhouse, Lever and Ashby job-board APIs. Skills are pulled out of each job description, duplicate URLs are skipped, and listings that have closed are marked inactive. See the [scraper README](backend/scraper/README.md) for details.
- **Backend** (`backend/`) is a Flask API using SQLAlchemy, with bcrypt password hashing and JWT login tokens. Tables are created automatically on first start.
- **Frontend** (`frontend/`) is React 19 with Vite, Tailwind CSS and React Router.
- **CI**: GitHub Actions runs the Pytest suite on every backend change, and runs the scrapers on a schedule.

## Tech stack

| Area | Tools |
|---|---|
| Frontend | React, Vite, Tailwind CSS, React Router, Axios |
| Backend | Python, Flask, SQLAlchemy, Flask-JWT-Extended, bcrypt |
| Data collection | Requests, BeautifulSoup, Greenhouse / Lever / Ashby APIs |
| Database | PostgreSQL |
| Testing and CI | Pytest, GitHub Actions |
| Hosting | Vercel (frontend), Render (API), Neon (database) |

## Running it locally

You need Python 3.11, Node.js 20+ and a PostgreSQL database (a local install or a free Neon project both work).

### Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

Create `backend/.env`:

```
DATABASE_URL=postgresql://user:password@localhost:5432/internship_tracker
JWT_SECRET_KEY=any-long-random-string
```

Then start the API on http://localhost:5000, and optionally fill the database with real listings:

```bash
python app.py
python run_scrapers.py
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Vite proxies `/api` requests to the backend on port 5000. For a deployed build, set `VITE_API_BASE_URL` to your API's URL.

### Tests

```bash
cd backend
python -m pytest -q
```

The tests use an in-memory SQLite database, so they don't need PostgreSQL.

# Altavisor

A production-grade admin panel with a dark industrial design aesthetic. Built with Next.js + MUI on the frontend and Django REST Framework on the backend.

## Tech Stack

**Frontend**
- Next.js 14 (App Router) + TypeScript
- Material UI (MUI) v5
- Google Fonts — Syne (headings) + DM Sans (body)

**Backend**
- Django 4.2 + Django REST Framework
- Simple JWT (access: 60 min, refresh: 7 days)
- SQLite (dev) / PostgreSQL (prod)
- python-decouple for env config

## Project Structure

```
altavisor/
├── frontend/        # Next.js app
└── backend/         # Django project
    ├── accounts/    # Auth app (custom User model, JWT endpoints)
    ├── people/      # People management app
    └── altavisor/   # Django project config
```

## Getting Started

Both servers must run simultaneously. Next.js proxies `/api/*` to Django so there are no CORS issues in dev.

### Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env          # then edit .env with your values
.venv/bin/python manage.py migrate
.venv/bin/python manage.py createsuperuser
.venv/bin/python manage.py runserver  # http://localhost:8000
```

### Frontend

```bash
cd frontend
npm install
npm run dev                   # http://localhost:3000
```

## API Reference

All requests to protected endpoints require `Authorization: Bearer <access_token>`.

### Auth — `/api/auth/`

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| POST | `login/` | public | Body: `{ email, password }` → `{ access, refresh, user }` |
| POST | `refresh/` | public | Body: `{ refresh }` → `{ access }` |
| POST | `logout/` | Bearer | Body: `{ refresh }` — blacklists token |
| GET | `me/` | Bearer | Current user profile |
| PATCH | `me/` | Bearer | Body: `{ full_name }` |
| POST | `change-password/` | Bearer | Body: `{ current_password, new_password, new_password_confirm }` |
| POST | `register/` | admin | Body: `{ email, password, full_name, role }` |
| GET | `sso/` | public | Placeholder — returns 501 |

Login stores `access_token` in `localStorage`. The frontend auth guard in `page.tsx` redirects to `/login` if absent.

---

### People — `/api/people/`

#### Persons

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| GET | `persons/` | Bearer | List persons. Query params: `search`, `is_active`, `category_id`, `page`, `page_size` (max 200) |
| POST | `persons/` | Bearer | Create person. Returns 409 with `candidates` on duplicate detection |
| POST | `persons/duplicate-check/` | Bearer | Body: `{ first_name, last_name, email?, phone? }` — dry-run duplicate check |
| GET | `persons/<id>/` | Bearer | Full person detail |
| PATCH | `persons/<id>/` | Bearer | Partial update. Returns 409 with `candidates` on duplicate detection |
| POST | `persons/<id>/deactivate/` | Bearer | Soft-deactivate; closes all active org relations and category assignments |
| POST | `persons/<id>/merge/` | admin | Body: `{ target_id }` — merges source into target (returns 501 until fully implemented) |

#### Person → Categories

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| GET | `persons/<id>/categories/` | Bearer | List category assignments. Query: `active_only` (default `true`) |
| POST | `persons/<id>/categories/` | Bearer | Body: `{ category_id }` — assign a category |
| DELETE | `persons/<id>/categories/<cat_id>/` | Bearer | Remove category assignment |

#### Person → Addresses

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| GET | `persons/<id>/addresses/` | Bearer | List addresses. Query: `active_only` (default `true`) |
| POST | `persons/<id>/addresses/` | Bearer | Add an address |
| PATCH | `persons/<id>/addresses/<addr_id>/` | Bearer | Partial update an address |

#### Person → Notes

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| GET | `persons/<id>/notes/` | Bearer | List notes (newest first) |
| POST | `persons/<id>/notes/` | Bearer | Body: `{ body }` — append an immutable note |

#### Person → Organizations

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| GET | `persons/<id>/organizations/` | Bearer | List org relations. Query: `active_only` (default `false`) |
| POST | `persons/<id>/organizations/` | Bearer | Link person to an organization |
| PATCH | `persons/<id>/organizations/<rel_id>/` | Bearer | Update relation fields |
| POST | `persons/<id>/organizations/<rel_id>/close/` | Bearer | Close an active org relation |

#### Person → Attachments

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| GET | `persons/<id>/attachments/` | Bearer | List attachments (file upload deferred to phase 2) |

#### Categories

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| GET | `categories/` | Bearer | List categories. Query: `is_active`, `is_system` |
| POST | `categories/create/` | admin | Create a category |
| PATCH | `categories/<id>/` | admin | Partial update a category |
| POST | `categories/<id>/deactivate/` | admin | Soft-deactivate a category |

## Navigation

| Tab | Sub-tabs |
|---|---|
| Overview | Summary, Activity Log, System Health |
| Settings | General, Appearance, Integrations, Advanced |
| Users | Accounts, Roles & Permissions, Invites |
| Security | Authentication, Audit Trail, Policies |
| Analytics | Usage, Reports, Exports |
| Infrastructure | Environments, Deployments, Logs |

## Environment Variables

Copy `backend/.env.example` to `backend/.env` and fill in your values. Required keys:

| Key | Description |
|---|---|
| `SECRET_KEY` | Django secret key — generate a strong random value for production |
| `DEBUG` | `True` for dev, `False` for prod |
| `ALLOWED_HOSTS` | Comma-separated list of allowed hostnames |
| `CORS_ALLOWED_ORIGINS` | Comma-separated list of allowed frontend origins |

## Production Notes

- Replace `SECRET_KEY` with a strong random value: `python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"`
- Set `DEBUG=False`
- Switch `DATABASES` in `settings.py` to PostgreSQL
- Run `manage.py collectstatic` and serve static files via a CDN or Nginx

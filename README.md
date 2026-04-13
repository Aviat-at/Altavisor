# Altavisor ERP

A production-grade, full-stack ERP platform with a dark industrial design aesthetic. Built with Next.js + MUI on the frontend and Django REST Framework on the backend. Designed around a master-data-first architecture with 26 core business modules organized across five layers: Foundation/Control, Master Data/Classification, Operations, Support/Intelligence, and Infrastructure.

> For deeper technical documentation see [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md), [`docs/MODULES.md`](docs/MODULES.md), and the diagrams under [`docs/diagrams/`](docs/diagrams/).

---

## Tech Stack

**Frontend**

| Package | Version | Role |
|---|---|---|
| `next` | 16.2.1 | App Router, SSR, API proxy rewrites |
| `react` / `react-dom` | 18.x | Component model |
| `@mui/material` | 5.15.20 | Component library |
| `@mui/icons-material` | 5.15.20 | Icon set (Rounded variants) |
| `typescript` | 5.x | Strict type safety |
| DM Sans / Syne | — | Body font / heading font (Google Fonts) |

**Backend**

| Package | Role |
|---|---|
| Django 4.2 + Django REST Framework | API server |
| `djangorestframework-simplejwt` | JWT auth (access: 60 min, refresh: 7 days) |
| SQLite (dev) / PostgreSQL (prod) | Database |
| `python-decouple` | Env config via `.env` |

---

## Project Structure

```
altavisor/
├── docs/                        # Technical documentation
│   ├── ARCHITECTURE.md          # Tech stack, folder conventions, theme, auth flow
│   ├── MODULES.md               # Every module and dashboard documented
│   └── diagrams/
│       ├── component-tree.mmd   # Mermaid: full component hierarchy
│       └── nav-flow.mmd         # Mermaid: navigation flow between all tabs
│
├── frontend/
│   └── src/
│       ├── app/
│       │   ├── layout.tsx       # Root HTML shell, font loading, ThemeRegistry
│       │   ├── page.tsx         # Auth guard — redirects to /login if no token
│       │   └── login/
│       │       └── page.tsx     # Login page — email/password + SSO button
│       ├── components/
│       │   ├── AdminShell.tsx   # Top-level layout, owns activeTab/activeSubTab state
│       │   ├── TopBar.tsx       # Fixed 52px header
│       │   ├── Sidebar.tsx      # Fixed 72px vertical icon nav
│       │   ├── FooterBar.tsx    # Fixed 32px footer
│       │   ├── MainCanvas.tsx   # Resolves and renders the active module
│       │   ├── ThemeRegistry.tsx# MUI provider + useColorMode() hook
│       │   ├── modules/         # New pattern — folder per module
│       │   │   ├── overview/    # Overview module
│       │   │   ├── customers/   # Customers module (mock data, backend pending)
│       │   │   └── people/      # People module (fully wired to backend)
│       │   └── dashboards/      # Legacy pattern — single file per section
│       │       ├── OverviewDashboard.tsx
│       │       ├── SettingsDashboard.tsx
│       │       ├── UsersDashboard.tsx
│       │       ├── SecurityDashboard.tsx
│       │       ├── AnalyticsDashboard.tsx
│       │       └── InfrastructureDashboard.tsx
│       ├── config/
│       │   └── nav.ts           # Single source of truth for all tabs and sub-tabs
│       └── lib/
│           └── theme.ts         # MUI theme factory — dark + light, all design tokens
│
└── backend/
    ├── accounts/                # Auth app — custom User model, JWT endpoints
    ├── people/                  # Person module — profiles, categories, org relationships
    └── altavisor/               # Django project config
```

---

## Getting Started

Both servers must run simultaneously. Next.js proxies all `/api/*` requests to Django (`http://127.0.0.1:8000`) so there are no CORS issues in development.

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
npm run dev     # development server  → http://localhost:3000
npm run build   # production build
npm run start   # serve production build
npm run lint    # ESLint via next lint
```

---

## Development Status

The project is in **active early development**. Core infrastructure, authentication, and the first master data module are complete. The remaining modules are planned and queued in priority order.

### Legend

| Symbol | Meaning |
|---|---|
| ✅ Complete | Backend + frontend fully implemented |
| 🔨 In Progress | Partially implemented or frontend-only shell |
| ⬜ Planned | Not yet started |

---

### Module Development Status

#### A. Foundation and Control

| # | Module | Backend | Frontend | Status |
|---|---|---|---|---|
| 1 | Dashboard and Workspace | ✅ | ✅ | ✅ Complete |
| 2 | Settings and System Administration | — | 🔨 Shell | 🔨 In Progress |
| 3 | User Management | ✅ | 🔨 Shell | 🔨 In Progress |
| 4 | Role and Permission Management | 🔨 Partial | 🔨 Shell | 🔨 In Progress |
| 5 | Authentication and Security | ✅ | 🔨 Shell | 🔨 In Progress |
| 6 | Audit Log and Activity Tracking | ⬜ | 🔨 Shell | 🔨 In Progress |

#### B. Master Data and Classification

| # | Module | Backend | Frontend | Status |
|---|---|---|---|---|
| 7 | Person Module (incl. categories) | ✅ | ✅ | ✅ Complete |
| 8 | Partner Company Module (incl. categories) | ⬜ | ⬜ | ⬜ Planned |
| 9 | Organization–Person Relationship Management | ✅ | ✅ | ✅ Complete |
| 10 | Product and Service Management | ⬜ | ⬜ | ⬜ Planned |
| 11 | Pricing, Discount, and Access Profile Management | ⬜ | ⬜ | ⬜ Planned |

#### C. Operational Business Modules

| # | Module | Backend | Frontend | Status |
|---|---|---|---|---|
| 12 | Customer Management | ⬜ | 🔨 Shell | 🔨 In Progress |
| 13 | Supplier Management | ⬜ | ⬜ | ⬜ Planned |
| 14 | Inventory and Warehouse Management | ⬜ | ⬜ | ⬜ Planned |
| 15 | Sales Management | ⬜ | ⬜ | ⬜ Planned |
| 16 | Purchase Management | ⬜ | ⬜ | ⬜ Planned |
| 17 | Finance and Accounting | ⬜ | ⬜ | ⬜ Planned |
| 18 | Commission Management | ⬜ | ⬜ | ⬜ Planned |
| 19 | Workflow and Approval Management | ⬜ | ⬜ | ⬜ Planned |

#### D. Support and Intelligence

| # | Module | Backend | Frontend | Status |
|---|---|---|---|---|
| 20 | Notification and Communication | ⬜ | ⬜ | ⬜ Planned |
| 21 | Document and Attachment Management | 🔨 List only | ⬜ | ⬜ Planned |
| 22 | Reporting and Analytics | — | 🔨 Shell | 🔨 In Progress |
| 23 | AI Integration | ⬜ | ⬜ | ⬜ Planned |
| 24 | API and Integration | ⬜ | ⬜ | ⬜ Planned |
| 25 | Dashboard, Search, and Global Navigation Services | 🔨 Partial | ✅ | 🔨 In Progress |

#### E. Infrastructure

| # | Module | Backend | Frontend | Status |
|---|---|---|---|---|
| 26 | DevOps, Deployment, and Environment Management | ⬜ | 🔨 Shell | ⬜ Planned |

---

### What Is Built

#### Backend (Django REST Framework)

**Authentication and Security** — `backend/accounts/`
- Custom `User` model with email as login identity; roles: `super_admin | admin | analyst | viewer`
- JWT-based auth via `djangorestframework-simplejwt` (access: 60 min, refresh: 7 days, rotation + blacklist)
- Endpoints: login, refresh, logout, profile (`me`), change password, register (admin only), SSO placeholder

**Person Module** — `backend/people/`
- Full person CRUD with duplicate detection (returns `candidates` on 409)
- Soft deactivation — closes all active org relations and category assignments
- Person merge stub (returns 501, full implementation pending)
- Sub-resources: categories (many-to-many), addresses, notes (immutable append), org relationships, attachments (list only — file upload deferred)

**Person Category Management** (part of Person Module)
- Category master table with system and custom category support
- Protected system categories (cannot be deactivated)
- Many-to-many assignment to persons with audit tracking

**Organization–Person Relationship Management**
- Links persons to partner companies with relationship type, designation, department
- Primary contact flag, start/end date tracking, close relationship action

#### Frontend (Next.js + MUI)

**Fully implemented** (complete UI and data flow):
- **People** — Directory, Profile, Categories, Settings sub-tabs
- **Overview/Dashboard** — Summary, Activity Log, System Health

**Shell only** (navigation and layout wired, backend not connected):
- **Customers** — Dashboard, Management, Profiles, Settings
- **Settings** — General, Appearance, Integrations, Advanced
- **Users** — Accounts, Roles & Permissions, Invites
- **Security** — Authentication, Audit Trail, Policies
- **Analytics** — Usage, Reports, Exports
- **Infrastructure** — Environments, Deployments, Logs

---

### What Needs to Be Built Next

**Priority 1 — Complete master data layer:**

1. **Partner Company Module** — company registration, legal info, addresses, notes, status lifecycle, and built-in company category management (mirrors Person Module pattern)
2. **Customer Management** — wire existing frontend shell to backend; register customer from existing person or company record
3. **Supplier Management** — register supplier from partner company, contact mapping, payment terms

**Priority 2 — Operational layer:**

4. Product and Service Management
5. Inventory and Warehouse Management
6. Pricing, Discount, and Access Profile Management
7. Sales Management (quotations → orders → fulfillment)
8. Purchase Management (requisitions → orders → goods receipt)
9. Finance and Accounting (invoices, payments, receivables/payables)
10. Commission Management
11. Workflow and Approval Management

**Priority 3 — Support, intelligence, and infrastructure:**

12. Notification and Communication
13. Document and Attachment Management (file upload)
14. Reporting and Analytics (full implementation)
15. Audit Log and Activity Tracking
16. AI Integration
17. API and Integration
18. DevOps / Deployment

---

## Core Module Architecture

The ERP is built around a **master-data-first design**. Person and Partner Company are the reusable core entities. Business behavior (discounts, pricing, access) is driven through configurable profiles, not hardcoded logic. Operational modules reuse these core entities rather than duplicating them.

```
A. Foundation and Control
   Dashboard · Settings · User Management · RBAC · Authentication · Audit Logging

B. Master Data and Classification
   Person (+ categories) · Partner Company (+ categories) · Product · Pricing/Discount/Access Profiles

C. Operational Business Modules
   Customer · Supplier · Inventory · Sales · Purchase · Finance · Commission · Workflow

D. Support and Intelligence
   Notifications · Documents · Reporting · AI Integration · API/Integrations · Global Navigation

E. Infrastructure
   DevOps · Deployment · Environment Management
```

---

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
| GET | `persons/` | Bearer | List persons. Query: `search`, `is_active`, `category_id`, `page`, `page_size` (max 200) |
| POST | `persons/` | Bearer | Create person. Returns 409 with `candidates` on duplicate detection |
| POST | `persons/duplicate-check/` | Bearer | Body: `{ first_name, last_name, email?, phone? }` — dry-run duplicate check |
| GET | `persons/<id>/` | Bearer | Full person detail |
| PATCH | `persons/<id>/` | Bearer | Partial update. Returns 409 with `candidates` on duplicate detection |
| POST | `persons/<id>/deactivate/` | Bearer | Soft-deactivate; closes all active org relations and category assignments |
| POST | `persons/<id>/merge/` | admin | Body: `{ target_id }` — merges source into target (returns 501 until implemented) |

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
| POST | 	`persons/<id>/organizations/` | Bearer | Link person to an organization |
| PATCH | `persons/<id>/organizations/<rel_id>/` | Bearer | Update relation fields |
| POST | `persons/<id>/organizations/<rel_id>/close/` | Bearer | Close an active org relation |

#### Person → Attachments

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| GET | `persons/<id>/attachments/` | Bearer | List attachments (file upload deferred to later phase) |

#### Person Categories (master)

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| GET | `categories/` | Bearer | List categories. Query: `is_active`, `is_system` |
| POST | `categories/create/` | admin | Create a category |
| PATCH | `categories/<id>/` | admin | Partial update a category |
| POST | `categories/<id>/deactivate/` | admin | Soft-deactivate a category |

---

## Frontend Navigation

| Tab | Sub-tabs | Status |
|---|---|---|
| Overview | Summary, Activity Log, System Health | ✅ Complete |
| Customers | Dashboard, Management, Profiles, Settings | 🔨 Shell (backend pending) |
| People | Directory, Profile, Categories, Settings | ✅ Complete |
| Settings | General, Appearance, Integrations, Advanced | 🔨 Shell |
| Users | Accounts, Roles & Permissions, Invites | 🔨 Shell |
| Security | Authentication, Audit Trail, Policies | 🔨 Shell |
| Analytics | Usage, Reports, Exports | 🔨 Shell |
| Infrastructure | Environments, Deployments, Logs | 🔨 Shell |

---

## Environment Variables

Copy `backend/.env.example` to `backend/.env` and fill in your values.

| Key | Description |
|---|---|
| `SECRET_KEY` | Django secret key — generate a strong random value for production |
| `DEBUG` | `True` for dev, `False` for prod |
| `ALLOWED_HOSTS` | Comma-separated list of allowed hostnames |
| `CORS_ALLOWED_ORIGINS` | Comma-separated list of allowed frontend origins |

---

## Production Notes

- Generate a strong secret key: `python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"`
- Set `DEBUG=False`
- Switch `DATABASES` in `settings.py` to PostgreSQL
- Run `manage.py collectstatic` and serve static files via CDN or Nginx
- Configure token rotation and blacklist cleanup via `django-crontab` or a task queue

# Architecture — Altavisor ERP

> Strictly derived from the source code. Nothing is assumed or invented.

---

## Tech Stack and Dependencies

### Backend

| Package | Version | Role |
|---|---|---|
| `django` | 4.2 | Web framework, ORM, admin, migrations |
| `djangorestframework` | latest | REST API layer — serializers, views, permissions |
| `djangorestframework-simplejwt` | latest | JWT access + refresh token auth |
| `django-cors-headers` | latest | CORS middleware |
| `python-decouple` | latest | `.env` config parsing |
| Python | 3.x | Runtime |

**Database:** SQLite (dev) — file `backend/db.sqlite3`. Switch `DATABASES` in `settings.py` to PostgreSQL for production.

### Frontend

| Package | Version | Role |
|---|---|---|
| `next` | 16.2.1 | App Router, SSR, API proxying |
| `react` / `react-dom` | 18.x | Component model |
| `typescript` | 5.x | Type safety, strict mode |

### UI and Styling

| Package | Version | Role |
|---|---|---|
| `@mui/material` | 5.15.20 | Component library |
| `@mui/icons-material` | 5.15.20 | Icon set (Rounded variants used throughout) |
| `@emotion/react` / `@emotion/styled` | latest | CSS-in-JS engine for MUI |

### Fonts (Google Fonts — loaded via `next/font/google`)

| Font | Usage |
|---|---|
| DM Sans | Body text, UI labels, form inputs |
| Syne | Headings and brand elements |

### Path Aliases (`tsconfig.json`)

```json
"@/*" → "./src/*"
```

All internal imports use `@/` — never relative paths across directories.

### Build and Dev Commands

```bash
npm run dev      # dev server on http://localhost:3000
npm run build    # production build
npm run start    # serve production build
npm run lint     # ESLint via next lint
npx tsc --noEmit # type-check without emitting
```

### API Proxy (`next.config.mjs`)

Next.js rewrites all `/api/*` requests to the Django backend at `http://127.0.0.1:8000/api/`. This removes all CORS requirements in development.

```js
// next.config.mjs
rewrites: [
  { source: "/api/:path*/",  destination: "http://127.0.0.1:8000/api/:path*/" },
  { source: "/api/:path*",   destination: "http://127.0.0.1:8000/api/:path*"  },
]
```

---

## Frontend Architecture

## Folder Structure and Conventions

```
frontend/src/
├── app/
│   ├── layout.tsx          # Root layout — HTML shell, font loading, ThemeRegistry
│   ├── page.tsx            # Auth guard → renders AdminShell or redirects to /login
│   └── login/
│       └── page.tsx        # Login page — email/password form, SSO button
│
├── components/
│   ├── AdminShell.tsx      # Top-level layout — owns activeTab / activeSubTab state
│   ├── TopBar.tsx          # Fixed 52px header — logo, search, theme toggle, avatar
│   ├── Sidebar.tsx         # Fixed 72px vertical nav — icon buttons, active pill
│   ├── FooterBar.tsx       # Fixed 32px footer — version, region, API console link
│   ├── MainCanvas.tsx      # Content area — resolves active module and renders it
│   ├── ThemeRegistry.tsx   # MUI theme provider — ColorModeContext, useColorMode()
│   │
│   ├── modules/            # Newer pattern: folder-per-module with index.tsx router
│   │   ├── overview/
│   │   │   └── index.tsx   # Thin wrapper around OverviewDashboard
│   │   ├── customers/
│   │   │   ├── index.tsx           # Sub-tab router
│   │   │   ├── DashboardPage.tsx   # KPI cards, charts, recent customers
│   │   │   ├── ManagementPage.tsx  # CRUD table with add/search/filter
│   │   │   ├── ProfilePage.tsx     # Customer profile + activity timeline
│   │   │   └── SettingsPage.tsx    # Onboarding, churn detection, webhooks
│   │   └── people/
│   │       ├── index.tsx           # Sub-tab router, owns selectedPersonId state
│   │       ├── DirectoryPage.tsx   # Paginated person list, search, category filter
│   │       ├── ProfilePage.tsx     # Full person profile — 5 sub-panels
│   │       ├── CategoriesPage.tsx  # Category CRUD — system/custom, deactivate
│   │       ├── SettingsPage.tsx    # Module reference docs and configuration
│   │       ├── types.ts            # All TypeScript interfaces for the people domain
│   │       └── api.ts              # All API calls for the people domain
│   │
│   └── dashboards/         # Older pattern: single file per section
│       ├── OverviewDashboard.tsx
│       ├── SettingsDashboard.tsx
│       ├── UsersDashboard.tsx
│       ├── SecurityDashboard.tsx
│       ├── AnalyticsDashboard.tsx
│       └── InfrastructureDashboard.tsx
│
├── config/
│   └── nav.ts              # Single source of truth for all navigation tabs and sub-tabs
│
└── lib/
    └── theme.ts            # MUI theme factory — dark + light, all design tokens
```

### Module vs Dashboard Convention

New business modules use the **modules/** pattern:
- Each module is a folder with `index.tsx` acting as a sub-tab router
- Sub-components are co-located in the same folder
- API calls and TypeScript types live in `api.ts` and `types.ts` within the module

Older sections use the **dashboards/** pattern:
- Single flat file per section
- All panels contained in one component

All new work should follow the **modules/** pattern.

---

## Component Tree and Module Layout

### Top-Level Shell

```
app/layout.tsx
└── ThemeRegistry                    (MUI provider, ColorModeContext)
    └── app/page.tsx                 (auth guard — checks localStorage access_token)
        ├── → app/login/page.tsx     (if no token)
        └── AdminShell               (if authenticated)
            ├── TopBar               (fixed 52px — logo, search, theme toggle, user menu)
            ├── Sidebar              (fixed 72px — icon nav, active indicator)
            ├── MainCanvas           (scrollable content — renders active module)
            └── FooterBar            (fixed 32px — version, region, status)
```

### MainCanvas Resolution

`MainCanvas` receives `activeTab` and `activeSubTab` from `AdminShell`. It imports all dashboard and module components and resolves which one to render based on `activeTab`:

```
MainCanvas
├── overview      → modules/overview/index.tsx
├── customers     → modules/customers/index.tsx
├── people        → modules/people/index.tsx
├── settings      → dashboards/SettingsDashboard
├── users         → dashboards/UsersDashboard
├── security      → dashboards/SecurityDashboard
├── analytics     → dashboards/AnalyticsDashboard
└── infrastructure→ dashboards/InfrastructureDashboard
```

### Customers Module Tree

```
modules/customers/index.tsx (router)
├── dashboard   → DashboardPage    (KPI cards, bar chart, recent customers table)
├── management  → ManagementPage   (search + filter + CRUD table + Add dialog)
├── profiles    → ProfilePage      (profile card + activity timeline)
└── settings    → SettingsPage     (onboarding, churn detection, webhooks)
```

### People Module Tree

```
modules/people/index.tsx (router — owns selectedPersonId state)
├── directory   → DirectoryPage    (paginated list, search, category filter, add person)
├── profile     → ProfilePage      (5-panel profile: overview/categories/addresses/notes/orgs)
├── categories  → CategoriesPage   (category list, add, deactivate, inline edit)
└── settings    → SettingsPage     (module reference docs)
```

### People ProfilePage Panels

```
ProfilePage
├── Overview panel      (name, email, phone, DOB, gender, status)
├── Categories panel    (assigned categories, add/remove)
├── Addresses panel     (list, add, edit, set default)
├── Notes panel         (immutable append-only timeline)
└── Organizations panel (linked orgs, role, dates, primary flag, close relation)
```

---

## Nav Config System (`src/config/nav.ts`)

`nav.ts` is the **single source of truth** for all navigation structure. `Sidebar` and `MainCanvas` both derive from it — the sidebar renders the icons and tab list; `MainCanvas` uses `tab.id` to resolve which component to render.

### Interfaces

```typescript
interface SubTab {
  id: string;
  label: string;
}

interface NavTab {
  id: string;
  label: string;
  icon: React.ElementType;   // MUI Rounded icon component
  subtabs: SubTab[];
}
```

### Current Nav Config

| Tab ID | Label | Icon | Sub-tabs |
|---|---|---|---|
| `overview` | Overview | DashboardRounded | summary, activity, health |
| `customers` | Customers | GroupsRounded | dashboard, management, profiles, settings |
| `people` | People | ContactsRounded | directory, profile, categories, settings |
| `settings` | Settings | TuneRounded | general, appearance, integrations, advanced |
| `users` | Users | PeopleRounded | accounts, roles, invites |
| `security` | Security | SecurityRounded | auth, audit, policies |
| `analytics` | Analytics | BarChartRounded | usage, reports, exports |
| `infrastructure` | Infrastructure | CloudRounded | environments, deployments, logs |

### Adding a New Module

1. Add entry to `nav.ts` with `id`, `label`, `icon`, and `subtabs`
2. Create `src/components/modules/<id>/index.tsx` as the sub-tab router
3. Create one `.tsx` file per sub-tab inside that folder
4. Register the import in `MainCanvas.tsx` with `case "<id>":`

---

## Theme and Design Tokens (`src/lib/theme.ts`)

### Theme Architecture

Two complete MUI themes — `darkTheme` and `lightTheme` — are built from a shared `buildComponents(mode)` factory. This is the only place colors, spacing, and component overrides are defined.

```
theme.ts
├── buildComponents(mode)   → shared component overrides
├── darkTheme               → dark palette + buildComponents("dark")
└── lightTheme              → light palette + buildComponents("light")
```

### Brand Colors

| Token | Value | Usage |
|---|---|---|
| Lime bright | `#C8F04A` | Primary actions, logo badge, active indicators |
| Lime dark | `#5CAD00` | Hover state for primary |

> `#C8F04A` is the **only intentional hardcoded hex value** in component files — it is the brand mark. All other colors must use MUI palette tokens.

### Dark Theme Palette

| Key | Value |
|---|---|
| `background.default` | `#0C0E0F` |
| `background.paper` | `#141618` |
| `text.primary` | `#E8EAED` |
| `text.secondary` | `#8A9099` |
| `divider` | `rgba(255,255,255,0.06)` |
| `primary.main` | `#C8F04A` |
| `primary.contrastText` | `#0C0E0F` |

### Color Usage Rule

Always use MUI palette tokens in `sx` props:

```tsx
// Correct
sx={{ color: "text.secondary", bgcolor: "background.paper" }}

// Wrong — never hardcode hex in components
sx={{ color: "#8A9099", bgcolor: "#141618" }}
```

### Fixed Layout Dimensions

| Component | Dimension |
|---|---|
| `TopBar` | 52px height |
| `Sidebar` | 72px width |
| `FooterBar` | 32px height |
| Main content | Remaining viewport |

### ThemeRegistry and Color Mode

`ThemeRegistry` wraps the entire app and exposes `ColorModeContext`. Mode is persisted to `localStorage`.

```typescript
// Import the hook anywhere in the component tree
import { useColorMode } from "@/components/ThemeRegistry";

const { mode, toggleColorMode } = useColorMode();
```

### Component Overrides (via `buildComponents`)

The following MUI components have custom overrides in `theme.ts`:

- `MuiButton` — rounded corners, no text transform, custom hover
- `MuiTextField` / `MuiOutlinedInput` — dark border and focus states
- `MuiPaper` / `MuiCard` — background.paper color, subtle border
- `MuiMenu` / `MuiMenuItem` — hover states, spacing
- `MuiDialog` / `MuiDialogTitle` — dark background, divider styling
- `MuiChip` — filled and outlined variants
- `MuiTooltip` — dark background
- `MuiTableHead` / `MuiTableRow` — alternating rows, header styling
- `MuiLinearProgress` — brand color track
- `MuiSelect` / `MuiInputLabel` — consistent dark field style

---

## Backend Architecture

### Folder Structure

```
backend/
├── altavisor/              # Django project config
│   ├── settings.py         # All settings — installed apps, JWT, CORS, DB, auth
│   ├── urls.py             # Root URL conf — mounts all app URL modules
│   ├── wsgi.py             # WSGI entry point (production)
│   └── asgi.py             # ASGI entry point
│
├── accounts/               # Auth app — User model, JWT endpoints
│   ├── models.py           # Custom User model (email login, role field)
│   ├── serializers.py      # Login, Register, UserSerializer, ChangePassword
│   ├── views.py            # login, refresh, logout, me, change_password, register, sso
│   ├── urls.py             # /api/auth/* routes
│   ├── admin.py            # Django admin registration
│   └── migrations/
│
├── people/                 # Person module — master data for human entities
│   ├── models.py           # Person, PersonCategory, PersonCategoryAssignment,
│   │                       # PersonAddress, PersonNote, PersonAttachment,
│   │                       # OrganizationPersonRelation, TimestampedModel
│   ├── services.py         # All write operations and business logic
│   ├── selectors.py        # All read/query operations
│   ├── serializers.py      # All request validation and response shapes
│   ├── views.py            # Thin HTTP layer — calls services/selectors only
│   ├── urls.py             # /api/people/* routes
│   ├── exceptions.py       # Domain exception hierarchy
│   ├── admin.py            # Django admin registration
│   └── migrations/
│
├── manage.py
└── requirements.txt
```

### Layered Architecture Pattern

Every backend app follows a strict four-layer separation:

```
HTTP Request
     │
     ▼
views.py          ← receive request, validate with serializer, call service or selector, return Response
     │                 NO ORM calls. NO business logic. NO domain decisions.
     ├── (writes) → services.py    ← all business logic, transactions, domain rules
     │                                calls models directly. raises domain exceptions.
     └── (reads)  → selectors.py  ← all ORM queries. never writes. returns querysets or instances.
                         │
                         ▼
                    models.py      ← schema only. no business logic.
```

**Rule enforced in every app:**
- Views call services (for writes) or selectors (for reads) — never ORM directly
- Services own all `@transaction.atomic` blocks and domain exceptions
- Selectors own all `select_related()` and `prefetch_related()` optimisations
- Serializers validate input shape and format output — no logic

### settings.py — Key Configuration

**Installed apps:**
```python
INSTALLED_APPS = [
    # Django built-ins
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # Third-party
    "rest_framework",
    "rest_framework_simplejwt",
    "corsheaders",
    # Local apps
    "accounts",
    "people",
]
```

**Auth model:** `AUTH_USER_MODEL = "accounts.User"` — Django uses the custom User model everywhere.

**DRF global defaults:**
```python
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ),
    "DEFAULT_PERMISSION_CLASSES": (
        "rest_framework.permissions.IsAuthenticated",
    ),
}
```
All endpoints require a valid JWT by default. Endpoints that deviate (e.g. `AllowAny` for login) override this explicitly in the view.

**JWT config:**
```python
SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME":  timedelta(minutes=60),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=7),
    "ROTATE_REFRESH_TOKENS":  True,
    "BLACKLIST_AFTER_ROTATION": False,
    "AUTH_HEADER_TYPES": ("Bearer",),
    "USER_ID_FIELD": "id",
    "USER_ID_CLAIM": "user_id",
}
```

**CORS:**
```python
CORS_ALLOWED_ORIGINS = ["http://localhost:3000", "http://127.0.0.1:3000"]
CORS_ALLOW_CREDENTIALS = True
```

**Password validators:** `UserAttributeSimilarity`, `MinimumLength` (8), `CommonPassword`, `NumericPassword`

### Root URL Configuration

```python
# altavisor/urls.py
urlpatterns = [
    path("admin/",       admin.site.urls),
    path("api/auth/",    include("accounts.urls")),
    path("api/people/",  include("people.urls")),
]
```

---

### accounts app

#### User Model (`accounts/models.py`)

DB table: `users`

| Field | Type | Notes |
|---|---|---|
| `email` | EmailField (unique) | `USERNAME_FIELD` — used instead of username |
| `full_name` | CharField(150) | Display name |
| `role` | CharField choices | `super_admin`, `admin`, `analyst`, `viewer` |
| `is_active` | BooleanField | Controls login access |
| `is_staff` | BooleanField | Django admin panel access |
| `date_joined` | DateTimeField (auto) | Set on creation |
| `last_login` | DateTimeField (null) | Updated on each login in the login view |

Computed property: `initials` — first character of each name part; falls back to first two chars of email.

Custom `UserManager` handles `create_user()` and `create_superuser()` with email normalisation.

#### Serializers (`accounts/serializers.py`)

| Serializer | Direction | Fields |
|---|---|---|
| `UserSerializer` | Read-only | `id, email, full_name, role, initials, date_joined, last_login` |
| `LoginSerializer` | Write | `email, password` — calls `authenticate()`; blocks inactive accounts |
| `RegisterSerializer` | Write | `email, full_name, role, password, password_confirm` — validates match; min length 8 |
| `ChangePasswordSerializer` | Write | `current_password, new_password, new_password_confirm` — validates match |

#### Views and Endpoints (`accounts/views.py` → `accounts/urls.py`)

All mounted at `/api/auth/`.

| Method | Endpoint | Permission | Behaviour |
|---|---|---|---|
| POST | `login/` | AllowAny | Authenticates via `LoginSerializer`; updates `last_login`; returns `{ access, refresh, user }` |
| POST | `refresh/` | AllowAny | Accepts `{ refresh }` token; returns `{ access }` |
| POST | `logout/` | IsAuthenticated | Calls `RefreshToken.blacklist()` on the provided refresh token (best-effort; ignores if already invalid) |
| GET | `me/` | IsAuthenticated | Returns `UserSerializer` of request user |
| PATCH | `me/` | IsAuthenticated | Updates `full_name` only; validates string type and max 150 chars |
| POST | `change-password/` | IsAuthenticated | Validates current password with `check_password()`; calls `set_password()` |
| POST | `register/` | IsAdminUser | Creates new user via `RegisterSerializer.save()` |
| GET | `sso/` | AllowAny | Placeholder — returns 501 with implementation note |

---

### people app

#### Models (`people/models.py`)

**`TimestampedModel`** — abstract base; adds `created_at` and `updated_at` (auto) to all people models except `PersonNote`.

**`PersonCategory`** — DB table: `people_person_categories`

| Field | Type | Notes |
|---|---|---|
| `name` | CharField(100, unique) | |
| `slug` | SlugField(120, unique) | Auto-generated from name via `slugify()` in service |
| `description` | TextField (blank) | |
| `is_system` | BooleanField | Blocks rename, re-slug, deactivate via API. Enforced in service layer |
| `is_active` | BooleanField (db_index) | Soft deactivation |

**`Person`** — DB table: `people_persons`

| Field | Type | Notes |
|---|---|---|
| `first_name` | CharField(100) | |
| `last_name` | CharField(100) | |
| `preferred_name` | CharField(100, blank) | Display name override |
| `email` | EmailField (unique, null, blank) | `None` stored (not `""`) to preserve unique constraint |
| `phone` | CharField(30, blank) | |
| `mobile` | CharField(30, blank) | |
| `date_of_birth` | DateField (null) | |
| `gender` | CharField choices | `male`, `female`, `other`, `prefer_not_to_say` |
| `is_active` | BooleanField (db_index) | |
| `created_by` | FK → User (SET_NULL) | |
| `categories` | M2M → PersonCategory | Through `PersonCategoryAssignment` |

DB indexes: `(last_name, first_name)`, `(email)`. Computed: `full_name`, `display_name`, `initials`.

**`PersonCategoryAssignment`** — DB table: `people_category_assignments`

| Field | Type | Notes |
|---|---|---|
| `person` | FK → Person (CASCADE) | |
| `category` | FK → PersonCategory (CASCADE) | |
| `assigned_by` | FK → User (SET_NULL) | |
| `is_active` | BooleanField (db_index) | Soft remove — row preserved for history |

`unique_together`: `(person, category)`. Service reactivates existing inactive row instead of creating a duplicate.

**`PersonAddress`** — DB table: `people_addresses`

| Field | Type | Notes |
|---|---|---|
| `person` | FK → Person (CASCADE) | |
| `label` | CharField choices | `billing`, `delivery`, `home`, `work`, `other` |
| `line1` | CharField(200) | |
| `line2` | CharField(200, blank) | |
| `city` | CharField(100) | |
| `state_province` | CharField(100, blank) | |
| `postal_code` | CharField(20, blank) | |
| `country` | CharField(100) | |
| `is_default` | BooleanField | Service enforces at most one default per person |
| `is_active` | BooleanField (db_index) | |

DB index: `(person, is_default)`.

**`PersonNote`** — DB table: `people_notes`

Immutable audit record. No `updated_at`. No soft delete. Author FK uses `SET_NULL` so notes survive user deletion.

| Field | Type |
|---|---|
| `person` | FK → Person (CASCADE) |
| `body` | TextField |
| `author` | FK → User (SET_NULL) |
| `created_at` | DateTimeField (auto) |

**`PersonAttachment`** — DB table: `people_attachments`

Model schema defined; file upload deferred. `MEDIA_ROOT` and `MEDIA_URL` not yet configured in `settings.py`.

| Field | Type | Notes |
|---|---|---|
| `person` | FK → Person (CASCADE) | |
| `label` | CharField(200) | |
| `file` | FileField | `upload_to="people/attachments/%Y/%m/"` |
| `uploaded_by` | FK → User (SET_NULL) | |
| `created_at` | DateTimeField (auto) | |

**`OrganizationPersonRelation`** — DB table: `people_org_relations`

| Field | Type | Notes |
|---|---|---|
| `person` | FK → Person (CASCADE) | |
| `organization_id` | PositiveIntegerField (db_index) | Plain ID — not a FK. Avoids GenericForeignKey performance penalty. Migrates to proper FK when companies app ships |
| `organization_type` | CharField(50) | e.g. `customer`, `supplier`, `partner` |
| `role` | CharField(100) | e.g. `representative`, `billing`, `commission_holder` |
| `is_primary` | BooleanField | |
| `is_active` | BooleanField (db_index) | |
| `started_on` | DateField (null) | |
| `ended_on` | DateField (null) | Set by `close_organization_relationship()` |

`unique_together`: `(person, organization_id, organization_type, role)`. DB index: `(organization_id, organization_type)`.

#### Services (`people/services.py`)

All writes. All business rules. All `@transaction.atomic` blocks.

| Service | Atomic | Key behaviour |
|---|---|---|
| `detect_duplicate_persons()` | No | Checks email (high), name (medium), phone (medium); returns ranked candidates list |
| `create_person()` | Yes | Runs duplicate check unless `force=True`; stores `None` for empty email |
| `update_person()` | Yes | `select_for_update()` prevents concurrent-write race; re-runs dupe check excluding self |
| `deactivate_person()` | Yes | Sets `is_active=False`; bulk-closes org relations; bulk-deactivates category assignments |
| `merge_persons()` | — | Raises `MergePersonError` — documented contract, intentionally not implemented until all downstream modules exist |
| `create_category()` | No | Auto-slugifies; blocks duplicate slug or name; always `is_system=False` via API |
| `update_category()` | No | Blocks name change on system categories; re-slugifies on name update |
| `deactivate_category()` | Yes | Blocks system categories; bulk-deactivates all assignments; idempotent |
| `assign_category()` | Yes | Reactivates existing inactive assignment (respects `unique_together`) instead of creating duplicate row |
| `remove_category()` | No | Soft-deactivates assignment; raises if no active assignment found |
| `create_address()` | Yes | Demotes existing default if `is_default=True` |
| `update_address()` | Yes | Demotes other defaults when promoting this one |
| `create_note()` | No | Validates non-empty body; immutable after creation |
| `link_person_to_organization()` | Yes | Blocks duplicate active relation for same `(person, org_id, org_type, role)` |
| `update_organization_relationship()` | No | Only `role`, `is_primary`, `started_on` are mutable |
| `close_organization_relationship()` | No | Sets `is_active=False`, `ended_on=today`; idempotent |

#### Selectors (`people/selectors.py`)

All reads. Never write. All ORM optimisation lives here.

| Selector | Optimisation | Notes |
|---|---|---|
| `list_persons()` | `select_related("created_by")` + `Prefetch("category_assignments", to_attr="active_assignments")` | Returns paginated dict; `to_attr` avoids N+1 in list serializer |
| `get_person_detail()` | Full prefetch of addresses, active_assignments, org_relations, notes, attachments | Single query set for detail view |
| `search_persons()` | `icontains` on first_name, last_name, email | Lightweight autocomplete; returns queryset (caller slices) |
| `list_categories()` | None | Optional `is_active`, `is_system` filters |
| `get_person_categories()` | `select_related("category", "assigned_by")` | |
| `get_person_addresses()` | Ordered `-is_default, label` | |
| `get_person_notes()` | `select_related("author")`, ordered `-created_at` | |
| `get_person_attachments()` | `select_related("uploaded_by")`, ordered `-created_at` | |
| `get_person_organizations()` | Ordered `-is_active, -started_on, -created_at` | `active_only=False` default — returns full history |

#### Domain Exceptions (`people/exceptions.py`)

```
PeopleModuleError (base)
├── PersonNotFoundError               — person does not exist
├── PersonInactiveError               — operation on deactivated person
├── DuplicatePersonError              — carries .candidates list with reason per candidate
├── CategoryNotFoundError             — category does not exist
├── CategoryInactiveError             — category is inactive; cannot assign
├── CategorySystemProtectedError      — system category; blocks rename/deactivate
├── DuplicateCategoryAssignmentError  — assign: already active; remove: no active assignment
├── AddressNotFoundError              — address not found for given person
├── OrganizationRelationNotFoundError — org relation not found
├── OrganizationRelationConflictError — duplicate active relation for same (person, org, type, role)
└── MergePersonError                  — merge not implemented; raised by placeholder service
```

#### Serializers (`people/serializers.py`)

| Serializer | Used for | Key fields |
|---|---|---|
| `PersonListSerializer` | GET `persons/` list | Reads `active_assignments` to_attr — no extra query |
| `PersonDetailSerializer` | GET/POST `persons/<id>/` | Nests addresses, category_assignments, org_relations, notes, attachments |
| `PersonWriteSerializer` | POST `persons/` | All fields optional except first/last name; `force` flag |
| `PersonUpdateSerializer` | PATCH `persons/<id>/` | All fields optional |
| `DuplicateCheckSerializer` | POST `persons/duplicate-check/` | first_name, last_name, email?, phone? |
| `DuplicateCandidateSerializer` | 409 conflict body | id, full_name, email, phone |
| `PersonCategorySerializer` | Category read | id, name, slug, description, is_system, is_active |
| `PersonCategoryWriteSerializer` | Category create/update | name, description |
| `PersonCategoryAssignmentSerializer` | Assignment read | Nests full PersonCategorySerializer; resolves `assigned_by_name` |
| `CategoryAssignWriteSerializer` | Assignment create | category_id only |
| `PersonAddressSerializer` | Address read | Includes `label_display` via `get_label_display` |
| `PersonAddressWriteSerializer` | Address create/update | label, line1, line2, city, state_province, postal_code, country, is_default |
| `PersonNoteSerializer` | Note read | Resolves `author_name` via method field |
| `PersonNoteWriteSerializer` | Note create | body only |
| `PersonAttachmentSerializer` | Attachment read | Resolves `uploaded_by_name` |
| `OrganizationPersonRelationSerializer` | Relation read | All fields |
| `OrganizationPersonRelationWriteSerializer` | Relation create | organization_id, organization_type, role, is_primary, started_on |
| `OrganizationPersonRelationUpdateSerializer` | Relation update | role, is_primary, started_on only |

#### Views and Endpoints (`people/views.py` → `people/urls.py`)

All mounted at `/api/people/`. View contract: receive → validate with serializer → call service/selector → return Response. No ORM, no logic.

| Method | Endpoint | Permission | View |
|---|---|---|---|
| GET, POST | `persons/` | IsAuthenticated | `persons_list_create` |
| POST | `persons/duplicate-check/` | IsAuthenticated | `person_duplicate_check` |
| GET, PATCH | `persons/<id>/` | IsAuthenticated | `person_detail_update` |
| POST | `persons/<id>/deactivate/` | IsAuthenticated | `person_deactivate` |
| POST | `persons/<id>/merge/` | IsAdminUser | `person_merge` — returns 501 |
| GET, POST | `persons/<id>/categories/` | IsAuthenticated | `person_categories` |
| DELETE | `persons/<id>/categories/<cat_id>/` | IsAuthenticated | `person_category_remove` |
| GET, POST | `persons/<id>/addresses/` | IsAuthenticated | `person_addresses` |
| PATCH | `persons/<id>/addresses/<addr_id>/` | IsAuthenticated | `person_address_update` |
| GET, POST | `persons/<id>/notes/` | IsAuthenticated | `person_notes` |
| GET, POST | `persons/<id>/organizations/` | IsAuthenticated | `person_organizations` |
| PATCH | `persons/<id>/organizations/<rel_id>/` | IsAuthenticated | `person_organization_update` |
| POST | `persons/<id>/organizations/<rel_id>/close/` | IsAuthenticated | `person_organization_close` |
| GET | `persons/<id>/attachments/` | IsAuthenticated | `person_attachments` — list only |
| GET | `categories/` | IsAuthenticated | `categories_list` |
| POST | `categories/create/` | IsAdminUser | `category_create` |
| PATCH | `categories/<id>/` | IsAdminUser | `category_update` |
| POST | `categories/<id>/deactivate/` | IsAdminUser | `category_deactivate` |

---

## Auth Flow

```
page.tsx (mount)
  └── check localStorage["access_token"]
        ├── missing → router.push("/login")
        └── present → render <AdminShell />

login/page.tsx
  └── POST /api/auth/login/ { email, password }
        ├── success → localStorage.setItem("access_token", ...)
        │            → router.push("/")
        └── error   → show error message

TopBar user menu → Logout
  └── POST /api/auth/logout/ { refresh }
        → localStorage.removeItem("access_token")
        → router.push("/login")
```

All API calls in `people/api.ts` inject the token via:

```typescript
headers: { Authorization: `Bearer ${localStorage.getItem("access_token")}` }
```

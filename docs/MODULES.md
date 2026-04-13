# Modules — Altavisor ERP

Complete reference for all 26 ERP modules. Each entry documents both the **backend** (Django models, services, selectors, serializers, views, URLs) and the **frontend** (React components, sub-tabs, panels, API layer) — current implementation and planned design.

**Status legend:**
- `✅ Complete` — backend + frontend fully implemented and connected
- `🔨 In Progress` — partially implemented on one or both sides
- `⬜ Planned` — not yet started on either side

---

## Module File Conventions

### Backend (Django REST Framework)

Each backend app follows a layered architecture:

```
backend/<app>/
├── models.py       # Database models — no business logic
├── services.py     # Write operations — all business logic and transactions
├── selectors.py    # Read operations — all ORM queries
├── serializers.py  # Request validation + response shaping — no logic
├── views.py        # HTTP layer — calls services/selectors, returns Responses
├── urls.py         # URL patterns for this app
├── exceptions.py   # Domain exceptions raised by services
└── migrations/     # Django migrations
```

**Rule:** Views contain no ORM calls or business logic. Services contain no HTTP logic. Selectors only read — never write.

### Frontend (Next.js + MUI)

Each frontend module follows this structure under `src/components/modules/`:

```
modules/<id>/
├── index.tsx       # Sub-tab router — receives activeSubTab, renders correct page
├── <Panel>Page.tsx # One file per sub-tab panel
├── types.ts        # TypeScript interfaces for this domain
└── api.ts          # All API call functions for this domain
```

Sections predating this pattern use a single file in `src/components/dashboards/`.

---

## Layer A — Foundation and Control

---

### 1. Dashboard and Workspace Module

**Status:** `✅ Complete` (current scope)

The central entry point into the ERP. Presents key business metrics, operational health, recent system activity, and role-based summaries. First screen after login.

**Key capabilities:**
- Role-based dashboard views showing relevant KPIs per user role
- KPI and summary cards for operational metrics
- Pending approvals and tasks panel
- Recent activity overview
- Personalized workspace per user
- Quick navigation shortcuts to key modules
- Notifications overview

#### Backend

No dedicated backend app. Data currently served as static values in the frontend. When full implementation ships, this will aggregate data from all other modules.

**Planned backend:** A read-only aggregation service that queries across modules and returns role-filtered dashboard payloads. No writes.

#### Frontend

**App:** `src/components/modules/overview/` + `src/components/dashboards/OverviewDashboard.tsx`
**Nav ID:** `overview`

`modules/overview/index.tsx` is a thin wrapper that renders `OverviewDashboard`. The dashboard itself handles sub-tab routing internally.

| Sub-tab | Content |
|---|---|
| `summary` | 4 KPI cards: Active Users, API Requests, Error Rate, Avg Response Time; Recent Activity list with timestamped entries and status color coding |
| `activity` | Activity log (currently shares summary render) |
| `health` | CPU usage, Memory, Disk I/O, Network throughput — each as a labeled LinearProgress bar |

---

### 2. Settings and System Administration Module

**Status:** `🔨 In Progress` — frontend shell only; no backend

Global system configuration. Acts as the control center for system-wide behavior across all modules.

**Key capabilities:**
- Company profile management (legal name, registration, logo)
- Branch and business unit configuration
- Department setup
- Tax settings
- Currency configuration
- Localization and regional settings
- Document numbering and code generation rules
- Notification settings
- Email configuration (SMTP, templates)
- Feature toggles per environment
- Workflow settings
- Integration settings for external services
- Global business preferences
- Audit and configuration history

#### Backend

**Status:** Not yet implemented.

**Planned app:** `backend/system/`

**Planned models:**
- `SystemSettings` — singleton or company-scoped settings record (org name, timezone, currency, tax config, numbering rules)
- `FeatureFlag` — named boolean toggles per environment
- `EmailConfig` — SMTP credentials and template defaults
- `AuditConfigLog` — history of settings changes with actor and timestamp

**Planned endpoints:**
```
GET/PATCH  /api/system/settings/
GET/POST   /api/system/feature-flags/
PATCH      /api/system/feature-flags/<id>/
GET        /api/system/settings/history/
```

#### Frontend

**App:** `src/components/dashboards/SettingsDashboard.tsx`
**Nav ID:** `settings`

| Sub-tab | Current content | Planned |
|---|---|---|
| `general` | Org name, domain, region (select), timezone (select) — static UI | Persist to `PATCH /api/system/settings/` |
| `appearance` | UI density, sidebar mode, animations toggle, accent color picker, font size slider | Per-user preference persistence |
| `integrations` | Slack webhook URL, GitHub link button — static UI | Wire to integration backend |
| `advanced` | Debug mode, telemetry, API rate limit, Danger Zone (reset/wipe buttons) — static UI | Feature flags API, danger zone actions |

**Planned additional sub-tabs:** Tax & Currency, Numbering Rules, Email Config, Localization

---

### 3. User Management Module

**Status:** `🔨 In Progress` — backend complete; frontend shell only

Manages ERP user accounts, login identities, onboarding, and account lifecycle.

**Key capabilities:**
- User account creation and update
- Account activation and deactivation
- Company email-based login identity
- Onboarding support with temporary credential generation
- First-login password reset enforcement
- User-to-person mapping (link system user to a Person record)
- Account status management
- Login history
- User audit trail

#### Backend

**App:** `backend/accounts/`
**DB table:** `users`

**Model — `User`** (extends `AbstractBaseUser`, `PermissionsMixin`):

| Field | Type | Notes |
|---|---|---|
| `email` | EmailField (unique) | Login identity — `USERNAME_FIELD` |
| `full_name` | CharField(150) | Display name |
| `role` | CharField choices | `super_admin`, `admin`, `analyst`, `viewer` |
| `is_active` | BooleanField | Account enabled/disabled |
| `is_staff` | BooleanField | Django admin access |
| `date_joined` | DateTimeField | Auto set on creation |
| `last_login` | DateTimeField | Updated on each login |

**Computed properties:**
- `initials` — first char of each name part; falls back to first two chars of email

**Serializers:**
- `UserSerializer` — read-only output: `id, email, full_name, role, initials, date_joined, last_login`
- `RegisterSerializer` — write: `email, full_name, role, password, password_confirm`; validates password match; min length 8
- `LoginSerializer` — write: `email, password`; calls `authenticate()`; checks `is_active`
- `ChangePasswordSerializer` — write: `current_password, new_password, new_password_confirm`

**Views and URLs** (all under `/api/auth/`):

| Method | Endpoint | Permission | Description |
|---|---|---|---|
| POST | `login/` | AllowAny | Authenticates user; updates `last_login`; returns `{ access, refresh, user }` |
| POST | `refresh/` | AllowAny | Accepts refresh token; returns new `{ access }` |
| POST | `logout/` | IsAuthenticated | Blacklists refresh token (best-effort) |
| GET | `me/` | IsAuthenticated | Returns current user profile |
| PATCH | `me/` | IsAuthenticated | Updates `full_name` only; validates max 150 chars |
| POST | `change-password/` | IsAuthenticated | Validates current password; sets new; requires 8+ chars |
| POST | `register/` | IsAdminUser | Creates new user account |
| GET | `sso/` | AllowAny | Placeholder — returns 501 |

**JWT config** (`settings.py`):
- `ACCESS_TOKEN_LIFETIME`: 60 minutes
- `REFRESH_TOKEN_LIFETIME`: 7 days
- `ROTATE_REFRESH_TOKENS`: True
- `AUTH_HEADER_TYPES`: `Bearer`

#### Frontend

**App:** `src/components/dashboards/UsersDashboard.tsx`
**Nav ID:** `users`

| Sub-tab | Current content | Planned |
|---|---|---|
| `accounts` | User list with search; columns: Name, Email, Role, Status, Last Active (static mock) | Full CRUD wired to `/api/auth/` — create, edit, activate/deactivate |
| `roles` | Stub placeholder | Move to Role and Permission module |
| `invites` | Stub placeholder | Invite flow with temporary credentials |

**Planned additional capabilities:** User-to-person mapping (link `User` to a `Person` record), first-login password reset enforcement, login history view

---

### 4. Role and Permission Management Module

**Status:** `🔨 In Progress` — roles exist as a User field; no permission management system yet

Controls ERP authorization through role-based access control (RBAC). Defines what each role can access and what actions they can perform.

**Key capabilities:**
- Role definition and maintenance
- Permission assignment by module and action type (create, read, update, delete, approve)
- User-role mapping
- Approval privilege assignment
- Restricted access to sensitive modules (finance, admin settings)
- Audit trail for all role and permission changes

**Example permissions:**
- Create sales orders
- Approve invoices
- Edit person records
- Manage supplier data
- Access financial reports
- Administer system settings

#### Backend

**Current state:** The `role` field on `User` (`super_admin`, `admin`, `analyst`, `viewer`) is the only RBAC mechanism. DRF permissions `IsAuthenticated` and `IsAdminUser` are used in views. No granular permission model exists.

**Planned app:** `backend/rbac/`

**Planned models:**
- `Role` — named role with description
- `Permission` — named permission with module and action (`module="people"`, `action="create"`)
- `RolePermission` — many-to-many through model linking Role to Permission
- `UserRole` — links User to Role (replacing the current `role` text field)

**Planned endpoints:**
```
GET/POST       /api/rbac/roles/
GET/PATCH      /api/rbac/roles/<id>/
GET/POST       /api/rbac/roles/<id>/permissions/
DELETE         /api/rbac/roles/<id>/permissions/<perm_id>/
GET/POST       /api/rbac/users/<id>/roles/
GET            /api/rbac/permissions/
```

#### Frontend

**Nav ID:** Currently `users` → `roles` sub-tab (stub)

**Planned sub-tabs:**

| Sub-tab | Planned content |
|---|---|
| `roles` | Role list — create, edit, view assigned permissions |
| `permissions` | Permission matrix by module and action type |
| `mapping` | Assign roles to users; view users per role |
| `audit` | Change history for all role and permission modifications |

---

### 5. Authentication and Security Module

**Status:** `🔨 In Progress` — backend complete; frontend shell only

Handles secure authentication and security policy enforcement. Works closely with User Management and RBAC.

**Key capabilities:**
- Secure password-based authentication
- Token and session handling
- Password hashing and reset flow
- MFA support
- Login protection and failed-attempt validation
- Session security and timeout enforcement
- Account lockout controls
- Security event logging
- Credential lifecycle control

#### Backend

**App:** `backend/accounts/` (shared with User Management)

**Implemented:**
- JWT access and refresh tokens via `djangorestframework-simplejwt`
- Refresh token rotation on each use (`ROTATE_REFRESH_TOKENS = True`)
- Blacklist on logout via `RefreshToken.blacklist()`
- Password hashing via Django's `AbstractBaseUser.set_password()`
- Password validators: similarity, minimum length (8), common password, numeric-only
- `is_active` flag blocks login for deactivated accounts

**Not yet implemented:** MFA, SSO/SAML/OIDC, account lockout after failed attempts, security event log, IP-based restrictions

**Planned additions to `backend/accounts/`:**
- `SecurityEvent` model — log of login attempts, failures, lockouts with IP and timestamp
- `MFAConfig` model — per-user MFA settings (TOTP secret, enabled flag)
- `AccountLockout` service — track failed attempts; lock after threshold

#### Frontend

**App:** `src/components/dashboards/SecurityDashboard.tsx`
**Nav ID:** `security`

| Sub-tab | Current content | Planned |
|---|---|---|
| `auth` | MFA enforcement toggle, SSO config, session timeout, password policy — static UI | Wire to backend policy endpoints |
| `audit` | Audit trail table: Actor, Action, Resource, IP, Time — static mock | Connect to `SecurityEvent` backend |
| `policies` | IP allowlist toggle, brute-force protection, geo-blocking, API key expiry — static UI | Policy enforcement backend |

---

### 6. Audit Log and Activity Tracking Module

**Status:** `🔨 In Progress` — frontend shell under Security; no dedicated backend app

Records all significant actions across the ERP for traceability, accountability, and compliance.

**Key capabilities:**
- User activity logging across all modules
- Record change history with field-level before/after diff
- Configuration change tracking
- Status transition history
- Login and authentication event logs
- Onboarding and account provisioning logs
- Approval decision history
- Category assignment history

#### Backend

**Current state:** No `AuditLog` model exists. `logging` calls exist in `people/services.py` writing to the Python logger (file/console only).

**Planned app:** `backend/audit/`

**Planned model — `AuditLog`:**

| Field | Type | Notes |
|---|---|---|
| `actor` | FK → User (SET_NULL) | User who performed the action |
| `action` | CharField | `create`, `update`, `deactivate`, `assign`, `close`, `login`, etc. |
| `resource_type` | CharField | `person`, `category`, `user`, `company`, etc. |
| `resource_id` | PositiveIntegerField | ID of the affected record |
| `before` | JSONField | State before the change (nullable) |
| `after` | JSONField | State after the change (nullable) |
| `ip_address` | GenericIPAddressField | Nullable |
| `created_at` | DateTimeField (auto) | |

**Planned endpoints:**
```
GET  /api/audit/logs/              # filtered list (resource_type, actor, date range)
GET  /api/audit/logs/<id>/         # detail
```

**Integration plan:** Services in all modules will call a shared `audit.services.log_action()` function after each write operation.

#### Frontend

**Nav ID:** `security` → `audit` sub-tab (planned: dedicated nav entry)

**Planned sub-tabs:**

| Sub-tab | Planned content |
|---|---|
| `activity` | User action log: actor, action, resource type + ID, timestamp, IP |
| `changes` | Field-level diff: before and after values per change |
| `access` | Login events, failed attempts, session activity |
| `approvals` | Approval decisions: actor, outcome, workflow, timestamp |

---

## Layer B — Master Data and Classification

---

### 7. Person Module

**Status:** `✅ Complete`

The central master data module for all human entities. Stores reusable person profiles that can be linked to multiple business contexts without duplication. A person may represent different roles over time (direct customer, company contact, commission holder) without requiring a new record. Includes built-in dynamic category management through a many-to-many framework.

**Typical person types:** Direct customer, company representative, supplier contact, commission holder, billing contact, delivery contact, employee-related contact, external business contact

**Key capabilities:**
- Person registration and profile management
- Contact information management (email, phone, mobile)
- Address management (multiple addresses with labels and default)
- Notes and attachments
- Lifecycle status management (active/inactive with soft deactivation)
- Person search and filtering
- Reusable person identity across modules without duplication
- Linked company relationships via Org–Person Relationship
- Dynamic category assignment (many-to-many)
- Duplicate detection on create and update (email, name, phone signals)
- Person merge (endpoint defined; full implementation deferred)

**Person category capabilities (built-in):**
- Dynamic category creation (system and custom)
- Protected system categories (cannot be renamed, re-slugged, or deactivated via API)
- Multiple category assignment per person
- Soft removal preserving assignment history
- Category-based discount and access profile mapping (planned — via Pricing module)
- Category history and audit tracking

**Example person categories:** Customer, Company Representative, VIP Gold, Commission Holder, Preferred Contact, Seasonal Buyer

#### Backend

**App:** `backend/people/`

**Architecture:** Four-layer pattern — models → services (writes) → selectors (reads) → views (HTTP).

---

**Models:**

**`PersonCategory`** — `people_person_categories`

| Field | Type | Notes |
|---|---|---|
| `name` | CharField(100, unique) | Category label |
| `slug` | SlugField(120, unique) | Auto-generated from name via `slugify()` |
| `description` | TextField (blank) | |
| `is_system` | BooleanField | System categories cannot be renamed, re-slugged, or deactivated via API |
| `is_active` | BooleanField (db_index) | Soft deactivation |
| `created_at` / `updated_at` | DateTimeField | Via `TimestampedModel` |

**`Person`** — `people_persons`

| Field | Type | Notes |
|---|---|---|
| `first_name` | CharField(100) | |
| `last_name` | CharField(100) | |
| `preferred_name` | CharField(100, blank) | Display name override |
| `email` | EmailField (unique, null, blank) | Null stored instead of empty string to preserve unique constraint |
| `phone` | CharField(30, blank) | |
| `mobile` | CharField(30, blank) | |
| `date_of_birth` | DateField (null) | |
| `gender` | CharField choices | `male`, `female`, `other`, `prefer_not_to_say` |
| `is_active` | BooleanField (db_index) | |
| `created_by` | FK → User (SET_NULL) | |
| `categories` | M2M → PersonCategory (through `PersonCategoryAssignment`) | |

Indexes: `(last_name, first_name)`, `(email)`

Computed properties: `full_name`, `display_name`, `initials`

**`PersonCategoryAssignment`** — `people_category_assignments`

| Field | Type | Notes |
|---|---|---|
| `person` | FK → Person (CASCADE) | |
| `category` | FK → PersonCategory (CASCADE) | |
| `assigned_by` | FK → User (SET_NULL) | |
| `is_active` | BooleanField (db_index) | Soft deactivation — preserved for history |

`unique_together`: `(person, category)` — one row per pair; reactivated instead of duplicated.

**`PersonAddress`** — `people_addresses`

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

Index: `(person, is_default)`

**`PersonNote`** — `people_notes`

| Field | Type | Notes |
|---|---|---|
| `person` | FK → Person (CASCADE) | |
| `body` | TextField | |
| `author` | FK → User (SET_NULL) | Preserved even if author is deleted |
| `created_at` | DateTimeField (auto) | No `updated_at` — notes are immutable |

**`PersonAttachment`** — `people_attachments`

| Field | Type | Notes |
|---|---|---|
| `person` | FK → Person (CASCADE) | |
| `label` | CharField(200) | |
| `file` | FileField | `upload_to="people/attachments/%Y/%m/"` — upload deferred to phase 2 |
| `uploaded_by` | FK → User (SET_NULL) | |
| `created_at` | DateTimeField (auto) | |

**`OrganizationPersonRelation`** — `people_org_relations`

| Field | Type | Notes |
|---|---|---|
| `person` | FK → Person (CASCADE) | |
| `organization_id` | PositiveIntegerField (db_index) | Plain ID — not a FK; migrated to proper FK when companies app ships |
| `organization_type` | CharField(50) | e.g. `customer`, `supplier`, `partner` |
| `role` | CharField(100) | e.g. `representative`, `billing`, `commission_holder` |
| `is_primary` | BooleanField | |
| `is_active` | BooleanField (db_index) | |
| `started_on` | DateField (null) | |
| `ended_on` | DateField (null) | Set by `close_organization_relationship()` |

`unique_together`: `(person, organization_id, organization_type, role)` — prevents duplicate rows.

---

**Services** (`services.py`) — all writes, all business rules:

| Service | Transaction | Description |
|---|---|---|
| `detect_duplicate_persons()` | No | Returns candidates: email match (high), name match (medium), phone match (medium) |
| `create_person()` | `@atomic` | Runs duplicate check unless `force=True`; stores `None` for empty email |
| `update_person()` | `@atomic` | `select_for_update()` to prevent race; re-runs duplicate check excluding self |
| `deactivate_person()` | `@atomic` | Sets `is_active=False`; bulk-closes org relations; bulk-deactivates category assignments |
| `merge_persons()` | — | Raises `MergePersonError` — intentionally unimplemented; documented contract for future |
| `create_category()` | No | Auto-slugifies name; rejects duplicate slug or name; `is_system=False` always |
| `update_category()` | No | Blocks name change on system categories; re-slugifies on name update |
| `deactivate_category()` | `@atomic` | Blocks system categories; bulk-deactivates all assignments for this category; idempotent |
| `assign_category()` | `@atomic` | Reactivates existing inactive assignment instead of creating duplicate row |
| `remove_category()` | No | Soft-deactivates assignment; raises if no active assignment found |
| `create_address()` | `@atomic` | Demotes existing default if `is_default=True` |
| `update_address()` | `@atomic` | Demotes other defaults if promoting this one |
| `create_note()` | No | Validates non-empty body; immutable after creation |
| `link_person_to_organization()` | `@atomic` | Blocks duplicate active relation for same (person, org_id, org_type, role) |
| `update_organization_relationship()` | No | Only `role`, `is_primary`, `started_on` are mutable |
| `close_organization_relationship()` | No | Sets `is_active=False`, `ended_on=today`; idempotent |

---

**Selectors** (`selectors.py`) — all reads:

| Selector | Returns | Notes |
|---|---|---|
| `list_persons()` | paginated dict | Prefetches `active_assignments` as `to_attr` to avoid N+1 |
| `get_person_detail()` | Person instance | Prefetches addresses, active_assignments, org_relations, notes, attachments |
| `search_persons()` | queryset | Lightweight autocomplete — name/email icontains |
| `list_categories()` | queryset | Optional `is_active`, `is_system` filters |
| `get_category()` | PersonCategory | Raises `CategoryNotFoundError` |
| `get_person_categories()` | queryset | `select_related("category", "assigned_by")` |
| `get_person_addresses()` | queryset | Default-first ordering |
| `get_person_notes()` | queryset | `select_related("author")`; newest first |
| `get_person_attachments()` | queryset | `select_related("uploaded_by")`; newest first |
| `get_person_organizations()` | queryset | `active_only=False` default — returns full history |

---

**Serializers** (`serializers.py`):

| Serializer | Used for |
|---|---|
| `PersonListSerializer` | GET `persons/` — compact list shape; reads `active_assignments` to_attr |
| `PersonDetailSerializer` | GET/POST `persons/<id>/` — full shape with all nested relations |
| `PersonWriteSerializer` | POST `persons/` — all fields optional except first/last name; includes `force` flag |
| `PersonUpdateSerializer` | PATCH `persons/<id>/` — all fields optional |
| `DuplicateCheckSerializer` | POST `persons/duplicate-check/` — first_name, last_name, email?, phone? |
| `DuplicateCandidateSerializer` | Included in 409 responses — id, full_name, email, phone |
| `PersonCategorySerializer` | Category read responses |
| `PersonCategoryWriteSerializer` | Category create/update |
| `PersonCategoryAssignmentSerializer` | Assignment read — nests full `PersonCategorySerializer` |
| `CategoryAssignWriteSerializer` | Assignment create — just `category_id` |
| `PersonAddressSerializer` | Address read — includes `label_display` |
| `PersonAddressWriteSerializer` | Address create/update |
| `PersonNoteSerializer` | Note read — resolves `author_name` via method field |
| `PersonNoteWriteSerializer` | Note create — just `body` |
| `PersonAttachmentSerializer` | Attachment read — resolves `uploaded_by_name` |
| `OrganizationPersonRelationSerializer` | Relation read |
| `OrganizationPersonRelationWriteSerializer` | Relation create |
| `OrganizationPersonRelationUpdateSerializer` | Relation update — role, is_primary, started_on only |

---

**Views and URLs** (all under `/api/people/`):

| Method | Endpoint | Permission | View function |
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

**Domain exceptions** (`exceptions.py`):

```
PeopleModuleError (base)
├── PersonNotFoundError
├── PersonInactiveError
├── DuplicatePersonError          — carries .candidates list
├── CategoryNotFoundError
├── CategoryInactiveError
├── CategorySystemProtectedError
├── DuplicateCategoryAssignmentError
├── AddressNotFoundError
├── OrganizationRelationNotFoundError
├── OrganizationRelationConflictError
└── MergePersonError
```

---

#### Frontend

**App:** `src/components/modules/people/`
**Nav ID:** `people`

`index.tsx` owns `selectedPersonId: number | null` state shared between Directory (sets it on row click) and Profile (reads it to load the right person).

**Sub-tabs:**

| Sub-tab | Component | Description |
|---|---|---|
| `directory` | `DirectoryPage.tsx` (~615 lines) | Paginated list, search, category filter, Add Person dialog |
| `profile` | `ProfilePage.tsx` (~1071 lines) | 5-panel person detail |
| `categories` | `CategoriesPage.tsx` (~445 lines) | Category master management |
| `settings` | `SettingsPage.tsx` | Module reference docs — no interactive settings |

**`DirectoryPage` features:**
- Search (name/email) with 400ms debounce → `GET /api/people/persons/?search=`
- Category filter dropdown → appends `category_id=`
- Active/All toggle → `is_active=true` or all
- Paginated table, 50 items/page — columns: Name, Email, Phone, Category, Status, Added
- Row click → sets `selectedPersonId`, switches to `profile` sub-tab
- Add Person dialog — two-step: fill form → `POST /api/people/persons/duplicate-check/` → if 409, shows candidates with Force override

**`ProfilePage` panels:**

| Panel | Actions | Endpoints used |
|---|---|---|
| Overview | Edit (with duplicate detection), Deactivate | `GET/PATCH /persons/<id>/`, `POST /persons/<id>/deactivate/` |
| Categories | Assign from dropdown, Remove | `GET/POST /persons/<id>/categories/`, `DELETE /persons/<id>/categories/<cat_id>/` |
| Addresses | Add, Edit, Set Default | `GET/POST /persons/<id>/addresses/`, `PATCH /persons/<id>/addresses/<addr_id>/` |
| Notes | Add (immutable, append-only) | `GET/POST /persons/<id>/notes/` |
| Organizations | Link org, Update relation, Close relation | `GET/POST /persons/<id>/organizations/`, `PATCH/POST-close /persons/<id>/organizations/<rel_id>/` |

**`CategoriesPage` features:**
- List (active-only or all toggle)
- System categories: lock badge, name/slug read-only
- Custom categories: Edit dialog (name, description)
- Add Category dialog, Deactivate with confirmation

**`api.ts`** — centralized API layer, all functions inject `Authorization: Bearer <token>` from `localStorage`:

| Function | Method | Endpoint |
|---|---|---|
| `listPersons(params)` | GET | `persons/` |
| `getPerson(id)` | GET | `persons/<id>/` |
| `createPerson(data)` | POST | `persons/` |
| `updatePerson(id, data)` | PATCH | `persons/<id>/` |
| `deactivatePerson(id)` | POST | `persons/<id>/deactivate/` |
| `listCategories(params)` | GET | `categories/` |
| `createCategory(data)` | POST | `categories/create/` |
| `updateCategory(id, data)` | PATCH | `categories/<id>/` |
| `deactivateCategory(id)` | POST | `categories/<id>/deactivate/` |
| `getPersonCategories(personId, params)` | GET | `persons/<id>/categories/` |
| `assignCategory(personId, categoryId)` | POST | `persons/<id>/categories/` |
| `removeCategory(personId, catId)` | DELETE | `persons/<id>/categories/<cat_id>/` |
| `getPersonAddresses(personId, params)` | GET | `persons/<id>/addresses/` |
| `createAddress(personId, data)` | POST | `persons/<id>/addresses/` |
| `updateAddress(personId, addrId, data)` | PATCH | `persons/<id>/addresses/<addr_id>/` |
| `getPersonNotes(personId)` | GET | `persons/<id>/notes/` |
| `createNote(personId, body)` | POST | `persons/<id>/notes/` |
| `getPersonOrganizations(personId, params)` | GET | `persons/<id>/organizations/` |
| `linkOrganization(personId, data)` | POST | `persons/<id>/organizations/` |
| `updateOrgRelation(personId, relId, data)` | PATCH | `persons/<id>/organizations/<rel_id>/` |
| `closeOrgRelation(personId, relId)` | POST | `persons/<id>/organizations/<rel_id>/close/` |

**`types.ts`** — all domain interfaces:

```typescript
PersonCategory             // id, name, slug, description, is_system, is_active, created_at, updated_at
PersonCategoryAssignment   // id, category: PersonCategory, assigned_by_name, is_active, created_at
PersonAddress              // id, label, label_display, line1, line2, city, state_province, postal_code, country, is_default, is_active
PersonNote                 // id, body, author_name, created_at
PersonAttachment           // id, label, file, uploaded_by_name, created_at
OrganizationPersonRelation // id, person_id, organization_id, organization_type, role, is_primary, is_active, started_on, ended_on
PersonListItem             // id, full_name, display_name, email, phone, is_active, primary_category, created_at
PersonDetail               // extends PersonListItem + addresses[], category_assignments[], org_relations[], notes[], attachments[]
PaginatedPersons           // results: PersonListItem[], count, page, page_size, has_next
DuplicateCandidate         // id, full_name, email, phone
ApiError                   // status: number, body: { detail?, code?, candidates?: DuplicateCandidate[] }
```

---

### 8. Partner Company Module

**Status:** `⬜ Planned`

Master data module for all external organizations. Mirrors the Person Module architecture — company registration, built-in category management, and address/note/attachment sub-resources follow the same patterns as the people domain.

**Typical partner company types:** Customer companies, suppliers, distributors, subcontractors, service providers, logistics companies, commission partners, strategic business partners

**Key capabilities:**
- Company registration (legal name, trading name, registration number, tax ID)
- Legal and contact information management
- Address management (registered, billing, branch offices)
- Notes and attachments
- Lifecycle status control (active/inactive with soft deactivation)
- Linked person management via Org–Person Relationship
- Company search and filtering
- Reusable company identity across modules without duplication
- Dynamic category assignment (many-to-many — same model as Person categories)

**Company category capabilities (built-in):**
- System and custom company categories
- Many-to-many category assignment per company
- Category-based discount and pricing profile mapping (via Pricing module)
- Category-based business access profile mapping
- Company segmentation and reporting

**Example company categories:** Customer Company, Supplier, Dealer, Strategic Partner, Logistics Partner, Preferred Supplier

#### Backend

**Planned app:** `backend/companies/`

**Planned models:**

- `CompanyCategory` — mirrors `PersonCategory`: name, slug, is_system, is_active
- `Company` — legal_name, trading_name, registration_number, tax_id, website, email, phone, is_active, created_by
- `CompanyCategoryAssignment` — M2M through model with is_active (same pattern as `PersonCategoryAssignment`)
- `CompanyAddress` — same fields as `PersonAddress`
- `CompanyNote` — immutable, same pattern as `PersonNote`
- `CompanyAttachment` — same pattern as `PersonAttachment`

**Planned services:** `create_company()`, `update_company()`, `deactivate_company()`, `assign_company_category()`, `remove_company_category()`, `deactivate_company_category()`, `create_company_address()`, `create_company_note()`

**Planned endpoints** (mirrors `/api/people/`):
```
GET/POST       /api/companies/companies/
POST           /api/companies/companies/duplicate-check/
GET/PATCH      /api/companies/companies/<id>/
POST           /api/companies/companies/<id>/deactivate/
GET/POST       /api/companies/companies/<id>/categories/
DELETE         /api/companies/companies/<id>/categories/<cat_id>/
GET/POST       /api/companies/companies/<id>/addresses/
PATCH          /api/companies/companies/<id>/addresses/<addr_id>/
GET/POST       /api/companies/companies/<id>/notes/
GET            /api/companies/companies/<id>/attachments/
GET            /api/companies/categories/
POST           /api/companies/categories/create/
PATCH          /api/companies/categories/<id>/
POST           /api/companies/categories/<id>/deactivate/
```

#### Frontend

**Planned Nav ID:** `companies`
**Planned app:** `src/components/modules/companies/`

**Planned sub-tabs:**

| Sub-tab | Planned content |
|---|---|
| `directory` | Paginated company list with search, category filter, status toggle |
| `profile` | Multi-panel: Overview, Categories, Addresses, Notes, Persons, Attachments |
| `categories` | Company category management — same UI pattern as People → Categories |
| `settings` | Module reference docs |

**Company category system** (built-in, same design as Person categories):
- One master company category table with `is_system` protection
- Many-to-many assignment per company
- Example categories: Customer Company, Supplier, Dealer, Strategic Partner, Logistics Partner, Preferred Supplier

---

### 9. Organization–Person Relationship Management

**Status:** `✅ Complete` (backend); frontend rendered inside Person Profile → Organizations panel

Manages relationships between persons and partner companies. Tracks who represents whom and in what capacity. One person can link to multiple companies; one company can have multiple linked persons.

**Key capabilities:**
- Link person to company with a defined relationship type
- Define relationship type, designation, and department
- Set primary contact flag per company
- Start and end date tracking (temporal lifecycle)
- Full relationship history (closed relations preserved)
- Support one person linked to multiple companies simultaneously
- Support one company linked to multiple persons

**Example relationship types:** Representative, Finance Contact, Sales Contact, Purchasing Contact, Billing Contact, Owner, Authorized Signatory

> A person marked as a company representative may later become a direct customer — no new person record is needed. The relationship is updated; the identity record stays the same.

#### Backend

**App:** `backend/people/` — org relations are sub-resources of the Person.

**Model:** `OrganizationPersonRelation` (documented fully in Module 7)

**Key design decision:** `organization_id` and `organization_type` are plain fields — not a FK — because the companies app does not exist yet. When `backend/companies/` ships, this becomes a proper `ForeignKey(Company)` migration.

**Services:** `link_person_to_organization()`, `update_organization_relationship()`, `close_organization_relationship()` — documented in Module 7.

**Endpoints:** All under `/api/people/persons/<id>/organizations/` — documented in Module 7.

**Reciprocal view (planned):** When the Company module ships, `GET /api/companies/companies/<id>/persons/` will return all person relations for a company, queried from the same `OrganizationPersonRelation` table filtered by `organization_id` and `organization_type`.

#### Frontend

Accessible via `people` → `profile` → Organizations panel. No standalone nav entry currently. Documented fully in Module 7's ProfilePage section.

---

### 10. Product and Service Management Module

**Status:** `⬜ Planned`

Master catalog for all products and services. Referenced by Sales, Purchase, Inventory, and Finance modules.

**Key capabilities:**
- Product master records (physical goods)
- Service master records (non-inventory items)
- SKU and item code management
- Product classification and category assignment
- Unit of measure (UOM) management
- Pricing references (list price, cost price)
- Tax class assignment
- Active/inactive lifecycle management
- Image and document attachments

#### Backend

**Planned app:** `backend/products/`

**Planned models:**
- `ProductCategory` — hierarchical classification (parent FK to self)
- `UnitOfMeasure` — `name`, `abbreviation`, `is_active`
- `Product` — `code` (SKU), `name`, `type` (`product`/`service`), `category`, `uom`, `list_price`, `cost_price`, `tax_class`, `is_active`, `description`
- `ProductAttachment` — image and document attachments

**Planned endpoints:**
```
GET/POST   /api/products/products/
GET/PATCH  /api/products/products/<id>/
POST       /api/products/products/<id>/deactivate/
GET/POST   /api/products/categories/
GET/POST   /api/products/uom/
```

#### Frontend

**Planned Nav ID:** `products`
**Planned app:** `src/components/modules/products/`

**Planned sub-tabs:**

| Sub-tab | Planned content |
|---|---|
| `catalog` | Paginated list with search, category, type (product/service) filters |
| `profile` | Product detail: code, name, description, category, UOM, pricing, tax, status |
| `categories` | Product category CRUD |
| `settings` | UOM management, code generation rules |

---

### 11. Pricing, Discount, and Access Profile Module

**Status:** `⬜ Planned`

Manages reusable business rule profiles linked to person and company categories. This is how category-based behavior (discounts, pricing tiers, access rights) is configured without hardcoding rules into each module.

**Design principle:** Category → Profile mapping. A category (e.g. "VIP Gold") links to a profile (e.g. "15% Discount"). Effective profile for any entity is resolved by finding their highest-priority active category with a linked profile.

**Key capabilities:**
- Discount profile management (percentage, fixed amount, tiered)
- Pricing profile setup (price list association — retail, wholesale, partner)
- Commission profile setup (rate, calculation method, conditions)
- Business access profile setup (module/feature visibility rules)
- Category-to-profile mapping with priority ordering
- Priority and conflict handling for multiple active profiles
- Effective profile resolution at runtime

**Example mappings:**
- VIP Gold category → 15% discount profile
- Dealer category → wholesale pricing profile
- Preferred Supplier category → procurement privilege access profile

#### Backend

**Planned app:** `backend/profiles/`

**Planned models:**
- `DiscountProfile` — `name`, `type` (`percentage`/`fixed`), `value`, `is_active`
- `PricingProfile` — `name`, linked price list reference, `is_active`
- `CommissionProfile` — `name`, `rate`, `calculation_method`, `is_active`
- `AccessProfile` — `name`, `rules` (JSON — module/feature visibility flags), `is_active`
- `PersonCategoryProfileMapping` — links `PersonCategory` → profile with `priority`, effective dates
- `CompanyCategoryProfileMapping` — links `CompanyCategory` → profile with `priority`, effective dates

**Planned endpoints:**
```
GET/POST   /api/profiles/discounts/
GET/POST   /api/profiles/pricing/
GET/POST   /api/profiles/commissions/
GET/POST   /api/profiles/access/
GET/POST   /api/profiles/category-mappings/person/
GET/POST   /api/profiles/category-mappings/company/
```

#### Frontend

**Planned Nav ID:** `profiles`
**Planned app:** `src/components/modules/profiles/`

**Planned sub-tabs:** Discount Profiles, Pricing Profiles, Commission Profiles, Access Profiles, Category Mapping

---

## Layer C — Operational Business Modules

---

### 12. Customer Management Module

**Status:** `🔨 In Progress` — frontend shell exists; no backend

Manages customer-specific commercial operations. A customer is registered from an existing Person or Partner Company record — no identity data is duplicated. This module adds commercial attributes on top of master data, never duplicating name, contact, or address information.

**Key capabilities:**
- Customer registration from existing Person or Partner Company record
- Customer profile management (credit settings, pricing rules)
- Billing and delivery references
- Customer pricing and discount eligibility (via Pricing module)
- Customer status management (prospect, active, inactive, churned)
- Credit limit and payment terms setup
- Customer transaction history (linked to Sales and Finance)
- Customer segmentation and analysis via category system

#### Backend

**Status:** Not yet implemented.

**Planned app:** `backend/customers/`

**Planned models:**
- `Customer` — `person` (FK, nullable) or `company` (FK, nullable); one of the two must be set; `credit_limit`, `payment_terms`, `pricing_profile`, `status`, `is_active`
- Constraint: `CHECK (person IS NOT NULL OR company IS NOT NULL)`

**Planned endpoints:**
```
GET/POST   /api/customers/customers/
GET/PATCH  /api/customers/customers/<id>/
POST       /api/customers/customers/<id>/deactivate/
GET        /api/customers/customers/<id>/transactions/
```

#### Frontend

**App:** `src/components/modules/customers/`
**Nav ID:** `customers`

| Sub-tab | Current content | Planned |
|---|---|---|
| `dashboard` | KPI cards, growth/churn bar chart, plan distribution, recent customers table — all mock | Wire to real backend; role-based KPIs |
| `management` | Search + filter + CRUD table + Add dialog — 8 mock records | Full CRUD connected to API |
| `profiles` | Profile card + activity timeline — mock | Load from real customer + person/company record |
| `settings` | Onboarding, churn detection, webhooks — static UI | Persist to backend settings |

---

### 13. Supplier Management Module

**Status:** `⬜ Planned`

Manages suppliers and procurement-related external entities. A supplier is registered from an existing Partner Company record — identity data stays in Partner Company; this module adds procurement-specific attributes.

**Key capabilities:**
- Supplier registration from existing Partner Company record
- Supplier contact person mapping (links to Person records)
- Supplier profile management
- Payment terms setup (net days, payment method, currency)
- Procurement linkage (connected to Purchase Management)
- Supplier lifecycle control (active/inactive)
- Supplier segmentation via category system
- Supplier performance tracking references
- Document and compliance attachment support (certificates, contracts)

#### Backend

**Planned app:** `backend/suppliers/`

**Planned models:**
- `Supplier` — `company` (FK → Company), `payment_terms`, `currency`, `lead_time_days`, `status`, `is_active`
- `SupplierContact` — link to `Person` as primary/secondary contact for this supplier

**Planned endpoints:**
```
GET/POST   /api/suppliers/suppliers/
GET/PATCH  /api/suppliers/suppliers/<id>/
POST       /api/suppliers/suppliers/<id>/deactivate/
GET/POST   /api/suppliers/suppliers/<id>/contacts/
```

#### Frontend

**Planned Nav ID:** `suppliers`
**Planned app:** `src/components/modules/suppliers/`

**Planned sub-tabs:** Directory, Profile (Overview, Contacts, Payment Terms, Documents, Performance), Settings

---

### 14. Inventory and Warehouse Management Module

**Status:** `⬜ Planned`

Manages physical stock, warehouse structure, and inventory movement across storage locations.

**Key capabilities:**
- Warehouse and storage location setup
- Real-time stock level tracking per item per location
- Inventory adjustments with reason codes and audit trail
- Stock transfer between locations
- Goods receipt (linked to Purchase Management)
- Goods issue (linked to Sales Management)
- Reorder level monitoring with low-stock alerts
- Stock valuation (FIFO, average cost — TBD)
- Batch, lot, or serial number tracking (if required)
- Full inventory movement history

#### Backend

**Planned app:** `backend/inventory/`

**Planned models:**
- `Warehouse` — `name`, `code`, `address`, `is_active`
- `StorageLocation` — `warehouse` (FK), `name`, `code`
- `StockLedger` — `product`, `warehouse`, `location`, `quantity`, `unit_cost`, `as_of`
- `StockMovement` — `type` (`receipt`/`issue`/`transfer`/`adjustment`), `product`, `from_location`, `to_location`, `quantity`, `reference`, `created_by`
- `ReorderRule` — `product`, `warehouse`, `reorder_point`, `reorder_quantity`

**Planned endpoints:**
```
GET/POST   /api/inventory/warehouses/
GET        /api/inventory/stock/               # current stock levels
POST       /api/inventory/adjustments/         # manual adjustments
POST       /api/inventory/transfers/           # stock transfers
GET        /api/inventory/movements/           # movement history
```

#### Frontend

**Planned Nav ID:** `inventory`

**Planned sub-tabs:** Overview (stock summary, low-stock alerts), Stock Ledger, Warehouses, Movements, Adjustments

---

### 15. Sales Management Module

**Status:** `⬜ Planned`

Manages the full sales lifecycle from quotation to order and fulfillment. Integrates with Customer, Product, Pricing, Inventory, and Workflow modules.

**Key capabilities:**
- Quotation and proposal creation
- Sales order creation (from quotation or direct)
- Customer pricing profile application
- Discount profile application
- Delivery coordination references
- Sales status lifecycle (draft → confirmed → fulfilled → closed)
- Sales history and analytics
- Integration with Inventory (stock deduction) and Finance (invoice generation)

#### Backend

**Planned app:** `backend/sales/`

**Planned models:**
- `SalesQuotation` — `customer`, `date`, `expiry_date`, `status`, `total`, `notes`
- `SalesQuotationLine` — `quotation`, `product`, `quantity`, `unit_price`, `discount`, `line_total`
- `SalesOrder` — `customer`, `quotation` (FK, nullable), `date`, `status`, `total`
- `SalesOrderLine` — `order`, `product`, `quantity`, `unit_price`, `discount`
- `DeliveryReference` — `order`, `date`, `status`, `notes`

**Planned endpoints:**
```
GET/POST   /api/sales/quotations/
GET/PATCH  /api/sales/quotations/<id>/
POST       /api/sales/quotations/<id>/convert/   # convert to order
GET/POST   /api/sales/orders/
GET/PATCH  /api/sales/orders/<id>/
POST       /api/sales/orders/<id>/fulfil/
```

#### Frontend

**Planned Nav ID:** `sales`

**Planned sub-tabs:** Dashboard (revenue KPIs, pipeline), Quotations, Orders, Delivery, History

---

### 16. Purchase Management Module

**Status:** `⬜ Planned`

Manages procurement activities and purchasing transactions with suppliers.

**Key capabilities:**
- Purchase requisition creation and approval
- Purchase order generation from approved requisition
- Supplier item references and pricing
- Multi-level procurement approval flows (via Workflow module)
- Goods receipt recording with inventory linkage
- Purchase status lifecycle (draft → approved → sent → received → closed)
- Procurement history and analytics

#### Backend

**Planned app:** `backend/purchasing/`

**Planned models:**
- `PurchaseRequisition` — `requested_by`, `date`, `status`, `notes`
- `PurchaseRequisitionLine` — `requisition`, `product`, `quantity`, `estimated_cost`
- `PurchaseOrder` — `supplier`, `requisition` (FK, nullable), `date`, `status`, `total`
- `PurchaseOrderLine` — `order`, `product`, `quantity`, `unit_cost`
- `GoodsReceipt` — `purchase_order`, `date`, `status`, `notes`
- `GoodsReceiptLine` — `receipt`, `order_line`, `quantity_received`

**Planned endpoints:**
```
GET/POST   /api/purchasing/requisitions/
POST       /api/purchasing/requisitions/<id>/approve/
GET/POST   /api/purchasing/orders/
POST       /api/purchasing/orders/<id>/send/
GET/POST   /api/purchasing/receipts/
```

#### Frontend

**Planned Nav ID:** `purchasing`

**Planned sub-tabs:** Dashboard (open orders, pending approvals, spend), Requisitions, Purchase Orders, Goods Receipt, History

---

### 17. Finance and Accounting Module

**Status:** `⬜ Planned`

Manages financial transactions, payment tracking, and financial control processes across ERP operations. Initial scope is operational finance — not full double-entry accounting. Scope can be expanded later.

**Key capabilities:**
- Invoice management (sales and purchase invoices)
- Receivables and payables tracking
- Payment recording and reconciliation
- Expense tracking and categorization
- Tax calculations per line item
- Financial summaries (AR/AP aging, cash position)
- Financial reporting
- Audit support (transaction history with user attribution)
- Transaction history

#### Backend

**Planned app:** `backend/finance/`

**Planned models:**
- `Invoice` — `type` (`sales`/`purchase`), `reference` (FK to order), `customer` or `supplier`, `date`, `due_date`, `status`, `total`
- `InvoiceLine` — `invoice`, `description`, `quantity`, `unit_price`, `tax_amount`, `line_total`
- `Payment` — `invoice`, `amount`, `date`, `method`, `reference`, `created_by`
- `Expense` — `category`, `amount`, `date`, `description`, `created_by`

**Planned endpoints:**
```
GET/POST   /api/finance/invoices/
GET/PATCH  /api/finance/invoices/<id>/
POST       /api/finance/invoices/<id>/pay/
GET        /api/finance/receivables/
GET        /api/finance/payables/
GET/POST   /api/finance/expenses/
GET        /api/finance/reports/summary/
```

#### Frontend

**Planned Nav ID:** `finance`

**Planned sub-tabs:** Dashboard (AR/AP summary, cash, overdue alerts), Invoices, Payments, Receivables, Payables, Expenses, Reports

---

### 18. Commission Management Module

**Status:** `⬜ Planned`

Manages commission-related persons, companies, eligibility rules, and payout references. Commission holders are persons with the "Commission Holder" category assigned in the Person Module.

**Key capabilities:**
- Commission holder mapping (link Person to commission profile)
- Commission profile assignment (rate, calculation method, conditions)
- Commission eligibility rule setup
- Commission reference tracking linked to sales or transactions
- Commission history and payout records
- Reporting and analysis
- Linkage with Sales (commission trigger) and Finance (payout processing)

#### Backend

**Planned app:** `backend/commissions/`

**Planned models:**
- `CommissionHolder` — `person` (FK), `profile` (FK → CommissionProfile), `is_active`
- `CommissionRecord` — `holder`, `reference_type`, `reference_id`, `amount`, `status`, `created_at`

**Planned endpoints:**
```
GET/POST   /api/commissions/holders/
GET/PATCH  /api/commissions/holders/<id>/
GET        /api/commissions/records/
GET        /api/commissions/records/<id>/
```

#### Frontend

**Planned Nav ID:** `commissions`

**Planned sub-tabs:** Holders, Rules (linked to Pricing/Discount module), Tracking, History

---

### 19. Workflow and Approval Management Module

**Status:** `⬜ Planned`

Manages approval chains, business process routing, and automated workflow decisions across the ERP. Used as an approval gate by Purchase, Finance, Customer, and other modules before state transitions occur.

**Key capabilities:**
- Configurable multi-step workflow definitions
- Multi-level approval chains
- Role-based approver assignment per step
- Workflow conditions and branching triggers
- Escalation support (auto-reassign on timeout)
- Status transition control (action blocked until approved)
- Workflow history and audit logs per record

**Example workflows:**
- Customer onboarding approval
- Purchase order approval
- Invoice approval
- Category change approval
- User account activation approval

#### Backend

**Planned app:** `backend/workflows/`

**Planned models:**
- `WorkflowDefinition` — `name`, `trigger_module`, `trigger_action`, `is_active`
- `WorkflowStep` — `definition`, `order`, `approver_role`, `timeout_hours`
- `WorkflowInstance` — `definition`, `resource_type`, `resource_id`, `status`, `current_step`, `created_by`
- `WorkflowDecision` — `instance`, `step`, `actor`, `decision` (`approved`/`rejected`), `note`, `decided_at`

**Planned endpoints:**
```
GET/POST   /api/workflows/definitions/
GET        /api/workflows/pending/           # items awaiting current user
POST       /api/workflows/instances/<id>/approve/
POST       /api/workflows/instances/<id>/reject/
GET        /api/workflows/instances/<id>/history/
```

#### Frontend

**Planned Nav ID:** `workflows`

**Planned sub-tabs:** Definitions (configure workflows), Pending Approvals (current user's inbox), History (completed workflows with decisions)

---

## Layer D — Support and Intelligence

---

### 20. Notification and Communication Module

**Status:** `⬜ Planned`

Manages ERP-generated communications and notification events. Covers both email and in-app delivery channels. The bell icon in `TopBar.tsx` is already present as a UI placeholder.

**Key capabilities:**
- Email notifications (SMTP-based, configurable via Settings module)
- In-app notification inbox
- Onboarding messages (welcome emails, first-login prompts)
- Workflow alerts (approval requested, approved, rejected)
- Reminder notifications (overdue payments, pending reviews)
- Template-based communication with variable substitution
- Notification delivery logs
- Notification history per user

#### Backend

**Planned app:** `backend/notifications/`

**Planned models:**
- `NotificationTemplate` — `name`, `channel` (`email`/`in_app`), `subject`, `body_template` (with variable slots)
- `Notification` — `recipient` (FK → User), `template`, `channel`, `status` (`pending`/`sent`/`failed`), `sent_at`, `payload` (JSON)

**Planned endpoints:**
```
GET        /api/notifications/                 # current user's unread notifications
POST       /api/notifications/<id>/read/
GET        /api/notifications/templates/
```

**Integration:** Services in all modules call `notifications.services.send()` after key events (approval requested, record created, etc.).

#### Frontend

No dedicated nav tab — integrates into the TopBar bell icon (currently static).

**Planned:** Notification dropdown/drawer from bell icon; unread count badge; mark-as-read.

---

### 21. Document and Attachment Management Module

**Status:** `🔨 In Progress` — attachment list endpoint exists; file upload deferred

Manages files and supporting documents linked to ERP records across all modules.

**Key capabilities:**
- Person attachments (ID documents, signed forms)
- Company attachments (registration documents, compliance certificates)
- Invoice and transaction files (PDF invoices, receipts)
- Compliance documents (contracts, certificates)
- Categorized document storage with labels
- Controlled access based on role permissions
- Document history and version tracking
- Attachment references across all modules (persons, companies, orders, invoices)

#### Backend

**Current state:** `PersonAttachment` model and `GET /api/people/persons/<id>/attachments/` exist. File upload (`POST`) is deferred — `MEDIA_ROOT` and `MEDIA_URL` are not yet configured in `settings.py`.

**Planned additions to `settings.py`:**
```python
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"
```

**Planned app expansion:** A shared `documents` app providing a generic attachment service usable by persons, companies, invoices, orders, etc. — avoiding per-module attachment models.

**Planned model:**
- `Attachment` — `content_type` (FK → ContentType), `object_id`, `label`, `file`, `file_size`, `mime_type`, `uploaded_by`, `created_at`

**Planned endpoints:**
```
GET/POST   /api/documents/attachments/?resource_type=person&resource_id=<id>
GET        /api/documents/attachments/<id>/
DELETE     /api/documents/attachments/<id>/
```

#### Frontend

No dedicated nav tab currently. Attachment panels exist inside Person ProfilePage (Panel 5 — list only).

**Planned:** Attachment panels on Company Profile, Invoice detail, Order detail. Upload dialog with file drag-and-drop.

---

### 22. Reporting and Analytics Module

**Status:** `🔨 In Progress` — frontend shell only; no backend data source

Provides operational visibility through dashboards, reports, exports, and summarized analytics across all ERP domains.

**Key capabilities:**
- Dashboard reporting (cross-module KPI summaries)
- Sales reports (volume, revenue, by customer, by product)
- Finance reports (AR/AP aging, cash flow summary)
- Inventory reports (stock levels, movement, valuation)
- Customer and supplier analytics
- Person and company segmentation reports
- Category-based analysis
- Exportable reports in CSV, Excel, PDF
- Filtered operational insights with date range and dimension controls

#### Backend

**Status:** Not yet implemented.

**Planned approach:** Read-only reporting views that aggregate data across modules. No separate models — queries across existing tables.

**Planned endpoints:**
```
GET   /api/reports/sales/summary/
GET   /api/reports/inventory/stock-summary/
GET   /api/reports/finance/ar-aging/
GET   /api/reports/customers/growth/
GET   /api/reports/exports/             # async export job submission
GET   /api/reports/exports/<job_id>/    # download when ready
```

#### Frontend

**App:** `src/components/dashboards/AnalyticsDashboard.tsx`
**Nav ID:** `analytics`

| Sub-tab | Current content | Planned |
|---|---|---|
| `usage` | Total Requests KPI, Error Rate KPI, request type breakdown — static mock | Business metrics: sales volume, customer growth, inventory turns |
| `reports` | Scheduled reports table with Name, Schedule, Format, Last Run, Download — static mock | Real report generation from backend |
| `exports` | Format selector (CSV/JSON/Excel), date range picker, dataset checkboxes — static UI | Export job submission and download |

---

### 23. AI Integration Module

**Status:** `⬜ Planned`

Provides a structured integration layer for external AI services. AI logic is kept separate from core business modules so providers can be swapped without redesigning the ERP.

**Architectural principle:** Business modules call AI service functions via an internal adapter interface. No module calls an external AI API directly. The AI layer sits between the API layer and external providers — providers can be replaced without changing any calling business module.

**Key capabilities:**
- AI provider integration with pluggable adapters (swap provider without changing callers)
- AI-assisted reporting and business data summarization
- Intelligent document analysis (extract fields from uploaded files)
- Business data summarization for dashboards
- Recommendation support (e.g. suggest reorder quantities, flag unusual patterns)
- Reusable AI service adapters
- Provider replacement flexibility
- AI request and response logging and monitoring

#### Backend

**Planned app:** `backend/ai/`

**Planned models:**
- `AIProvider` — `name`, `adapter_class`, `config` (JSON), `is_active`
- `AIRequestLog` — `provider`, `request_type`, `input_summary`, `output_summary`, `latency_ms`, `status`, `created_at`

**Planned services:**
- `ai.services.summarize(text)` — text summarization
- `ai.services.extract_fields(document)` — document field extraction
- `ai.services.recommend(context)` — recommendation generation

**Planned endpoints:**
```
POST  /api/ai/summarize/
POST  /api/ai/extract/
GET   /api/ai/logs/
```

#### Frontend

No dedicated nav tab initially. AI capabilities surfaced inline in relevant module panels (e.g. "Summarize notes" button in Person Profile, "Analyze document" in attachments panel).

---

### 24. API and Integration Module

**Status:** `⬜ Planned`

Exposes ERP functionality to internal and external consumers through secure, versioned REST APIs and integration endpoints.

**Key capabilities:**
- Versioned REST API exposure (`/api/v1/`, `/api/v2/`)
- Authenticated API access via API keys for external consumers
- Module endpoint organization
- Webhook support for outbound events on record changes
- External system integration adapters
- Partner, mobile, and client application integration support
- Versioning support to avoid breaking changes
- API rate limiting and monitoring per consumer

#### Backend

**Planned additions to existing DRF setup:**
- API key model for external consumers (`APIKey` — `name`, `key_hash`, `owner`, `permissions`, `last_used`, `is_active`)
- Versioned URL namespace (`/api/v1/`, `/api/v2/`)
- Rate limiting middleware per API key
- Webhook model — `WebhookEndpoint` (`url`, `events`, `secret`, `is_active`)
- Outbound webhook dispatcher — fires on record create/update/deactivate events

**Planned endpoints:**
```
GET/POST   /api/integrations/api-keys/
DELETE     /api/integrations/api-keys/<id>/
GET/POST   /api/integrations/webhooks/
DELETE     /api/integrations/webhooks/<id>/
GET        /api/integrations/webhooks/<id>/logs/
```

#### Frontend

No dedicated module UI initially. API key management surfaces under Settings → Integrations sub-tab.

---

### 25. Dashboard, Search, and Global Navigation Services

**Status:** `🔨 In Progress` — navigation fully working; global search not yet implemented

System-wide usability services that support cross-module access and navigation efficiency. Not a standalone page — integrated into the shell layout.

**Key capabilities:**
- Global search across all ERP records (persons, companies, customers, products, orders)
- Quick record lookup with typeahead results
- Recent records panel (last-viewed across all modules)
- Keyboard shortcuts for navigation
- Bookmarks or favorites per user
- Navigation helpers and shortcuts
- Dashboard data aggregation from multiple modules

#### Backend

**Current state:** No backend search endpoint. All data fetched per-module.

**Planned:** A global search endpoint that fans out to multiple module selectors and returns ranked results:
```
GET  /api/search/?q=<query>
→ { persons: [...], companies: [...], customers: [...], products: [...] }
```

#### Frontend

**Current state:**
- Full navigation system working: `nav.ts` → `Sidebar` → `MainCanvas`
- `TopBar.tsx` contains a search icon (not yet functional)
- Recent activity in Overview Dashboard

**Planned:**
- Global search typeahead from TopBar — calls `/api/search/`
- Recent records list (last-viewed across all modules)
- Keyboard shortcut support

---

## Layer E — Infrastructure

---

### 26. DevOps, Deployment, and Environment Management Module

**Status:** `🔨 In Progress` — frontend shell exists; no backend connection

Covers the operational infrastructure required to run the ERP in a stable and scalable way.

**Key capabilities:**
- Containerized deployment (Docker + orchestration)
- Environment configuration management (dev, staging, production, QA)
- CI/CD pipeline integration
- Cloud deployment on AWS or Azure
- PostgreSQL hosting and maintenance
- Secret management (environment-level, not stored in code)
- Monitoring and alerting integration
- Logging and observability (structured logs, log aggregation)
- Backup and recovery planning

#### Backend

**Current state:** Django dev server on `localhost:8000`. SQLite database. No container or deployment config exists in the repository.

**Planned:**
- `Dockerfile` and `docker-compose.yml` for local and production
- `gunicorn` as the production WSGI server
- `nginx` for static file serving and reverse proxy
- Environment-based `settings_production.py` — PostgreSQL, `DEBUG=False`, `ALLOWED_HOSTS`, `SECRET_KEY` from environment
- `MEDIA_ROOT` configured for file upload support
- Health check endpoint: `GET /api/health/` → `{ status: "ok", db: "ok" }`

#### Frontend

**App:** `src/components/dashboards/InfrastructureDashboard.tsx`
**Nav ID:** `infrastructure`

| Sub-tab | Current content | Planned |
|---|---|---|
| `environments` | Grid: Production, Staging, Development, QA cards with status badges, region, last deployed — static mock | Wire to deployment state API or CI/CD webhook |
| `deployments` | Deployment history table: Branch, Commit, Author, Status, Duration, Time — static mock | CI/CD pipeline integration |
| `logs` | Log stream: Level (INFO/WARN/ERROR color coded), Service, Message, Timestamp — static mock | Connect to real log aggregation (e.g. CloudWatch, Loki) |

---

## Module Dependency Map

```
Foundation (A) ── no dependencies; provides services consumed by all layers

                  ┌─────────────────────────────────────────────────┐
Master Data (B)   │ Person ──────────────────────────────────────────┤
                  │ Partner Company ─────────────────────────────────┤
                  │ Org–Person Relationship ─────────────────────────┼──→ Customer, Supplier, Commission
                  │ Product ─────────────────────────────────────────┼──→ Inventory, Sales, Purchase
                  │ Pricing/Discount Profiles ───────────────────────┤──→ Customer, Sales
                  └─────────────────────────────────────────────────┘

                  ┌─────────────────────────────────────────────────┐
Operational (C)   │ Customer ──────────→ Sales, Finance              │
                  │ Supplier ──────────→ Purchase, Finance           │
                  │ Inventory ─────────→ Sales (deduction), Purchase │
                  │ Sales ─────────────→ Finance (invoicing)         │
                  │ Purchase ──────────→ Finance (payables)          │
                  │ Finance ───────────→ Reporting                   │
                  │ Commission ────────→ Sales (trigger), Finance    │
                  │ Workflow ──────────→ Customer, Purchase, Finance │
                  └─────────────────────────────────────────────────┘

                  ┌─────────────────────────────────────────────────┐
Support (D)       │ Notifications ─→ consumed by Workflow, Users      │
                  │ Documents ─────→ consumed by Person, Company,    │
                  │                  Finance, Orders                 │
                  │ Reporting ─────→ reads from Sales, Inventory,   │
                  │                  Finance, Customer               │
                  │ AI ────────────→ consumed by Reporting, Docs     │
                  │ API/Integrations→ exposes all modules externally │
                  └─────────────────────────────────────────────────┘

Infrastructure (E) ── hosts and operates all of the above
```

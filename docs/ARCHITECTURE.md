# Architecture — Altavisor Frontend

> Strictly derived from the source code at `frontend/src/`. Nothing is assumed or invented.

---

## Tech Stack and Dependencies

### Runtime and Framework

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

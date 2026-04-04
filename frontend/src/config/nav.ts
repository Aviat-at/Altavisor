import DashboardRoundedIcon  from "@mui/icons-material/DashboardRounded";
import TuneRoundedIcon       from "@mui/icons-material/TuneRounded";
import PeopleRoundedIcon     from "@mui/icons-material/PeopleRounded";
import SecurityRoundedIcon   from "@mui/icons-material/SecurityRounded";
import BarChartRoundedIcon   from "@mui/icons-material/BarChartRounded";
import CloudRoundedIcon      from "@mui/icons-material/CloudRounded";
import GroupsRoundedIcon     from "@mui/icons-material/GroupsRounded";
import ContactsRoundedIcon   from "@mui/icons-material/ContactsRounded";

export interface SubTab {
  id: string;
  label: string;
}

export interface NavTab {
  id: string;
  label: string;
  icon: React.ElementType;
  subtabs: SubTab[];
}

const navConfig: NavTab[] = [
  {
    id: "overview",
    label: "Overview",
    icon: DashboardRoundedIcon,
    subtabs: [
      { id: "summary",  label: "Summary"      },
      { id: "activity", label: "Activity Log"  },
      { id: "health",   label: "System Health" },
    ],
  },
  // ── Add your business modules here ────────────────────────────────────────
  // Each module follows the same pattern:
  //   1. Add the entry below with an id, label, icon, and subtabs array
  //   2. Create src/components/dashboards/<id>/index.tsx  (the router)
  //   3. Create one .tsx file per sub-tab inside that folder
  //   4. Register the import in MainCanvas.tsx
  {
    id: "customers",
    label: "Customers",
    icon: GroupsRoundedIcon,
    subtabs: [
      { id: "dashboard",  label: "Dashboard"   },
      { id: "management", label: "Management"  },
      { id: "profiles",   label: "Profiles"    },
      { id: "settings",   label: "Settings"    },
    ],
  },
  {
    id: "people",
    label: "People",
    icon: ContactsRoundedIcon,
    subtabs: [
      { id: "directory",  label: "Directory"  },
      { id: "profile",    label: "Profile"    },
      { id: "categories", label: "Categories" },
      { id: "settings",   label: "Settings"   },
    ],
  },
  {
    id: "settings",
    label: "Settings",
    icon: TuneRoundedIcon,
    subtabs: [
      { id: "general",      label: "General"      },
      { id: "appearance",   label: "Appearance"   },
      { id: "integrations", label: "Integrations" },
      { id: "advanced",     label: "Advanced"     },
    ],
  },
  {
    id: "users",
    label: "Users",
    icon: PeopleRoundedIcon,
    subtabs: [
      { id: "accounts", label: "Accounts"           },
      { id: "roles",    label: "Roles & Permissions" },
      { id: "invites",  label: "Invites"            },
    ],
  },
  {
    id: "security",
    label: "Security",
    icon: SecurityRoundedIcon,
    subtabs: [
      { id: "auth",     label: "Authentication" },
      { id: "audit",    label: "Audit Trail"    },
      { id: "policies", label: "Policies"       },
    ],
  },
  {
    id: "analytics",
    label: "Analytics",
    icon: BarChartRoundedIcon,
    subtabs: [
      { id: "usage",   label: "Usage"   },
      { id: "reports", label: "Reports" },
      { id: "exports", label: "Exports" },
    ],
  },
  {
    id: "infrastructure",
    label: "Infrastructure",
    icon: CloudRoundedIcon,
    subtabs: [
      { id: "environments", label: "Environments" },
      { id: "deployments",  label: "Deployments"  },
      { id: "logs",         label: "Logs"         },
    ],
  },
];

export default navConfig;

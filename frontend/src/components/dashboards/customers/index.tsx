"use client";
import React from "react";
import DashboardPage  from "./DashboardPage";
import ManagementPage from "./ManagementPage";
import ProfilePage    from "./ProfilePage";
import SettingsPage   from "./SettingsPage";

// ── To add a new page ──────────────────────────────────────────────────────
// 1. Create NewPage.tsx in this folder
// 2. Import it above
// 3. Add:  if (subTabId === "new-page-id") return <NewPage />;
// 4. Add the sub-tab in src/config/nav.ts under the "customers" entry

export default function CustomersDashboard({ subTabId }: { subTabId: string }) {
  if (subTabId === "dashboard")  return <DashboardPage />;
  if (subTabId === "management") return <ManagementPage />;
  if (subTabId === "profiles")   return <ProfilePage />;
  if (subTabId === "settings")   return <SettingsPage />;
  return <DashboardPage />;
}

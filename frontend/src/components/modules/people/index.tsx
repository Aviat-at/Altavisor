"use client";
import React, { useState } from "react";
import DirectoryPage  from "./DirectoryPage";
import ProfilePage    from "./ProfilePage";
import CategoriesPage from "./CategoriesPage";
import SettingsPage   from "./SettingsPage";

// ── To add a new page ──────────────────────────────────────────────────────
// 1. Create NewPage.tsx in this folder
// 2. Import it above
// 3. Add:  if (subTabId === "new-page-id") return <NewPage />;
// 4. Add the sub-tab in src/config/nav.ts under the "people" entry

export default function PeopleDashboard({ subTabId }: { subTabId: string }) {
  // selectedPersonId is shared between Directory (sets it) and Profile (reads it).
  // Clicking a person row in DirectoryPage selects them; the user then switches
  // to the Profile sub-tab to view the full detail.
  const [selectedPersonId, setSelectedPersonId] = useState<number | null>(null);

  if (subTabId === "directory")  return <DirectoryPage onSelectPerson={setSelectedPersonId} />;
  if (subTabId === "profile")    return <ProfilePage personId={selectedPersonId} />;
  if (subTabId === "categories") return <CategoriesPage />;
  if (subTabId === "settings")   return <SettingsPage />;
  return <DirectoryPage onSelectPerson={setSelectedPersonId} />;
}

"use client";
import React from "react";
import { Box, Typography, Tabs, Tab } from "@mui/material";
import { NavTab } from "@/config/nav";

import OverviewDashboard       from "./modules/overview";
import CustomersDashboard      from "./modules/customers";
import PeopleDashboard         from "./modules/people";
import SettingsDashboard       from "./dashboards/SettingsDashboard";
import UsersDashboard          from "./dashboards/UsersDashboard";
import SecurityDashboard       from "./dashboards/SecurityDashboard";
import AnalyticsDashboard      from "./dashboards/AnalyticsDashboard";
import InfrastructureDashboard from "./dashboards/InfrastructureDashboard";

const dashboards: Record<string, React.ComponentType<{ subTabId: string }>> = {
  overview:       OverviewDashboard,
  customers:      CustomersDashboard,
  people:         PeopleDashboard,
  settings:       SettingsDashboard,
  users:          UsersDashboard,
  security:       SecurityDashboard,
  analytics:      AnalyticsDashboard,
  infrastructure: InfrastructureDashboard,
};

interface MainCanvasProps {
  tab: NavTab;
  subTabId: string;
  onSubTabChange: (id: string) => void;
}

export default function MainCanvas({ tab, subTabId, onSubTabChange }: MainCanvasProps) {
  const Dashboard = dashboards[tab.id] || OverviewDashboard;

  return (
    <Box sx={{ flex: 1, display: "flex", flexDirection: "column", overflow: "hidden", bgcolor: "background.default" }}>

      {/* Sub-nav bar */}
      <Box sx={{
        height: 44, minHeight: 44,
        display: "flex", alignItems: "center",
        px: 3,
        bgcolor: "background.paper",
        borderBottom: "1px solid",
        borderColor: "divider",
        gap: 2,
      }}>
        <Typography sx={{
          fontFamily: "'Syne', sans-serif",
          fontWeight: 700,
          fontSize: "0.75rem",
          color: "text.disabled",
          textTransform: "uppercase",
          letterSpacing: "0.08em",
          flexShrink: 0,
        }}>
          {tab.label}
        </Typography>

        <Box sx={{ width: "1px", height: 16, bgcolor: "divider", flexShrink: 0 }} />

        <Tabs
          value={subTabId}
          onChange={(_, val) => onSubTabChange(val)}
          TabIndicatorProps={{ style: { height: 2 } }}
          sx={{
            minHeight: 44,
            "& .MuiTabs-indicator": { bgcolor: "primary.main" },
            "& .MuiTab-root": {
              minHeight: 44,
              textTransform: "none",
              fontFamily: "'DM Sans', sans-serif",
              fontWeight: 500,
              fontSize: "0.8rem",
              color: "text.disabled",
              px: 1.5, py: 0,
              "&.Mui-selected": { color: "primary.main", fontWeight: 600 },
              "&:hover": { color: "text.secondary" },
            },
          }}
        >
          {tab.subtabs.map((sub) => (
            <Tab key={sub.id} label={sub.label} value={sub.id} disableRipple />
          ))}
        </Tabs>
      </Box>

      {/* Scrollable content */}
      <Box sx={{ flex: 1, overflowY: "auto", p: 3 }}>
        <Dashboard subTabId={subTabId} />
      </Box>
    </Box>
  );
}

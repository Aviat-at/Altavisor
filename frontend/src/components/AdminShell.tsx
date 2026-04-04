"use client";
import React, { useState } from "react";
import { Box } from "@mui/material";
import TopBar from "./TopBar";
import Sidebar from "./Sidebar";
import MainCanvas from "./MainCanvas";
import FooterBar from "./FooterBar";
import navConfig from "@/config/nav";

export default function AdminShell() {
  const [activeTabId, setActiveTabId] = useState(navConfig[0].id);
  const [activeSubTabId, setActiveSubTabId] = useState(navConfig[0].subtabs[0].id);

  const activeTab = navConfig.find((t) => t.id === activeTabId)!;

  const handleTabChange = (tabId: string) => {
    setActiveTabId(tabId);
    const tab = navConfig.find((t) => t.id === tabId)!;
    setActiveSubTabId(tab.subtabs[0].id);
  };

  return (
    <Box sx={{ display: "flex", flexDirection: "column", height: "100vh", bgcolor: "background.default", overflow: "hidden" }}>
      <TopBar />

      <Box sx={{ display: "flex", flex: 1, overflow: "hidden" }}>
        <Sidebar
          tabs={navConfig}
          activeTabId={activeTabId}
          onTabChange={handleTabChange}
        />
        <MainCanvas
          tab={activeTab}
          subTabId={activeSubTabId}
          onSubTabChange={setActiveSubTabId}
        />
      </Box>

      <FooterBar />
    </Box>
  );
}

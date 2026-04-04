"use client";
import React from "react";
import { Box, Tooltip } from "@mui/material";
import { NavTab } from "@/config/nav";

interface SidebarProps {
  tabs: NavTab[];
  activeTabId: string;
  onTabChange: (tabId: string) => void;
}

export default function Sidebar({ tabs, activeTabId, onTabChange }: SidebarProps) {
  return (
    <Box
      sx={{
        width: 72,
        height: "100%",
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        pt: 2,
        pb: 2,
        gap: 0.5,
        bgcolor: "background.default",
        borderRight: "1px solid",
        borderColor: "divider",
        flexShrink: 0,
      }}
    >
      {tabs.map((tab) => {
        const Icon = tab.icon;
        const isActive = tab.id === activeTabId;
        return (
          <Tooltip title={tab.label} placement="right" key={tab.id}>
            <Box
              onClick={() => onTabChange(tab.id)}
              sx={{
                width: 44,
                height: 44,
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                borderRadius: "8px",
                cursor: "pointer",
                position: "relative",
                bgcolor: isActive ? "action.selected" : "transparent",
                color: isActive ? "primary.main" : "text.disabled",
                transition: "all 0.15s ease",
                "&:hover": {
                  bgcolor: isActive ? "action.selected" : "action.hover",
                  color: isActive ? "primary.main" : "text.secondary",
                },
                // Active left border pill
                "&::before": isActive
                  ? {
                      content: '""',
                      position: "absolute",
                      left: -10,
                      top: "50%",
                      transform: "translateY(-50%)",
                      width: 3,
                      height: 18,
                      bgcolor: "primary.main",
                      borderRadius: "0 2px 2px 0",
                    }
                  : {},
              }}
            >
              <Icon sx={{ fontSize: 40 }} />
            </Box>
          </Tooltip>
        );
      })}
    </Box>
  );
}

"use client";
import React, { useState } from "react";
import {
  Box, Typography, IconButton, Avatar, Tooltip, Badge,
  Menu, MenuItem, Divider, CircularProgress,
} from "@mui/material";
import NotificationsNoneRoundedIcon from "@mui/icons-material/NotificationsNoneRounded";
import HelpOutlineRoundedIcon       from "@mui/icons-material/HelpOutlineRounded";
import SearchRoundedIcon            from "@mui/icons-material/SearchRounded";
import PersonOutlineRoundedIcon     from "@mui/icons-material/PersonOutlineRounded";
import LockResetRoundedIcon         from "@mui/icons-material/LockResetRounded";
import LogoutRoundedIcon            from "@mui/icons-material/LogoutRounded";
import DarkModeRoundedIcon          from "@mui/icons-material/DarkModeRounded";
import LightModeRoundedIcon         from "@mui/icons-material/LightModeRounded";
import { useRouter } from "next/navigation";
import { useColorMode } from "./ThemeRegistry";

export default function TopBar() {
  const router = useRouter();
  const { mode, toggleColorMode } = useColorMode();
  const [anchorEl, setAnchorEl]   = useState<null | HTMLElement>(null);
  const [loggingOut, setLoggingOut] = useState(false);

  const handleAvatarClick = (e: React.MouseEvent<HTMLElement>) => setAnchorEl(e.currentTarget);
  const handleClose = () => setAnchorEl(null);

  const handleLogout = async () => {
    setLoggingOut(true);
    const refresh = localStorage.getItem("refresh_token");
    try {
      await fetch("/api/auth/logout/", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${localStorage.getItem("access_token")}`,
        },
        body: JSON.stringify({ refresh }),
      });
    } catch {
      // best-effort — clear tokens regardless
    } finally {
      localStorage.removeItem("access_token");
      localStorage.removeItem("refresh_token");
      router.replace("/login");
    }
  };

  return (
    <Box
      sx={{
        height: 52,
        minHeight: 52,
        display: "flex",
        alignItems: "center",
        px: 2.5,
        bgcolor: "background.default",
        borderBottom: "1px solid",
        borderColor: "divider",
        zIndex: 100,
        gap: 2,
      }}
    >
      {/* Brand */}
      <Box sx={{ display: "flex", alignItems: "center", gap: 1.2 }}>
        <Box
          sx={{
            width: 26, height: 26,
            bgcolor: "#C8F04A",          // intentionally hardcoded — brand mark
            borderRadius: "5px",
            display: "flex", alignItems: "center", justifyContent: "center",
            flexShrink: 0,
          }}
        >
          <svg width="14" height="14" viewBox="0 0 16 16" fill="none">
            <path d="M8 2L14 13H2L8 2Z" fill="#0D0E10" />
          </svg>
        </Box>
        <Typography
          sx={{
            fontFamily: "'Syne', sans-serif",
            fontWeight: 800,
            fontSize: "1.25rem",
            letterSpacing: "-0.02em",
            color: "text.primary",
            userSelect: "none",
          }}
        >
          Altavisor
        </Typography>
      </Box>

      <Box sx={{ width: "1px", height: 20, bgcolor: "divider" }} />

      <Typography variant="caption" sx={{ color: "text.secondary", fontSize: "0.72rem" }}>
        Workspace:{" "}
        <span style={{ color: "#C8F04A", fontWeight: 600 }}>Production</span>
      </Typography>

      <Box sx={{ flex: 1 }} />

      {/* Theme toggle */}
      <Tooltip title={mode === "dark" ? "Switch to light mode" : "Switch to dark mode"}>
        <IconButton
          size="small"
          onClick={toggleColorMode}
          sx={{ color: "text.disabled", "&:hover": { color: "text.secondary" } }}
        >
          {mode === "dark"
            ? <LightModeRoundedIcon sx={{ fontSize: 17 }} />
            : <DarkModeRoundedIcon  sx={{ fontSize: 17 }} />}
        </IconButton>
      </Tooltip>

      <Tooltip title="Search">
        <IconButton size="small" sx={{ color: "text.disabled", "&:hover": { color: "text.secondary" } }}>
          <SearchRoundedIcon sx={{ fontSize: 17 }} />
        </IconButton>
      </Tooltip>

      <Tooltip title="Notifications">
        <IconButton size="small" sx={{ color: "text.disabled", "&:hover": { color: "text.secondary" } }}>
          <Badge
            badgeContent={3}
            sx={{ "& .MuiBadge-badge": { bgcolor: "primary.main", color: "primary.contrastText", fontSize: "0.55rem", fontWeight: 700, minWidth: 14, height: 14 } }}
          >
            <NotificationsNoneRoundedIcon sx={{ fontSize: 17 }} />
          </Badge>
        </IconButton>
      </Tooltip>

      <Tooltip title="Help">
        <IconButton size="small" sx={{ color: "text.disabled", "&:hover": { color: "text.secondary" } }}>
          <HelpOutlineRoundedIcon sx={{ fontSize: 17 }} />
        </IconButton>
      </Tooltip>

      {/* User avatar */}
      <Tooltip title="Account">
        <Avatar
          onClick={handleAvatarClick}
          sx={{
            width: 28, height: 28,
            bgcolor: "action.disabledBackground",
            color: "primary.main",
            fontSize: "0.68rem",
            fontWeight: 700,
            fontFamily: "'Syne', sans-serif",
            cursor: "pointer",
            border: "1px solid",
            borderColor: "action.selected",
            transition: "border-color 0.15s",
            "&:hover": { borderColor: "primary.main" },
          }}
        >
          AV
        </Avatar>
      </Tooltip>

      {/* Dropdown */}
      <Menu
        anchorEl={anchorEl}
        open={Boolean(anchorEl)}
        onClose={handleClose}
        transformOrigin={{ horizontal: "right", vertical: "top" }}
        anchorOrigin={{ horizontal: "right", vertical: "bottom" }}
        slotProps={{ paper: { sx: { mt: 0.75, minWidth: 200, borderRadius: "8px" } } }}
      >
        <Box sx={{ px: 2, py: 1.5 }}>
          <Typography variant="body2" sx={{ color: "text.primary", fontWeight: 600, fontSize: "0.8rem" }}>
            Admin User
          </Typography>
          <Typography variant="caption" sx={{ color: "text.secondary" }}>
            admin@altavisor.io
          </Typography>
        </Box>

        <Divider />

        <MenuItem onClick={handleClose} sx={{ py: 1, px: 2, gap: 1.25, fontSize: "0.8rem", color: "text.secondary", "&:hover": { color: "text.primary" } }}>
          <PersonOutlineRoundedIcon sx={{ fontSize: 16 }} />
          Profile
        </MenuItem>

        <MenuItem onClick={handleClose} sx={{ py: 1, px: 2, gap: 1.25, fontSize: "0.8rem", color: "text.secondary", "&:hover": { color: "text.primary" } }}>
          <LockResetRoundedIcon sx={{ fontSize: 16 }} />
          Change password
        </MenuItem>

        <Divider />

        <MenuItem
          onClick={handleLogout}
          disabled={loggingOut}
          sx={{ py: 1, px: 2, gap: 1.25, fontSize: "0.8rem", color: "error.main", "&:hover": { bgcolor: "rgba(240,74,74,0.06)", color: "error.light" }, "&.Mui-disabled": { opacity: 0.5 } }}
        >
          {loggingOut
            ? <CircularProgress size={14} sx={{ color: "error.main" }} />
            : <LogoutRoundedIcon sx={{ fontSize: 16 }} />}
          {loggingOut ? "Signing out…" : "Sign out"}
        </MenuItem>
      </Menu>
    </Box>
  );
}

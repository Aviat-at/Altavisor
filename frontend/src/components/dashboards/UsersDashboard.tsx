"use client";
import React from "react";
import { Box, Typography, Paper, Avatar, Chip, Button, TextField, InputAdornment } from "@mui/material";
import SearchRoundedIcon from "@mui/icons-material/SearchRounded";
import AddRoundedIcon    from "@mui/icons-material/AddRounded";

const users = [
  { name: "Alex Chen",     email: "alex@altavisor.io",   role: "Admin",     status: "Active",   avatar: "AC" },
  { name: "Maria Santos",  email: "maria@altavisor.io",  role: "Developer", status: "Active",   avatar: "MS" },
  { name: "Jordan Kim",    email: "jordan@altavisor.io", role: "Viewer",    status: "Inactive", avatar: "JK" },
  { name: "Sam Rivera",    email: "sam@altavisor.io",    role: "Developer", status: "Active",   avatar: "SR" },
];

function AccountsPanel() {
  return (
    <Box>
      <Box sx={{ display: "flex", gap: 1.5, mb: 2.5, alignItems: "center" }}>
        <TextField
          placeholder="Search users..."
          size="small"
          InputProps={{ startAdornment: <InputAdornment position="start"><SearchRoundedIcon sx={{ fontSize: 16, color: "text.secondary" }} /></InputAdornment> }}
          sx={{ flex: 1, maxWidth: 300 }}
        />
        <Button variant="contained" startIcon={<AddRoundedIcon />} size="small">
          Invite User
        </Button>
      </Box>

      <Paper sx={{ borderRadius: 2, overflow: "hidden" }}>
        <Box sx={{ px: 2.5, py: 1.2, display: "grid", gridTemplateColumns: "2fr 1.5fr 1fr 1fr", borderBottom: "1px solid", borderColor: "divider" }}>
          {["Name", "Email", "Role", "Status"].map((h) => (
            <Typography key={h} variant="caption" sx={{ color: "text.secondary", fontWeight: 600, fontSize: "0.68rem", textTransform: "uppercase", letterSpacing: "0.07em" }}>
              {h}
            </Typography>
          ))}
        </Box>

        {users.map((u, i) => (
          <Box key={i} sx={{ px: 2.5, py: 1.5, display: "grid", gridTemplateColumns: "2fr 1.5fr 1fr 1fr", alignItems: "center", borderBottom: i < users.length - 1 ? "1px solid" : "none", borderColor: "divider", "&:hover": { bgcolor: "action.hover" } }}>
            <Box sx={{ display: "flex", alignItems: "center", gap: 1.2 }}>
              <Avatar sx={{ width: 28, height: 28, fontSize: "0.65rem", fontWeight: 700, bgcolor: "action.selected", color: "primary.main", fontFamily: "'Syne', sans-serif" }}>
                {u.avatar}
              </Avatar>
              <Typography variant="body2" sx={{ fontWeight: 500, fontSize: "0.82rem" }}>{u.name}</Typography>
            </Box>
            <Typography variant="caption" sx={{ color: "text.secondary" }}>{u.email}</Typography>
            <Chip label={u.role} size="small" sx={{ fontSize: "0.68rem", height: 20, bgcolor: "action.disabledBackground", color: "text.secondary" }} />
            <Chip
              label={u.status}
              size="small"
              sx={{
                fontSize: "0.68rem",
                height: 20,
                bgcolor: u.status === "Active" ? "action.selected" : "action.disabledBackground",
                color: u.status === "Active" ? "primary.main" : "text.secondary",
              }}
            />
          </Box>
        ))}
      </Paper>
    </Box>
  );
}

function GenericPanel({ title }: { title: string }) {
  return (
    <Paper sx={{ p: 3, borderRadius: 2 }}>
      <Typography variant="subtitle2" sx={{ fontFamily: "'Syne', sans-serif", fontWeight: 600, mb: 1 }}>{title}</Typography>
      <Typography variant="body2" sx={{ color: "text.secondary", fontSize: "0.8rem" }}>
        Configure {title.toLowerCase()} settings here. This section is ready to be populated with your specific requirements.
      </Typography>
    </Paper>
  );
}

export default function UsersDashboard({ subTabId }: { subTabId: string }) {
  if (subTabId === "accounts") return <AccountsPanel />;
  if (subTabId === "roles")    return <GenericPanel title="Roles & Permissions" />;
  return <GenericPanel title="Invites" />;
}

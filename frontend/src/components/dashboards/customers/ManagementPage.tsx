"use client";
import React, { useState } from "react";
import {
  Box, Typography, Paper, TextField, InputAdornment,
  Button, Chip, MenuItem, Select, FormControl, Avatar,
} from "@mui/material";
import SearchRoundedIcon   from "@mui/icons-material/SearchRounded";
import FilterListRoundedIcon from "@mui/icons-material/FilterListRounded";
import PersonAddRoundedIcon  from "@mui/icons-material/PersonAddRounded";

const allCustomers = [
  { id: "C-001", name: "Sarah Kim",      email: "sarah@example.com",   plan: "Pro",        status: "Active",   joined: "Jan 12, 2026", spend: "$1,240" },
  { id: "C-002", name: "James Okafor",   email: "james@example.com",   plan: "Starter",    status: "Active",   joined: "Jan 18, 2026", spend: "$180"   },
  { id: "C-003", name: "Priya Nair",     email: "priya@example.com",   plan: "Enterprise", status: "Active",   joined: "Feb 2, 2026",  spend: "$4,800" },
  { id: "C-004", name: "Tom Walsh",      email: "tom@example.com",     plan: "Starter",    status: "Inactive", joined: "Feb 5, 2026",  spend: "$90"    },
  { id: "C-005", name: "Elena Popescu",  email: "elena@example.com",   plan: "Pro",        status: "Active",   joined: "Feb 14, 2026", spend: "$960"   },
  { id: "C-006", name: "Marcus Lee",     email: "marcus@example.com",  plan: "Enterprise", status: "Active",   joined: "Feb 20, 2026", spend: "$5,200" },
  { id: "C-007", name: "Amara Diallo",   email: "amara@example.com",   plan: "Pro",        status: "Active",   joined: "Mar 1, 2026",  spend: "$720"   },
  { id: "C-008", name: "Raj Patel",      email: "raj@example.com",     plan: "Starter",    status: "Churned",  joined: "Mar 3, 2026",  spend: "$60"    },
];

const planColor = (p: string) =>
  p === "Enterprise" ? { bg: "rgba(74,160,240,0.1)",  color: "#4AA0F0" }
  : p === "Pro"      ? { bg: "rgba(200,240,74,0.1)",  color: "#C8F04A" }
  :                    { bg: "rgba(255,255,255,0.05)", color: "#6B7080" };

const statusColor = (s: string) =>
  s === "Active"   ? { bg: "rgba(200,240,74,0.1)",  color: "#C8F04A" }
  : s === "Inactive" ? { bg: "rgba(255,255,255,0.05)", color: "#6B7080" }
  :                    { bg: "rgba(240,74,74,0.1)",   color: "#F04A4A" };

export default function ManagementPage() {
  const [search, setSearch]   = useState("");
  const [planFilter, setPlan] = useState("All");

  const filtered = allCustomers.filter((c) => {
    const matchSearch = !search || c.name.toLowerCase().includes(search.toLowerCase()) || c.email.includes(search);
    const matchPlan   = planFilter === "All" || c.plan === planFilter;
    return matchSearch && matchPlan;
  });

  return (
    <Box>
      {/* Toolbar */}
      <Box sx={{ display: "flex", gap: 1.5, mb: 2, alignItems: "center", flexWrap: "wrap" }}>
        <TextField
          placeholder="Search customers..."
          size="small"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          InputProps={{ startAdornment: <InputAdornment position="start"><SearchRoundedIcon sx={{ fontSize: 15, color: "text.secondary" }} /></InputAdornment> }}
          sx={{ width: 260 }}
        />
        <FormControl size="small">
          <Select value={planFilter} onChange={(e) => setPlan(e.target.value)}
            sx={{ fontSize: "0.8rem", bgcolor: "rgba(255,255,255,0.03)", minWidth: 130 }}>
            <MenuItem value="All">All plans</MenuItem>
            <MenuItem value="Enterprise">Enterprise</MenuItem>
            <MenuItem value="Pro">Pro</MenuItem>
            <MenuItem value="Starter">Starter</MenuItem>
          </Select>
        </FormControl>
        <Box sx={{ flex: 1 }} />
        <Button size="small" variant="contained" startIcon={<PersonAddRoundedIcon sx={{ fontSize: "14px !important" }} />}
          sx={{ bgcolor: "#C8F04A", color: "#0D0E10", fontWeight: 700, fontSize: "0.78rem", "&:hover": { bgcolor: "#D4F55A" } }}>
          Add Customer
        </Button>
      </Box>

      {/* Table */}
      <Paper sx={{ bgcolor: "#13151A", border: "1px solid", borderColor: "divider", borderRadius: 2, overflow: "hidden" }}>
        {/* Header */}
        <Box sx={{ px: 2.5, py: 1.2, display: "grid", gridTemplateColumns: "50px 2fr 2fr 110px 100px 120px 90px", borderBottom: "1px solid", borderColor: "divider" }}>
          {["ID", "Name", "Email", "Plan", "Status", "Joined", "Spend"].map((h) => (
            <Typography key={h} variant="caption" sx={{ color: "text.secondary", fontWeight: 600, fontSize: "0.67rem", textTransform: "uppercase", letterSpacing: "0.07em" }}>
              {h}
            </Typography>
          ))}
        </Box>

        {/* Rows */}
        {filtered.length === 0 ? (
          <Box sx={{ py: 4, textAlign: "center" }}>
            <Typography variant="body2" sx={{ color: "text.secondary" }}>No customers match your filters.</Typography>
          </Box>
        ) : filtered.map((c, i) => (
          <Box key={c.id} sx={{
            px: 2.5, py: 1.4,
            display: "grid", gridTemplateColumns: "50px 2fr 2fr 110px 100px 120px 90px",
            alignItems: "center",
            borderBottom: i < filtered.length - 1 ? "1px solid" : "none",
            borderColor: "divider",
            "&:hover": { bgcolor: "rgba(255,255,255,0.02)", cursor: "pointer" },
          }}>
            <Typography variant="caption" sx={{ color: "text.secondary", fontFamily: "monospace", fontSize: "0.7rem" }}>{c.id}</Typography>

            <Box sx={{ display: "flex", alignItems: "center", gap: 1 }}>
              <Avatar sx={{ width: 26, height: 26, fontSize: "0.6rem", fontWeight: 700, bgcolor: "rgba(200,240,74,0.12)", color: "#C8F04A", fontFamily: "'Syne', sans-serif" }}>
                {c.name.split(" ").map(n => n[0]).join("")}
              </Avatar>
              <Typography variant="body2" sx={{ fontWeight: 500, fontSize: "0.8rem" }}>{c.name}</Typography>
            </Box>

            <Typography variant="caption" sx={{ color: "text.secondary", fontSize: "0.78rem" }}>{c.email}</Typography>

            <Chip label={c.plan} size="small" sx={{ fontSize: "0.67rem", height: 18, width: "fit-content", bgcolor: planColor(c.plan).bg, color: planColor(c.plan).color, fontWeight: 600 }} />

            <Chip label={c.status} size="small" sx={{ fontSize: "0.67rem", height: 18, width: "fit-content", bgcolor: statusColor(c.status).bg, color: statusColor(c.status).color, fontWeight: 600 }} />

            <Typography variant="caption" sx={{ color: "text.secondary" }}>{c.joined}</Typography>

            <Typography variant="caption" sx={{ color: "text.primary", fontWeight: 600, fontSize: "0.8rem" }}>{c.spend}</Typography>
          </Box>
        ))}
      </Paper>

      <Box sx={{ mt: 1.5, display: "flex", justifyContent: "space-between", alignItems: "center" }}>
        <Typography variant="caption" sx={{ color: "text.secondary" }}>
          Showing {filtered.length} of {allCustomers.length} customers
        </Typography>
      </Box>
    </Box>
  );
}

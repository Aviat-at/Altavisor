"use client";
import React, { useState } from "react";
import {
  Box, Typography, Paper, Grid, Chip, Button, Divider,
} from "@mui/material";
import EmailRoundedIcon        from "@mui/icons-material/EmailRounded";
import EditRoundedIcon         from "@mui/icons-material/EditRounded";
import HistoryRoundedIcon      from "@mui/icons-material/HistoryRounded";
import CheckCircleOutlineRoundedIcon from "@mui/icons-material/CheckCircleOutlineRounded";

// Sample profile — in a real app this would come from props or an API call
const profile = {
  id:        "C-003",
  name:      "Priya Nair",
  email:     "priya@example.com",
  phone:     "+1 (415) 555-0198",
  company:   "NexaCloud Inc.",
  plan:      "Enterprise",
  status:    "Active",
  joined:    "Feb 2, 2026",
  totalSpend:"$4,800",
  location:  "San Francisco, CA",
  notes:     "Key account. Renewal due April 2027. Interested in SSO add-on.",
};

const activity = [
  { action: "Upgraded plan from Pro to Enterprise", time: "Feb 2, 2026",  type: "plan"    },
  { action: "Invoice #1042 paid — $1,200",          time: "Mar 1, 2026",  type: "billing" },
  { action: "Opened email campaign: Q1 Update",     time: "Mar 10, 2026", type: "email"   },
  { action: "Support ticket #88 resolved",          time: "Mar 14, 2026", type: "support" },
  { action: "Login from new device (Chrome/Mac)",   time: "Mar 20, 2026", type: "auth"    },
];

const typeColor: any = {
  plan:    { bg: "rgba(200,240,74,0.08)",  color: "#C8F04A" },
  billing: { bg: "rgba(74,160,240,0.08)",  color: "#4AA0F0" },
  email:   { bg: "rgba(74,240,200,0.08)",  color: "#4AF0C8" },
  support: { bg: "rgba(240,184,74,0.08)",  color: "#F0B84A" },
  auth:    { bg: "rgba(255,255,255,0.05)", color: "#6B7080" },
};

export default function ProfilePage() {
  const [selectedId, setSelectedId] = useState("C-003");

  return (
    <Box>
      {/* Note: in a real app, you'd pick a customer from the Management page.
          For now we show a sample profile. */}
      <Grid container spacing={2.5}>

        {/* Left — profile card */}
        <Grid item xs={12} md={4}>
          <Paper sx={{ bgcolor: "#13151A", border: "1px solid", borderColor: "divider", borderRadius: 2, overflow: "hidden" }}>
            {/* Header */}
            <Box sx={{ p: 2.5, borderBottom: "1px solid", borderColor: "divider", display: "flex", alignItems: "center", gap: 1.5 }}>
              <Box sx={{
                width: 44, height: 44, borderRadius: "50%",
                bgcolor: "rgba(74,160,240,0.12)",
                display: "flex", alignItems: "center", justifyContent: "center", flexShrink: 0,
              }}>
                <Typography sx={{ fontSize: "0.85rem", fontWeight: 700, color: "#4AA0F0", fontFamily: "'Syne', sans-serif" }}>
                  {profile.name.split(" ").map(n => n[0]).join("")}
                </Typography>
              </Box>
              <Box sx={{ flex: 1 }}>
                <Typography variant="subtitle2" sx={{ fontFamily: "'Syne', sans-serif", fontWeight: 700 }}>{profile.name}</Typography>
                <Typography variant="caption" sx={{ color: "text.secondary", fontSize: "0.72rem" }}>{profile.company}</Typography>
              </Box>
              <Chip label={profile.status} size="small" sx={{ fontSize: "0.67rem", height: 18, bgcolor: "rgba(200,240,74,0.1)", color: "#C8F04A", fontWeight: 600 }} />
            </Box>

            {/* Details */}
            <Box sx={{ p: 2.5 }}>
              {[
                { label: "Customer ID", value: profile.id },
                { label: "Email",       value: profile.email },
                { label: "Phone",       value: profile.phone },
                { label: "Location",    value: profile.location },
                { label: "Plan",        value: profile.plan },
                { label: "Joined",      value: profile.joined },
                { label: "Total Spend", value: profile.totalSpend },
              ].map((row, i, arr) => (
                <Box key={row.label} sx={{ display: "flex", justifyContent: "space-between", py: 1, borderBottom: i < arr.length - 1 ? "1px solid" : "none", borderColor: "divider" }}>
                  <Typography variant="caption" sx={{ color: "text.secondary", fontSize: "0.75rem" }}>{row.label}</Typography>
                  <Typography variant="caption" sx={{ fontWeight: 500, fontSize: "0.75rem", textAlign: "right", maxWidth: 160 }}>{row.value}</Typography>
                </Box>
              ))}

              {/* Notes */}
              <Box sx={{ mt: 2 }}>
                <Typography variant="caption" sx={{ color: "text.secondary", fontWeight: 600, fontSize: "0.68rem", textTransform: "uppercase", letterSpacing: "0.07em" }}>
                  Notes
                </Typography>
                <Typography variant="body2" sx={{ mt: 0.8, fontSize: "0.78rem", color: "text.secondary", lineHeight: 1.6 }}>
                  {profile.notes}
                </Typography>
              </Box>

              {/* Actions */}
              <Box sx={{ display: "flex", gap: 1, mt: 2.5 }}>
                <Button size="small" variant="outlined" startIcon={<EmailRoundedIcon sx={{ fontSize: "13px !important" }} />}
                  sx={{ flex: 1, borderColor: "divider", color: "text.secondary", fontSize: "0.75rem" }}>
                  Email
                </Button>
                <Button size="small" variant="outlined" startIcon={<EditRoundedIcon sx={{ fontSize: "13px !important" }} />}
                  sx={{ flex: 1, borderColor: "divider", color: "text.secondary", fontSize: "0.75rem" }}>
                  Edit
                </Button>
              </Box>
            </Box>
          </Paper>
        </Grid>

        {/* Right — activity timeline */}
        <Grid item xs={12} md={8}>
          <Paper sx={{ bgcolor: "#13151A", border: "1px solid", borderColor: "divider", borderRadius: 2 }}>
            <Box sx={{ px: 2.5, py: 1.8, borderBottom: "1px solid", borderColor: "divider", display: "flex", alignItems: "center", gap: 1 }}>
              <HistoryRoundedIcon sx={{ fontSize: 16, color: "text.secondary" }} />
              <Typography variant="subtitle2" sx={{ fontFamily: "'Syne', sans-serif", fontWeight: 600 }}>
                Activity Timeline
              </Typography>
            </Box>
            <Box sx={{ p: 2.5 }}>
              {activity.map((a, i) => (
                <Box key={i} sx={{ display: "flex", gap: 2, mb: i < activity.length - 1 ? 2 : 0 }}>
                  {/* Timeline dot + line */}
                  <Box sx={{ display: "flex", flexDirection: "column", alignItems: "center", flexShrink: 0 }}>
                    <Box sx={{ width: 8, height: 8, borderRadius: "50%", bgcolor: typeColor[a.type].color, mt: 0.4 }} />
                    {i < activity.length - 1 && (
                      <Box sx={{ width: 1, flex: 1, bgcolor: "divider", mt: 0.5 }} />
                    )}
                  </Box>
                  {/* Content */}
                  <Box sx={{ flex: 1, pb: i < activity.length - 1 ? 1.5 : 0 }}>
                    <Box sx={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", gap: 1 }}>
                      <Typography variant="body2" sx={{ fontSize: "0.8rem", lineHeight: 1.4 }}>{a.action}</Typography>
                      <Chip label={a.type} size="small" sx={{ fontSize: "0.63rem", height: 16, flexShrink: 0, bgcolor: typeColor[a.type].bg, color: typeColor[a.type].color, fontWeight: 600, textTransform: "capitalize" }} />
                    </Box>
                    <Typography variant="caption" sx={{ color: "text.secondary", fontSize: "0.7rem" }}>{a.time}</Typography>
                  </Box>
                </Box>
              ))}
            </Box>
          </Paper>
        </Grid>

      </Grid>
    </Box>
  );
}

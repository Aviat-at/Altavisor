"use client";
import React from "react";
import { Box, Typography, Paper, Grid, Chip, LinearProgress } from "@mui/material";
import TrendingUpRoundedIcon from "@mui/icons-material/TrendingUpRounded";
import TrendingDownRoundedIcon from "@mui/icons-material/TrendingDownRounded";
import CheckCircleOutlineRoundedIcon from "@mui/icons-material/CheckCircleOutlineRounded";
import WarningAmberRoundedIcon from "@mui/icons-material/WarningAmberRounded";

function StatCard({ label, value, delta, positive }: any) {
  return (
    <Paper
      sx={{
        p: 2.5,
        bgcolor: "#13151A",
        border: "1px solid",
        borderColor: "divider",
        borderRadius: 2,
      }}
    >
      <Typography variant="caption" sx={{ color: "text.secondary", fontWeight: 500, fontSize: "0.7rem", textTransform: "uppercase", letterSpacing: "0.06em" }}>
        {label}
      </Typography>
      <Typography sx={{ fontSize: "1.8rem", fontWeight: 700, fontFamily: "'Syne', sans-serif", color: "text.primary", mt: 0.5, lineHeight: 1.1 }}>
        {value}
      </Typography>
      <Box sx={{ display: "flex", alignItems: "center", gap: 0.5, mt: 0.8 }}>
        {positive ? (
          <TrendingUpRoundedIcon sx={{ fontSize: 14, color: "#C8F04A" }} />
        ) : (
          <TrendingDownRoundedIcon sx={{ fontSize: 14, color: "#F04A4A" }} />
        )}
        <Typography variant="caption" sx={{ color: positive ? "#C8F04A" : "#F04A4A", fontWeight: 600, fontSize: "0.72rem" }}>
          {delta}
        </Typography>
        <Typography variant="caption" sx={{ color: "text.secondary", fontSize: "0.7rem" }}>
          vs last week
        </Typography>
      </Box>
    </Paper>
  );
}

export default function OverviewDashboard({ subTabId }: { subTabId: string }) {
  if (subTabId === "summary") {
    return (
      <Box>
        <Grid container spacing={2} sx={{ mb: 3 }}>
          <Grid item xs={12} sm={6} md={3}>
            <StatCard label="Active Users" value="2,841" delta="+12.4%" positive />
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <StatCard label="API Requests" value="98.2K" delta="+8.1%" positive />
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <StatCard label="Error Rate" value="0.03%" delta="-0.01%" positive />
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <StatCard label="Avg Response" value="142ms" delta="+5ms" positive={false} />
          </Grid>
        </Grid>

        {/* Recent Activity */}
        <Paper sx={{ p: 2.5, bgcolor: "#13151A", border: "1px solid", borderColor: "divider", borderRadius: 2 }}>
          <Typography variant="subtitle2" sx={{ fontFamily: "'Syne', sans-serif", fontWeight: 600, mb: 2 }}>
            Recent Activity
          </Typography>
          {[
            { msg: "Deployment completed successfully", time: "2 min ago", ok: true },
            { msg: "New user onboarding workflow triggered", time: "15 min ago", ok: true },
            { msg: "Rate limit warning — API endpoint /v2/data", time: "1 hr ago", ok: false },
            { msg: "Backup snapshot created", time: "3 hr ago", ok: true },
          ].map((item, i) => (
            <Box
              key={i}
              sx={{
                display: "flex",
                alignItems: "center",
                gap: 1.5,
                py: 1,
                borderBottom: i < 3 ? "1px solid" : "none",
                borderColor: "divider",
              }}
            >
              {item.ok ? (
                <CheckCircleOutlineRoundedIcon sx={{ fontSize: 15, color: "#C8F04A", flexShrink: 0 }} />
              ) : (
                <WarningAmberRoundedIcon sx={{ fontSize: 15, color: "#F0B84A", flexShrink: 0 }} />
              )}
              <Typography variant="body2" sx={{ flex: 1, fontSize: "0.8rem" }}>
                {item.msg}
              </Typography>
              <Typography variant="caption" sx={{ color: "text.secondary", flexShrink: 0 }}>
                {item.time}
              </Typography>
            </Box>
          ))}
        </Paper>
      </Box>
    );
  }

  if (subTabId === "health") {
    return (
      <Box>
        <Paper sx={{ p: 2.5, bgcolor: "#13151A", border: "1px solid", borderColor: "divider", borderRadius: 2 }}>
          <Typography variant="subtitle2" sx={{ fontFamily: "'Syne', sans-serif", fontWeight: 600, mb: 2.5 }}>
            System Health
          </Typography>
          {[
            { label: "CPU Usage", value: 38, color: "#C8F04A" },
            { label: "Memory", value: 61, color: "#4AF0C8" },
            { label: "Disk I/O", value: 22, color: "#C8F04A" },
            { label: "Network", value: 75, color: "#F0B84A" },
          ].map((item) => (
            <Box key={item.label} sx={{ mb: 2 }}>
              <Box sx={{ display: "flex", justifyContent: "space-between", mb: 0.5 }}>
                <Typography variant="caption" sx={{ color: "text.secondary", fontWeight: 500 }}>{item.label}</Typography>
                <Typography variant="caption" sx={{ color: item.color, fontWeight: 700 }}>{item.value}%</Typography>
              </Box>
              <LinearProgress
                variant="determinate"
                value={item.value}
                sx={{
                  height: 5,
                  borderRadius: 3,
                  bgcolor: "rgba(255,255,255,0.06)",
                  "& .MuiLinearProgress-bar": { bgcolor: item.color, borderRadius: 3 },
                }}
              />
            </Box>
          ))}
        </Paper>
      </Box>
    );
  }

  return (
    <Box>
      <Typography variant="body2" sx={{ color: "text.secondary" }}>
        Select a sub-section to view content.
      </Typography>
    </Box>
  );
}

"use client";
import React, { useState } from "react";
import {
  Box, Typography, Paper, Grid, Button, Chip, LinearProgress,
} from "@mui/material";
import { useTheme } from "@mui/material/styles";
import PersonAddRoundedIcon    from "@mui/icons-material/PersonAddRounded";
import FileDownloadRoundedIcon from "@mui/icons-material/FileDownloadRounded";
import EmailRoundedIcon        from "@mui/icons-material/EmailRounded";
import TrendingUpRoundedIcon   from "@mui/icons-material/TrendingUpRounded";
import TrendingDownRoundedIcon from "@mui/icons-material/TrendingDownRounded";

const kpis = [
  { label: "Total Customers", value: "1,240", delta: "+8.2%",  positive: true  },
  { label: "Active",          value: "983",   delta: "+5.1%",  positive: true  },
  { label: "New This Month",  value: "42",    delta: "+12.0%", positive: true  },
  { label: "Churned",         value: "9",     delta: "+3",     positive: false },
];

function Sparkline({ data, color }: { data: number[]; color: string }) {
  const max = Math.max(...data), min = Math.min(...data);
  const w = 100, h = 32, p = 2;
  const pts = data.map((v, i) => {
    const x = p + (i / (data.length - 1)) * (w - p * 2);
    const y = h - p - ((v - min) / ((max - min) || 1)) * (h - p * 2);
    return `${x},${y}`;
  }).join(" ");
  return (
    <svg width={w} height={h} viewBox={`0 0 ${w} ${h}`} fill="none">
      <polyline points={pts} stroke={color} strokeWidth="1.8" strokeLinejoin="round" strokeLinecap="round" />
    </svg>
  );
}

const months   = ["Oct", "Nov", "Dec", "Jan", "Feb", "Mar"];
const newCusts = [28, 34, 22, 38, 30, 42];
const churned  = [5,  8,  4,  7,  6,  9];

function BarChart({ primaryColor, errorColor, textColor, lineColor }: { primaryColor: string; errorColor: string; textColor: string; lineColor: string }) {
  const maxVal = Math.max(...newCusts);
  const W = 340, H = 120, barW = 28, gap = 26, startX = 28;
  return (
    <svg width="100%" viewBox={`0 0 ${W} ${H + 30}`} fill="none">
      {months.map((m, i) => {
        const x    = startX + i * (barW + gap);
        const newH = (newCusts[i] / maxVal) * H;
        const chH  = (churned[i]  / maxVal) * H;
        return (
          <g key={m}>
            <rect x={x}                      y={H - newH} width={barW * 0.55} height={newH} fill={primaryColor} opacity={0.85} rx="2" />
            <rect x={x + barW * 0.55 + 2}   y={H - chH}  width={barW * 0.35} height={chH}  fill={errorColor}   opacity={0.65} rx="2" />
            <text x={x + barW * 0.45} y={H + 18} textAnchor="middle" fontSize="9" fill={textColor}>{m}</text>
          </g>
        );
      })}
      <line x1={20} y1={0} x2={20} y2={H} stroke={lineColor} strokeWidth="0.5" />
    </svg>
  );
}

const recentCustomers = [
  { name: "Sarah Kim",     email: "sarah@example.com",  plan: "Pro",       status: "Active",   time: "2 min ago"  },
  { name: "James Okafor",  email: "james@example.com",  plan: "Starter",   status: "Active",   time: "18 min ago" },
  { name: "Priya Nair",    email: "priya@example.com",  plan: "Enterprise",status: "Active",   time: "1 hr ago"   },
  { name: "Tom Walsh",     email: "tom@example.com",    plan: "Starter",   status: "Inactive", time: "3 hr ago"   },
  { name: "Elena Popescu", email: "elena@example.com",  plan: "Pro",       status: "Active",   time: "5 hr ago"   },
];

export default function DashboardPage() {
  const theme = useTheme();

  const planColor = (p: string) =>
    p === "Enterprise" ? { bg: "rgba(74,160,240,0.10)",  color: theme.palette.info.main    }
    : p === "Pro"      ? { bg: "action.selected",         color: theme.palette.primary.main }
    :                    { bg: "action.disabledBackground",color: theme.palette.text.secondary };

  return (
    <Box>
      {/* KPI row */}
      <Grid container spacing={2} sx={{ mb: 2.5 }}>
        {kpis.map((k, i) => (
          <Grid item xs={12} sm={6} md={3} key={i}>
            <Paper sx={{ p: 2.5, borderRadius: 2 }}>
              <Typography variant="caption" sx={{ color: "text.secondary", fontWeight: 600, fontSize: "0.68rem", textTransform: "uppercase", letterSpacing: "0.07em" }}>
                {k.label}
              </Typography>
              <Box sx={{ display: "flex", justifyContent: "space-between", alignItems: "flex-end", mt: 0.8 }}>
                <Typography sx={{ fontSize: "1.7rem", fontWeight: 800, fontFamily: "'Syne', sans-serif", lineHeight: 1.1 }}>
                  {k.value}
                </Typography>
                <Sparkline
                  color={k.positive ? theme.palette.primary.main : theme.palette.error.main}
                  data={k.positive ? [20, 28, 24, 32, 30, 38, 36, 42] : [3, 5, 4, 7, 5, 6, 8, 9]}
                />
              </Box>
              <Box sx={{ display: "flex", alignItems: "center", gap: 0.5, mt: 0.5 }}>
                {k.positive
                  ? <TrendingUpRoundedIcon   sx={{ fontSize: 12, color: "primary.main" }} />
                  : <TrendingDownRoundedIcon sx={{ fontSize: 12, color: "error.main"   }} />}
                <Typography variant="caption" sx={{ color: k.positive ? "primary.main" : "error.main", fontWeight: 700, fontSize: "0.7rem" }}>
                  {k.delta}
                </Typography>
                <Typography variant="caption" sx={{ color: "text.secondary", fontSize: "0.68rem" }}>vs last month</Typography>
              </Box>
            </Paper>
          </Grid>
        ))}
      </Grid>

      <Grid container spacing={2.5} sx={{ mb: 2.5 }}>

        {/* Bar chart */}
        <Grid item xs={12} md={5}>
          <Paper sx={{ p: 2.5, borderRadius: 2, height: "100%" }}>
            <Box sx={{ display: "flex", justifyContent: "space-between", alignItems: "center", mb: 2 }}>
              <Typography variant="subtitle2" sx={{ fontFamily: "'Syne', sans-serif", fontWeight: 600 }}>
                Growth vs Churn
              </Typography>
              <Box sx={{ display: "flex", gap: 1.5 }}>
                <Box sx={{ display: "flex", alignItems: "center", gap: 0.5 }}>
                  <Box sx={{ width: 8, height: 8, borderRadius: 1, bgcolor: "primary.main" }} />
                  <Typography variant="caption" sx={{ color: "text.secondary", fontSize: "0.68rem" }}>New</Typography>
                </Box>
                <Box sx={{ display: "flex", alignItems: "center", gap: 0.5 }}>
                  <Box sx={{ width: 8, height: 8, borderRadius: 1, bgcolor: "error.main" }} />
                  <Typography variant="caption" sx={{ color: "text.secondary", fontSize: "0.68rem" }}>Churned</Typography>
                </Box>
              </Box>
            </Box>

            <BarChart
              primaryColor={theme.palette.primary.main}
              errorColor={theme.palette.error.main}
              textColor={theme.palette.text.secondary}
              lineColor={theme.palette.divider}
            />

            {/* Plan distribution */}
            <Box sx={{ mt: 2 }}>
              <Typography variant="caption" sx={{ color: "text.secondary", fontSize: "0.68rem", fontWeight: 600, textTransform: "uppercase", letterSpacing: "0.07em" }}>
                Plan Distribution
              </Typography>
              {[
                { label: "Enterprise", value: 18, color: theme.palette.info.main    },
                { label: "Pro",        value: 45, color: theme.palette.primary.main },
                { label: "Starter",    value: 37, color: theme.palette.text.secondary },
              ].map((p) => (
                <Box key={p.label} sx={{ mt: 1.2 }}>
                  <Box sx={{ display: "flex", justifyContent: "space-between", mb: 0.4 }}>
                    <Typography variant="caption" sx={{ color: "text.secondary", fontSize: "0.72rem" }}>{p.label}</Typography>
                    <Typography variant="caption" sx={{ color: p.color, fontWeight: 700, fontSize: "0.72rem" }}>{p.value}%</Typography>
                  </Box>
                  <LinearProgress variant="determinate" value={p.value} sx={{ height: 4, borderRadius: 2, "& .MuiLinearProgress-bar": { bgcolor: p.color, borderRadius: 2 } }} />
                </Box>
              ))}
            </Box>
          </Paper>
        </Grid>

        {/* Quick actions + recent customers */}
        <Grid item xs={12} md={7}>
          <Box sx={{ display: "flex", flexDirection: "column", gap: 2.5, height: "100%" }}>

            <Paper sx={{ p: 2, borderRadius: 2 }}>
              <Typography variant="caption" sx={{ color: "text.secondary", fontWeight: 600, fontSize: "0.68rem", textTransform: "uppercase", letterSpacing: "0.07em", display: "block", mb: 1.5 }}>
                Quick Actions
              </Typography>
              <Box sx={{ display: "flex", gap: 1, flexWrap: "wrap" }}>
                <Button size="small" variant="contained" startIcon={<PersonAddRoundedIcon sx={{ fontSize: "14px !important" }} />}>
                  Add Customer
                </Button>
                <Button size="small" variant="outlined" startIcon={<EmailRoundedIcon sx={{ fontSize: "14px !important" }} />} sx={{ borderColor: "divider", color: "text.secondary", fontSize: "0.78rem" }}>
                  Send Campaign
                </Button>
                <Button size="small" variant="outlined" startIcon={<FileDownloadRoundedIcon sx={{ fontSize: "14px !important" }} />} sx={{ borderColor: "divider", color: "text.secondary", fontSize: "0.78rem" }}>
                  Export CSV
                </Button>
              </Box>
            </Paper>

            <Paper sx={{ borderRadius: 2, flex: 1, overflow: "hidden" }}>
              <Box sx={{ px: 2.5, py: 1.8, borderBottom: "1px solid", borderColor: "divider", display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                <Typography variant="subtitle2" sx={{ fontFamily: "'Syne', sans-serif", fontWeight: 600 }}>
                  Recent Customers
                </Typography>
                <Typography variant="caption" sx={{ color: "primary.main", fontWeight: 600, fontSize: "0.72rem", cursor: "pointer" }}>
                  View all →
                </Typography>
              </Box>
              {recentCustomers.map((c, i) => {
                const pc = planColor(c.plan);
                return (
                  <Box key={i} sx={{ px: 2.5, py: 1.3, display: "flex", alignItems: "center", gap: 1.5, borderBottom: i < recentCustomers.length - 1 ? "1px solid" : "none", borderColor: "divider", "&:hover": { bgcolor: "action.hover", cursor: "pointer" } }}>
                    <Box sx={{ width: 30, height: 30, borderRadius: "50%", bgcolor: "action.selected", display: "flex", alignItems: "center", justifyContent: "center", flexShrink: 0 }}>
                      <Typography sx={{ fontSize: "0.65rem", fontWeight: 700, color: "primary.main", fontFamily: "'Syne', sans-serif" }}>
                        {c.name.split(" ").map(n => n[0]).join("")}
                      </Typography>
                    </Box>
                    <Box sx={{ flex: 1, minWidth: 0 }}>
                      <Typography variant="body2" sx={{ fontWeight: 500, fontSize: "0.8rem", lineHeight: 1.2 }}>{c.name}</Typography>
                      <Typography variant="caption" sx={{ color: "text.secondary", fontSize: "0.7rem" }}>{c.email}</Typography>
                    </Box>
                    <Chip label={c.plan} size="small" sx={{ fontSize: "0.65rem", height: 18, bgcolor: pc.bg, color: pc.color, fontWeight: 600, flexShrink: 0 }} />
                    <Box sx={{ width: 6, height: 6, borderRadius: "50%", bgcolor: c.status === "Active" ? "primary.main" : "text.disabled", flexShrink: 0 }} />
                    <Typography variant="caption" sx={{ color: "text.secondary", fontSize: "0.68rem", flexShrink: 0, minWidth: 60, textAlign: "right" }}>{c.time}</Typography>
                  </Box>
                );
              })}
            </Paper>

          </Box>
        </Grid>
      </Grid>
    </Box>
  );
}

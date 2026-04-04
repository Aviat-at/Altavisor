"use client";
import React, { useState } from "react";
import {
  Box, Typography, Paper, Grid, MenuItem, Select,
  FormControl, Button, Chip, LinearProgress,
} from "@mui/material";
import { useTheme } from "@mui/material/styles";
import DownloadRoundedIcon  from "@mui/icons-material/DownloadRounded";
import TrendingUpRoundedIcon from "@mui/icons-material/TrendingUpRounded";

function Sparkline({ data, color }: { data: number[]; color: string }) {
  const max = Math.max(...data);
  const min = Math.min(...data);
  const w = 120, h = 36, pad = 2;
  const pts = data.map((v, i) => {
    const x = pad + (i / (data.length - 1)) * (w - pad * 2);
    const y = h - pad - ((v - min) / (max - min || 1)) * (h - pad * 2);
    return `${x},${y}`;
  }).join(" ");
  return (
    <svg width={w} height={h} viewBox={`0 0 ${w} ${h}`} fill="none">
      <polyline points={pts} stroke={color} strokeWidth="1.8" strokeLinejoin="round" strokeLinecap="round" />
    </svg>
  );
}

const weekData    = [420, 510, 489, 620, 590, 710, 680, 740, 810, 790, 870, 920, 880, 980];
const errorData   = [12, 8, 15, 6, 9, 4, 7, 3, 5, 2, 4, 3, 2, 1];
const latencyData = [140, 132, 158, 145, 138, 142, 136, 141, 129, 133, 127, 130, 125, 128];

function MetricCard({ label, value, delta, positive, sparkData, color }: any) {
  return (
    <Paper sx={{ p: 2.5, borderRadius: 2 }}>
      <Typography variant="caption" sx={{ color: "text.secondary", fontWeight: 600, fontSize: "0.68rem", textTransform: "uppercase", letterSpacing: "0.07em" }}>
        {label}
      </Typography>
      <Box sx={{ display: "flex", alignItems: "flex-end", justifyContent: "space-between", mt: 1 }}>
        <Box>
          <Typography sx={{ fontSize: "1.6rem", fontWeight: 800, fontFamily: "'Syne', sans-serif", lineHeight: 1.1 }}>{value}</Typography>
          <Box sx={{ display: "flex", alignItems: "center", gap: 0.5, mt: 0.5 }}>
            <TrendingUpRoundedIcon sx={{ fontSize: 12, color: positive ? "primary.main" : "error.main", transform: positive ? "none" : "rotate(180deg)" }} />
            <Typography variant="caption" sx={{ color: positive ? "primary.main" : "error.main", fontWeight: 600, fontSize: "0.7rem" }}>{delta}</Typography>
          </Box>
        </Box>
        <Sparkline data={sparkData} color={color} />
      </Box>
    </Paper>
  );
}

function UsagePanel() {
  const theme = useTheme();
  const [period, setPeriod] = useState("7d");
  const breakdown = [
    { label: "API Calls",        value: 68, count: "66.8K" },
    { label: "Dashboard Views",  value: 21, count: "20.6K" },
    { label: "Webhook Triggers", value: 8,  count: "7.8K"  },
    { label: "Exports",          value: 3,  count: "2.9K"  },
  ];

  return (
    <Box>
      <Box sx={{ display: "flex", justifyContent: "space-between", alignItems: "center", mb: 2.5 }}>
        <Typography variant="subtitle2" sx={{ fontFamily: "'Syne', sans-serif", fontWeight: 700 }}>Usage Overview</Typography>
        <FormControl size="small">
          <Select value={period} onChange={(e) => setPeriod(e.target.value)} sx={{ fontSize: "0.78rem" }}>
            <MenuItem value="7d">Last 7 days</MenuItem>
            <MenuItem value="30d">Last 30 days</MenuItem>
            <MenuItem value="90d">Last 90 days</MenuItem>
          </Select>
        </FormControl>
      </Box>

      <Grid container spacing={2} sx={{ mb: 3 }}>
        <Grid item xs={12} sm={4}><MetricCard label="Total Requests" value="98.1K" delta="+14.2%" positive sparkData={weekData}    color={theme.palette.primary.main} /></Grid>
        <Grid item xs={12} sm={4}><MetricCard label="Error Rate"     value="0.03%" delta="-40%"   positive sparkData={errorData}   color={theme.palette.secondary.main} /></Grid>
        <Grid item xs={12} sm={4}><MetricCard label="Avg Latency"    value="128ms" delta="-8.6%"  positive sparkData={latencyData} color={theme.palette.primary.main} /></Grid>
      </Grid>

      <Paper sx={{ borderRadius: 2, p: 2.5 }}>
        <Typography variant="subtitle2" sx={{ fontFamily: "'Syne', sans-serif", fontWeight: 600, mb: 2 }}>Request Breakdown</Typography>
        {breakdown.map((item) => (
          <Box key={item.label} sx={{ mb: 2 }}>
            <Box sx={{ display: "flex", justifyContent: "space-between", mb: 0.5 }}>
              <Typography variant="caption" sx={{ color: "text.secondary" }}>{item.label}</Typography>
              <Box sx={{ display: "flex", gap: 1.5 }}>
                <Typography variant="caption" sx={{ fontWeight: 600 }}>{item.count}</Typography>
                <Typography variant="caption" sx={{ color: "primary.main", fontWeight: 700, width: 32, textAlign: "right" }}>{item.value}%</Typography>
              </Box>
            </Box>
            <LinearProgress variant="determinate" value={item.value} sx={{ height: 4, borderRadius: 2, "& .MuiLinearProgress-bar": { bgcolor: "primary.main", borderRadius: 2 } }} />
          </Box>
        ))}
      </Paper>
    </Box>
  );
}

function ReportsPanel() {
  const reports = [
    { name: "Monthly Usage Summary",  date: "Mar 1, 2026",  status: "Ready",      size: "2.4 MB" },
    { name: "Security Audit Report",  date: "Feb 28, 2026", status: "Ready",      size: "890 KB" },
    { name: "API Performance Report", date: "Feb 15, 2026", status: "Ready",      size: "1.1 MB" },
    { name: "User Activity Report",   date: "Feb 1, 2026",  status: "Processing", size: "—"      },
  ];

  return (
    <Box>
      <Box sx={{ display: "flex", justifyContent: "space-between", alignItems: "center", mb: 2.5 }}>
        <Typography variant="subtitle2" sx={{ fontFamily: "'Syne', sans-serif", fontWeight: 700 }}>Scheduled Reports</Typography>
        <Button variant="outlined" size="small" sx={{ borderColor: "divider", color: "text.secondary", fontSize: "0.76rem" }}>+ New Report</Button>
      </Box>
      <Paper sx={{ borderRadius: 2, overflow: "hidden" }}>
        <Box sx={{ px: 2.5, py: 1.2, display: "grid", gridTemplateColumns: "2fr 1.2fr 1fr 1fr 80px", borderBottom: "1px solid", borderColor: "divider" }}>
          {["Report Name", "Generated", "Status", "Size", ""].map((h, i) => (
            <Typography key={i} variant="caption" sx={{ color: "text.secondary", fontWeight: 600, fontSize: "0.67rem", textTransform: "uppercase", letterSpacing: "0.07em" }}>{h}</Typography>
          ))}
        </Box>
        {reports.map((r, i) => (
          <Box key={i} sx={{ px: 2.5, py: 1.5, display: "grid", gridTemplateColumns: "2fr 1.2fr 1fr 1fr 80px", alignItems: "center", borderBottom: i < reports.length - 1 ? "1px solid" : "none", borderColor: "divider", "&:hover": { bgcolor: "action.hover" } }}>
            <Typography variant="body2" sx={{ fontWeight: 500, fontSize: "0.82rem" }}>{r.name}</Typography>
            <Typography variant="caption" sx={{ color: "text.secondary" }}>{r.date}</Typography>
            <Chip label={r.status} size="small" sx={{ fontSize: "0.67rem", height: 18, width: "fit-content", bgcolor: r.status === "Ready" ? "action.selected" : "rgba(74,160,240,0.1)", color: r.status === "Ready" ? "primary.main" : "info.main", fontWeight: 600 }} />
            <Typography variant="caption" sx={{ color: "text.secondary" }}>{r.size}</Typography>
            <Button size="small" disabled={r.status !== "Ready"} startIcon={<DownloadRoundedIcon sx={{ fontSize: "12px !important" }} />} sx={{ fontSize: "0.72rem", color: "text.secondary", minWidth: 0, p: 0.5, "&:hover": { color: "primary.main" } }}>Download</Button>
          </Box>
        ))}
      </Paper>
    </Box>
  );
}

function ExportsPanel() {
  const [format, setFormat] = useState("csv");
  const [range, setRange]   = useState("30d");
  const datasets = ["API Request Logs", "User Activity", "Error Events", "Billing Records", "Audit Trail"];

  return (
    <Box>
      <Paper sx={{ borderRadius: 2, p: 2.5, mb: 2.5 }}>
        <Typography variant="subtitle2" sx={{ fontFamily: "'Syne', sans-serif", fontWeight: 600, mb: 2 }}>Configure Export</Typography>
        <Grid container spacing={2}>
          <Grid item xs={12} sm={4}>
            <Typography variant="caption" sx={{ color: "text.secondary", mb: 0.8, display: "block" }}>Format</Typography>
            <FormControl size="small" fullWidth>
              <Select value={format} onChange={(e) => setFormat(e.target.value)}>
                <MenuItem value="csv">CSV</MenuItem>
                <MenuItem value="json">JSON</MenuItem>
                <MenuItem value="parquet">Parquet</MenuItem>
                <MenuItem value="xlsx">Excel (.xlsx)</MenuItem>
              </Select>
            </FormControl>
          </Grid>
          <Grid item xs={12} sm={4}>
            <Typography variant="caption" sx={{ color: "text.secondary", mb: 0.8, display: "block" }}>Date Range</Typography>
            <FormControl size="small" fullWidth>
              <Select value={range} onChange={(e) => setRange(e.target.value)}>
                <MenuItem value="7d">Last 7 days</MenuItem>
                <MenuItem value="30d">Last 30 days</MenuItem>
                <MenuItem value="90d">Last 90 days</MenuItem>
                <MenuItem value="custom">Custom range</MenuItem>
              </Select>
            </FormControl>
          </Grid>
          <Grid item xs={12} sm={4} sx={{ display: "flex", alignItems: "flex-end" }}>
            <Button fullWidth variant="contained" startIcon={<DownloadRoundedIcon />}>Export Now</Button>
          </Grid>
        </Grid>
      </Paper>

      <Paper sx={{ borderRadius: 2, overflow: "hidden" }}>
        <Box sx={{ px: 2.5, py: 1.5, borderBottom: "1px solid", borderColor: "divider" }}>
          <Typography variant="subtitle2" sx={{ fontFamily: "'Syne', sans-serif", fontWeight: 600 }}>Available Datasets</Typography>
        </Box>
        {datasets.map((d, i) => (
          <Box key={i} sx={{ px: 2.5, py: 1.4, display: "flex", alignItems: "center", justifyContent: "space-between", borderBottom: i < datasets.length - 1 ? "1px solid" : "none", borderColor: "divider", "&:hover": { bgcolor: "action.hover" } }}>
            <Typography variant="body2" sx={{ fontSize: "0.82rem" }}>{d}</Typography>
            <Button size="small" sx={{ fontSize: "0.72rem", color: "primary.main", minWidth: 0 }}>Select</Button>
          </Box>
        ))}
      </Paper>
    </Box>
  );
}

export default function AnalyticsDashboard({ subTabId }: { subTabId: string }) {
  if (subTabId === "usage")   return <UsagePanel />;
  if (subTabId === "reports") return <ReportsPanel />;
  return <ExportsPanel />;
}

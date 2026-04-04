"use client";
import React, { useState } from "react";
import {
  Box, Typography, Paper, Chip, Button, TextField,
  InputAdornment, LinearProgress, Grid,
} from "@mui/material";
import { useTheme } from "@mui/material/styles";
import SearchRoundedIcon              from "@mui/icons-material/SearchRounded";
import CheckCircleOutlineRoundedIcon  from "@mui/icons-material/CheckCircleOutlineRounded";
import RadioButtonUncheckedRoundedIcon from "@mui/icons-material/RadioButtonUncheckedRounded";
import ErrorOutlineRoundedIcon        from "@mui/icons-material/ErrorOutlineRounded";

// Semantic status → palette key mapping
const STATUS_PALETTE = {
  healthy:   { color: "#4AE08A", bg: "rgba(74,224,138,0.10)" },
  deploying: { color: "#4AA0F0", bg: "rgba(74,160,240,0.10)" },
  degraded:  { color: "#F0B84A", bg: "rgba(240,184,74,0.10)" },
  error:     { color: "#F04A4A", bg: "rgba(240,74,74,0.10)"  },
  success:   { color: "#4AE08A", bg: "rgba(74,224,138,0.10)" },
  running:   { color: "#4AA0F0", bg: "rgba(74,160,240,0.10)" },
  failed:    { color: "#F04A4A", bg: "rgba(240,74,74,0.10)"  },
} as const;

type StatusKey = keyof typeof STATUS_PALETTE;
const statusColor = (s: string) => (STATUS_PALETTE[s as StatusKey] ?? STATUS_PALETTE.error).color;
const statusBg    = (s: string) => (STATUS_PALETTE[s as StatusKey] ?? STATUS_PALETTE.error).bg;

function StatusIcon({ status }: { status: string }) {
  if (status === "healthy") return <CheckCircleOutlineRoundedIcon  sx={{ fontSize: 14, color: statusColor("healthy")   }} />;
  if (status === "error")   return <ErrorOutlineRoundedIcon        sx={{ fontSize: 14, color: statusColor("error")     }} />;
  return                           <RadioButtonUncheckedRoundedIcon sx={{ fontSize: 14, color: statusColor("deploying") }} />;
}

function EnvironmentsPanel() {
  const envs = [
    { name: "Production",  region: "us-east-1",  status: "healthy",   version: "v2.4.1",       uptime: "99.98%", cpu: 38 },
    { name: "Staging",     region: "us-east-1",  status: "healthy",   version: "v2.5.0-rc1",   uptime: "99.80%", cpu: 22 },
    { name: "Development", region: "us-west-2",  status: "deploying", version: "v2.5.0-dev",   uptime: "97.10%", cpu: 55 },
    { name: "QA",          region: "eu-central-1", status: "degraded", version: "v2.4.1",       uptime: "95.40%", cpu: 71 },
  ];

  return (
    <Box>
      <Box sx={{ display: "flex", justifyContent: "space-between", alignItems: "center", mb: 2.5 }}>
        <Typography variant="subtitle2" sx={{ fontFamily: "'Syne', sans-serif", fontWeight: 700 }}>Environments</Typography>
        <Button variant="outlined" size="small" sx={{ borderColor: "divider", color: "text.secondary", fontSize: "0.76rem" }}>+ New Environment</Button>
      </Box>
      <Grid container spacing={2}>
        {envs.map((env) => (
          <Grid item xs={12} sm={6} key={env.name}>
            <Paper sx={{ p: 2.5, borderRadius: 2 }}>
              <Box sx={{ display: "flex", alignItems: "center", justifyContent: "space-between", mb: 1.5 }}>
                <Box sx={{ display: "flex", alignItems: "center", gap: 1 }}>
                  <StatusIcon status={env.status} />
                  <Typography variant="subtitle2" sx={{ fontFamily: "'Syne', sans-serif", fontWeight: 600 }}>{env.name}</Typography>
                </Box>
                <Chip label={env.status} size="small" sx={{ fontSize: "0.67rem", height: 18, bgcolor: statusBg(env.status), color: statusColor(env.status), fontWeight: 700, textTransform: "capitalize" }} />
              </Box>
              <Box sx={{ display: "flex", gap: 2, mb: 1.5, flexWrap: "wrap" }}>
                <Box>
                  <Typography variant="caption" sx={{ color: "text.secondary", fontSize: "0.67rem", display: "block" }}>REGION</Typography>
                  <Typography variant="caption" sx={{ fontWeight: 500, fontSize: "0.75rem" }}>{env.region}</Typography>
                </Box>
                <Box>
                  <Typography variant="caption" sx={{ color: "text.secondary", fontSize: "0.67rem", display: "block" }}>VERSION</Typography>
                  <Typography variant="caption" sx={{ fontWeight: 500, fontSize: "0.75rem" }}>{env.version}</Typography>
                </Box>
                <Box>
                  <Typography variant="caption" sx={{ color: "text.secondary", fontSize: "0.67rem", display: "block" }}>UPTIME</Typography>
                  <Typography variant="caption" sx={{ fontWeight: 500, fontSize: "0.75rem", color: "primary.main" }}>{env.uptime}</Typography>
                </Box>
              </Box>
              <Box>
                <Box sx={{ display: "flex", justifyContent: "space-between", mb: 0.4 }}>
                  <Typography variant="caption" sx={{ color: "text.secondary", fontSize: "0.67rem" }}>CPU</Typography>
                  <Typography variant="caption" sx={{ color: statusColor(env.status), fontWeight: 700, fontSize: "0.67rem" }}>{env.cpu}%</Typography>
                </Box>
                <LinearProgress variant="determinate" value={env.cpu} sx={{ height: 3, borderRadius: 2, "& .MuiLinearProgress-bar": { bgcolor: statusColor(env.status), borderRadius: 2 } }} />
              </Box>
            </Paper>
          </Grid>
        ))}
      </Grid>
    </Box>
  );
}

function DeploymentsPanel() {
  const deploys = [
    { id: "dep-1182", env: "Production",  branch: "main",         author: "alex@altavisor.io",   status: "success", time: "2 min ago",  duration: "1m 42s" },
    { id: "dep-1181", env: "Staging",     branch: "feat/ui-refresh", author: "maria@altavisor.io", status: "success", time: "28 min ago", duration: "2m 01s" },
    { id: "dep-1180", env: "Development", branch: "feat/new-api",  author: "sam@altavisor.io",    status: "running", time: "1 hr ago",   duration: "—"      },
    { id: "dep-1179", env: "QA",          branch: "fix/auth-bug",  author: "jordan@altavisor.io", status: "failed",  time: "3 hr ago",   duration: "0m 58s" },
    { id: "dep-1178", env: "Production",  branch: "main",         author: "alex@altavisor.io",   status: "success", time: "1 day ago",  duration: "1m 38s" },
  ];

  return (
    <Box>
      <Box sx={{ display: "flex", justifyContent: "space-between", alignItems: "center", mb: 2.5 }}>
        <Typography variant="subtitle2" sx={{ fontFamily: "'Syne', sans-serif", fontWeight: 700 }}>Recent Deployments</Typography>
        <Button variant="contained" size="small">Trigger Deploy</Button>
      </Box>
      <Paper sx={{ borderRadius: 2, overflow: "hidden" }}>
        <Box sx={{ px: 2.5, py: 1.2, display: "grid", gridTemplateColumns: "90px 1fr 1.4fr 1.4fr 80px 80px", borderBottom: "1px solid", borderColor: "divider" }}>
          {["ID", "Environment", "Branch", "Author", "Status", "Time"].map((h) => (
            <Typography key={h} variant="caption" sx={{ color: "text.secondary", fontWeight: 600, fontSize: "0.67rem", textTransform: "uppercase", letterSpacing: "0.07em" }}>{h}</Typography>
          ))}
        </Box>
        {deploys.map((d, i) => (
          <Box key={i} sx={{ px: 2.5, py: 1.4, display: "grid", gridTemplateColumns: "90px 1fr 1.4fr 1.4fr 80px 80px", alignItems: "center", borderBottom: i < deploys.length - 1 ? "1px solid" : "none", borderColor: "divider", "&:hover": { bgcolor: "action.hover" } }}>
            <Typography variant="caption" sx={{ color: "info.main", fontFamily: "monospace", fontSize: "0.75rem" }}>{d.id}</Typography>
            <Typography variant="caption" sx={{ fontWeight: 500 }}>{d.env}</Typography>
            <Typography variant="caption" sx={{ color: "text.secondary", fontFamily: "monospace", fontSize: "0.72rem" }}>{d.branch}</Typography>
            <Typography variant="caption" sx={{ color: "text.secondary" }}>{d.author}</Typography>
            <Chip label={d.status} size="small" sx={{ fontSize: "0.67rem", height: 18, width: "fit-content", bgcolor: statusBg(d.status), color: statusColor(d.status), fontWeight: 700, textTransform: "capitalize" }} />
            <Typography variant="caption" sx={{ color: "text.secondary" }}>{d.time}</Typography>
          </Box>
        ))}
      </Paper>
    </Box>
  );
}

function LogsPanel() {
  const theme = useTheme();
  const isDark = theme.palette.mode === "dark";
  const [search, setSearch] = useState("");

  const logs = [
    { time: "14:22:01", level: "INFO",  msg: "Deployment dep-1182 completed successfully",           service: "deployer"   },
    { time: "14:21:44", level: "INFO",  msg: "Health check passed for production environment",       service: "monitor"    },
    { time: "14:20:18", level: "WARN",  msg: "Memory usage exceeded 80% on prod-worker-03",          service: "metrics"    },
    { time: "14:18:52", level: "INFO",  msg: "Auto-scaling triggered — adding 1 worker node",        service: "autoscaler" },
    { time: "14:15:30", level: "ERROR", msg: "Connection timeout on database replica us-east-1b",    service: "db-proxy"   },
    { time: "14:12:07", level: "INFO",  msg: "SSL certificate renewed for altavisor.io",             service: "certbot"    },
    { time: "14:10:44", level: "INFO",  msg: "Backup snapshot completed — 4.2 GB",                  service: "backup"     },
    { time: "14:08:11", level: "WARN",  msg: "Slow query detected: >2000ms on /v2/analytics",        service: "api"        },
  ];

  const levelColor = (l: string) =>
    l === "ERROR" ? theme.palette.error.main
    : l === "WARN" ? theme.palette.warning.main
    : theme.palette.secondary.main;

  const filtered = logs.filter((l) => !search || l.msg.toLowerCase().includes(search.toLowerCase()) || l.service.includes(search));

  return (
    <Box>
      <Box sx={{ display: "flex", justifyContent: "space-between", alignItems: "center", mb: 2.5 }}>
        <Typography variant="subtitle2" sx={{ fontFamily: "'Syne', sans-serif", fontWeight: 700 }}>Infrastructure Logs</Typography>
        <TextField
          placeholder="Filter logs..."
          size="small"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          InputProps={{ startAdornment: <InputAdornment position="start"><SearchRoundedIcon sx={{ fontSize: 15, color: "text.secondary" }} /></InputAdornment> }}
          sx={{ width: 240 }}
        />
      </Box>

      <Paper sx={{ borderRadius: 2, overflow: "hidden", bgcolor: isDark ? "#0A0C0F" : "#F8F9FA" }}>
        {filtered.map((log, i) => (
          <Box key={i} sx={{ px: 2, py: 1, display: "flex", gap: 2, alignItems: "flex-start", borderBottom: i < filtered.length - 1 ? "1px solid" : "none", borderColor: "divider", "&:hover": { bgcolor: "action.hover" } }}>
            <Typography sx={{ fontSize: "0.72rem", color: "text.disabled", fontFamily: "monospace", flexShrink: 0, lineHeight: 1.6 }}>{log.time}</Typography>
            <Typography sx={{ fontSize: "0.68rem", fontWeight: 700, color: levelColor(log.level), fontFamily: "monospace", flexShrink: 0, width: 40, lineHeight: 1.6 }}>{log.level}</Typography>
            <Typography sx={{ fontSize: "0.72rem", color: "text.secondary", fontFamily: "monospace", flexShrink: 0, lineHeight: 1.6 }}>[{log.service}]</Typography>
            <Typography sx={{ fontSize: "0.72rem", color: "text.primary", fontFamily: "monospace", lineHeight: 1.6, flex: 1 }}>{log.msg}</Typography>
          </Box>
        ))}
      </Paper>
    </Box>
  );
}

export default function InfrastructureDashboard({ subTabId }: { subTabId: string }) {
  if (subTabId === "environments")  return <EnvironmentsPanel />;
  if (subTabId === "deployments")   return <DeploymentsPanel />;
  return <LogsPanel />;
}

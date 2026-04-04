"use client";
import React from "react";
import { Box, Typography, IconButton, Tooltip } from "@mui/material";
import CircleRoundedIcon    from "@mui/icons-material/CircleRounded";
import OpenInNewRoundedIcon from "@mui/icons-material/OpenInNewRounded";
import CodeRoundedIcon      from "@mui/icons-material/CodeRounded";
import InfoOutlinedIcon     from "@mui/icons-material/InfoOutlined";

export default function FooterBar() {
  return (
    <Box
      sx={{
        height: 32,
        minHeight: 32,
        display: "flex",
        alignItems: "center",
        px: 2,
        gap: 2,
        bgcolor: "background.default",
        borderTop: "1px solid",
        borderColor: "divider",
        zIndex: 100,
        overflow: "hidden",
      }}
    >
      {/* Status */}
      <Box sx={{ display: "flex", alignItems: "center", gap: 0.6 }}>
        <CircleRoundedIcon sx={{ fontSize: 7, color: "primary.main" }} />
        <Typography variant="caption" sx={{ color: "primary.main", fontSize: "0.68rem", fontWeight: 600 }}>
          All systems operational
        </Typography>
      </Box>

      <Box sx={{ width: "1px", height: 14, bgcolor: "divider" }} />

      <Typography variant="caption" sx={{ color: "text.secondary", fontSize: "0.68rem" }}>
        v2.4.1
      </Typography>

      <Box sx={{ width: "1px", height: 14, bgcolor: "divider" }} />

      <Typography variant="caption" sx={{ color: "text.secondary", fontSize: "0.68rem" }}>
        Region: <span style={{ fontWeight: 500 }}>us-east-1</span>
      </Typography>

      <Box sx={{ flex: 1 }} />

      <Typography variant="caption" sx={{ color: "text.disabled", fontSize: "0.65rem" }}>
        © 2025 Altavisor
      </Typography>

      <Box sx={{ width: "1px", height: 14, bgcolor: "divider" }} />

      <Tooltip title="API Console">
        <IconButton size="small" sx={{ color: "text.disabled", p: 0.3, "&:hover": { color: "text.secondary" } }}>
          <CodeRoundedIcon sx={{ fontSize: 13 }} />
        </IconButton>
      </Tooltip>

      <Tooltip title="Documentation">
        <IconButton size="small" sx={{ color: "text.disabled", p: 0.3, "&:hover": { color: "text.secondary" } }}>
          <OpenInNewRoundedIcon sx={{ fontSize: 13 }} />
        </IconButton>
      </Tooltip>

      <Tooltip title="Changelog">
        <IconButton size="small" sx={{ color: "text.disabled", p: 0.3, "&:hover": { color: "text.secondary" } }}>
          <InfoOutlinedIcon sx={{ fontSize: 13 }} />
        </IconButton>
      </Tooltip>
    </Box>
  );
}

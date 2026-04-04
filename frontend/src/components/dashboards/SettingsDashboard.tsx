"use client";
import React, { useState } from "react";
import {
  Box, Typography, Paper, TextField, Switch, Select, MenuItem,
  FormControlLabel, Button, Divider, Chip, FormControl,
  Slider, ToggleButtonGroup, ToggleButton, Alert,
} from "@mui/material";
import SaveRoundedIcon from "@mui/icons-material/SaveRounded";

function SettingsSection({ title, description, children }: any) {
  return (
    <Paper sx={{ mb: 2.5, borderRadius: 2, overflow: "hidden" }}>
      <Box sx={{ px: 2.5, pt: 2.5, pb: 2, borderBottom: "1px solid", borderColor: "divider" }}>
        <Typography variant="subtitle2" sx={{ fontFamily: "'Syne', sans-serif", fontWeight: 600, mb: 0.3 }}>
          {title}
        </Typography>
        {description && (
          <Typography variant="caption" sx={{ color: "text.secondary", fontSize: "0.75rem" }}>
            {description}
          </Typography>
        )}
      </Box>
      <Box sx={{ p: 2.5 }}>{children}</Box>
    </Paper>
  );
}

function FieldRow({ label, hint, children }: any) {
  return (
    <Box sx={{ display: "flex", alignItems: "flex-start", gap: 2, py: 1.5, "&:not(:last-child)": { borderBottom: "1px solid", borderColor: "divider" } }}>
      <Box sx={{ flex: "0 0 200px" }}>
        <Typography variant="body2" sx={{ fontWeight: 500, fontSize: "0.82rem" }}>{label}</Typography>
        {hint && <Typography variant="caption" sx={{ color: "text.secondary", fontSize: "0.72rem" }}>{hint}</Typography>}
      </Box>
      <Box sx={{ flex: 1 }}>{children}</Box>
    </Box>
  );
}

function GeneralSettings() {
  const [org, setOrg]         = useState("Altavisor Corp");
  const [domain, setDomain]   = useState("altavisor.io");
  const [region, setRegion]   = useState("us-east-1");
  const [timezone, setTimezone] = useState("UTC");
  const [saved, setSaved]     = useState(false);

  return (
    <Box>
      {saved && (
        <Alert severity="success" onClose={() => setSaved(false)} sx={{ mb: 2 }}>
          Settings saved successfully.
        </Alert>
      )}

      <SettingsSection title="Organization" description="Basic information about your workspace">
        <FieldRow label="Organization Name" hint="Displayed across the platform">
          <TextField value={org} onChange={(e) => setOrg(e.target.value)} fullWidth />
        </FieldRow>
        <FieldRow label="Primary Domain" hint="Your verified domain">
          <TextField value={domain} onChange={(e) => setDomain(e.target.value)} fullWidth />
        </FieldRow>
        <FieldRow label="Plan">
          <Chip label="Pro" size="small" sx={{ bgcolor: "action.selected", color: "primary.main", fontSize: "0.72rem" }} />
        </FieldRow>
      </SettingsSection>

      <SettingsSection title="Locale & Region" description="Control regional defaults for your team">
        <FieldRow label="Primary Region" hint="Cloud hosting region">
          <FormControl size="small" sx={{ minWidth: 200 }}>
            <Select value={region} onChange={(e) => setRegion(e.target.value)}>
              <MenuItem value="us-east-1">US East (N. Virginia)</MenuItem>
              <MenuItem value="us-west-2">US West (Oregon)</MenuItem>
              <MenuItem value="eu-central-1">EU (Frankfurt)</MenuItem>
              <MenuItem value="ap-southeast-1">Asia Pacific (Singapore)</MenuItem>
            </Select>
          </FormControl>
        </FieldRow>
        <FieldRow label="Default Timezone">
          <FormControl size="small" sx={{ minWidth: 200 }}>
            <Select value={timezone} onChange={(e) => setTimezone(e.target.value)}>
              <MenuItem value="UTC">UTC</MenuItem>
              <MenuItem value="America/New_York">Eastern Time</MenuItem>
              <MenuItem value="America/Los_Angeles">Pacific Time</MenuItem>
              <MenuItem value="Europe/London">London</MenuItem>
              <MenuItem value="Asia/Tokyo">Tokyo</MenuItem>
            </Select>
          </FormControl>
        </FieldRow>
      </SettingsSection>

      <Box sx={{ display: "flex", justifyContent: "flex-end" }}>
        <Button variant="contained" startIcon={<SaveRoundedIcon />} onClick={() => setSaved(true)}>
          Save Changes
        </Button>
      </Box>
    </Box>
  );
}

function AppearanceSettings() {
  const [density, setDensity]           = useState("comfortable");
  const [accentColor, setAccentColor]   = useState("#C8F04A");
  const [fontSize, setFontSize]         = useState(14);
  const [animations, setAnimations]     = useState(true);
  const [compactSidebar, setCompactSidebar] = useState(false);

  const colors = ["#C8F04A", "#4AF0C8", "#F04A8A", "#4A8AF0", "#F0B84A"];

  return (
    <Box>
      <SettingsSection title="Layout & Density" description="Adjust visual spacing and layout preferences">
        <FieldRow label="UI Density" hint="Affects spacing across the panel">
          <ToggleButtonGroup value={density} exclusive onChange={(_, v) => v && setDensity(v)} size="small">
            <ToggleButton value="compact">Compact</ToggleButton>
            <ToggleButton value="comfortable">Comfortable</ToggleButton>
            <ToggleButton value="spacious">Spacious</ToggleButton>
          </ToggleButtonGroup>
        </FieldRow>
        <FieldRow label="Compact Sidebar" hint="Collapse sidebar labels">
          <Switch checked={compactSidebar} onChange={(e) => setCompactSidebar(e.target.checked)} />
        </FieldRow>
        <FieldRow label="Animations" hint="Transition and motion effects">
          <Switch checked={animations} onChange={(e) => setAnimations(e.target.checked)} />
        </FieldRow>
      </SettingsSection>

      <SettingsSection title="Accent Color" description="Customize the primary highlight color">
        <FieldRow label="Color Preset">
          <Box sx={{ display: "flex", gap: 1 }}>
            {colors.map((c) => (
              <Box
                key={c}
                onClick={() => setAccentColor(c)}
                sx={{
                  width: 28, height: 28,
                  borderRadius: "6px",
                  bgcolor: c,
                  cursor: "pointer",
                  border: accentColor === c ? "2px solid white" : "2px solid transparent",
                  boxSizing: "border-box",
                  transition: "transform 0.1s",
                  "&:hover": { transform: "scale(1.1)" },
                }}
              />
            ))}
          </Box>
        </FieldRow>
        <FieldRow label="Custom Hex">
          <TextField value={accentColor} onChange={(e) => setAccentColor(e.target.value)} size="small" sx={{ width: 140 }} />
        </FieldRow>
      </SettingsSection>

      <SettingsSection title="Typography" description="Base font size for the interface">
        <FieldRow label="Base Font Size" hint={`${fontSize}px`}>
          <Box sx={{ width: 240 }}>
            <Slider value={fontSize} onChange={(_, v) => setFontSize(v as number)} min={12} max={18} step={1} marks />
          </Box>
        </FieldRow>
      </SettingsSection>
    </Box>
  );
}

function IntegrationsSettings() {
  const [slackEnabled, setSlackEnabled]   = useState(true);
  const [webhookUrl, setWebhookUrl]       = useState("https://hooks.slack.com/services/T00000000/B00000000/...");
  const [githubEnabled, setGithubEnabled] = useState(false);

  return (
    <Box>
      <SettingsSection title="Slack" description="Get notifications and alerts in Slack">
        <FieldRow label="Enable Integration">
          <Switch checked={slackEnabled} onChange={(e) => setSlackEnabled(e.target.checked)} />
        </FieldRow>
        {slackEnabled && (
          <>
            <FieldRow label="Webhook URL" hint="Incoming webhook from Slack App settings">
              <TextField value={webhookUrl} onChange={(e) => setWebhookUrl(e.target.value)} fullWidth />
            </FieldRow>
            <FieldRow label="Notify on">
              <Box sx={{ display: "flex", gap: 0.8, flexWrap: "wrap" }}>
                {["Deployments", "Errors", "Security Events", "Reports"].map((t) => (
                  <Chip key={t} label={t} size="small" sx={{ bgcolor: "action.selected", color: "primary.main", fontSize: "0.72rem" }} />
                ))}
              </Box>
            </FieldRow>
          </>
        )}
      </SettingsSection>

      <SettingsSection title="GitHub" description="Link repositories for deployment tracking">
        <FieldRow label="Enable Integration">
          <Switch checked={githubEnabled} onChange={(e) => setGithubEnabled(e.target.checked)} />
        </FieldRow>
        {!githubEnabled && (
          <Box sx={{ mt: 1 }}>
            <Button variant="outlined" size="small" sx={{ borderColor: "divider", color: "text.secondary", fontSize: "0.78rem" }}>
              Connect GitHub Account
            </Button>
          </Box>
        )}
      </SettingsSection>
    </Box>
  );
}

function AdvancedSettings() {
  const [debugMode, setDebugMode] = useState(false);
  const [telemetry, setTelemetry] = useState(true);
  const [rateLimit, setRateLimit] = useState(1000);

  return (
    <Box>
      <SettingsSection title="Developer Options" description="Advanced controls for power users">
        <FieldRow label="Debug Mode" hint="Enables verbose logging">
          <Switch checked={debugMode} onChange={(e) => setDebugMode(e.target.checked)} />
        </FieldRow>
        <FieldRow label="Usage Telemetry" hint="Share anonymous usage data">
          <Switch checked={telemetry} onChange={(e) => setTelemetry(e.target.checked)} />
        </FieldRow>
        <FieldRow label="API Rate Limit" hint="Requests per minute">
          <TextField type="number" value={rateLimit} onChange={(e) => setRateLimit(Number(e.target.value))} size="small" sx={{ width: 120 }} />
        </FieldRow>
      </SettingsSection>

      <SettingsSection title="Danger Zone" description="Irreversible actions — proceed with caution">
        <Box sx={{ display: "flex", gap: 1.5, flexWrap: "wrap" }}>
          <Button variant="outlined" size="small" color="error" sx={{ fontSize: "0.78rem" }}>
            Reset All Settings
          </Button>
          <Button variant="outlined" size="small" color="error" sx={{ fontSize: "0.78rem" }}>
            Delete Workspace
          </Button>
        </Box>
      </SettingsSection>
    </Box>
  );
}

const panels: Record<string, React.ComponentType> = {
  general:      GeneralSettings,
  appearance:   AppearanceSettings,
  integrations: IntegrationsSettings,
  advanced:     AdvancedSettings,
};

export default function SettingsDashboard({ subTabId }: { subTabId: string }) {
  const Panel = panels[subTabId] || GeneralSettings;
  return <Panel />;
}

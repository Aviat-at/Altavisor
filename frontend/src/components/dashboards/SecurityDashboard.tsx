"use client";
import React, { useState } from "react";
import {
  Box, Typography, Paper, Switch, TextField, Button,
  Chip, Divider, Select, MenuItem, FormControl,
} from "@mui/material";
import PersonRoundedIcon from "@mui/icons-material/PersonRounded";

function FieldRow({ label, hint, children }: any) {
  return (
    <Box sx={{ display: "flex", alignItems: "flex-start", gap: 2, py: 1.5, "&:not(:last-child)": { borderBottom: "1px solid", borderColor: "divider" } }}>
      <Box sx={{ flex: "0 0 220px" }}>
        <Typography variant="body2" sx={{ fontWeight: 500, fontSize: "0.82rem" }}>{label}</Typography>
        {hint && <Typography variant="caption" sx={{ color: "text.secondary", fontSize: "0.72rem" }}>{hint}</Typography>}
      </Box>
      <Box sx={{ flex: 1 }}>{children}</Box>
    </Box>
  );
}

function Section({ title, description, children }: any) {
  return (
    <Paper sx={{ mb: 2.5, borderRadius: 2, overflow: "hidden" }}>
      <Box sx={{ px: 2.5, pt: 2.5, pb: 2, borderBottom: "1px solid", borderColor: "divider" }}>
        <Typography variant="subtitle2" sx={{ fontFamily: "'Syne', sans-serif", fontWeight: 600, mb: 0.3 }}>{title}</Typography>
        {description && <Typography variant="caption" sx={{ color: "text.secondary", fontSize: "0.75rem" }}>{description}</Typography>}
      </Box>
      <Box sx={{ p: 2.5 }}>{children}</Box>
    </Paper>
  );
}

function AuthPanel() {
  const [mfa, setMfa]                   = useState(true);
  const [sso, setSso]                   = useState(false);
  const [sessionTimeout, setSessionTimeout] = useState("8");
  const [passwordMin, setPasswordMin]   = useState("12");
  const [savedMsg, setSavedMsg]         = useState(false);

  return (
    <Box>
      <Section title="Multi-Factor Authentication" description="Require MFA for all users or specific roles">
        <FieldRow label="Enforce MFA" hint="All users must enroll in MFA">
          <Switch checked={mfa} onChange={(e) => setMfa(e.target.checked)} />
        </FieldRow>
        <FieldRow label="Allowed Methods" hint="Authenticator methods users may use">
          <Box sx={{ display: "flex", gap: 0.8, flexWrap: "wrap" }}>
            {["TOTP App", "SMS", "Hardware Key", "Email OTP"].map((m) => (
              <Chip key={m} label={m} size="small" sx={{ fontSize: "0.72rem", bgcolor: "action.selected", color: "primary.main" }} />
            ))}
          </Box>
        </FieldRow>
      </Section>

      <Section title="Single Sign-On (SSO)" description="Configure SAML 2.0 or OIDC identity providers">
        <FieldRow label="Enable SSO">
          <Switch checked={sso} onChange={(e) => setSso(e.target.checked)} />
        </FieldRow>
        {sso && (
          <>
            <FieldRow label="Provider" hint="Your identity provider">
              <FormControl size="small" sx={{ minWidth: 180 }}>
                <Select defaultValue="okta">
                  <MenuItem value="okta">Okta</MenuItem>
                  <MenuItem value="azure">Azure AD</MenuItem>
                  <MenuItem value="google">Google Workspace</MenuItem>
                  <MenuItem value="custom">Custom SAML</MenuItem>
                </Select>
              </FormControl>
            </FieldRow>
            <FieldRow label="Entity ID / Issuer">
              <TextField size="small" placeholder="https://your-idp.example.com" fullWidth />
            </FieldRow>
          </>
        )}
      </Section>

      <Section title="Session & Password Policy">
        <FieldRow label="Session Timeout (hours)" hint="Auto-logout after inactivity">
          <TextField type="number" size="small" value={sessionTimeout} onChange={(e) => setSessionTimeout(e.target.value)} sx={{ width: 100 }} />
        </FieldRow>
        <FieldRow label="Min Password Length">
          <TextField type="number" size="small" value={passwordMin} onChange={(e) => setPasswordMin(e.target.value)} sx={{ width: 100 }} />
        </FieldRow>
        <FieldRow label="Password Requirements" hint="Enforced for all users">
          <Box sx={{ display: "flex", gap: 0.8, flexWrap: "wrap" }}>
            {["Uppercase", "Number", "Symbol", "No reuse (last 5)"].map((r) => (
              <Chip key={r} label={r} size="small" sx={{ fontSize: "0.7rem", bgcolor: "action.disabledBackground", color: "text.secondary" }} />
            ))}
          </Box>
        </FieldRow>
      </Section>

      <Box sx={{ display: "flex", justifyContent: "flex-end" }}>
        <Button variant="contained" onClick={() => { setSavedMsg(true); setTimeout(() => setSavedMsg(false), 2000); }}>
          {savedMsg ? "Saved ✓" : "Save Changes"}
        </Button>
      </Box>
    </Box>
  );
}

function AuditPanel() {
  const events = [
    { actor: "alex@altavisor.io",   action: "Updated security policy",             ip: "203.0.113.5",  time: "Today, 14:22" },
    { actor: "maria@altavisor.io",  action: "Invited new user",                    ip: "198.51.100.2", time: "Today, 12:08" },
    { actor: "sam@altavisor.io",    action: "API key rotated",                     ip: "192.0.2.18",   time: "Today, 09:44" },
    { actor: "System",              action: "Auto-logout triggered (session timeout)", ip: "—",         time: "Yesterday, 23:01" },
    { actor: "jordan@altavisor.io", action: "Role changed: Viewer → Developer",    ip: "10.0.0.44",    time: "Yesterday, 17:30" },
    { actor: "alex@altavisor.io",   action: "SSO provider configured",             ip: "203.0.113.5",  time: "Mar 14, 10:15" },
  ];

  return (
    <Box>
      <Box sx={{ display: "flex", justifyContent: "space-between", alignItems: "center", mb: 2.5 }}>
        <Typography variant="subtitle2" sx={{ fontFamily: "'Syne', sans-serif", fontWeight: 700 }}>Audit Trail</Typography>
        <Button variant="outlined" size="small" sx={{ borderColor: "divider", color: "text.secondary", fontSize: "0.76rem" }}>Export Log</Button>
      </Box>
      <Paper sx={{ borderRadius: 2, overflow: "hidden" }}>
        <Box sx={{ px: 2.5, py: 1.2, display: "grid", gridTemplateColumns: "1.5fr 2fr 1fr 1.2fr", borderBottom: "1px solid", borderColor: "divider" }}>
          {["Actor", "Action", "IP Address", "Time"].map((h) => (
            <Typography key={h} variant="caption" sx={{ color: "text.secondary", fontWeight: 600, fontSize: "0.67rem", textTransform: "uppercase", letterSpacing: "0.07em" }}>{h}</Typography>
          ))}
        </Box>
        {events.map((e, i) => (
          <Box key={i} sx={{ px: 2.5, py: 1.4, display: "grid", gridTemplateColumns: "1.5fr 2fr 1fr 1.2fr", alignItems: "center", borderBottom: i < events.length - 1 ? "1px solid" : "none", borderColor: "divider", "&:hover": { bgcolor: "action.hover" } }}>
            <Box sx={{ display: "flex", alignItems: "center", gap: 0.8 }}>
              <PersonRoundedIcon sx={{ fontSize: 13, color: "text.secondary" }} />
              <Typography variant="caption" sx={{ fontWeight: 500, fontSize: "0.78rem" }}>{e.actor}</Typography>
            </Box>
            <Typography variant="caption" sx={{ color: "text.secondary" }}>{e.action}</Typography>
            <Typography variant="caption" sx={{ color: "text.secondary", fontFamily: "monospace", fontSize: "0.72rem" }}>{e.ip}</Typography>
            <Typography variant="caption" sx={{ color: "text.secondary" }}>{e.time}</Typography>
          </Box>
        ))}
      </Paper>
    </Box>
  );
}

function PoliciesPanel() {
  const [ipAllowlist, setIpAllowlist] = useState(false);
  const [bruteForce, setBruteForce]   = useState(true);
  const [geoBlock, setGeoBlock]       = useState(false);

  return (
    <Box>
      <Section title="Access Policies" description="Control how and from where users can access your workspace">
        <FieldRow label="IP Allowlist" hint="Restrict access to specific IP ranges">
          <Switch checked={ipAllowlist} onChange={(e) => setIpAllowlist(e.target.checked)} />
        </FieldRow>
        {ipAllowlist && (
          <FieldRow label="Allowed IPs / CIDRs" hint="One per line">
            <TextField multiline rows={3} size="small" placeholder={"203.0.113.0/24\n10.0.0.0/8"} fullWidth />
          </FieldRow>
        )}
        <FieldRow label="Brute-Force Protection" hint="Lock accounts after failed attempts">
          <Switch checked={bruteForce} onChange={(e) => setBruteForce(e.target.checked)} />
        </FieldRow>
        <FieldRow label="Geo-Blocking" hint="Block logins from specific countries">
          <Switch checked={geoBlock} onChange={(e) => setGeoBlock(e.target.checked)} />
        </FieldRow>
      </Section>
      <Section title="API Security" description="Protect API key access and rotation policies">
        <FieldRow label="Key Expiry (days)" hint="Auto-expire API keys after N days">
          <TextField type="number" size="small" defaultValue="90" sx={{ width: 100 }} />
        </FieldRow>
        <FieldRow label="Require Scopes" hint="Force explicit scopes on all new keys">
          <Switch defaultChecked />
        </FieldRow>
      </Section>
    </Box>
  );
}

export default function SecurityDashboard({ subTabId }: { subTabId: string }) {
  if (subTabId === "auth")  return <AuthPanel />;
  if (subTabId === "audit") return <AuditPanel />;
  return <PoliciesPanel />;
}

"use client";
import React, { useState } from "react";
import {
  Box, Typography, Paper, TextField, Switch, Select,
  MenuItem, FormControl, Button, Chip,
} from "@mui/material";
import SaveRoundedIcon from "@mui/icons-material/SaveRounded";

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

export default function SettingsPage() {
  const [defaultPlan, setDefaultPlan]       = useState("Starter");
  const [trialDays, setTrialDays]           = useState("14");
  const [autoEmail, setAutoEmail]           = useState(true);
  const [churnAlert, setChurnAlert]         = useState(true);
  const [churnThreshold, setChurnThreshold] = useState("30");
  const [webhookUrl, setWebhookUrl]         = useState("");
  const [saved, setSaved]                   = useState(false);

  return (
    <Box>
      <Section title="Onboarding" description="Defaults applied when a new customer is created">
        <FieldRow label="Default Plan" hint="Plan assigned on signup">
          <FormControl size="small" sx={{ minWidth: 160 }}>
            <Select value={defaultPlan} onChange={(e) => setDefaultPlan(e.target.value)}>
              <MenuItem value="Starter">Starter</MenuItem>
              <MenuItem value="Pro">Pro</MenuItem>
              <MenuItem value="Enterprise">Enterprise</MenuItem>
            </Select>
          </FormControl>
        </FieldRow>
        <FieldRow label="Trial Period (days)" hint="0 = no trial">
          <TextField type="number" size="small" value={trialDays} onChange={(e) => setTrialDays(e.target.value)} sx={{ width: 100 }} />
        </FieldRow>
        <FieldRow label="Welcome Email" hint="Send automatically on signup">
          <Switch checked={autoEmail} onChange={(e) => setAutoEmail(e.target.checked)} />
        </FieldRow>
      </Section>

      <Section title="Churn Detection" description="Get alerted when customers show risk signals">
        <FieldRow label="Enable Alerts">
          <Switch checked={churnAlert} onChange={(e) => setChurnAlert(e.target.checked)} />
        </FieldRow>
        {churnAlert && (
          <FieldRow label="Inactivity Threshold (days)" hint="Alert if no login after N days">
            <TextField type="number" size="small" value={churnThreshold} onChange={(e) => setChurnThreshold(e.target.value)} sx={{ width: 100 }} />
          </FieldRow>
        )}
      </Section>

      <Section title="Webhooks" description="POST customer events to your own endpoints">
        <FieldRow label="Webhook URL" hint="Receives customer.created, customer.updated, customer.churned">
          <TextField size="small" fullWidth placeholder="https://your-app.com/webhooks/customers" value={webhookUrl} onChange={(e) => setWebhookUrl(e.target.value)} />
        </FieldRow>
        <FieldRow label="Events">
          <Box sx={{ display: "flex", gap: 0.8, flexWrap: "wrap" }}>
            {["customer.created", "customer.updated", "customer.churned", "plan.changed"].map((ev) => (
              <Chip key={ev} label={ev} size="small" sx={{ fontFamily: "monospace", fontSize: "0.68rem", bgcolor: "action.disabledBackground", color: "text.secondary" }} />
            ))}
          </Box>
        </FieldRow>
      </Section>

      <Box sx={{ display: "flex", justifyContent: "flex-end" }}>
        <Button
          variant="contained"
          startIcon={<SaveRoundedIcon />}
          onClick={() => { setSaved(true); setTimeout(() => setSaved(false), 2000); }}
        >
          {saved ? "Saved ✓" : "Save Changes"}
        </Button>
      </Box>
    </Box>
  );
}

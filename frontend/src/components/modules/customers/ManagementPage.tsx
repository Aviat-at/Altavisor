"use client";
import React, { useState } from "react";
import {
  Box, Typography, Paper, TextField, InputAdornment,
  Button, Chip, MenuItem, Select, FormControl, Avatar,
  Dialog, DialogTitle, DialogContent, DialogActions,
  IconButton, Divider, Alert,
} from "@mui/material";
import { useTheme } from "@mui/material/styles";
import SearchRoundedIcon   from "@mui/icons-material/SearchRounded";
import PersonAddRoundedIcon from "@mui/icons-material/PersonAddRounded";
import CloseRoundedIcon    from "@mui/icons-material/CloseRounded";

type Plan   = "Enterprise" | "Pro" | "Starter";
type Status = "Active" | "Inactive" | "Churned";

interface Customer {
  id: string; name: string; email: string;
  plan: Plan; status: Status; joined: string; spend: string;
}

const SEED: Customer[] = [
  { id: "C-001", name: "Sarah Kim",     email: "sarah@example.com",  plan: "Pro",        status: "Active",   joined: "Jan 12, 2026", spend: "$1,240" },
  { id: "C-002", name: "James Okafor", email: "james@example.com",  plan: "Starter",    status: "Active",   joined: "Jan 18, 2026", spend: "$180"   },
  { id: "C-003", name: "Priya Nair",   email: "priya@example.com",  plan: "Enterprise", status: "Active",   joined: "Feb 2, 2026",  spend: "$4,800" },
  { id: "C-004", name: "Tom Walsh",    email: "tom@example.com",    plan: "Starter",    status: "Inactive", joined: "Feb 5, 2026",  spend: "$90"    },
  { id: "C-005", name: "Elena Popescu",email: "elena@example.com",  plan: "Pro",        status: "Active",   joined: "Feb 14, 2026", spend: "$960"   },
  { id: "C-006", name: "Marcus Lee",   email: "marcus@example.com", plan: "Enterprise", status: "Active",   joined: "Feb 20, 2026", spend: "$5,200" },
  { id: "C-007", name: "Amara Diallo", email: "amara@example.com",  plan: "Pro",        status: "Active",   joined: "Mar 1, 2026",  spend: "$720"   },
  { id: "C-008", name: "Raj Patel",    email: "raj@example.com",    plan: "Starter",    status: "Churned",  joined: "Mar 3, 2026",  spend: "$60"    },
];

const blank = () => ({ name: "", email: "", plan: "Starter" as Plan, status: "Active" as Status, spend: "" });

const FieldLabel = ({ children }: { children: React.ReactNode }) => (
  <Typography variant="caption" sx={{ color: "text.secondary", fontWeight: 500, mb: 0.75, display: "block", letterSpacing: "0.04em", textTransform: "uppercase", fontSize: "0.67rem" }}>
    {children}
  </Typography>
);

export default function ManagementPage() {
  const theme = useTheme();

  const [customers, setCustomers] = useState<Customer[]>(SEED);
  const [search,    setSearch]    = useState("");
  const [planFilter, setPlan]     = useState("All");
  const [open,   setOpen]         = useState(false);
  const [form,   setForm]         = useState(blank());
  const [errors, setErrors]       = useState<Partial<typeof form>>({});

  const planColor = (p: string) =>
    p === "Enterprise" ? { bg: "rgba(74,160,240,0.10)", color: theme.palette.info.main     }
    : p === "Pro"      ? { bg: "action.selected",       color: theme.palette.primary.main  }
    :                    { bg: "action.disabledBackground", color: theme.palette.text.secondary };

  const statusColor = (s: string) =>
    s === "Active"   ? { bg: "action.selected",       color: theme.palette.primary.main   }
    : s === "Inactive" ? { bg: "action.disabledBackground", color: theme.palette.text.secondary }
    :                    { bg: "rgba(240,74,74,0.10)", color: theme.palette.error.main     };

  const filtered = customers.filter((c) => {
    const matchSearch = !search || c.name.toLowerCase().includes(search.toLowerCase()) || c.email.includes(search);
    const matchPlan   = planFilter === "All" || c.plan === planFilter;
    return matchSearch && matchPlan;
  });

  const handleOpen  = () => { setForm(blank()); setErrors({}); setOpen(true); };
  const handleClose = () => setOpen(false);

  const validate = () => {
    const e: Partial<typeof form> = {};
    if (!form.name.trim())  e.name  = "Full name is required.";
    if (!form.email.trim()) e.email = "Email is required.";
    else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(form.email)) e.email = "Enter a valid email address.";
    else if (customers.some((c) => c.email === form.email.trim())) e.email = "A customer with this email already exists.";
    return e;
  };

  const handleSubmit = () => {
    const e = validate();
    if (Object.keys(e).length) { setErrors(e); return; }
    const nextId = `C-${String(customers.length + 1).padStart(3, "0")}`;
    const today  = new Date().toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric" });
    const spend  = form.spend.trim() ? (form.spend.startsWith("$") ? form.spend : `$${form.spend}`) : "$0";
    setCustomers((prev) => [...prev, { id: nextId, name: form.name.trim(), email: form.email.trim(), plan: form.plan, status: form.status, joined: today, spend }]);
    handleClose();
  };

  const set = (field: keyof typeof form) => (e: React.ChangeEvent<HTMLInputElement | { value: unknown }>) => {
    setForm((prev) => ({ ...prev, [field]: (e.target as HTMLInputElement).value }));
    setErrors((prev) => ({ ...prev, [field]: undefined }));
  };

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
          <Select value={planFilter} onChange={(e) => setPlan(e.target.value)} sx={{ fontSize: "0.8rem", minWidth: 130 }}>
            <MenuItem value="All">All plans</MenuItem>
            <MenuItem value="Enterprise">Enterprise</MenuItem>
            <MenuItem value="Pro">Pro</MenuItem>
            <MenuItem value="Starter">Starter</MenuItem>
          </Select>
        </FormControl>
        <Box sx={{ flex: 1 }} />
        <Button size="small" variant="contained" startIcon={<PersonAddRoundedIcon sx={{ fontSize: "14px !important" }} />} onClick={handleOpen} sx={{ fontSize: "0.78rem" }}>
          Add Customer
        </Button>
      </Box>

      {/* Table */}
      <Paper sx={{ borderRadius: 2, overflow: "hidden" }}>
        <Box sx={{ px: 2.5, py: 1.2, display: "grid", gridTemplateColumns: "50px 2fr 2fr 110px 100px 120px 90px", borderBottom: "1px solid", borderColor: "divider" }}>
          {["ID", "Name", "Email", "Plan", "Status", "Joined", "Spend"].map((h) => (
            <Typography key={h} variant="caption" sx={{ color: "text.secondary", fontWeight: 600, fontSize: "0.67rem", textTransform: "uppercase", letterSpacing: "0.07em" }}>
              {h}
            </Typography>
          ))}
        </Box>
        {filtered.length === 0 ? (
          <Box sx={{ py: 4, textAlign: "center" }}>
            <Typography variant="body2" sx={{ color: "text.secondary" }}>No customers match your filters.</Typography>
          </Box>
        ) : filtered.map((c, i) => {
          const pc = planColor(c.plan);
          const sc = statusColor(c.status);
          return (
            <Box key={c.id} sx={{ px: 2.5, py: 1.4, display: "grid", gridTemplateColumns: "50px 2fr 2fr 110px 100px 120px 90px", alignItems: "center", borderBottom: i < filtered.length - 1 ? "1px solid" : "none", borderColor: "divider", "&:hover": { bgcolor: "action.hover", cursor: "pointer" } }}>
              <Typography variant="caption" sx={{ color: "text.secondary", fontFamily: "monospace", fontSize: "0.7rem" }}>{c.id}</Typography>
              <Box sx={{ display: "flex", alignItems: "center", gap: 1 }}>
                <Avatar sx={{ width: 26, height: 26, fontSize: "0.6rem", fontWeight: 700, bgcolor: "action.selected", color: "primary.main", fontFamily: "'Syne', sans-serif" }}>
                  {c.name.split(" ").map(n => n[0]).join("")}
                </Avatar>
                <Typography variant="body2" sx={{ fontWeight: 500, fontSize: "0.8rem" }}>{c.name}</Typography>
              </Box>
              <Typography variant="caption" sx={{ color: "text.secondary", fontSize: "0.78rem" }}>{c.email}</Typography>
              <Chip label={c.plan}   size="small" sx={{ fontSize: "0.67rem", height: 18, width: "fit-content", bgcolor: pc.bg, color: pc.color }} />
              <Chip label={c.status} size="small" sx={{ fontSize: "0.67rem", height: 18, width: "fit-content", bgcolor: sc.bg, color: sc.color }} />
              <Typography variant="caption" sx={{ color: "text.secondary" }}>{c.joined}</Typography>
              <Typography variant="caption" sx={{ fontWeight: 600, fontSize: "0.8rem" }}>{c.spend}</Typography>
            </Box>
          );
        })}
      </Paper>

      <Box sx={{ mt: 1.5 }}>
        <Typography variant="caption" sx={{ color: "text.secondary" }}>
          Showing {filtered.length} of {customers.length} customers
        </Typography>
      </Box>

      {/* Add Customer Dialog */}
      <Dialog open={open} onClose={handleClose} maxWidth="sm" fullWidth PaperProps={{ sx: { borderRadius: "12px" } }}>
        <DialogTitle sx={{ p: 0 }}>
          <Box sx={{ display: "flex", alignItems: "center", justifyContent: "space-between", px: 3, pt: 2.5, pb: 2 }}>
            <Box>
              <Typography variant="h6" sx={{ fontFamily: "'Syne', sans-serif", fontWeight: 700, fontSize: "1rem" }}>
                Add Customer
              </Typography>
              <Typography variant="caption" sx={{ color: "text.secondary" }}>
                Create a new customer record in the system.
              </Typography>
            </Box>
            <IconButton size="small" onClick={handleClose} sx={{ color: "text.secondary", "&:hover": { color: "text.primary", bgcolor: "action.hover" } }}>
              <CloseRoundedIcon sx={{ fontSize: 18 }} />
            </IconButton>
          </Box>
          <Divider />
        </DialogTitle>

        <DialogContent sx={{ px: 3, pt: 2.5, pb: 1 }}>
          <Box sx={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 2.5 }}>
            <Box sx={{ gridColumn: "1 / -1" }}>
              <FieldLabel>Full Name *</FieldLabel>
              <TextField fullWidth size="small" placeholder="e.g. Sarah Kim" value={form.name} onChange={set("name")} error={!!errors.name} helperText={errors.name} autoFocus />
            </Box>
            <Box sx={{ gridColumn: "1 / -1" }}>
              <FieldLabel>Email Address *</FieldLabel>
              <TextField fullWidth size="small" placeholder="customer@company.com" type="email" value={form.email} onChange={set("email")} error={!!errors.email} helperText={errors.email} />
            </Box>
            <Box>
              <FieldLabel>Plan</FieldLabel>
              <FormControl fullWidth size="small">
                <Select value={form.plan} onChange={(e) => { setForm((p) => ({ ...p, plan: e.target.value as Plan })); }}>
                  <MenuItem value="Starter">Starter</MenuItem>
                  <MenuItem value="Pro">Pro</MenuItem>
                  <MenuItem value="Enterprise">Enterprise</MenuItem>
                </Select>
              </FormControl>
            </Box>
            <Box>
              <FieldLabel>Status</FieldLabel>
              <FormControl fullWidth size="small">
                <Select value={form.status} onChange={(e) => { setForm((p) => ({ ...p, status: e.target.value as Status })); }}>
                  <MenuItem value="Active">Active</MenuItem>
                  <MenuItem value="Inactive">Inactive</MenuItem>
                  <MenuItem value="Churned">Churned</MenuItem>
                </Select>
              </FormControl>
            </Box>
            <Box sx={{ gridColumn: "1 / -1" }}>
              <FieldLabel>Initial Spend</FieldLabel>
              <TextField fullWidth size="small" placeholder="e.g. 1200  ($ prefix is optional)" value={form.spend} onChange={set("spend")} />
            </Box>
          </Box>
        </DialogContent>

        <DialogActions sx={{ px: 3, py: 2.5 }}>
          <Button onClick={handleClose} sx={{ color: "text.secondary", fontSize: "0.8rem", "&:hover": { bgcolor: "action.hover", color: "text.primary" } }}>
            Cancel
          </Button>
          <Button variant="contained" onClick={handleSubmit} sx={{ fontSize: "0.8rem", px: 2.5 }}>
            Add Customer
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
}

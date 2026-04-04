"use client";
import React, { useCallback, useEffect, useState } from "react";
import {
  Alert, Avatar, Box, Button, Chip, CircularProgress, Dialog,
  DialogActions, DialogContent, DialogTitle, Divider, FormControl,
  IconButton, InputAdornment, MenuItem, Paper, Select, TextField,
  Typography,
} from "@mui/material";
import { useTheme } from "@mui/material/styles";
import AddRoundedIcon      from "@mui/icons-material/AddRounded";
import CloseRoundedIcon    from "@mui/icons-material/CloseRounded";
import SearchRoundedIcon   from "@mui/icons-material/SearchRounded";
import NavigateBeforeRoundedIcon from "@mui/icons-material/NavigateBeforeRounded";
import NavigateNextRoundedIcon   from "@mui/icons-material/NavigateNextRounded";
import WarningAmberRoundedIcon   from "@mui/icons-material/WarningAmberRounded";

import * as api from "./api";
import type { ApiError, DuplicateCandidate, PersonCategory, PersonListItem } from "./types";

const PAGE_SIZE = 50;

const GENDER_OPTIONS = [
  { value: "",  label: "Not specified" },
  { value: "M", label: "Male"          },
  { value: "F", label: "Female"        },
  { value: "O", label: "Other"         },
  { value: "N", label: "Prefer not to say" },
];

const blankForm = () => ({
  first_name: "", last_name: "", preferred_name: "",
  email: "", phone: "", mobile: "", gender: "",
});

const FieldLabel = ({ children }: { children: React.ReactNode }) => (
  <Typography variant="caption" sx={{
    color: "text.secondary", fontWeight: 500, mb: 0.75, display: "block",
    letterSpacing: "0.04em", textTransform: "uppercase", fontSize: "0.67rem",
  }}>
    {children}
  </Typography>
);

interface Props {
  onSelectPerson: (id: number) => void;
}

export default function DirectoryPage({ onSelectPerson }: Props) {
  const theme = useTheme();

  // ── Data state ──────────────────────────────────────────────────────────────
  const [persons,    setPersons]    = useState<PersonListItem[]>([]);
  const [categories, setCategories] = useState<PersonCategory[]>([]);
  const [count,      setCount]      = useState(0);
  const [hasNext,    setHasNext]    = useState(false);
  const [loading,    setLoading]    = useState(true);
  const [loadErr,    setLoadErr]    = useState<string | null>(null);

  // ── Filter / pagination state ───────────────────────────────────────────────
  const [searchInput,    setSearchInput]    = useState("");
  const [search,         setSearch]         = useState("");
  const [categoryFilter, setCategoryFilter] = useState<number | "">("");
  const [showInactive,   setShowInactive]   = useState(false);
  const [page,           setPage]           = useState(1);

  // ── Add person dialog state ─────────────────────────────────────────────────
  const [dialogOpen,          setDialogOpen]          = useState(false);
  const [form,                setForm]                = useState(blankForm());
  const [formErrors,          setFormErrors]          = useState<Partial<typeof form>>({});
  const [submitting,          setSubmitting]          = useState(false);
  const [submitError,         setSubmitError]         = useState<string | null>(null);
  const [duplicateCandidates, setDuplicateCandidates] = useState<DuplicateCandidate[]>([]);
  const [duplicateStep,       setDuplicateStep]       = useState(false);

  // ── Debounce search input ───────────────────────────────────────────────────
  useEffect(() => {
    const t = setTimeout(() => { setSearch(searchInput); setPage(1); }, 400);
    return () => clearTimeout(t);
  }, [searchInput]);

  // ── Load categories (for filter dropdown) ──────────────────────────────────
  useEffect(() => {
    api.listCategories({ is_active: true })
      .then(setCategories)
      .catch(() => {});
  }, []);

  // ── Load persons ────────────────────────────────────────────────────────────
  const loadPersons = useCallback(() => {
    let cancelled = false;
    setLoading(true);
    setLoadErr(null);
    api.listPersons({
      search:      search || undefined,
      category_id: categoryFilter || undefined,
      is_active:   showInactive ? undefined : true,
      page,
      page_size: PAGE_SIZE,
    })
      .then((data) => {
        if (cancelled) return;
        setPersons(data.results);
        setCount(data.count);
        setHasNext(data.has_next);
      })
      .catch(() => {
        if (!cancelled) setLoadErr("Failed to load people. Check your connection.");
      })
      .finally(() => { if (!cancelled) setLoading(false); });
    return () => { cancelled = true; };
  }, [search, categoryFilter, showInactive, page]);

  useEffect(() => { return loadPersons(); }, [loadPersons]);

  // ── Dialog helpers ──────────────────────────────────────────────────────────
  const handleOpen = () => {
    setForm(blankForm());
    setFormErrors({});
    setSubmitError(null);
    setDuplicateCandidates([]);
    setDuplicateStep(false);
    setDialogOpen(true);
  };

  const handleClose = () => {
    if (submitting) return;
    setDialogOpen(false);
  };

  const setField = (field: keyof typeof form) =>
    (e: React.ChangeEvent<HTMLInputElement>) => {
      setForm((prev) => ({ ...prev, [field]: e.target.value }));
      setFormErrors((prev) => ({ ...prev, [field]: undefined }));
    };

  const validate = (): Partial<typeof form> => {
    const e: Partial<typeof form> = {};
    if (!form.first_name.trim()) e.first_name = "First name is required.";
    if (!form.last_name.trim())  e.last_name  = "Last name is required.";
    return e;
  };

  const handleSubmit = async (force = false) => {
    if (!force) {
      const e = validate();
      if (Object.keys(e).length) { setFormErrors(e); return; }
    }

    setSubmitting(true);
    setSubmitError(null);

    try {
      await api.createPerson({
        first_name:     form.first_name.trim(),
        last_name:      form.last_name.trim(),
        preferred_name: form.preferred_name.trim(),
        email:          form.email.trim() || null,
        phone:          form.phone.trim(),
        mobile:         form.mobile.trim(),
        gender:         form.gender,
        force,
      });
      setDialogOpen(false);
      loadPersons();
    } catch (err) {
      const apiErr = err as ApiError;
      if (apiErr.status === 409 && apiErr.body?.code === "duplicate_detected") {
        setDuplicateCandidates((apiErr.body.candidates ?? []) as DuplicateCandidate[]);
        setDuplicateStep(true);
      } else if (apiErr.status === 400) {
        const e: Partial<typeof form> = {};
        for (const [k, v] of Object.entries(apiErr.body ?? {})) {
          if (k in form) e[k as keyof typeof form] = Array.isArray(v) ? v[0] : String(v);
        }
        setFormErrors(e);
      } else {
        setSubmitError(apiErr.body?.detail ?? "Something went wrong. Please try again.");
      }
    } finally {
      setSubmitting(false);
    }
  };

  // ── Color helpers ────────────────────────────────────────────────────────────
  const statusChip = (active: boolean) =>
    active
      ? { bg: "action.selected", color: theme.palette.primary.main, label: "Active" }
      : { bg: "action.disabledBackground", color: theme.palette.text.secondary, label: "Inactive" };

  const categoryChip = {
    bg: "rgba(74,160,240,0.09)",
    color: theme.palette.info.main,
  };

  // ── Render ───────────────────────────────────────────────────────────────────
  return (
    <Box>
      {/* Toolbar */}
      <Box sx={{ display: "flex", gap: 1.5, mb: 2, alignItems: "center", flexWrap: "wrap" }}>
        <TextField
          placeholder="Search by name or email…"
          size="small"
          value={searchInput}
          onChange={(e) => setSearchInput(e.target.value)}
          InputProps={{
            startAdornment: (
              <InputAdornment position="start">
                <SearchRoundedIcon sx={{ fontSize: 15, color: "text.secondary" }} />
              </InputAdornment>
            ),
          }}
          sx={{ width: 260 }}
        />
        

        <FormControl size="small">
          <Select
            value={categoryFilter}
            onChange={(e) => { setCategoryFilter(e.target.value as number | ""); setPage(1); }}
            displayEmpty
            sx={{ fontSize: "0.8rem", minWidth: 150 }}
          >
            <MenuItem value="">All categories</MenuItem>
            {categories.map((c) => (
              <MenuItem key={c.id} value={c.id}>{c.name}</MenuItem>
            ))}
          </Select>
        </FormControl>

        <FormControl size="small">
          <Select
            value={showInactive ? "all" : "active"}
            onChange={(e) => { setShowInactive(e.target.value === "all"); setPage(1); }}
            sx={{ fontSize: "0.8rem", minWidth: 120 }}
          >
            <MenuItem value="active">Active only</MenuItem>
            <MenuItem value="all">All records</MenuItem>
          </Select>
        </FormControl>

        <Box sx={{ flex: 1 }} />

        <Button
          size="small"
          variant="contained"
          startIcon={<AddRoundedIcon sx={{ fontSize: "14px !important" }} />}
          onClick={handleOpen}
          sx={{ fontSize: "0.78rem" }}
        >
          Add Person
        </Button>
      </Box>

      {/* Error */}
      {loadErr && (
        <Alert severity="error" sx={{ mb: 2, borderRadius: 2, fontSize: "0.8rem" }}>
          {loadErr}
        </Alert>
      )}

      {/* Table */}
      <Paper sx={{ borderRadius: 2, overflow: "hidden" }}>
        {/* Header */}
        <Box sx={{
          px: 2.5, py: 1.2,
          display: "grid",
          gridTemplateColumns: "2fr 2fr 1.2fr 140px 80px 110px",
          borderBottom: "1px solid", borderColor: "divider",
        }}>
          {["Name", "Email", "Phone", "Category", "Status", "Added"].map((h) => (
            <Typography key={h} variant="caption" sx={{
              color: "text.secondary", fontWeight: 600,
              fontSize: "0.67rem", textTransform: "uppercase", letterSpacing: "0.07em",
            }}>
              {h}
            </Typography>
          ))}
        </Box>

        {/* Loading */}
        {loading && (
          <Box sx={{ py: 5, display: "flex", justifyContent: "center" }}>
            <CircularProgress size={22} thickness={4} sx={{ color: "primary.main" }} />
          </Box>
        )}

        {/* Empty */}
        {!loading && persons.length === 0 && (
          <Box sx={{ py: 4, textAlign: "center" }}>
            <Typography variant="body2" sx={{ color: "text.secondary" }}>
              No people match your filters.
            </Typography>
          </Box>
        )}

        {/* Rows */}
        {!loading && persons.map((p, i) => {
          const sc = statusChip(p.is_active);
          const joined = new Date(p.created_at).toLocaleDateString("en-GB", {
            day: "numeric", month: "short", year: "numeric",
          });
          return (
            <Box
              key={p.id}
              onClick={() => onSelectPerson(p.id)}
              sx={{
                px: 2.5, py: 1.4,
                display: "grid",
                gridTemplateColumns: "2fr 2fr 1.2fr 140px 80px 110px",
                alignItems: "center",
                borderBottom: i < persons.length - 1 ? "1px solid" : "none",
                borderColor: "divider",
                cursor: "pointer",
                "&:hover": { bgcolor: "action.hover" },
              }}
            >
              {/* Name */}
              <Box sx={{ display: "flex", alignItems: "center", gap: 1 }}>
                <Avatar sx={{
                  width: 26, height: 26,
                  fontSize: "0.6rem", fontWeight: 700,
                  bgcolor: "action.selected", color: "primary.main",
                  fontFamily: "'Syne', sans-serif",
                }}>
                  {p.full_name.split(" ").map((n) => n[0]).join("").slice(0, 2)}
                </Avatar>
                <Typography variant="body2" sx={{ fontWeight: 500, fontSize: "0.8rem" }}>
                  {p.display_name}
                </Typography>
              </Box>

              {/* Email */}
              <Typography variant="caption" sx={{ color: "text.secondary", fontSize: "0.78rem" }}>
                {p.email ?? "—"}
              </Typography>

              {/* Phone */}
              <Typography variant="caption" sx={{ color: "text.secondary", fontSize: "0.78rem" }}>
                {p.phone || "—"}
              </Typography>

              {/* Category */}
              {p.primary_category ? (
                <Chip
                  label={p.primary_category}
                  size="small"
                  sx={{
                    fontSize: "0.67rem", height: 18, width: "fit-content",
                    bgcolor: categoryChip.bg, color: categoryChip.color,
                  }}
                />
              ) : (
                <Typography variant="caption" sx={{ color: "text.disabled", fontSize: "0.72rem" }}>
                  —
                </Typography>
              )}

              {/* Status */}
              <Chip
                label={sc.label}
                size="small"
                sx={{ fontSize: "0.67rem", height: 18, width: "fit-content", bgcolor: sc.bg, color: sc.color }}
              />

              {/* Created */}
              <Typography variant="caption" sx={{ color: "text.secondary" }}>
                {joined}
              </Typography>
            </Box>
          );
        })}
      </Paper>

      {/* Footer: count + pagination */}
      <Box sx={{ mt: 1.5, display: "flex", alignItems: "center", gap: 1 }}>
        <Typography variant="caption" sx={{ color: "text.secondary", flex: 1 }}>
          {loading ? "Loading…" : `${count} ${count === 1 ? "person" : "people"} found`}
          {!loading && persons.length > 0 && " · click a row to select"}
        </Typography>

        {(page > 1 || hasNext) && (
          <Box sx={{ display: "flex", alignItems: "center", gap: 0.5 }}>
            <IconButton
              size="small"
              disabled={page <= 1 || loading}
              onClick={() => setPage((p) => p - 1)}
              sx={{ color: "text.secondary" }}
            >
              <NavigateBeforeRoundedIcon sx={{ fontSize: 18 }} />
            </IconButton>
            <Typography variant="caption" sx={{ color: "text.secondary", minWidth: 40, textAlign: "center" }}>
              {page}
            </Typography>
            <IconButton
              size="small"
              disabled={!hasNext || loading}
              onClick={() => setPage((p) => p + 1)}
              sx={{ color: "text.secondary" }}
            >
              <NavigateNextRoundedIcon sx={{ fontSize: 18 }} />
            </IconButton>
          </Box>
        )}
      </Box>

      {/* ── Add Person Dialog ──────────────────────────────────────────────── */}
      <Dialog
        open={dialogOpen}
        onClose={handleClose}
        maxWidth="sm"
        fullWidth
        PaperProps={{ sx: { borderRadius: "12px" } }}
      >
        <DialogTitle sx={{ p: 0 }}>
          <Box sx={{
            display: "flex", alignItems: "center", justifyContent: "space-between",
            px: 3, pt: 2.5, pb: 2,
          }}>
            <Box>
              <Typography variant="h6" sx={{
                fontFamily: "'Syne', sans-serif", fontWeight: 700, fontSize: "1rem",
              }}>
                {duplicateStep ? "Possible Duplicates Found" : "Add Person"}
              </Typography>
              <Typography variant="caption" sx={{ color: "text.secondary" }}>
                {duplicateStep
                  ? "Review the existing records below before proceeding."
                  : "Create a new person record in the directory."}
              </Typography>
            </Box>
            <IconButton
              size="small"
              onClick={handleClose}
              disabled={submitting}
              sx={{ color: "text.secondary", "&:hover": { color: "text.primary", bgcolor: "action.hover" } }}
            >
              <CloseRoundedIcon sx={{ fontSize: 18 }} />
            </IconButton>
          </Box>
          <Divider />
        </DialogTitle>

        <DialogContent sx={{ px: 3, pt: 2.5, pb: 1 }}>

          {/* ── Step 1: Form ─────────────────────────────────────────── */}
          {!duplicateStep && (
            <Box sx={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 2.5 }}>
              <Box>
                <FieldLabel>First Name *</FieldLabel>
                <TextField
                  fullWidth size="small" autoFocus
                  placeholder="e.g. Alice"
                  value={form.first_name}
                  onChange={setField("first_name")}
                  error={!!formErrors.first_name}
                  helperText={formErrors.first_name}
                />
              </Box>
              <Box>
                <FieldLabel>Last Name *</FieldLabel>
                <TextField
                  fullWidth size="small"
                  placeholder="e.g. Smith"
                  value={form.last_name}
                  onChange={setField("last_name")}
                  error={!!formErrors.last_name}
                  helperText={formErrors.last_name}
                />
              </Box>
              <Box sx={{ gridColumn: "1 / -1" }}>
                <FieldLabel>Preferred Name</FieldLabel>
                <TextField
                  fullWidth size="small"
                  placeholder="Display name override (optional)"
                  value={form.preferred_name}
                  onChange={setField("preferred_name")}
                />
              </Box>
              <Box sx={{ gridColumn: "1 / -1" }}>
                <FieldLabel>Email</FieldLabel>
                <TextField
                  fullWidth size="small" type="email"
                  placeholder="alice@example.com"
                  value={form.email}
                  onChange={setField("email")}
                  error={!!formErrors.email}
                  helperText={formErrors.email}
                />
              </Box>
              <Box>
                <FieldLabel>Phone</FieldLabel>
                <TextField
                  fullWidth size="small"
                  placeholder="+44 20 7946 0958"
                  value={form.phone}
                  onChange={setField("phone")}
                />
              </Box>
              <Box>
                <FieldLabel>Mobile</FieldLabel>
                <TextField
                  fullWidth size="small"
                  placeholder="+44 7700 900000"
                  value={form.mobile}
                  onChange={setField("mobile")}
                />
              </Box>
              <Box>
                <FieldLabel>Gender</FieldLabel>
                <FormControl fullWidth size="small">
                  <Select
                    value={form.gender}
                    onChange={(e) => setForm((p) => ({ ...p, gender: e.target.value }))}
                  >
                    {GENDER_OPTIONS.map((o) => (
                      <MenuItem key={o.value} value={o.value}>{o.label}</MenuItem>
                    ))}
                  </Select>
                </FormControl>
              </Box>
            </Box>
          )}

          {/* ── Step 2: Duplicate warning ─────────────────────────────── */}
          {duplicateStep && (
            <Box>
              <Alert
                severity="warning"
                icon={<WarningAmberRoundedIcon fontSize="small" />}
                sx={{ mb: 2, borderRadius: 1.5, fontSize: "0.8rem" }}
              >
                The following existing records are similar to the person you are
                creating. You can still proceed — set <strong>Create Anyway</strong> to
                confirm this is a different person.
              </Alert>

              {duplicateCandidates.map((c) => (
                <Box
                  key={c.id}
                  sx={{
                    display: "flex", alignItems: "center", gap: 1.5,
                    py: 1.5, borderBottom: "1px solid", borderColor: "divider",
                    "&:last-child": { borderBottom: "none" },
                  }}
                >
                  <Avatar sx={{
                    width: 30, height: 30, fontSize: "0.65rem", fontWeight: 700,
                    bgcolor: "rgba(240,184,74,0.12)", color: "#F0B84A",
                    fontFamily: "'Syne', sans-serif",
                  }}>
                    {c.full_name.split(" ").map((n) => n[0]).join("").slice(0, 2)}
                  </Avatar>
                  <Box sx={{ flex: 1 }}>
                    <Typography variant="body2" sx={{ fontWeight: 500, fontSize: "0.82rem" }}>
                      {c.full_name}
                    </Typography>
                    <Typography variant="caption" sx={{ color: "text.secondary", fontSize: "0.72rem" }}>
                      {[c.email, c.phone].filter(Boolean).join(" · ") || "No contact details"}
                    </Typography>
                  </Box>
                </Box>
              ))}
            </Box>
          )}

          {submitError && (
            <Alert severity="error" sx={{ mt: 2, borderRadius: 1.5, fontSize: "0.8rem" }}>
              {submitError}
            </Alert>
          )}
        </DialogContent>

        <DialogActions sx={{ px: 3, py: 2.5 }}>
          {duplicateStep ? (
            <>
              <Button
                onClick={() => setDuplicateStep(false)}
                disabled={submitting}
                sx={{ color: "text.secondary", fontSize: "0.8rem", "&:hover": { bgcolor: "action.hover", color: "text.primary" } }}
              >
                Back
              </Button>
              <Button
                variant="contained"
                onClick={() => handleSubmit(true)}
                disabled={submitting}
                sx={{ fontSize: "0.8rem", px: 2.5 }}
              >
                {submitting ? "Creating…" : "Create Anyway"}
              </Button>
            </>
          ) : (
            <>
              <Button
                onClick={handleClose}
                disabled={submitting}
                sx={{ color: "text.secondary", fontSize: "0.8rem", "&:hover": { bgcolor: "action.hover", color: "text.primary" } }}
              >
                Cancel
              </Button>
              <Button
                variant="contained"
                onClick={() => handleSubmit(false)}
                disabled={submitting}
                sx={{ fontSize: "0.8rem", px: 2.5 }}
              >
                {submitting ? "Checking…" : "Add Person"}
              </Button>
            </>
          )}
        </DialogActions>
      </Dialog>
    </Box>
  );
}

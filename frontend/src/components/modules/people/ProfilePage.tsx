"use client";
import React, { useCallback, useEffect, useState } from "react";
import {
  Alert, Avatar, Box, Button, Chip, CircularProgress, Dialog,
  DialogActions, DialogContent, DialogTitle, Divider, FormControl,
  Grid, IconButton, MenuItem, Paper, Select, Tab, Tabs, TextField,
  Typography,
} from "@mui/material";
import { useTheme } from "@mui/material/styles";
import AddRoundedIcon          from "@mui/icons-material/AddRounded";
import CloseRoundedIcon        from "@mui/icons-material/CloseRounded";
import EditRoundedIcon         from "@mui/icons-material/EditRounded";
import PersonOffRoundedIcon    from "@mui/icons-material/PersonOffRounded";
import LockRoundedIcon         from "@mui/icons-material/LockRounded";
import NoteAddRoundedIcon      from "@mui/icons-material/NoteAddRounded";
import BusinessRoundedIcon     from "@mui/icons-material/BusinessRounded";
import WarningAmberRoundedIcon from "@mui/icons-material/WarningAmberRounded";
import HomeRoundedIcon         from "@mui/icons-material/HomeRounded";
import WorkRoundedIcon         from "@mui/icons-material/WorkRounded";
import LocationOnRoundedIcon   from "@mui/icons-material/LocationOnRounded";

import * as api from "./api";
import type {
  ApiError, DuplicateCandidate, OrganizationPersonRelation,
  PersonAddress, PersonCategory, PersonDetail,
} from "./types";

// ── Helpers ───────────────────────────────────────────────────────────────────

const GENDER_OPTIONS = [
  { value: "",  label: "Not specified"    },
  { value: "M", label: "Male"             },
  { value: "F", label: "Female"           },
  { value: "O", label: "Other"            },
  { value: "N", label: "Prefer not to say"},
];

const ADDRESS_LABELS = [
  { value: "home",     label: "Home"     },
  { value: "work",     label: "Work"     },
  { value: "billing",  label: "Billing"  },
  { value: "delivery", label: "Delivery" },
  { value: "other",    label: "Other"    },
];

const FieldLabel = ({ children }: { children: React.ReactNode }) => (
  <Typography variant="caption" sx={{
    color: "text.secondary", fontWeight: 500, mb: 0.75, display: "block",
    letterSpacing: "0.04em", textTransform: "uppercase", fontSize: "0.67rem",
  }}>
    {children}
  </Typography>
);

function SectionLabel({ children }: { children: React.ReactNode }) {
  return (
    <Typography variant="caption" sx={{
      color: "text.secondary", fontWeight: 600, fontSize: "0.68rem",
      textTransform: "uppercase", letterSpacing: "0.07em",
    }}>
      {children}
    </Typography>
  );
}

function addressLabelIcon(label: string) {
  if (label === "work")    return <WorkRoundedIcon sx={{ fontSize: 13 }} />;
  if (label === "billing") return <BusinessRoundedIcon sx={{ fontSize: 13 }} />;
  if (label === "home")    return <HomeRoundedIcon sx={{ fontSize: 13 }} />;
  return <LocationOnRoundedIcon sx={{ fontSize: 13 }} />;
}

function fmt(d: string | null) {
  if (!d) return "—";
  return new Date(d).toLocaleDateString("en-GB", { day: "numeric", month: "short", year: "numeric" });
}

// ── Empty state ───────────────────────────────────────────────────────────────

function EmptyState() {
  return (
    <Box sx={{ display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", height: 300 }}>
      <PersonOffRoundedIcon sx={{ fontSize: 36, color: "text.disabled", mb: 1.5 }} />
      <Typography variant="subtitle2" sx={{ color: "text.secondary", fontFamily: "'Syne', sans-serif" }}>
        No person selected
      </Typography>
      <Typography variant="caption" sx={{ color: "text.disabled", mt: 0.5 }}>
        Click a row in the Directory tab to select a person.
      </Typography>
    </Box>
  );
}

// ── Props ─────────────────────────────────────────────────────────────────────

interface Props {
  personId: number | null;
}

// ── Component ─────────────────────────────────────────────────────────────────

export default function ProfilePage({ personId }: Props) {
  const theme = useTheme();

  const [person,       setPerson]       = useState<PersonDetail | null>(null);
  const [loading,      setLoading]      = useState(false);
  const [loadErr,      setLoadErr]      = useState<string | null>(null);
  const [innerTab,     setInnerTab]     = useState("overview");
  const [categories,   setCategories]   = useState<PersonCategory[]>([]);

  // Edit person dialog
  const [editOpen,     setEditOpen]     = useState(false);
  const [editForm,     setEditForm]     = useState<Record<string, string>>({});
  const [editErrors,   setEditErrors]   = useState<Record<string, string>>({});
  const [editSaving,   setEditSaving]   = useState(false);
  const [editErr,      setEditErr]      = useState<string | null>(null);
  const [editDupStep,  setEditDupStep]  = useState(false);
  const [editDupCands, setEditDupCands] = useState<DuplicateCandidate[]>([]);

  // Deactivate confirm
  const [deactivating, setDeactivating] = useState(false);
  const [deactivateErr, setDeactivateErr] = useState<string | null>(null);

  // Note
  const [noteBody,     setNoteBody]     = useState("");
  const [noteSaving,   setNoteSaving]   = useState(false);
  const [noteErr,      setNoteErr]      = useState<string | null>(null);

  // Address dialog
  const [addrOpen,     setAddrOpen]     = useState(false);
  const [addrEdit,     setAddrEdit]     = useState<PersonAddress | null>(null);
  const [addrForm,     setAddrForm]     = useState<Record<string, string | boolean>>({});
  const [addrErrors,   setAddrErrors]   = useState<Record<string, string>>({});
  const [addrSaving,   setAddrSaving]   = useState(false);
  const [addrErr,      setAddrErr]      = useState<string | null>(null);

  // Org link dialog
  const [orgOpen,      setOrgOpen]      = useState(false);
  const [orgForm,      setOrgForm]      = useState({ organization_id: "", organization_type: "", role: "", is_primary: false });
  const [orgErrors,    setOrgErrors]    = useState<Partial<typeof orgForm>>({});
  const [orgSaving,    setOrgSaving]    = useState(false);
  const [orgErr,       setOrgErr]       = useState<string | null>(null);

  // Assign category dialog
  const [assignOpen,   setAssignOpen]   = useState(false);
  const [assignCatId,  setAssignCatId]  = useState<number | "">("");
  const [assignSaving, setAssignSaving] = useState(false);
  const [assignErr,    setAssignErr]    = useState<string | null>(null);

  // ── Data loading ──────────────────────────────────────────────────────────

  const loadPerson = useCallback(() => {
    if (!personId) return;
    let cancelled = false;
    setLoading(true);
    setLoadErr(null);
    api.getPerson(personId)
      .then((data) => { if (!cancelled) setPerson(data); })
      .catch(() => { if (!cancelled) setLoadErr("Failed to load person details."); })
      .finally(() => { if (!cancelled) setLoading(false); });
    return () => { cancelled = true; };
  }, [personId]);

  useEffect(() => { return loadPerson(); }, [loadPerson]);

  useEffect(() => {
    api.listCategories({ is_active: true }).then(setCategories).catch(() => {});
  }, []);

  // ── Edit person ───────────────────────────────────────────────────────────

  const openEdit = () => {
    if (!person) return;
    setEditForm({
      first_name:     person.first_name,
      last_name:      person.last_name,
      preferred_name: person.preferred_name,
      email:          person.email ?? "",
      phone:          person.phone,
      mobile:         person.mobile,
      date_of_birth:  person.date_of_birth ?? "",
      gender:         person.gender,
    });
    setEditErrors({});
    setEditErr(null);
    setEditDupStep(false);
    setEditDupCands([]);
    setEditOpen(true);
  };

  const submitEdit = async (force = false) => {
    setEditSaving(true);
    setEditErr(null);
    try {
      await api.updatePerson(personId!, {
        ...editForm,
        email: editForm.email?.trim() || null,
        force,
      });
      setEditOpen(false);
      loadPerson();
    } catch (err) {
      const e = err as ApiError;
      if (e.status === 409 && e.body?.code === "duplicate_detected") {
        setEditDupCands((e.body.candidates ?? []) as DuplicateCandidate[]);
        setEditDupStep(true);
      } else if (e.status === 400) {
        const fe: Record<string, string> = {};
        for (const [k, v] of Object.entries(e.body ?? {})) {
          fe[k] = Array.isArray(v) ? v[0] : String(v);
        }
        setEditErrors(fe);
      } else {
        setEditErr(e.body?.detail ?? "Could not save changes.");
      }
    } finally {
      setEditSaving(false);
    }
  };

  // ── Deactivate ────────────────────────────────────────────────────────────

  const handleDeactivate = async () => {
    if (!person || !window.confirm(`Deactivate ${person.full_name}? This will also close all active org relations and category assignments.`)) return;
    setDeactivating(true);
    setDeactivateErr(null);
    try {
      await api.deactivatePerson(personId!);
      loadPerson();
    } catch (err) {
      setDeactivateErr((err as ApiError).body?.detail ?? "Could not deactivate.");
    } finally {
      setDeactivating(false);
    }
  };

  // ── Notes ─────────────────────────────────────────────────────────────────

  const submitNote = async () => {
    if (!noteBody.trim()) return;
    setNoteSaving(true);
    setNoteErr(null);
    try {
      await api.createNote(personId!, noteBody.trim());
      setNoteBody("");
      loadPerson();
    } catch (err) {
      setNoteErr((err as ApiError).body?.detail ?? "Could not add note.");
    } finally {
      setNoteSaving(false);
    }
  };

  // ── Addresses ─────────────────────────────────────────────────────────────

  const openAddressDialog = (addr: PersonAddress | null = null) => {
    setAddrEdit(addr);
    setAddrForm(addr ? {
      label: addr.label, line1: addr.line1, line2: addr.line2 ?? "",
      city: addr.city, state_province: addr.state_province ?? "",
      postal_code: addr.postal_code ?? "", country: addr.country,
      is_default: addr.is_default,
    } : {
      label: "home", line1: "", line2: "", city: "",
      state_province: "", postal_code: "", country: "", is_default: false,
    });
    setAddrErrors({});
    setAddrErr(null);
    setAddrOpen(true);
  };

  const submitAddress = async () => {
    const e: Record<string, string> = {};
    if (!String(addrForm.line1).trim()) e.line1 = "Address line 1 is required.";
    if (!String(addrForm.city).trim())  e.city  = "City is required.";
    if (!String(addrForm.country).trim()) e.country = "Country is required.";
    if (Object.keys(e).length) { setAddrErrors(e); return; }

    setAddrSaving(true);
    setAddrErr(null);
    try {
      if (addrEdit) {
        await api.updateAddress(personId!, addrEdit.id, addrForm);
      } else {
        await api.createAddress(personId!, addrForm);
      }
      loadPerson();
      setAddrOpen(false);
    } catch (err) {
      setAddrErr((err as ApiError).body?.detail ?? "Could not save address.");
    } finally {
      setAddrSaving(false);
    }
  };

  // ── Organizations ─────────────────────────────────────────────────────────

  const submitOrg = async () => {
    const e: Partial<typeof orgForm> = {};
    if (!orgForm.organization_id.trim()) e.organization_id = "Organisation ID is required.";
    if (!orgForm.organization_type.trim()) e.organization_type = "Type is required.";
    if (!orgForm.role.trim()) e.role = "Role is required.";
    if (Object.keys(e).length) { setOrgErrors(e as typeof orgErrors); return; }

    setOrgSaving(true);
    setOrgErr(null);
    try {
      await api.linkOrganization(personId!, {
        organization_id:   parseInt(orgForm.organization_id),
        organization_type: orgForm.organization_type.trim(),
        role:              orgForm.role.trim(),
        is_primary:        orgForm.is_primary,
      });
      loadPerson();
      setOrgOpen(false);
    } catch (err) {
      setOrgErr((err as ApiError).body?.detail ?? "Could not link organisation.");
    } finally {
      setOrgSaving(false);
    }
  };

  const handleCloseOrg = async (rel: OrganizationPersonRelation) => {
    if (!window.confirm(`Close the ${rel.role} relationship with ${rel.organization_type} #${rel.organization_id}?`)) return;
    try {
      await api.closeOrgRelation(personId!, rel.id);
      loadPerson();
    } catch {}
  };

  // ── Category assignment ───────────────────────────────────────────────────

  const submitAssign = async () => {
    if (!assignCatId) return;
    setAssignSaving(true);
    setAssignErr(null);
    try {
      await api.assignCategory(personId!, assignCatId as number);
      loadPerson();
      setAssignOpen(false);
      setAssignCatId("");
    } catch (err) {
      setAssignErr((err as ApiError).body?.detail ?? "Could not assign category.");
    } finally {
      setAssignSaving(false);
    }
  };

  const handleRemoveCategory = async (catId: number) => {
    try {
      await api.removeCategory(personId!, catId);
      loadPerson();
    } catch {}
  };

  // ── Render ────────────────────────────────────────────────────────────────

  if (!personId) return <EmptyState />;

  if (loading && !person) {
    return (
      <Box sx={{ display: "flex", justifyContent: "center", py: 6 }}>
        <CircularProgress size={24} thickness={4} sx={{ color: "primary.main" }} />
      </Box>
    );
  }

  if (loadErr || !person) {
    return (
      <Alert severity="error" sx={{ borderRadius: 2, fontSize: "0.8rem" }}>
        {loadErr ?? "Person not found."}
      </Alert>
    );
  }

  const isActive = person.is_active;
  const initials = person.initials || person.full_name.split(" ").map((n) => n[0]).join("").slice(0, 2);

  return (
    <Box>
      {deactivateErr && (
        <Alert severity="error" sx={{ mb: 2, borderRadius: 2, fontSize: "0.8rem" }}>
          {deactivateErr}
        </Alert>
      )}

      <Grid container spacing={2.5}>

        {/* ── Left: person card ──────────────────────────────────────────── */}
        <Grid item xs={12} md={4}>
          <Paper sx={{ borderRadius: 2, overflow: "hidden" }}>
            {/* Header */}
            <Box sx={{ p: 2.5, borderBottom: "1px solid", borderColor: "divider", display: "flex", alignItems: "center", gap: 1.5 }}>
              <Box sx={{
                width: 44, height: 44, borderRadius: "50%",
                bgcolor: isActive ? "action.selected" : "action.disabledBackground",
                display: "flex", alignItems: "center", justifyContent: "center", flexShrink: 0,
              }}>
                <Typography sx={{
                  fontSize: "0.82rem", fontWeight: 700,
                  color: isActive ? "primary.main" : "text.disabled",
                  fontFamily: "'Syne', sans-serif",
                }}>
                  {initials}
                </Typography>
              </Box>
              <Box sx={{ flex: 1, minWidth: 0 }}>
                <Typography variant="subtitle2" sx={{ fontFamily: "'Syne', sans-serif", fontWeight: 700, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
                  {person.display_name}
                </Typography>
                {person.preferred_name && person.preferred_name !== person.full_name && (
                  <Typography variant="caption" sx={{ color: "text.secondary", fontSize: "0.7rem" }}>
                    {person.full_name}
                  </Typography>
                )}
              </Box>
              <Chip
                label={isActive ? "Active" : "Inactive"}
                size="small"
                sx={{
                  fontSize: "0.67rem", height: 18,
                  bgcolor: isActive ? "action.selected" : "action.disabledBackground",
                  color: isActive ? "primary.main" : "text.secondary",
                  fontWeight: 600,
                }}
              />
            </Box>

            {/* Metadata rows */}
            <Box sx={{ p: 2.5 }}>
              {[
                { label: "ID",       value: `#${person.id}` },
                { label: "Email",    value: person.email ?? "—" },
                { label: "Phone",    value: person.phone  || "—" },
                { label: "Mobile",   value: person.mobile || "—" },
                { label: "DOB",      value: person.date_of_birth ? fmt(person.date_of_birth) : "—" },
                { label: "Gender",   value: person.gender_display || "—" },
                { label: "Added",    value: fmt(person.created_at) },
              ].map((row, i, arr) => (
                <Box key={row.label} sx={{
                  display: "flex", justifyContent: "space-between", py: 0.9,
                  borderBottom: i < arr.length - 1 ? "1px solid" : "none",
                  borderColor: "divider",
                }}>
                  <Typography variant="caption" sx={{ color: "text.secondary", fontSize: "0.75rem" }}>
                    {row.label}
                  </Typography>
                  <Typography variant="caption" sx={{ fontWeight: 500, fontSize: "0.75rem", textAlign: "right", maxWidth: 160, wordBreak: "break-all" }}>
                    {row.value}
                  </Typography>
                </Box>
              ))}

              {/* Actions */}
              <Box sx={{ display: "flex", gap: 1, mt: 2.5 }}>
                <Button
                  size="small" variant="outlined"
                  startIcon={<EditRoundedIcon sx={{ fontSize: "13px !important" }} />}
                  onClick={openEdit}
                  sx={{ flex: 1, borderColor: "divider", color: "text.secondary", fontSize: "0.75rem" }}
                >
                  Edit
                </Button>
                {isActive && (
                  <Button
                    size="small" variant="outlined"
                    startIcon={<PersonOffRoundedIcon sx={{ fontSize: "13px !important" }} />}
                    onClick={handleDeactivate}
                    disabled={deactivating}
                    sx={{ flex: 1, borderColor: "divider", color: "error.main", fontSize: "0.75rem", "&:hover": { borderColor: "error.main", bgcolor: "rgba(240,74,74,0.05)" } }}
                  >
                    {deactivating ? "…" : "Deactivate"}
                  </Button>
                )}
              </Box>
            </Box>
          </Paper>
        </Grid>

        {/* ── Right: tabbed sections ─────────────────────────────────────── */}
        <Grid item xs={12} md={8}>
          <Paper sx={{ borderRadius: 2, overflow: "hidden" }}>
            <Tabs
              value={innerTab}
              onChange={(_, v) => setInnerTab(v)}
              TabIndicatorProps={{ style: { height: 2 } }}
              sx={{
                minHeight: 42, borderBottom: "1px solid", borderColor: "divider",
                px: 2,
                "& .MuiTab-root": {
                  minHeight: 42, textTransform: "none",
                  fontFamily: "'DM Sans', sans-serif", fontWeight: 500,
                  fontSize: "0.78rem", color: "text.disabled",
                  px: 1.5, py: 0,
                  "&.Mui-selected": { color: "primary.main", fontWeight: 600 },
                },
                "& .MuiTabs-indicator": { bgcolor: "primary.main" },
              }}
            >
              {[
                { value: "overview",       label: "Overview"       },
                { value: "categories",     label: "Categories"     },
                { value: "addresses",      label: "Addresses"      },
                { value: "notes",          label: "Notes"          },
                { value: "organizations",  label: "Organisations"  },
              ].map((t) => (
                <Tab key={t.value} label={t.label} value={t.value} disableRipple />
              ))}
            </Tabs>

            <Box sx={{ p: 2.5 }}>

              {/* ── Overview ─────────────────────────────────────────────── */}
              {innerTab === "overview" && (
                <Box>
                  <SectionLabel>Contact Details</SectionLabel>
                  <Box sx={{ mt: 1.5 }}>
                    {[
                      { label: "Full name",      value: person.full_name },
                      { label: "Preferred name", value: person.preferred_name || "—" },
                      { label: "Email",          value: person.email ?? "—" },
                      { label: "Phone",          value: person.phone  || "—" },
                      { label: "Mobile",         value: person.mobile || "—" },
                    ].map((row, i, arr) => (
                      <Box key={row.label} sx={{
                        display: "flex", gap: 2, py: 1,
                        borderBottom: i < arr.length - 1 ? "1px solid" : "none",
                        borderColor: "divider",
                      }}>
                        <Typography variant="caption" sx={{ color: "text.secondary", fontSize: "0.75rem", width: 120, flexShrink: 0 }}>
                          {row.label}
                        </Typography>
                        <Typography variant="caption" sx={{ fontWeight: 500, fontSize: "0.75rem", wordBreak: "break-all" }}>
                          {row.value}
                        </Typography>
                      </Box>
                    ))}
                  </Box>

                  <Box sx={{ mt: 3 }}>
                    <SectionLabel>Personal</SectionLabel>
                    <Box sx={{ mt: 1.5 }}>
                      {[
                        { label: "Date of birth", value: person.date_of_birth ? fmt(person.date_of_birth) : "—" },
                        { label: "Gender",        value: person.gender_display || "—" },
                      ].map((row, i, arr) => (
                        <Box key={row.label} sx={{
                          display: "flex", gap: 2, py: 1,
                          borderBottom: i < arr.length - 1 ? "1px solid" : "none",
                          borderColor: "divider",
                        }}>
                          <Typography variant="caption" sx={{ color: "text.secondary", fontSize: "0.75rem", width: 120, flexShrink: 0 }}>
                            {row.label}
                          </Typography>
                          <Typography variant="caption" sx={{ fontWeight: 500, fontSize: "0.75rem" }}>
                            {row.value}
                          </Typography>
                        </Box>
                      ))}
                    </Box>
                  </Box>

                  {person.created_by_name && (
                    <Typography variant="caption" sx={{ color: "text.disabled", fontSize: "0.7rem", mt: 3, display: "block" }}>
                      Created by {person.created_by_name} · {fmt(person.created_at)}
                    </Typography>
                  )}
                </Box>
              )}

              {/* ── Categories ───────────────────────────────────────────── */}
              {innerTab === "categories" && (
                <Box>
                  <Box sx={{ display: "flex", alignItems: "center", mb: 2 }}>
                    <SectionLabel>Assigned Categories</SectionLabel>
                    <Box sx={{ flex: 1 }} />
                    <Button
                      size="small"
                      startIcon={<AddRoundedIcon sx={{ fontSize: "13px !important" }} />}
                      onClick={() => { setAssignCatId(""); setAssignErr(null); setAssignOpen(true); }}
                      sx={{ fontSize: "0.75rem", color: "text.secondary", "&:hover": { color: "text.primary" } }}
                    >
                      Assign
                    </Button>
                  </Box>

                  {person.category_assignments.length === 0 ? (
                    <Typography variant="body2" sx={{ color: "text.secondary", fontSize: "0.8rem" }}>
                      No categories assigned.
                    </Typography>
                  ) : (
                    <Box sx={{ display: "flex", flexWrap: "wrap", gap: 1 }}>
                      {person.category_assignments.map((a) => (
                        <Chip
                          key={a.id}
                          label={a.category.name}
                          size="small"
                          onDelete={() => handleRemoveCategory(a.category.id)}
                          sx={{
                            fontSize: "0.75rem", height: 24,
                            bgcolor: "rgba(74,160,240,0.09)",
                            color: "info.main",
                            "& .MuiChip-deleteIcon": { fontSize: 13, color: "info.main", opacity: 0.7, "&:hover": { opacity: 1 } },
                          }}
                        />
                      ))}
                    </Box>
                  )}
                </Box>
              )}

              {/* ── Addresses ────────────────────────────────────────────── */}
              {innerTab === "addresses" && (
                <Box>
                  <Box sx={{ display: "flex", alignItems: "center", mb: 2 }}>
                    <SectionLabel>Addresses</SectionLabel>
                    <Box sx={{ flex: 1 }} />
                    <Button
                      size="small"
                      startIcon={<AddRoundedIcon sx={{ fontSize: "13px !important" }} />}
                      onClick={() => openAddressDialog(null)}
                      sx={{ fontSize: "0.75rem", color: "text.secondary", "&:hover": { color: "text.primary" } }}
                    >
                      Add
                    </Button>
                  </Box>

                  {person.addresses.length === 0 ? (
                    <Typography variant="body2" sx={{ color: "text.secondary", fontSize: "0.8rem" }}>
                      No addresses on record.
                    </Typography>
                  ) : (
                    <Box sx={{ display: "flex", flexDirection: "column", gap: 1.5 }}>
                      {person.addresses.map((addr) => (
                        <Box key={addr.id} sx={{
                          p: 1.8, borderRadius: 1.5,
                          border: "1px solid", borderColor: addr.is_default ? "primary.main" : "divider",
                          bgcolor: addr.is_default ? "action.selected" : "transparent",
                        }}>
                          <Box sx={{ display: "flex", alignItems: "center", gap: 0.8, mb: 0.8 }}>
                            <Box sx={{ color: "text.secondary" }}>{addressLabelIcon(addr.label)}</Box>
                            <Typography variant="caption" sx={{ fontWeight: 600, fontSize: "0.72rem", textTransform: "capitalize", color: addr.is_default ? "primary.main" : "text.secondary" }}>
                              {addr.label_display}
                              {addr.is_default && " · Default"}
                            </Typography>
                            <Box sx={{ flex: 1 }} />
                            <IconButton
                              size="small"
                              onClick={() => openAddressDialog(addr)}
                              sx={{ color: "text.disabled", "&:hover": { color: "text.primary" }, p: 0.5 }}
                            >
                              <EditRoundedIcon sx={{ fontSize: 13 }} />
                            </IconButton>
                          </Box>
                          <Typography variant="body2" sx={{ fontSize: "0.8rem", lineHeight: 1.5 }}>
                            {[addr.line1, addr.line2, addr.city, addr.state_province, addr.postal_code, addr.country]
                              .filter(Boolean).join(", ")}
                          </Typography>
                        </Box>
                      ))}
                    </Box>
                  )}
                </Box>
              )}

              {/* ── Notes ────────────────────────────────────────────────── */}
              {innerTab === "notes" && (
                <Box>
                  {/* Add note */}
                  <Box sx={{ mb: 2.5 }}>
                    <SectionLabel>Add Note</SectionLabel>
                    <Box sx={{ mt: 1, display: "flex", gap: 1.5, alignItems: "flex-start" }}>
                      <TextField
                        multiline minRows={2} fullWidth size="small"
                        placeholder="Enter a note… (notes are permanent and cannot be edited)"
                        value={noteBody}
                        onChange={(e) => { setNoteBody(e.target.value); setNoteErr(null); }}
                        disabled={noteSaving}
                        sx={{ fontSize: "0.8rem" }}
                      />
                      <Button
                        size="small"
                        variant="outlined"
                        onClick={submitNote}
                        disabled={noteSaving || !noteBody.trim()}
                        startIcon={<NoteAddRoundedIcon sx={{ fontSize: "13px !important" }} />}
                        sx={{ borderColor: "divider", color: "text.secondary", fontSize: "0.75rem", mt: 0.25, whiteSpace: "nowrap" }}
                      >
                        {noteSaving ? "Saving…" : "Add"}
                      </Button>
                    </Box>
                    {noteErr && (
                      <Typography variant="caption" sx={{ color: "error.main", mt: 0.5, display: "block", fontSize: "0.72rem" }}>
                        {noteErr}
                      </Typography>
                    )}
                  </Box>

                  <Divider sx={{ mb: 2.5 }} />

                  <SectionLabel>History</SectionLabel>

                  {person.notes.length === 0 ? (
                    <Typography variant="body2" sx={{ color: "text.secondary", fontSize: "0.8rem", mt: 1.5 }}>
                      No notes yet.
                    </Typography>
                  ) : (
                    <Box sx={{ mt: 1.5 }}>
                      {person.notes.map((note, i) => (
                        <Box key={note.id} sx={{ display: "flex", gap: 2, mb: i < person.notes.length - 1 ? 2 : 0 }}>
                          <Box sx={{ display: "flex", flexDirection: "column", alignItems: "center", flexShrink: 0 }}>
                            <Box sx={{ width: 7, height: 7, borderRadius: "50%", bgcolor: "primary.main", mt: 0.5 }} />
                            {i < person.notes.length - 1 && <Box sx={{ width: 1, flex: 1, bgcolor: "divider", mt: 0.5 }} />}
                          </Box>
                          <Box sx={{ flex: 1, pb: i < person.notes.length - 1 ? 1.5 : 0 }}>
                            <Typography variant="body2" sx={{ fontSize: "0.8rem", lineHeight: 1.5 }}>
                              {note.body}
                            </Typography>
                            <Typography variant="caption" sx={{ color: "text.secondary", fontSize: "0.7rem" }}>
                              {note.author_name ? `${note.author_name} · ` : ""}{fmt(note.created_at)}
                            </Typography>
                          </Box>
                        </Box>
                      ))}
                    </Box>
                  )}
                </Box>
              )}

              {/* ── Organisations ─────────────────────────────────────────── */}
              {innerTab === "organizations" && (
                <Box>
                  <Box sx={{ display: "flex", alignItems: "center", mb: 2 }}>
                    <SectionLabel>Organisation Links</SectionLabel>
                    <Box sx={{ flex: 1 }} />
                    <Button
                      size="small"
                      startIcon={<AddRoundedIcon sx={{ fontSize: "13px !important" }} />}
                      onClick={() => { setOrgForm({ organization_id: "", organization_type: "", role: "", is_primary: false }); setOrgErrors({}); setOrgErr(null); setOrgOpen(true); }}
                      sx={{ fontSize: "0.75rem", color: "text.secondary", "&:hover": { color: "text.primary" } }}
                    >
                      Link
                    </Button>
                  </Box>

                  {person.org_relations.length === 0 ? (
                    <Typography variant="body2" sx={{ color: "text.secondary", fontSize: "0.8rem" }}>
                      No organisation links.
                    </Typography>
                  ) : (
                    <Box sx={{ display: "flex", flexDirection: "column", gap: 0 }}>
                      {person.org_relations.map((rel, i) => (
                        <Box key={rel.id} sx={{
                          display: "flex", alignItems: "center", gap: 1.5,
                          py: 1.4,
                          borderBottom: i < person.org_relations.length - 1 ? "1px solid" : "none",
                          borderColor: "divider",
                        }}>
                          <Box sx={{
                            width: 30, height: 30, borderRadius: 1, flexShrink: 0,
                            bgcolor: rel.is_active ? "rgba(74,160,240,0.09)" : "action.disabledBackground",
                            display: "flex", alignItems: "center", justifyContent: "center",
                          }}>
                            <BusinessRoundedIcon sx={{ fontSize: 15, color: rel.is_active ? "info.main" : "text.disabled" }} />
                          </Box>
                          <Box sx={{ flex: 1 }}>
                            <Box sx={{ display: "flex", alignItems: "center", gap: 0.8 }}>
                              <Typography variant="body2" sx={{ fontWeight: 500, fontSize: "0.8rem" }}>
                                {rel.organization_type} #{rel.organization_id}
                              </Typography>
                              {rel.is_primary && (
                                <Chip label="Primary" size="small" sx={{ fontSize: "0.62rem", height: 16, bgcolor: "action.selected", color: "primary.main" }} />
                              )}
                              {!rel.is_active && (
                                <Chip label="Closed" size="small" sx={{ fontSize: "0.62rem", height: 16, bgcolor: "action.disabledBackground", color: "text.disabled" }} />
                              )}
                            </Box>
                            <Typography variant="caption" sx={{ color: "text.secondary", fontSize: "0.72rem" }}>
                              {rel.role}
                              {rel.started_on ? ` · from ${fmt(rel.started_on)}` : ""}
                              {rel.ended_on   ? ` to ${fmt(rel.ended_on)}` : ""}
                            </Typography>
                          </Box>
                          {rel.is_active && (
                            <Button
                              size="small"
                              onClick={() => handleCloseOrg(rel)}
                              sx={{ fontSize: "0.72rem", color: "text.disabled", "&:hover": { color: "error.main" }, minWidth: 0 }}
                            >
                              Close
                            </Button>
                          )}
                        </Box>
                      ))}
                    </Box>
                  )}
                </Box>
              )}

            </Box>
          </Paper>
        </Grid>
      </Grid>

      {/* ── Edit Person Dialog ────────────────────────────────────────────── */}
      <Dialog open={editOpen} onClose={() => !editSaving && setEditOpen(false)} maxWidth="sm" fullWidth PaperProps={{ sx: { borderRadius: "12px" } }}>
        <DialogTitle sx={{ p: 0 }}>
          <Box sx={{ display: "flex", alignItems: "center", justifyContent: "space-between", px: 3, pt: 2.5, pb: 2 }}>
            <Typography variant="h6" sx={{ fontFamily: "'Syne', sans-serif", fontWeight: 700, fontSize: "1rem" }}>
              {editDupStep ? "Possible Duplicates" : "Edit Person"}
            </Typography>
            <IconButton size="small" onClick={() => !editSaving && setEditOpen(false)} sx={{ color: "text.secondary" }}>
              <CloseRoundedIcon sx={{ fontSize: 18 }} />
            </IconButton>
          </Box>
          <Divider />
        </DialogTitle>

        <DialogContent sx={{ px: 3, pt: 2.5, pb: 1 }}>
          {editDupStep ? (
            <Box>
              <Alert severity="warning" sx={{ mb: 2, borderRadius: 1.5, fontSize: "0.8rem" }}>
                Similar records found. Confirm this is a different person by clicking <strong>Save Anyway</strong>.
              </Alert>
              {editDupCands.map((c) => (
                <Box key={c.id} sx={{ display: "flex", alignItems: "center", gap: 1.5, py: 1.2, borderBottom: "1px solid", borderColor: "divider", "&:last-child": { borderBottom: "none" } }}>
                  <Avatar sx={{ width: 28, height: 28, fontSize: "0.6rem", fontWeight: 700, bgcolor: "rgba(240,184,74,0.12)", color: "#F0B84A", fontFamily: "'Syne', sans-serif" }}>
                    {c.full_name.split(" ").map((n) => n[0]).join("").slice(0, 2)}
                  </Avatar>
                  <Box>
                    <Typography variant="body2" sx={{ fontWeight: 500, fontSize: "0.82rem" }}>{c.full_name}</Typography>
                    <Typography variant="caption" sx={{ color: "text.secondary", fontSize: "0.72rem" }}>{c.email ?? c.phone ?? "—"}</Typography>
                  </Box>
                </Box>
              ))}
            </Box>
          ) : (
            <Box sx={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 2.5 }}>
              {[
                { key: "first_name", label: "First Name *", placeholder: "Alice", full: false },
                { key: "last_name",  label: "Last Name *",  placeholder: "Smith", full: false },
              ].map(({ key, label, placeholder, full }) => (
                <Box key={key} sx={{ gridColumn: full ? "1 / -1" : undefined }}>
                  <FieldLabel>{label}</FieldLabel>
                  <TextField fullWidth size="small" placeholder={placeholder}
                    value={editForm[key] ?? ""} onChange={(e) => setEditForm((p) => ({ ...p, [key]: e.target.value }))}
                    error={!!editErrors[key]} helperText={editErrors[key]}
                  />
                </Box>
              ))}
              <Box sx={{ gridColumn: "1 / -1" }}>
                <FieldLabel>Preferred Name</FieldLabel>
                <TextField fullWidth size="small" value={editForm.preferred_name ?? ""}
                  onChange={(e) => setEditForm((p) => ({ ...p, preferred_name: e.target.value }))}
                />
              </Box>
              <Box sx={{ gridColumn: "1 / -1" }}>
                <FieldLabel>Email</FieldLabel>
                <TextField fullWidth size="small" type="email" value={editForm.email ?? ""}
                  onChange={(e) => setEditForm((p) => ({ ...p, email: e.target.value }))}
                  error={!!editErrors.email} helperText={editErrors.email}
                />
              </Box>
              <Box>
                <FieldLabel>Phone</FieldLabel>
                <TextField fullWidth size="small" value={editForm.phone ?? ""} onChange={(e) => setEditForm((p) => ({ ...p, phone: e.target.value }))} />
              </Box>
              <Box>
                <FieldLabel>Mobile</FieldLabel>
                <TextField fullWidth size="small" value={editForm.mobile ?? ""} onChange={(e) => setEditForm((p) => ({ ...p, mobile: e.target.value }))} />
              </Box>
              <Box>
                <FieldLabel>Date of Birth</FieldLabel>
                <TextField fullWidth size="small" type="date" value={editForm.date_of_birth ?? ""}
                  onChange={(e) => setEditForm((p) => ({ ...p, date_of_birth: e.target.value }))}
                  InputLabelProps={{ shrink: true }}
                />
              </Box>
              <Box>
                <FieldLabel>Gender</FieldLabel>
                <FormControl fullWidth size="small">
                  <Select value={editForm.gender ?? ""} onChange={(e) => setEditForm((p) => ({ ...p, gender: e.target.value }))}>
                    {GENDER_OPTIONS.map((o) => <MenuItem key={o.value} value={o.value}>{o.label}</MenuItem>)}
                  </Select>
                </FormControl>
              </Box>
            </Box>
          )}
          {editErr && <Alert severity="error" sx={{ mt: 2, borderRadius: 1.5, fontSize: "0.8rem" }}>{editErr}</Alert>}
        </DialogContent>

        <DialogActions sx={{ px: 3, py: 2.5 }}>
          {editDupStep ? (
            <>
              <Button onClick={() => setEditDupStep(false)} disabled={editSaving} sx={{ color: "text.secondary", fontSize: "0.8rem" }}>Back</Button>
              <Button variant="contained" onClick={() => submitEdit(true)} disabled={editSaving} sx={{ fontSize: "0.8rem", px: 2.5 }}>
                {editSaving ? "Saving…" : "Save Anyway"}
              </Button>
            </>
          ) : (
            <>
              <Button onClick={() => setEditOpen(false)} disabled={editSaving} sx={{ color: "text.secondary", fontSize: "0.8rem" }}>Cancel</Button>
              <Button variant="contained" onClick={() => submitEdit(false)} disabled={editSaving} sx={{ fontSize: "0.8rem", px: 2.5 }}>
                {editSaving ? "Saving…" : "Save Changes"}
              </Button>
            </>
          )}
        </DialogActions>
      </Dialog>

      {/* ── Add Address Dialog ────────────────────────────────────────────── */}
      <Dialog open={addrOpen} onClose={() => !addrSaving && setAddrOpen(false)} maxWidth="sm" fullWidth PaperProps={{ sx: { borderRadius: "12px" } }}>
        <DialogTitle sx={{ p: 0 }}>
          <Box sx={{ display: "flex", alignItems: "center", justifyContent: "space-between", px: 3, pt: 2.5, pb: 2 }}>
            <Typography variant="h6" sx={{ fontFamily: "'Syne', sans-serif", fontWeight: 700, fontSize: "1rem" }}>
              {addrEdit ? "Edit Address" : "Add Address"}
            </Typography>
            <IconButton size="small" onClick={() => !addrSaving && setAddrOpen(false)} sx={{ color: "text.secondary" }}>
              <CloseRoundedIcon sx={{ fontSize: 18 }} />
            </IconButton>
          </Box>
          <Divider />
        </DialogTitle>
        <DialogContent sx={{ px: 3, pt: 2.5, pb: 1 }}>
          <Box sx={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 2.5 }}>
            <Box>
              <FieldLabel>Label</FieldLabel>
              <FormControl fullWidth size="small">
                <Select value={String(addrForm.label ?? "home")} onChange={(e) => setAddrForm((p) => ({ ...p, label: e.target.value }))}>
                  {ADDRESS_LABELS.map((l) => <MenuItem key={l.value} value={l.value}>{l.label}</MenuItem>)}
                </Select>
              </FormControl>
            </Box>
            <Box sx={{ display: "flex", alignItems: "flex-end", pb: 0.2 }}>
              <label style={{ display: "flex", alignItems: "center", gap: 6, cursor: "pointer", fontSize: "0.8rem" }}>
                <input
                  type="checkbox"
                  checked={Boolean(addrForm.is_default)}
                  onChange={(e) => setAddrForm((p) => ({ ...p, is_default: e.target.checked }))}
                />
                <Typography variant="body2" sx={{ fontSize: "0.8rem" }}>Set as default</Typography>
              </label>
            </Box>
            <Box sx={{ gridColumn: "1 / -1" }}>
              <FieldLabel>Line 1 *</FieldLabel>
              <TextField fullWidth size="small" value={String(addrForm.line1 ?? "")} onChange={(e) => setAddrForm((p) => ({ ...p, line1: e.target.value }))} error={!!addrErrors.line1} helperText={addrErrors.line1} />
            </Box>
            <Box sx={{ gridColumn: "1 / -1" }}>
              <FieldLabel>Line 2</FieldLabel>
              <TextField fullWidth size="small" value={String(addrForm.line2 ?? "")} onChange={(e) => setAddrForm((p) => ({ ...p, line2: e.target.value }))} />
            </Box>
            <Box>
              <FieldLabel>City *</FieldLabel>
              <TextField fullWidth size="small" value={String(addrForm.city ?? "")} onChange={(e) => setAddrForm((p) => ({ ...p, city: e.target.value }))} error={!!addrErrors.city} helperText={addrErrors.city} />
            </Box>
            <Box>
              <FieldLabel>State / Province</FieldLabel>
              <TextField fullWidth size="small" value={String(addrForm.state_province ?? "")} onChange={(e) => setAddrForm((p) => ({ ...p, state_province: e.target.value }))} />
            </Box>
            <Box>
              <FieldLabel>Postal Code</FieldLabel>
              <TextField fullWidth size="small" value={String(addrForm.postal_code ?? "")} onChange={(e) => setAddrForm((p) => ({ ...p, postal_code: e.target.value }))} />
            </Box>
            <Box>
              <FieldLabel>Country *</FieldLabel>
              <TextField fullWidth size="small" value={String(addrForm.country ?? "")} onChange={(e) => setAddrForm((p) => ({ ...p, country: e.target.value }))} error={!!addrErrors.country} helperText={addrErrors.country} />
            </Box>
          </Box>
          {addrErr && <Alert severity="error" sx={{ mt: 2, borderRadius: 1.5, fontSize: "0.8rem" }}>{addrErr}</Alert>}
        </DialogContent>
        <DialogActions sx={{ px: 3, py: 2.5 }}>
          <Button onClick={() => setAddrOpen(false)} disabled={addrSaving} sx={{ color: "text.secondary", fontSize: "0.8rem" }}>Cancel</Button>
          <Button variant="contained" onClick={submitAddress} disabled={addrSaving} sx={{ fontSize: "0.8rem", px: 2.5 }}>
            {addrSaving ? "Saving…" : addrEdit ? "Save Changes" : "Add Address"}
          </Button>
        </DialogActions>
      </Dialog>

      {/* ── Link Organisation Dialog ──────────────────────────────────────── */}
      <Dialog open={orgOpen} onClose={() => !orgSaving && setOrgOpen(false)} maxWidth="xs" fullWidth PaperProps={{ sx: { borderRadius: "12px" } }}>
        <DialogTitle sx={{ p: 0 }}>
          <Box sx={{ display: "flex", alignItems: "center", justifyContent: "space-between", px: 3, pt: 2.5, pb: 2 }}>
            <Box>
              <Typography variant="h6" sx={{ fontFamily: "'Syne', sans-serif", fontWeight: 700, fontSize: "1rem" }}>Link Organisation</Typography>
              <Typography variant="caption" sx={{ color: "text.secondary" }}>Associate this person with an organisation record.</Typography>
            </Box>
            <IconButton size="small" onClick={() => !orgSaving && setOrgOpen(false)} sx={{ color: "text.secondary" }}>
              <CloseRoundedIcon sx={{ fontSize: 18 }} />
            </IconButton>
          </Box>
          <Divider />
        </DialogTitle>
        <DialogContent sx={{ px: 3, pt: 2.5, pb: 1 }}>
          <Box sx={{ display: "flex", flexDirection: "column", gap: 2.5 }}>
            <Box>
              <FieldLabel>Organisation ID *</FieldLabel>
              <TextField fullWidth size="small" type="number" placeholder="e.g. 42"
                value={orgForm.organization_id} onChange={(e) => setOrgForm((p) => ({ ...p, organization_id: e.target.value }))}
                error={!!orgErrors.organization_id} helperText={orgErrors.organization_id}
              />
            </Box>
            <Box>
              <FieldLabel>Organisation Type *</FieldLabel>
              <TextField fullWidth size="small" placeholder="e.g. customer, supplier"
                value={orgForm.organization_type} onChange={(e) => setOrgForm((p) => ({ ...p, organization_type: e.target.value }))}
                error={!!orgErrors.organization_type} helperText={orgErrors.organization_type}
              />
            </Box>
            <Box>
              <FieldLabel>Role *</FieldLabel>
              <TextField fullWidth size="small" placeholder="e.g. contact, owner"
                value={orgForm.role} onChange={(e) => setOrgForm((p) => ({ ...p, role: e.target.value }))}
                error={!!orgErrors.role} helperText={orgErrors.role}
              />
            </Box>
            <label style={{ display: "flex", alignItems: "center", gap: 6, cursor: "pointer" }}>
              <input type="checkbox" checked={orgForm.is_primary} onChange={(e) => setOrgForm((p) => ({ ...p, is_primary: e.target.checked }))} />
              <Typography variant="body2" sx={{ fontSize: "0.8rem" }}>Mark as primary contact</Typography>
            </label>
          </Box>
          {orgErr && <Alert severity="error" sx={{ mt: 2, borderRadius: 1.5, fontSize: "0.8rem" }}>{orgErr}</Alert>}
        </DialogContent>
        <DialogActions sx={{ px: 3, py: 2.5 }}>
          <Button onClick={() => setOrgOpen(false)} disabled={orgSaving} sx={{ color: "text.secondary", fontSize: "0.8rem" }}>Cancel</Button>
          <Button variant="contained" onClick={submitOrg} disabled={orgSaving} sx={{ fontSize: "0.8rem", px: 2.5 }}>
            {orgSaving ? "Linking…" : "Link Organisation"}
          </Button>
        </DialogActions>
      </Dialog>

      {/* ── Assign Category Dialog ─────────────────────────────────────────── */}
      <Dialog open={assignOpen} onClose={() => !assignSaving && setAssignOpen(false)} maxWidth="xs" fullWidth PaperProps={{ sx: { borderRadius: "12px" } }}>
        <DialogTitle sx={{ p: 0 }}>
          <Box sx={{ display: "flex", alignItems: "center", justifyContent: "space-between", px: 3, pt: 2.5, pb: 2 }}>
            <Typography variant="h6" sx={{ fontFamily: "'Syne', sans-serif", fontWeight: 700, fontSize: "1rem" }}>
              Assign Category
            </Typography>
            <IconButton size="small" onClick={() => !assignSaving && setAssignOpen(false)} sx={{ color: "text.secondary" }}>
              <CloseRoundedIcon sx={{ fontSize: 18 }} />
            </IconButton>
          </Box>
          <Divider />
        </DialogTitle>
        <DialogContent sx={{ px: 3, pt: 2.5, pb: 1 }}>
          <FieldLabel>Category</FieldLabel>
          <FormControl fullWidth size="small">
            <Select
              value={assignCatId}
              onChange={(e) => setAssignCatId(e.target.value as number | "")}
              displayEmpty
            >
              <MenuItem value="" disabled>Select a category…</MenuItem>
              {categories
                .filter((c) => !person.category_assignments.some((a) => a.category.id === c.id))
                .map((c) => (
                  <MenuItem key={c.id} value={c.id}>{c.name}</MenuItem>
                ))}
            </Select>
          </FormControl>
          {assignErr && <Alert severity="error" sx={{ mt: 2, borderRadius: 1.5, fontSize: "0.8rem" }}>{assignErr}</Alert>}
        </DialogContent>
        <DialogActions sx={{ px: 3, py: 2.5 }}>
          <Button onClick={() => setAssignOpen(false)} disabled={assignSaving} sx={{ color: "text.secondary", fontSize: "0.8rem" }}>Cancel</Button>
          <Button variant="contained" onClick={submitAssign} disabled={assignSaving || !assignCatId} sx={{ fontSize: "0.8rem", px: 2.5 }}>
            {assignSaving ? "Assigning…" : "Assign"}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
}

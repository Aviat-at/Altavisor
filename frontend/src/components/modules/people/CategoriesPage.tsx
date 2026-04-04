"use client";
import React, { useCallback, useEffect, useState } from "react";
import {
  Alert, Box, Button, Chip, CircularProgress, Dialog,
  DialogActions, DialogContent, DialogTitle, Divider,
  IconButton, Paper, TextField, Typography,
} from "@mui/material";
import { useTheme } from "@mui/material/styles";
import AddRoundedIcon        from "@mui/icons-material/AddRounded";
import CloseRoundedIcon      from "@mui/icons-material/CloseRounded";
import EditRoundedIcon       from "@mui/icons-material/EditRounded";
import LockRoundedIcon       from "@mui/icons-material/LockRounded";
import BlockRoundedIcon      from "@mui/icons-material/BlockRounded";

import * as api from "./api";
import type { ApiError, PersonCategory } from "./types";

const FieldLabel = ({ children }: { children: React.ReactNode }) => (
  <Typography variant="caption" sx={{
    color: "text.secondary", fontWeight: 500, mb: 0.75, display: "block",
    letterSpacing: "0.04em", textTransform: "uppercase", fontSize: "0.67rem",
  }}>
    {children}
  </Typography>
);

const blankForm = () => ({ name: "", description: "" });

export default function CategoriesPage() {
  const theme = useTheme();

  const [categories, setCategories] = useState<PersonCategory[]>([]);
  const [loading,    setLoading]    = useState(true);
  const [loadErr,    setLoadErr]    = useState<string | null>(null);

  // Show all (active + inactive)
  const [showAll, setShowAll] = useState(false);

  // Add dialog
  const [addOpen,    setAddOpen]    = useState(false);
  const [addForm,    setAddForm]    = useState(blankForm());
  const [addErrors,  setAddErrors]  = useState<Partial<typeof addForm>>({});
  const [addSaving,  setAddSaving]  = useState(false);
  const [addErr,     setAddErr]     = useState<string | null>(null);

  // Edit dialog
  const [editTarget, setEditTarget] = useState<PersonCategory | null>(null);
  const [editForm,   setEditForm]   = useState(blankForm());
  const [editErrors, setEditErrors] = useState<Partial<typeof editForm>>({});
  const [editSaving, setEditSaving] = useState(false);
  const [editErr,    setEditErr]    = useState<string | null>(null);

  // Deactivate
  const [deactivatingId, setDeactivatingId] = useState<number | null>(null);
  const [deactivateErr,  setDeactivateErr]  = useState<string | null>(null);

  // ── Load ─────────────────────────────────────────────────────────────────

  const loadCategories = useCallback(() => {
    let cancelled = false;
    setLoading(true);
    setLoadErr(null);
    const params = showAll ? {} : { is_active: true };
    api.listCategories(params)
      .then((data) => { if (!cancelled) setCategories(data); })
      .catch(() => { if (!cancelled) setLoadErr("Failed to load categories."); })
      .finally(() => { if (!cancelled) setLoading(false); });
    return () => { cancelled = true; };
  }, [showAll]);

  useEffect(() => { return loadCategories(); }, [loadCategories]);

  // ── Add ───────────────────────────────────────────────────────────────────

  const openAdd = () => {
    setAddForm(blankForm());
    setAddErrors({});
    setAddErr(null);
    setAddOpen(true);
  };

  const submitAdd = async () => {
    const e: Partial<typeof addForm> = {};
    if (!addForm.name.trim()) e.name = "Name is required.";
    if (Object.keys(e).length) { setAddErrors(e); return; }

    setAddSaving(true);
    setAddErr(null);
    try {
      await api.createCategory({ name: addForm.name.trim(), description: addForm.description.trim() });
      loadCategories();
      setAddOpen(false);
    } catch (err) {
      const ae = err as ApiError;
      if (ae.status === 409) setAddErr(ae.body?.detail ?? "A category with this name already exists.");
      else setAddErr(ae.body?.detail ?? "Could not create category.");
    } finally {
      setAddSaving(false);
    }
  };

  // ── Edit ──────────────────────────────────────────────────────────────────

  const openEdit = (cat: PersonCategory) => {
    setEditTarget(cat);
    setEditForm({ name: cat.name, description: cat.description });
    setEditErrors({});
    setEditErr(null);
  };

  const submitEdit = async () => {
    if (!editTarget) return;
    const e: Partial<typeof editForm> = {};
    if (!editForm.name.trim()) e.name = "Name is required.";
    if (Object.keys(e).length) { setEditErrors(e); return; }

    setEditSaving(true);
    setEditErr(null);
    try {
      await api.updateCategory(editTarget.id, { name: editForm.name.trim(), description: editForm.description.trim() });
      loadCategories();
      setEditTarget(null);
    } catch (err) {
      const ae = err as ApiError;
      if (ae.status === 409) setEditErr(ae.body?.detail ?? "Name conflict.");
      else setEditErr(ae.body?.detail ?? "Could not save changes.");
    } finally {
      setEditSaving(false);
    }
  };

  // ── Deactivate ────────────────────────────────────────────────────────────

  const handleDeactivate = async (cat: PersonCategory) => {
    if (!window.confirm(`Deactivate "${cat.name}"? This will also remove it from all current assignments.`)) return;
    setDeactivatingId(cat.id);
    setDeactivateErr(null);
    try {
      await api.deactivateCategory(cat.id);
      loadCategories();
    } catch (err) {
      const ae = err as ApiError;
      setDeactivateErr(ae.body?.detail ?? "Could not deactivate category.");
    } finally {
      setDeactivatingId(null);
    }
  };

  // ── Color helpers ─────────────────────────────────────────────────────────

  const activeChip = (active: boolean) =>
    active
      ? { bg: "action.selected",            color: theme.palette.primary.main    }
      : { bg: "action.disabledBackground",  color: theme.palette.text.secondary  };

  // ── Render ────────────────────────────────────────────────────────────────

  return (
    <Box>
      {/* Toolbar */}
      <Box sx={{ display: "flex", gap: 1.5, mb: 2, alignItems: "center" }}>
        <Typography variant="body2" sx={{ color: "text.secondary", fontSize: "0.8rem", flex: 1 }}>
          Categories are used to classify people in the directory.
          System categories are read-only.
        </Typography>

        <Button
          size="small"
          variant={showAll ? "outlined" : "text"}
          onClick={() => setShowAll((v) => !v)}
          sx={{ fontSize: "0.78rem", color: "text.secondary", borderColor: "divider" }}
        >
          {showAll ? "Showing all" : "Active only"}
        </Button>

        <Button
          size="small"
          variant="contained"
          startIcon={<AddRoundedIcon sx={{ fontSize: "14px !important" }} />}
          onClick={openAdd}
          sx={{ fontSize: "0.78rem" }}
        >
          Add Category
        </Button>
      </Box>

      {deactivateErr && (
        <Alert severity="error" sx={{ mb: 2, borderRadius: 2, fontSize: "0.8rem" }}>
          {deactivateErr}
        </Alert>
      )}
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
          gridTemplateColumns: "2fr 3fr 80px 80px 130px",
          borderBottom: "1px solid", borderColor: "divider",
        }}>
          {["Name", "Description", "System", "Status", "Actions"].map((h) => (
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
        {!loading && categories.length === 0 && (
          <Box sx={{ py: 4, textAlign: "center" }}>
            <Typography variant="body2" sx={{ color: "text.secondary" }}>
              No categories found.
            </Typography>
          </Box>
        )}

        {/* Rows */}
        {!loading && categories.map((cat, i) => {
          const sc = activeChip(cat.is_active);
          const isEditing = editTarget?.id === cat.id;
          const isDeactivating = deactivatingId === cat.id;

          return (
            <Box key={cat.id} sx={{
              borderBottom: i < categories.length - 1 ? "1px solid" : "none",
              borderColor: "divider",
              opacity: cat.is_active ? 1 : 0.6,
            }}>
              {/* Row */}
              {!isEditing && (
                <Box sx={{
                  px: 2.5, py: 1.4,
                  display: "grid",
                  gridTemplateColumns: "2fr 3fr 80px 80px 130px",
                  alignItems: "center",
                }}>
                  {/* Name */}
                  <Box sx={{ display: "flex", alignItems: "center", gap: 0.8 }}>
                    {cat.is_system && (
                      <LockRoundedIcon sx={{ fontSize: 13, color: "text.disabled", flexShrink: 0 }} />
                    )}
                    <Typography variant="body2" sx={{ fontWeight: 500, fontSize: "0.8rem" }}>
                      {cat.name}
                    </Typography>
                  </Box>

                  {/* Description */}
                  <Typography variant="caption" sx={{ color: "text.secondary", fontSize: "0.78rem", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
                    {cat.description || "—"}
                  </Typography>

                  {/* System */}
                  {cat.is_system ? (
                    <Chip label="System" size="small" sx={{ fontSize: "0.65rem", height: 18, width: "fit-content", bgcolor: "rgba(128,128,128,0.09)", color: "text.secondary" }} />
                  ) : (
                    <Typography variant="caption" sx={{ color: "text.disabled", fontSize: "0.72rem" }}>—</Typography>
                  )}

                  {/* Status */}
                  <Chip label={cat.is_active ? "Active" : "Inactive"} size="small" sx={{ fontSize: "0.65rem", height: 18, width: "fit-content", bgcolor: sc.bg, color: sc.color }} />

                  {/* Actions */}
                  <Box sx={{ display: "flex", gap: 0.5 }}>
                    {!cat.is_system && cat.is_active && (
                      <>
                        <IconButton
                          size="small"
                          onClick={() => openEdit(cat)}
                          sx={{ color: "text.secondary", "&:hover": { color: "text.primary", bgcolor: "action.hover" }, p: 0.75 }}
                        >
                          <EditRoundedIcon sx={{ fontSize: 15 }} />
                        </IconButton>
                        <IconButton
                          size="small"
                          onClick={() => handleDeactivate(cat)}
                          disabled={isDeactivating}
                          sx={{ color: "text.secondary", "&:hover": { color: "error.main", bgcolor: "rgba(240,74,74,0.05)" }, p: 0.75 }}
                        >
                          {isDeactivating
                            ? <CircularProgress size={13} thickness={4} sx={{ color: "text.disabled" }} />
                            : <BlockRoundedIcon sx={{ fontSize: 15 }} />
                          }
                        </IconButton>
                      </>
                    )}
                    {cat.is_system && (
                      <Typography variant="caption" sx={{ color: "text.disabled", fontSize: "0.7rem", pl: 0.5, pt: 0.5 }}>
                        Read-only
                      </Typography>
                    )}
                  </Box>
                </Box>
              )}

              {/* Inline edit row */}
              {isEditing && (
                <Box sx={{ px: 2.5, py: 1.5, display: "flex", gap: 2, alignItems: "flex-start", bgcolor: "action.hover" }}>
                  <Box sx={{ flex: "0 0 200px" }}>
                    <TextField
                      fullWidth size="small" autoFocus
                      value={editForm.name}
                      onChange={(e) => { setEditForm((p) => ({ ...p, name: e.target.value })); setEditErrors({}); }}
                      error={!!editErrors.name}
                      helperText={editErrors.name}
                      placeholder="Category name"
                    />
                  </Box>
                  <Box sx={{ flex: 1 }}>
                    <TextField
                      fullWidth size="small"
                      value={editForm.description}
                      onChange={(e) => setEditForm((p) => ({ ...p, description: e.target.value }))}
                      placeholder="Description (optional)"
                    />
                  </Box>
                  {editErr && (
                    <Typography variant="caption" sx={{ color: "error.main", fontSize: "0.72rem", pt: 1 }}>
                      {editErr}
                    </Typography>
                  )}
                  <Box sx={{ display: "flex", gap: 0.5, pt: 0.2 }}>
                    <Button
                      size="small" variant="contained"
                      onClick={submitEdit}
                      disabled={editSaving}
                      sx={{ fontSize: "0.75rem", px: 2 }}
                    >
                      {editSaving ? "Saving…" : "Save"}
                    </Button>
                    <Button
                      size="small"
                      onClick={() => setEditTarget(null)}
                      disabled={editSaving}
                      sx={{ fontSize: "0.75rem", color: "text.secondary" }}
                    >
                      Cancel
                    </Button>
                  </Box>
                </Box>
              )}
            </Box>
          );
        })}
      </Paper>

      <Box sx={{ mt: 1.5 }}>
        <Typography variant="caption" sx={{ color: "text.secondary" }}>
          {!loading && `${categories.length} ${categories.length === 1 ? "category" : "categories"}`}
          {showAll && " (including inactive)"}
        </Typography>
      </Box>

      {/* ── Add Category Dialog ───────────────────────────────────────────── */}
      <Dialog
        open={addOpen}
        onClose={() => !addSaving && setAddOpen(false)}
        maxWidth="xs"
        fullWidth
        PaperProps={{ sx: { borderRadius: "12px" } }}
      >
        <DialogTitle sx={{ p: 0 }}>
          <Box sx={{ display: "flex", alignItems: "center", justifyContent: "space-between", px: 3, pt: 2.5, pb: 2 }}>
            <Box>
              <Typography variant="h6" sx={{ fontFamily: "'Syne', sans-serif", fontWeight: 700, fontSize: "1rem" }}>
                Add Category
              </Typography>
              <Typography variant="caption" sx={{ color: "text.secondary" }}>
                A URL slug will be generated automatically from the name.
              </Typography>
            </Box>
            <IconButton size="small" onClick={() => !addSaving && setAddOpen(false)} sx={{ color: "text.secondary" }}>
              <CloseRoundedIcon sx={{ fontSize: 18 }} />
            </IconButton>
          </Box>
          <Divider />
        </DialogTitle>

        <DialogContent sx={{ px: 3, pt: 2.5, pb: 1 }}>
          <Box sx={{ display: "flex", flexDirection: "column", gap: 2.5 }}>
            <Box>
              <FieldLabel>Name *</FieldLabel>
              <TextField
                fullWidth size="small" autoFocus
                placeholder="e.g. Supplier"
                value={addForm.name}
                onChange={(e) => { setAddForm((p) => ({ ...p, name: e.target.value })); setAddErrors({}); }}
                error={!!addErrors.name}
                helperText={addErrors.name}
              />
            </Box>
            <Box>
              <FieldLabel>Description</FieldLabel>
              <TextField
                fullWidth size="small" multiline minRows={2}
                placeholder="Optional description of this category"
                value={addForm.description}
                onChange={(e) => setAddForm((p) => ({ ...p, description: e.target.value }))}
              />
            </Box>
          </Box>
          {addErr && (
            <Alert severity="error" sx={{ mt: 2, borderRadius: 1.5, fontSize: "0.8rem" }}>
              {addErr}
            </Alert>
          )}
        </DialogContent>

        <DialogActions sx={{ px: 3, py: 2.5 }}>
          <Button
            onClick={() => setAddOpen(false)}
            disabled={addSaving}
            sx={{ color: "text.secondary", fontSize: "0.8rem", "&:hover": { bgcolor: "action.hover", color: "text.primary" } }}
          >
            Cancel
          </Button>
          <Button
            variant="contained"
            onClick={submitAdd}
            disabled={addSaving}
            sx={{ fontSize: "0.8rem", px: 2.5 }}
          >
            {addSaving ? "Creating…" : "Add Category"}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
}

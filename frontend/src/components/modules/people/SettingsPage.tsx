"use client";
import React from "react";
import { Box, Chip, Paper, Typography } from "@mui/material";
import InfoOutlinedIcon       from "@mui/icons-material/InfoOutlined";
import SearchRoundedIcon      from "@mui/icons-material/SearchRounded";
import LockRoundedIcon        from "@mui/icons-material/LockRounded";
import MergeRoundedIcon       from "@mui/icons-material/MergeRounded";
import CategoryRoundedIcon    from "@mui/icons-material/CategoryRounded";

function Section({
  title, description, children,
}: { title: string; description?: string; children: React.ReactNode }) {
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

function FieldRow({ label, hint, children }: { label: string; hint?: string; children: React.ReactNode }) {
  return (
    <Box sx={{
      display: "flex", alignItems: "flex-start", gap: 2, py: 1.5,
      "&:not(:last-child)": { borderBottom: "1px solid", borderColor: "divider" },
    }}>
      <Box sx={{ flex: "0 0 200px" }}>
        <Typography variant="body2" sx={{ fontWeight: 500, fontSize: "0.82rem" }}>{label}</Typography>
        {hint && <Typography variant="caption" sx={{ color: "text.secondary", fontSize: "0.72rem" }}>{hint}</Typography>}
      </Box>
      <Box sx={{ flex: 1 }}>{children}</Box>
    </Box>
  );
}

function InfoChip({ label }: { label: string }) {
  return (
    <Chip
      label={label}
      size="small"
      sx={{ fontFamily: "monospace", fontSize: "0.7rem", bgcolor: "action.disabledBackground", color: "text.secondary" }}
    />
  );
}

export default function SettingsPage() {
  return (
    <Box>
      {/* About */}
      <Section
        title="About the People Module"
        description="Reference information about how this module works."
      >
        <FieldRow
          label="Purpose"
          hint="What this module manages"
        >
          <Typography variant="body2" sx={{ fontSize: "0.8rem", color: "text.secondary", lineHeight: 1.6 }}>
            The People module is the central contact directory. It stores individuals
            (contacts, employees, partners) independently of any organisation or pricing
            module. People can be linked to multiple organisations and classified with
            multiple categories.
          </Typography>
        </FieldRow>
        <FieldRow
          label="Soft deactivation"
          hint="Records are never hard-deleted"
        >
          <Typography variant="body2" component="div" sx={{ fontSize: "0.8rem", color: "text.secondary", lineHeight: 1.6 }}>
            Deactivating a person closes all their active organisation links and removes
            all category assignments. The record remains queryable in the API with
            <Box component="span" sx={{ mx: 0.5 }}><InfoChip label="is_active=false" /></Box>.
            Hard deletion is not supported.
          </Typography>
        </FieldRow>
        <FieldRow
          label="Notes"
          hint="Append-only audit trail"
        >
          <Typography variant="body2" sx={{ fontSize: "0.8rem", color: "text.secondary", lineHeight: 1.6 }}>
            Notes on a person are immutable once saved. They cannot be edited or deleted.
            Use them as an audit trail, not as a scratchpad.
          </Typography>
        </FieldRow>
      </Section>

      {/* Duplicate detection */}
      <Section
        title="Duplicate Detection"
        description="The service layer checks for likely duplicates before creating or updating a person."
      >
        <FieldRow label="Email match" hint="High confidence">
          <Box sx={{ display: "flex", flexDirection: "column", gap: 0.8 }}>
            <Typography variant="body2" sx={{ fontSize: "0.8rem", color: "text.secondary" }}>
              If the submitted email matches an existing person's email exactly, the record
              is flagged as a probable duplicate.
            </Typography>
            <InfoChip label="confidence: high" />
          </Box>
        </FieldRow>
        <FieldRow label="Name match" hint="Medium confidence">
          <Box sx={{ display: "flex", flexDirection: "column", gap: 0.8 }}>
            <Typography variant="body2" sx={{ fontSize: "0.8rem", color: "text.secondary" }}>
              Case-insensitive match on both{" "}
              <Box component="span" sx={{ mx: 0.4 }}><InfoChip label="first_name" /></Box>
              {" "}and{" "}
              <Box component="span" sx={{ mx: 0.4 }}><InfoChip label="last_name" /></Box>
              {" "}triggers a medium-confidence warning.
            </Typography>
            <InfoChip label="confidence: medium" />
          </Box>
        </FieldRow>
        <FieldRow label="Phone match" hint="Medium confidence">
          <Box sx={{ display: "flex", flexDirection: "column", gap: 0.8 }}>
            <Typography variant="body2" sx={{ fontSize: "0.8rem", color: "text.secondary" }}>
              If the submitted phone number matches an existing person, it is included
              as a medium-confidence candidate.
            </Typography>
            <InfoChip label="confidence: medium" />
          </Box>
        </FieldRow>
        <FieldRow label="Override">
          <Typography variant="body2" component="div" sx={{ fontSize: "0.8rem", color: "text.secondary", lineHeight: 1.6 }}>
            After reviewing the candidates shown in the Directory dialog, a user can
            confirm creation with{" "}
            <Box component="span" sx={{ mx: 0.4 }}><InfoChip label="force=true" /></Box>.
            {" "}This is surfaced in the UI as the <strong>Create Anyway</strong> button.
          </Typography>
        </FieldRow>
      </Section>

      {/* Category system */}
      <Section
        title="Category System"
        description="How person categories work and their constraints."
      >
        <FieldRow label="System categories" hint="Protected by the service layer">
          <Typography variant="body2" component="div" sx={{ fontSize: "0.8rem", color: "text.secondary", lineHeight: 1.6 }}>
            Categories created by the application (marked{" "}
            <Box component="span" sx={{ mx: 0.4 }}><InfoChip label="is_system=true" /></Box>)
            {" "}cannot be renamed, deactivated, or deleted. They are shown with a lock icon
            in the Categories tab.
          </Typography>
        </FieldRow>
        <FieldRow label="Slugs" hint="Auto-generated">
          <Typography variant="body2" sx={{ fontSize: "0.8rem", color: "text.secondary" }}>
            A URL-safe slug is generated automatically from the category name on creation.
            Slugs are immutable after creation.
          </Typography>
        </FieldRow>
        <FieldRow label="Assignments">
          <Typography variant="body2" sx={{ fontSize: "0.8rem", color: "text.secondary" }}>
            A person can hold multiple category assignments simultaneously. Assignments
            can be removed (soft-deactivated) without losing the assignment history.
          </Typography>
        </FieldRow>
      </Section>

      {/* Merge */}
      <Section
        title="Person Merge"
        description="Merging two person records is planned but not yet implemented."
      >
        <Box sx={{ display: "flex", alignItems: "flex-start", gap: 1.5 }}>
          <MergeRoundedIcon sx={{ fontSize: 18, color: "text.disabled", mt: 0.2, flexShrink: 0 }} />
          <Typography variant="body2" component="div" sx={{ fontSize: "0.8rem", color: "text.secondary", lineHeight: 1.6 }}>
            The merge endpoint ({" "}
            <Box component="span" sx={{ mx: 0.4 }}><InfoChip label="POST /api/people/persons/:id/merge/" /></Box>)
            {" "}currently returns{" "}
            <Box component="span" sx={{ mx: 0.4 }}><InfoChip label="501 Not Implemented" /></Box>.
            Full merge support — re-pointing all downstream foreign keys and
            deactivating the source record — will be added in a future release.
          </Typography>
        </Box>
      </Section>
    </Box>
  );
}

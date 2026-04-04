"use client";
import React, { useState } from "react";
import {
  Box, Card, TextField, Button, Typography, Checkbox,
  FormControlLabel, Divider, Alert, CircularProgress,
  InputAdornment, IconButton, Link,
} from "@mui/material";
import { useTheme } from "@mui/material/styles";
import LockOutlinedIcon  from "@mui/icons-material/LockOutlined";
import VisibilityIcon    from "@mui/icons-material/Visibility";
import VisibilityOffIcon from "@mui/icons-material/VisibilityOff";
import EmailOutlinedIcon from "@mui/icons-material/EmailOutlined";
import KeyIcon           from "@mui/icons-material/Key";
import { useRouter } from "next/navigation";

function GridOverlay() {
  const { palette } = useTheme();
  const lineColor = palette.mode === "dark" ? "rgba(255,255,255,0.025)" : "rgba(0,0,0,0.05)";
  return (
    <Box
      aria-hidden
      sx={{
        position: "fixed", inset: 0, pointerEvents: "none",
        backgroundImage: `linear-gradient(${lineColor} 1px, transparent 1px), linear-gradient(90deg, ${lineColor} 1px, transparent 1px)`,
        backgroundSize: "48px 48px",
        zIndex: 0,
      }}
    />
  );
}

function GlowBlob({ top, left, color, size }: { top: string; left: string; color: string; size: number }) {
  return (
    <Box aria-hidden sx={{ position: "fixed", top, left, width: size, height: size, borderRadius: "50%", background: color, filter: "blur(120px)", opacity: 0.18, pointerEvents: "none", zIndex: 0 }} />
  );
}

export default function LoginPage() {
  const router = useRouter();
  const theme = useTheme();
  const isDark = theme.palette.mode === "dark";

  const [email, setEmail]           = useState("");
  const [password, setPassword]     = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [rememberMe, setRememberMe] = useState(false);
  const [loading, setLoading]       = useState(false);
  const [error, setError]           = useState("");

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!email || !password) { setError("Please enter your email and password."); return; }
    setLoading(true);
    setError("");
    try {
      const res = await fetch("/api/auth/login/", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, password }),
      });
      if (!res.ok) {
        const data = await res.json().catch(() => ({}));
        throw new Error(data.detail || "Invalid credentials. Please try again.");
      }
      const data = await res.json();
      localStorage.setItem("access_token", data.access);
      if (rememberMe && data.refresh) localStorage.setItem("refresh_token", data.refresh);
      router.push("/");
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Login failed. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <Box sx={{ minHeight: "100vh", display: "flex", alignItems: "center", justifyContent: "center", bgcolor: "background.default", position: "relative", overflow: "hidden", px: 2 }}>
      <GridOverlay />
      {isDark && (
        <>
          <GlowBlob top="-10%" left="-5%"  color="#C8F04A" size={500} />
          <GlowBlob top="60%"  left="75%"  color="#4AF0C8" size={400} />
        </>
      )}

      <Card elevation={0} sx={{ position: "relative", zIndex: 1, width: "100%", maxWidth: 420, borderRadius: "12px", p: { xs: 3, sm: 4 } }}>

        {/* Brand header */}
        <Box sx={{ textAlign: "center", mb: 4 }}>
          <Box sx={{ width: 48, height: 48, borderRadius: "10px", background: "linear-gradient(135deg, #C8F04A 0%, #4AF0C8 100%)", display: "flex", alignItems: "center", justifyContent: "center", mx: "auto", mb: 2 }}>
            <LockOutlinedIcon sx={{ color: "#0D0E10", fontSize: 24 }} />
          </Box>
          <Typography variant="h5" sx={{ fontFamily: "'Syne', sans-serif", fontWeight: 700, letterSpacing: "-0.02em", mb: 0.5 }}>
            Altavisor
          </Typography>
          <Typography variant="body2" sx={{ color: "text.secondary", letterSpacing: "0.06em", textTransform: "uppercase", fontSize: "0.7rem" }}>
            Admin Portal
          </Typography>
        </Box>

        <Typography variant="h6" sx={{ fontFamily: "'Syne', sans-serif", fontWeight: 600, mb: 0.5 }}>
          Sign in
        </Typography>
        <Typography variant="body2" sx={{ color: "text.secondary", mb: 3 }}>
          Enter your credentials to access the admin panel.
        </Typography>

        {error && (
          <Alert severity="error" sx={{ mb: 2.5, fontSize: "0.8rem" }}>
            {error}
          </Alert>
        )}

        <Box component="form" onSubmit={handleSubmit} noValidate>
          {/* Email */}
          <Box sx={{ mb: 2 }}>
            <Typography variant="caption" sx={{ color: "text.secondary", fontWeight: 500, mb: 0.75, display: "block", letterSpacing: "0.04em", textTransform: "uppercase", fontSize: "0.67rem" }}>
              Email Address
            </Typography>
            <TextField
              fullWidth type="email" placeholder="admin@altavisor.io"
              value={email} onChange={(e) => setEmail(e.target.value)}
              autoComplete="email" autoFocus
              InputProps={{ startAdornment: <InputAdornment position="start"><EmailOutlinedIcon sx={{ color: "text.disabled", fontSize: 18 }} /></InputAdornment> }}
            />
          </Box>

          {/* Password */}
          <Box sx={{ mb: 1.5 }}>
            <Typography variant="caption" sx={{ color: "text.secondary", fontWeight: 500, mb: 0.75, display: "block", letterSpacing: "0.04em", textTransform: "uppercase", fontSize: "0.67rem" }}>
              Password
            </Typography>
            <TextField
              fullWidth type={showPassword ? "text" : "password"} placeholder="••••••••••••"
              value={password} onChange={(e) => setPassword(e.target.value)}
              autoComplete="current-password"
              InputProps={{
                startAdornment: <InputAdornment position="start"><KeyIcon sx={{ color: "text.disabled", fontSize: 18 }} /></InputAdornment>,
                endAdornment: (
                  <InputAdornment position="end">
                    <IconButton size="small" onClick={() => setShowPassword((s) => !s)} edge="end" sx={{ color: "text.disabled", "&:hover": { color: "text.secondary" } }} tabIndex={-1}>
                      {showPassword ? <VisibilityOffIcon sx={{ fontSize: 18 }} /> : <VisibilityIcon sx={{ fontSize: 18 }} />}
                    </IconButton>
                  </InputAdornment>
                ),
              }}
            />
          </Box>

          {/* Remember + forgot */}
          <Box sx={{ display: "flex", alignItems: "center", justifyContent: "space-between", mb: 3 }}>
            <FormControlLabel
              control={<Checkbox size="small" checked={rememberMe} onChange={(e) => setRememberMe(e.target.checked)} sx={{ color: "action.disabledBackground", "&.Mui-checked": { color: "primary.main" }, p: 0.5 }} />}
              label={<Typography variant="caption" sx={{ color: "text.secondary" }}>Remember me</Typography>}
            />
            <Link href="#" underline="hover" sx={{ fontSize: "0.75rem", color: "primary.main", fontWeight: 500 }}>
              Forgot password?
            </Link>
          </Box>

          {/* Sign in */}
          <Button type="submit" fullWidth variant="contained" disabled={loading} sx={{ mb: 2, py: 1.25, fontWeight: 700, fontSize: "0.875rem", letterSpacing: "0.02em", borderRadius: "8px" }}>
            {loading ? <CircularProgress size={18} sx={{ color: "primary.contrastText", opacity: 0.7 }} /> : "Sign in"}
          </Button>

          <Box sx={{ display: "flex", alignItems: "center", gap: 1.5, mb: 2 }}>
            <Divider sx={{ flex: 1 }} />
            <Typography variant="caption" sx={{ color: "text.disabled", whiteSpace: "nowrap" }}>or continue with</Typography>
            <Divider sx={{ flex: 1 }} />
          </Box>

          <Button fullWidth variant="outlined" onClick={() => { window.location.href = "/api/auth/sso/"; }}
            sx={{ py: 1.1, fontSize: "0.8rem", fontWeight: 500, borderRadius: "8px", borderColor: "divider", color: "text.secondary", "&:hover": { borderColor: "divider", bgcolor: "action.hover", color: "text.primary" } }}>
            Single Sign-On (SSO)
          </Button>
        </Box>

        <Typography variant="caption" sx={{ display: "block", textAlign: "center", color: "text.disabled", mt: 4, lineHeight: 1.6 }}>
          Protected by Altavisor Security.{" "}
          <Link href="#" underline="hover" sx={{ color: "text.secondary" }}>Terms</Link>
          {" "}&middot;{" "}
          <Link href="#" underline="hover" sx={{ color: "text.secondary" }}>Privacy</Link>
        </Typography>
      </Card>
    </Box>
  );
}

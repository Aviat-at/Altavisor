import { createTheme, alpha, Theme } from "@mui/material/styles";

// ─── Brand ─────────────────────────────────────────────────────────────────
// In dark mode: bright lime works great on dark backgrounds.
// In light mode: a darker lime is needed for readable text / buttons on white.
const LIME_BRIGHT = "#C8F04A"; // brand accent — used as bg tints + dark-mode text
const LIME_DARK   = "#5CAD00"; // accessible dark lime — light-mode primary (text/buttons)

// ─── Typography tokens ──────────────────────────────────────────────────────
const fontBody    = "'DM Sans', sans-serif";
const fontHeading = "'Syne', sans-serif";

const typography = {
  fontFamily: fontBody,
  h1: { fontFamily: fontHeading, fontWeight: 800 },
  h2: { fontFamily: fontHeading, fontWeight: 700 },
  h3: { fontFamily: fontHeading, fontWeight: 700 },
  h4: { fontFamily: fontHeading, fontWeight: 600 },
  h5: { fontFamily: fontHeading, fontWeight: 600 },
  h6: { fontFamily: fontHeading, fontWeight: 600 },
} as const;

const shape = { borderRadius: 6 };

// ─── Component overrides (mode-aware) ───────────────────────────────────────
function buildComponents(mode: "dark" | "light") {
  const isDark = mode === "dark";
  const primaryMain = isDark ? LIME_BRIGHT : LIME_DARK;

  return {
    MuiCssBaseline: {
      styleOverrides: {
        "*": { boxSizing: "border-box" },
        "html, body, #__next": { height: "100%", margin: 0 },
        "::-webkit-scrollbar": { width: "5px", height: "5px" },
        "::-webkit-scrollbar-track": { background: isDark ? "#0C0D0F" : "#ECEEF2" },
        "::-webkit-scrollbar-thumb": {
          background: isDark ? "#2A2E38" : "#C0C4CC",
          borderRadius: "3px",
        },
      },
    },

    MuiPaper: {
      styleOverrides: {
        root: {
          backgroundImage: "none", // kills MUI's default dark-mode gradient
          border: isDark ? "1px solid rgba(255,255,255,0.07)" : "1px solid rgba(0,0,0,0.08)",
        },
      },
    },

    MuiButton: {
      styleOverrides: {
        root: { textTransform: "none" as const, fontWeight: 500, letterSpacing: "0.01em" },
        containedPrimary: {
          "&:hover": {
            backgroundColor: isDark ? alpha(LIME_BRIGHT, 0.85) : "#4A9A00",
          },
        },
      },
    },

    MuiTextField: {
      defaultProps: { variant: "outlined" as const, size: "small" as const },
    },

    MuiOutlinedInput: {
      styleOverrides: {
        root: {
          background: isDark ? "rgba(255,255,255,0.03)" : "rgba(0,0,0,0.02)",
          "& fieldset": { borderColor: isDark ? "rgba(255,255,255,0.10)" : "rgba(0,0,0,0.15)" },
          "&:hover fieldset": { borderColor: isDark ? "rgba(255,255,255,0.22)" : "rgba(0,0,0,0.30)" },
          "&.Mui-focused fieldset": { borderColor: primaryMain },
        },
      },
    },

    MuiDivider: {
      styleOverrides: {
        root: { borderColor: isDark ? "rgba(255,255,255,0.07)" : "rgba(0,0,0,0.08)" },
      },
    },

    MuiSwitch: {
      styleOverrides: {
        switchBase: {
          "&.Mui-checked": {
            color: primaryMain,
            "& + .MuiSwitch-track": {
              backgroundColor: alpha(primaryMain, 0.4),
              opacity: 1,
            },
          },
        },
      },
    },

    MuiSlider: {
      styleOverrides: {
        root: { color: primaryMain },
        thumb: { width: 14, height: 14, backgroundColor: primaryMain },
        mark: { backgroundColor: isDark ? "rgba(255,255,255,0.2)" : "rgba(0,0,0,0.2)" },
      },
    },

    MuiToggleButton: {
      styleOverrides: {
        root: {
          color: isDark ? "rgba(255,255,255,0.5)" : "rgba(0,0,0,0.5)",
          borderColor: isDark ? "rgba(255,255,255,0.10)" : "rgba(0,0,0,0.15)",
          fontSize: "0.75rem",
          textTransform: "none" as const,
          "&.Mui-selected": {
            color: primaryMain,
            backgroundColor: alpha(primaryMain, 0.12),
            borderColor: alpha(primaryMain, 0.35),
            "&:hover": { backgroundColor: alpha(primaryMain, 0.16) },
          },
        },
      },
    },

    MuiLinearProgress: {
      styleOverrides: {
        root: {
          borderRadius: 3,
          backgroundColor: isDark ? "rgba(255,255,255,0.07)" : "rgba(0,0,0,0.08)",
        },
      },
    },

    MuiChip: {
      styleOverrides: {
        root: { fontWeight: 600 },
      },
    },

    MuiTooltip: {
      styleOverrides: {
        tooltip: {
          fontSize: "0.72rem",
          background: isDark ? "#22252E" : "#1A1C20",
          color: "#E8EAF0",
          borderRadius: 6,
        },
      },
    },

    MuiMenu: {
      styleOverrides: {
        paper: {
          backgroundImage: "none",
          border: isDark ? "1px solid rgba(255,255,255,0.07)" : "1px solid rgba(0,0,0,0.08)",
          boxShadow: isDark ? "0 8px 32px rgba(0,0,0,0.4)" : "0 8px 32px rgba(0,0,0,0.12)",
        },
      },
    },

    MuiDialog: {
      styleOverrides: {
        paper: {
          backgroundImage: "none",
          border: isDark ? "1px solid rgba(255,255,255,0.07)" : "1px solid rgba(0,0,0,0.08)",
          boxShadow: isDark ? "0 24px 64px rgba(0,0,0,0.6)" : "0 24px 64px rgba(0,0,0,0.18)",
        },
      },
    },

    MuiAlert: {
      styleOverrides: {
        root: { borderRadius: 8, fontSize: "0.82rem" },
      },
    },
  };
}

// ─── Dark theme ─────────────────────────────────────────────────────────────
export const darkTheme = createTheme({
  palette: {
    mode: "dark",
    primary:   { main: LIME_BRIGHT, dark: "#A8CA30", light: "#D6F560", contrastText: "#0C0D0F" },
    secondary: { main: "#4AF0C8",   dark: "#2EBFA0" },
    error:     { main: "#F04A4A" },
    warning:   { main: "#F0B84A" },
    info:      { main: "#4AA0F0" },
    success:   { main: "#4AE08A" },
    background: { default: "#0C0D0F", paper: "#13151A" },
    text:      { primary: "#E8EAF0", secondary: "#6B7080", disabled: "#3A4050" },
    divider:   "rgba(255,255,255,0.07)",
    action: {
      hover:              "rgba(255,255,255,0.04)",
      selected:           "rgba(200,240,74,0.12)",
      disabledBackground: "rgba(255,255,255,0.07)",
      disabled:           "rgba(255,255,255,0.30)",
    },
  },
  typography,
  shape,
  components: buildComponents("dark"),
});

// ─── Light theme ─────────────────────────────────────────────────────────────
export const lightTheme = createTheme({
  palette: {
    mode: "light",
    primary:   { main: LIME_DARK,  light: LIME_BRIGHT, dark: "#3D7A00", contrastText: "#FFFFFF" },
    secondary: { main: "#009976",  dark: "#007055" },
    error:     { main: "#D63C3C" },
    warning:   { main: "#B76E00" },
    info:      { main: "#0275D8" },
    success:   { main: "#1E8A45" },
    background: { default: "#F4F5F7", paper: "#FFFFFF" },
    text:      { primary: "#111318", secondary: "#5A6070", disabled: "#9AA0B0" },
    divider:   "rgba(0,0,0,0.08)",
    action: {
      hover:              "rgba(0,0,0,0.04)",
      selected:           "rgba(92,173,0,0.12)",
      disabledBackground: "rgba(0,0,0,0.07)",
      disabled:           "rgba(0,0,0,0.26)",
    },
  },
  typography,
  shape,
  components: buildComponents("light"),
});

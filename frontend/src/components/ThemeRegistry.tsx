"use client";
import * as React from "react";
import { ThemeProvider } from "@mui/material/styles";
import CssBaseline from "@mui/material/CssBaseline";
import { darkTheme, lightTheme } from "@/lib/theme";

type ColorMode = "dark" | "light";

interface ColorModeContextValue {
  mode: ColorMode;
  toggleColorMode: () => void;
}

export const ColorModeContext = React.createContext<ColorModeContextValue>({
  mode: "dark",
  toggleColorMode: () => {},
});

export function useColorMode() {
  return React.useContext(ColorModeContext);
}

export default function ThemeRegistry({ children }: { children: React.ReactNode }) {
  const [mode, setMode] = React.useState<ColorMode>("dark");

  // Hydrate from localStorage after mount (avoids SSR mismatch)
  React.useEffect(() => {
    const saved = localStorage.getItem("color-mode") as ColorMode | null;
    if (saved === "light" || saved === "dark") setMode(saved);
  }, []);

  const toggleColorMode = React.useCallback(() => {
    setMode((prev) => {
      const next = prev === "dark" ? "light" : "dark";
      localStorage.setItem("color-mode", next);
      return next;
    });
  }, []);

  const ctx = React.useMemo(() => ({ mode, toggleColorMode }), [mode, toggleColorMode]);
  const theme = mode === "dark" ? darkTheme : lightTheme;

  return (
    <ColorModeContext.Provider value={ctx}>
      <ThemeProvider theme={theme}>
        <CssBaseline />
        {children}
      </ThemeProvider>
    </ColorModeContext.Provider>
  );
}

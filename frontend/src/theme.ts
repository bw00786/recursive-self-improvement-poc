import { createTheme } from "@mui/material/styles";

export const theme = createTheme({
  palette: {
    mode: "dark",
    primary: { main: "#6ea8fe" },
    secondary: { main: "#9b7bff" },
    success: { main: "#4caf7d" },
    error: { main: "#e57373" },
    warning: { main: "#ffb74d" },
    background: { default: "#0d1117", paper: "#161b22" },
  },
  typography: {
    fontFamily: "'Segoe UI', 'Inter', system-ui, sans-serif",
    h5: { fontWeight: 700, letterSpacing: 1 },
  },
  shape: { borderRadius: 10 },
});

import { AppBar, Box, Drawer, List, ListItemButton, ListItemIcon, ListItemText, Toolbar, Typography } from "@mui/material";
import DashboardIcon from "@mui/icons-material/Dashboard";
import ScienceIcon from "@mui/icons-material/Science";
import EmojiEventsIcon from "@mui/icons-material/EmojiEvents";
import AccountTreeIcon from "@mui/icons-material/AccountTree";
import ApprovalIcon from "@mui/icons-material/Approval";
import SettingsIcon from "@mui/icons-material/Settings";
import { Link, useLocation } from "react-router-dom";
import { ReactNode } from "react";

const NAV = [
  { to: "/", label: "Dashboard", icon: <DashboardIcon /> },
  { to: "/experiments", label: "Experiments", icon: <ScienceIcon /> },
  { to: "/approvals", label: "Approval Queue", icon: <ApprovalIcon /> },
  { to: "/champions", label: "Champions", icon: <EmojiEventsIcon /> },
  { to: "/evolution", label: "Evolution", icon: <AccountTreeIcon /> },
  { to: "/system", label: "System", icon: <SettingsIcon /> },
];

export default function Layout({ children }: { children: ReactNode }) {
  const loc = useLocation();
  return (
    <Box sx={{ display: "flex" }}>
      <AppBar position="fixed" sx={{ zIndex: (t) => t.zIndex.drawer + 1, bgcolor: "#010409", borderBottom: "1px solid #30363d" }}>
        <Toolbar>
          <ScienceIcon sx={{ mr: 1.5, color: "#6ea8fe" }} />
          <Typography variant="h5" color="primary">RECURSIVE AI LAB</Typography>
          <Typography variant="caption" sx={{ ml: 2, color: "text.secondary" }}>
            controlled self-improvement control plane
          </Typography>
        </Toolbar>
      </AppBar>
      <Drawer variant="permanent" sx={{ width: 220, "& .MuiDrawer-paper": { width: 220, boxSizing: "border-box" } }}>
        <Toolbar />
        <List>
          {NAV.map((n) => (
            <ListItemButton key={n.to} component={Link} to={n.to} selected={loc.pathname === n.to}>
              <ListItemIcon>{n.icon}</ListItemIcon>
              <ListItemText primary={n.label} />
            </ListItemButton>
          ))}
        </List>
      </Drawer>
      <Box component="main" sx={{ flexGrow: 1, p: 3 }}>
        <Toolbar />
        {children}
      </Box>
    </Box>
  );
}

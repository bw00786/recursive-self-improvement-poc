import { Box, LinearProgress, Typography } from "@mui/material";

export default function MetricBar({ label, value, format = "pct" }: {
  label: string; value: number; format?: "pct" | "sec";
}) {
  const pct = format === "pct" ? value * 100 : Math.max(0, 100 - value * 10);
  const display = format === "pct" ? `${(value * 100).toFixed(1)}` : `${value.toFixed(2)}s`;
  return (
    <Box sx={{ display: "flex", alignItems: "center", gap: 2, my: 0.75 }}>
      <Typography sx={{ width: 170 }} color="text.secondary">{label}</Typography>
      <LinearProgress variant="determinate" value={Math.min(100, pct)}
        sx={{ flexGrow: 1, height: 10, borderRadius: 5 }} />
      <Typography sx={{ width: 70, textAlign: "right", fontFamily: "monospace" }}>{display}</Typography>
    </Box>
  );
}

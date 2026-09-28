import { useQuery } from "@tanstack/react-query";
import { Box, Card, CardContent, Chip, Typography } from "@mui/material";
import { Bar, BarChart, CartesianGrid, Cell, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { api } from "../api/client";

export default function Evolution() {
  const { data: experiments } = useQuery({ queryKey: ["experiments"], queryFn: api.experiments });
  const { data: strategies } = useQuery({ queryKey: ["strategies"], queryFn: api.strategies });

  const history = [...(experiments ?? [])].reverse();
  const stratChart = (strategies ?? []).map((s) => ({
    name: s.strategy,
    rate: +(s.success_rate * 100).toFixed(1),
    improvement: +s.average_improvement.toFixed(2),
  }));

  return (
    <Box>
      <Typography variant="h5" gutterBottom>Evolution &amp; Strategy Learning</Typography>
      <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
        The recursive layer: strategy statistics are learned from real experiments and
        fed back into the improvement agent's next hypothesis selection.
      </Typography>

      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Typography variant="overline" color="text.secondary">EXPERIMENT TIMELINE</Typography>
          {history.length === 0 && <Typography color="text.secondary">No experiments yet.</Typography>}
          {history.map((e) => (
            <Box key={e.id} sx={{ display: "flex", gap: 1.5, alignItems: "center", py: 0.75, borderBottom: "1px solid #21262d" }}>
              <Typography fontFamily="monospace" color="text.secondary">#{e.id}</Typography>
              <Chip size="small" label={e.strategy ?? "…"} variant="outlined" />
              <Typography sx={{ flexGrow: 1 }} variant="body2" noWrap>
                {(e.hypothesis as { hypothesis?: string } | null)?.hypothesis ?? ""}
              </Typography>
              <Typography fontFamily="monospace"
                color={e.status === "PROMOTED" ? "success.main" : e.status === "REJECTED" || e.status === "FAILED" ? "error.main" : "warning.main"}>
                {e.result_score != null ? e.result_score.toFixed(1) : "—"} {e.status}
              </Typography>
            </Box>
          ))}
        </CardContent>
      </Card>

      <Card>
        <CardContent sx={{ height: 300 }}>
          <Typography variant="overline" color="text.secondary">
            LEARNED STRATEGY SUCCESS RATES (from actual experiments)
          </Typography>
          {stratChart.length === 0 ? (
            <Typography color="text.secondary" sx={{ mt: 2 }}>
              No strategy data yet — run a few improvement cycles.
            </Typography>
          ) : (
            <ResponsiveContainer>
              <BarChart data={stratChart} margin={{ top: 20, right: 30, left: 0, bottom: 40 }}>
                <CartesianGrid stroke="#30363d" />
                <XAxis dataKey="name" stroke="#8b949e" angle={-20} textAnchor="end" interval={0} />
                <YAxis unit="%" stroke="#8b949e" />
                <Tooltip contentStyle={{ background: "#161b22", border: "1px solid #30363d" }} />
                <Bar dataKey="rate" name="success rate">
                  {stratChart.map((s) => (
                    <Cell key={s.name} fill={s.rate >= 50 ? "#4caf7d" : "#e57373"} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          )}
        </CardContent>
      </Card>
    </Box>
  );
}

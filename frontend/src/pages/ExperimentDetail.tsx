import { useQuery } from "@tanstack/react-query";
import { Alert, Box, Card, CardContent, Chip, Grid, Typography } from "@mui/material";
import { useParams } from "react-router-dom";
import { api } from "../api/client";
import StatusChip from "../components/StatusChip";

export default function ExperimentDetail() {
  const { id = "" } = useParams();
  const { data: exp } = useQuery({ queryKey: ["experiment", id], queryFn: () => api.experiment(id) });
  const { data: candidates } = useQuery({
    queryKey: ["experiment-candidates", id], queryFn: () => api.experimentCandidates(id),
  });
  const cand = candidates?.[0];
  const { data: evals } = useQuery({
    queryKey: ["evaluations", cand?.id],
    queryFn: () => api.evaluations(cand!.id),
    enabled: !!cand?.metrics,
  });
  if (!exp) return null;
  const h = exp.hypothesis as Record<string, unknown> | null;

  return (
    <Box>
      <Typography variant="h5" gutterBottom>Experiment #{exp.id} <StatusChip status={exp.status} /></Typography>
      {exp.error && <Alert severity="error" sx={{ mb: 2 }}>{exp.error}</Alert>}
      <Grid container spacing={3}>
        <Grid item xs={12} md={6}>
          <Card><CardContent>
            <Typography variant="overline" color="text.secondary">HYPOTHESIS</Typography>
            <Typography sx={{ mt: 1 }}>{String(h?.hypothesis ?? "—")}</Typography>
            <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
              Change: {String(h?.proposed_change ?? "—")}
            </Typography>
            <Typography variant="body2" color="text.secondary">
              Expected: {String(h?.expected_metric ?? "")} +{String(h?.expected_improvement ?? "")}
              {"  "}· Risk: {String(h?.risk ?? "—")}
            </Typography>
            <Box sx={{ mt: 1 }}>
              {((h?.implementation_plan as string[]) ?? []).map((s, i) => (
                <Chip key={i} size="small" label={s} sx={{ mr: 0.5, mb: 0.5 }} variant="outlined" />
              ))}
            </Box>
          </CardContent></Card>
        </Grid>
        <Grid item xs={12} md={6}>
          <Card><CardContent>
            <Typography variant="overline" color="text.secondary">RESULT</Typography>
            {cand?.decision ? (
              <Box sx={{ mt: 1 }}>
                <Typography variant="h6">
                  {cand.decision.champion_score.toFixed(1)} → {cand.decision.candidate_score.toFixed(1)}
                  <Typography component="span" color={cand.decision.delta > 0 ? "success.main" : "error.main"} sx={{ ml: 1 }}>
                    {cand.decision.delta > 0 ? "+" : ""}{cand.decision.delta.toFixed(1)}
                  </Typography>
                </Typography>
                {cand.decision.hard_violations.map((v) => (
                  <Alert key={v} severity="error" sx={{ mt: 1 }}>{v}</Alert>
                ))}
                {cand.decision.reasons.map((r) => (
                  <Typography key={r} variant="body2" color="warning.main">{r}</Typography>
                ))}
                <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
                  Files changed: {cand.files_changed.join(", ") || "none"}
                </Typography>
              </Box>
            ) : (
              <Typography color="text.secondary" sx={{ mt: 1 }}>
                {exp.status === "FAILED" ? "Experiment failed." : "Running — results appear when evaluation completes."}
              </Typography>
            )}
          </CardContent></Card>
        </Grid>
        {evals && evals.length > 0 && (
          <Grid item xs={12}>
            <Card><CardContent>
              <Typography variant="overline" color="text.secondary">PER-METRIC COMPARISON</Typography>
              {evals.map((e) => (
                <Box key={e.id} sx={{ display: "flex", gap: 2, py: 0.5, fontFamily: "monospace" }}>
                  <Typography sx={{ width: 180 }}>{e.metric_name}</Typography>
                  <Typography sx={{ width: 100 }}>{e.metric_value.toFixed(4)}</Typography>
                  <Typography color="text.secondary" sx={{ width: 100 }}>
                    base {e.baseline_value?.toFixed(4) ?? "—"}
                  </Typography>
                  <Typography color={(e.delta ?? 0) >= 0 ? "success.main" : "error.main"}>
                    {e.delta != null ? `${e.delta >= 0 ? "+" : ""}${e.delta.toFixed(4)}` : ""}
                  </Typography>
                </Box>
              ))}
            </CardContent></Card>
          </Grid>
        )}
      </Grid>
    </Box>
  );
}

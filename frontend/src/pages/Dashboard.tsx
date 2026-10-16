import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Alert, Box, Button, Card, CardContent, Grid, TextField, Typography } from "@mui/material";
import PlayArrowIcon from "@mui/icons-material/PlayArrow";
import { useNavigate } from "react-router-dom";
import { api } from "../api/client";
import MetricBar from "../components/MetricBar";
import StatusChip from "../components/StatusChip";

export default function Dashboard() {
  const qc = useQueryClient();
  const nav = useNavigate();
  const { data: m } = useQuery({ queryKey: ["metrics"], queryFn: api.metrics });
  const { data: experiments } = useQuery({ queryKey: ["experiments"], queryFn: api.experiments });

  const startCycle = useMutation({
    mutationFn: async () => {
      const exp = await api.createExperiment();
      await api.runExperiment(exp.id);
      return exp;
    },
    onSuccess: (exp) => {
      qc.invalidateQueries();
      nav(`/experiments/${exp.id}`);
    },
  });
  const baseline = useMutation({
    mutationFn: api.runBaseline,
    onSuccess: () => qc.invalidateQueries(),
  });
  const [cycles, setCycles] = useState(5);
  const { data: auto } = useQuery({ queryKey: ["auto"], queryFn: api.autoStatus });
  const autoStart = useMutation({
    mutationFn: () => api.autoStart(cycles),
    onSuccess: () => qc.invalidateQueries(),
  });
  const autoStop = useMutation({
    mutationFn: api.autoStop,
    onSuccess: () => qc.invalidateQueries(),
  });

  const running = experiments?.find((e) => ["RUNNING", "GENERATING", "EVALUATING"].includes(e.status));

  return (
    <Box>
      <Box sx={{ display: "flex", gap: 2, mb: 3, alignItems: "center", flexWrap: "wrap" }}>
        <Button variant="contained" startIcon={<PlayArrowIcon />}
          disabled={startCycle.isPending || !!running || !!auto?.running}
          onClick={() => startCycle.mutate()}>
          Start Improvement Cycle
        </Button>
        <Button variant="outlined" disabled={baseline.isPending || !!auto?.running}
          onClick={() => baseline.mutate()}>
          Re-run Baseline
        </Button>
        <TextField size="small" type="number" label="Cycles" sx={{ width: 90 }}
          value={cycles} disabled={!!auto?.running}
          inputProps={{ min: 1, max: 50 }}
          onChange={(e) => setCycles(Math.max(1, Math.min(50, Number(e.target.value) || 1)))} />
        {auto?.running ? (
          <Button color="warning" variant="outlined" disabled={auto.stop_requested || autoStop.isPending}
            onClick={() => autoStop.mutate()}>
            {auto.stop_requested ? "Stopping after this cycle…" : "Stop Auto Run"}
          </Button>
        ) : (
          <Button variant="contained" color="secondary" disabled={autoStart.isPending || !!running}
            onClick={() => autoStart.mutate()}>
            Auto-run {cycles} cycles
          </Button>
        )}
      </Box>
      {startCycle.isError && <Alert severity="error" sx={{ mb: 2 }}>{String(startCycle.error)}</Alert>}
      {autoStart.isError && <Alert severity="error" sx={{ mb: 2 }}>{String(autoStart.error)}</Alert>}
      {auto?.running && (
        <Alert severity="info" sx={{ mb: 2 }}>
          Auto run: cycle {Math.min(auto.cycles_completed + 1, auto.cycles_requested)} of {auto.cycles_requested}
          {auto.promoted.length > 0 && ` — promoted ${auto.promoted.map((v) => "v" + v).join(", ")}`}
        </Alert>
      )}
      {!auto?.running && auto?.stop_reason && (
        <Alert severity="success" sx={{ mb: 2 }}>
          Last auto run: {auto.cycles_completed}/{auto.cycles_requested} cycles, stopped — {auto.stop_reason}
          {auto.promoted.length > 0 ? `; promoted ${auto.promoted.map((v) => "v" + v).join(", ")}` : "; no promotions"}
        </Alert>
      )}

      <Grid container spacing={3}>
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="overline" color="text.secondary">CHAMPION</Typography>
              <Typography variant="h4">
                v{m?.champion?.version ?? "—"}
                <Typography component="span" variant="h5" color="primary" sx={{ ml: 2 }}>
                  score {m?.champion?.score?.toFixed(1) ?? "—"}
                </Typography>
              </Typography>
              <Box sx={{ mt: 2 }}>
                <MetricBar label="Accuracy" value={m?.champion?.metrics?.accuracy ?? 0} />
                <MetricBar label="Citation accuracy" value={m?.champion?.metrics?.citation_accuracy ?? 0} />
                <MetricBar label="Retrieval recall" value={m?.champion?.metrics?.retrieval_recall ?? 0} />
                <MetricBar label="Reliability" value={m?.champion?.metrics?.reliability ?? 0} />
                <MetricBar label="Latency" value={m?.champion?.metrics?.latency_avg_s ?? 0} format="sec" />
              </Box>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} md={6}>
          <Card sx={{ mb: 3 }}>
            <CardContent>
              <Typography variant="overline" color="text.secondary">CURRENT EXPERIMENT</Typography>
              {running ? (
                <Box sx={{ mt: 1 }}>
                  <Typography>#{running.id} — {running.strategy ?? "starting…"}</Typography>
                  <Box sx={{ mt: 1 }}><StatusChip status={running.status} /></Box>
                  <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
                    {(running.hypothesis as { hypothesis?: string } | null)?.hypothesis ?? ""}
                  </Typography>
                </Box>
              ) : (
                <Typography color="text.secondary" sx={{ mt: 1 }}>
                  No experiment running. Start an improvement cycle.
                </Typography>
              )}
            </CardContent>
          </Card>
          <Card>
            <CardContent>
              <Typography variant="overline" color="text.secondary">LAB STATISTICS</Typography>
              <Grid container spacing={1} sx={{ mt: 0.5 }}>
                {[
                  ["Experiments", m?.experiments_total],
                  ["Promoted", m?.experiments_promoted],
                  ["Rejected", m?.experiments_rejected],
                  ["Failed", m?.experiments_failed],
                  ["Awaiting approval", m?.awaiting_approval],
                ].map(([label, v]) => (
                  <Grid item xs={4} key={label as string}>
                    <Typography variant="h5">{v ?? "—"}</Typography>
                    <Typography variant="caption" color="text.secondary">{label}</Typography>
                  </Grid>
                ))}
              </Grid>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Box>
  );
}

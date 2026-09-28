import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Alert, Box, Button, Card, CardContent, Grid, Typography } from "@mui/material";
import { api } from "../api/client";

export default function Approvals() {
  const qc = useQueryClient();
  const { data } = useQuery({
    queryKey: ["candidates"],
    queryFn: api.candidates,
    select: (cs) => cs.filter((c) => c.status === "AWAITING_APPROVAL"),
  });
  const act = useMutation({
    mutationFn: ({ id, approve }: { id: string; approve: boolean }) =>
      approve ? api.approve(id) : api.reject(id),
    onSuccess: () => qc.invalidateQueries(),
  });

  return (
    <Box>
      <Typography variant="h5" gutterBottom>Approval Queue</Typography>
      <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
        Promotion never happens automatically. Every champion change requires a human decision.
      </Typography>
      {act.isError && <Alert severity="error" sx={{ mb: 2 }}>{String(act.error)}</Alert>}
      {data?.length === 0 && <Alert severity="info">No candidates awaiting approval.</Alert>}
      <Grid container spacing={2}>
        {data?.map((c) => (
          <Grid item xs={12} md={6} key={c.id}>
            <Card>
              <CardContent>
                <Typography variant="h6">{c.id}</Typography>
                <Typography variant="body2" color="text.secondary">{c.description}</Typography>
                {c.decision && (
                  <Box sx={{ my: 1.5, fontFamily: "monospace" }}>
                    <Typography>
                      Score: {c.decision.champion_score.toFixed(1)} → {c.decision.candidate_score.toFixed(1)}
                      <Typography component="span" color="success.main"> (+{c.decision.delta.toFixed(1)})</Typography>
                    </Typography>
                    {c.metrics && (
                      <Typography variant="body2" color="text.secondary">
                        acc {(c.metrics.accuracy * 100).toFixed(1)}% · cit{" "}
                        {(c.metrics.citation_accuracy * 100).toFixed(1)}% · recall{" "}
                        {(c.metrics.retrieval_recall * 100).toFixed(1)}% ·{" "}
                        {c.metrics.latency_avg_s.toFixed(2)}s
                      </Typography>
                    )}
                    <Typography variant="body2" color="text.secondary">
                      Files: {c.files_changed.join(", ")}
                    </Typography>
                  </Box>
                )}
                <Box sx={{ display: "flex", gap: 1 }}>
                  <Button color="error" variant="outlined" disabled={act.isPending}
                    onClick={() => act.mutate({ id: c.id, approve: false })}>REJECT</Button>
                  <Button color="success" variant="contained" disabled={act.isPending}
                    onClick={() => act.mutate({ id: c.id, approve: true })}>APPROVE &amp; PROMOTE</Button>
                </Box>
              </CardContent>
            </Card>
          </Grid>
        ))}
      </Grid>
    </Box>
  );
}

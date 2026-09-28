import { useQuery } from "@tanstack/react-query";
import { Card, CardContent, Chip, Grid, Typography } from "@mui/material";
import CheckCircleIcon from "@mui/icons-material/CheckCircle";
import CancelIcon from "@mui/icons-material/Cancel";
import { api } from "../api/client";

function Row({ label, ok, detail }: { label: string; ok: boolean; detail: string }) {
  return (
    <Grid container alignItems="center" sx={{ py: 1, borderBottom: "1px solid #21262d" }}>
      <Grid item xs={4}><Typography color="text.secondary">{label}</Typography></Grid>
      <Grid item xs={1}>
        {ok ? <CheckCircleIcon color="success" /> : <CancelIcon color="error" />}
      </Grid>
      <Grid item xs={7}><Typography fontFamily="monospace">{detail}</Typography></Grid>
    </Grid>
  );
}

export default function SystemPage() {
  const { data: h } = useQuery({ queryKey: ["health"], queryFn: api.health });
  if (!h) return null;
  return (
    <>
      <Typography variant="h5" gutterBottom>System</Typography>
      <Card sx={{ maxWidth: 760 }}>
        <CardContent>
          <Row label="LLM" ok={h.ollama_reachable || h.mock_llm} detail={h.llm} />
          <Row label="Ollama" ok={h.ollama_reachable} detail={h.ollama_reachable ? "connected" : "unreachable (mock mode)"} />
          <Row label="Docker sandbox" ok={h.docker_available}
            detail={h.docker_available ? `isolated (${h.sandbox_mode})` : "unavailable — local fallback (not isolated)"} />
          <Row label="Human approval gate" ok={h.require_human_approval}
            detail={h.require_human_approval ? "required" : "disabled"} />
          <Row label="Langfuse" ok={true} detail={h.langfuse_enabled ? "enabled" : "disabled (optional)"} />
        </CardContent>
      </Card>
      <Typography variant="body2" color="text.secondary" sx={{ mt: 2, maxWidth: 760 }}>
        The improvement agent can propose changes but can never modify the benchmark,
        evaluator, promotion rules, security controls, or audit log — and no candidate
        is promoted without explicit human approval.
      </Typography>
    </>
  );
}

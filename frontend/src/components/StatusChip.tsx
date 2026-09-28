import { Chip } from "@mui/material";

const COLORS: Record<string, "success" | "error" | "warning" | "info" | "default"> = {
  PROMOTED: "success",
  AWAITING_APPROVAL: "warning",
  REJECTED: "error",
  FAILED: "error",
  RUNNING: "info",
  GENERATING: "info",
  EVALUATING: "info",
  PROPOSED: "default",
  CREATED: "default",
  EVALUATED: "info",
};

export default function StatusChip({ status }: { status: string }) {
  return <Chip size="small" label={status} color={COLORS[status] ?? "default"} variant={status === "PROMOTED" ? "filled" : "outlined"} />;
}

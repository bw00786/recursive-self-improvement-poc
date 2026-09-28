import { useQuery } from "@tanstack/react-query";
import { Paper, Table, TableBody, TableCell, TableHead, TableRow, Typography } from "@mui/material";
import { Link } from "react-router-dom";
import { api } from "../api/client";
import StatusChip from "../components/StatusChip";

export default function Experiments() {
  const { data } = useQuery({ queryKey: ["experiments"], queryFn: api.experiments });
  return (
    <>
      <Typography variant="h5" gutterBottom>Experiments</Typography>
      <Paper>
        <Table size="small">
          <TableHead>
            <TableRow>
              <TableCell>ID</TableCell><TableCell>Strategy</TableCell>
              <TableCell>Hypothesis</TableCell><TableCell>Status</TableCell>
              <TableCell align="right">Score</TableCell><TableCell>Created</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {data?.map((e) => (
              <TableRow key={e.id} hover>
                <TableCell>
                  <Link to={`/experiments/${e.id}`} style={{ color: "#6ea8fe" }}>#{e.id}</Link>
                </TableCell>
                <TableCell>{e.strategy ?? "—"}</TableCell>
                <TableCell sx={{ maxWidth: 380 }}>
                  <Typography variant="body2" noWrap>
                    {(e.hypothesis as { hypothesis?: string } | null)?.hypothesis ?? "—"}
                  </Typography>
                </TableCell>
                <TableCell><StatusChip status={e.status} /></TableCell>
                <TableCell align="right">{e.result_score?.toFixed(1) ?? "—"}</TableCell>
                <TableCell>{new Date(e.created_at).toLocaleString()}</TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </Paper>
    </>
  );
}

import { useQuery } from "@tanstack/react-query";
import { Card, CardContent, Paper, Table, TableBody, TableCell, TableHead, TableRow, Typography } from "@mui/material";
import { Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis, CartesianGrid } from "recharts";
import { api } from "../api/client";

export default function Champions() {
  const { data } = useQuery({ queryKey: ["champions"], queryFn: api.champions });
  const chart = data?.map((c) => ({ version: `v${c.version}`, score: c.score })) ?? [];
  return (
    <>
      <Typography variant="h5" gutterBottom>Champion History</Typography>
      <Card sx={{ mb: 3, height: 280 }}>
        <CardContent sx={{ height: "100%" }}>
          <ResponsiveContainer>
            <LineChart data={chart} margin={{ top: 10, right: 30, bottom: 0, left: 0 }}>
              <CartesianGrid stroke="#30363d" />
              <XAxis dataKey="version" stroke="#8b949e" />
              <YAxis domain={["dataMin - 2", "dataMax + 2"]} stroke="#8b949e" />
              <Tooltip contentStyle={{ background: "#161b22", border: "1px solid #30363d" }} />
              <Line type="monotone" dataKey="score" stroke="#6ea8fe" strokeWidth={3} dot={{ r: 5 }} />
            </LineChart>
          </ResponsiveContainer>
        </CardContent>
      </Card>
      <Paper>
        <Table size="small">
          <TableHead>
            <TableRow>
              <TableCell>Version</TableCell><TableCell align="right">Score</TableCell>
              <TableCell align="right">Accuracy</TableCell><TableCell align="right">Recall</TableCell>
              <TableCell>Status</TableCell><TableCell>Approved by</TableCell><TableCell>Created</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {data?.map((c) => (
              <TableRow key={c.id}>
                <TableCell>v{c.version}</TableCell>
                <TableCell align="right">{c.score.toFixed(2)}</TableCell>
                <TableCell align="right">{((c.metrics?.accuracy ?? 0) * 100).toFixed(1)}%</TableCell>
                <TableCell align="right">{((c.metrics?.retrieval_recall ?? 0) * 100).toFixed(1)}%</TableCell>
                <TableCell>{c.status}</TableCell>
                <TableCell>{c.approved_by}</TableCell>
                <TableCell>{new Date(c.created_at).toLocaleString()}</TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </Paper>
    </>
  );
}

# API

Base URL: `http://localhost:8100`

| Method | Path | Purpose |
|---|---|---|
| GET | /api/health | service/LLM/docker status |
| GET | /api/champion | active champion |
| GET | /api/champions | version history |
| GET | /api/experiments | list experiments |
| POST | /api/experiments | create experiment `{objective}` |
| GET | /api/experiments/{id} | experiment detail |
| GET | /api/experiments/{id}/candidates | its candidates |
| POST | /api/experiments/{id}/run | run the improvement loop (background) |
| GET | /api/candidates | list candidates |
| GET | /api/candidates/{id} | candidate detail |
| POST | /api/candidates/{id}/approve | human approve -> promote |
| POST | /api/candidates/{id}/reject | human reject |
| GET | /api/evaluations/{candidateId} | per-metric rows |
| GET | /api/metrics | dashboard summary |
| GET | /api/strategies | learned strategy statistics |
| POST | /api/benchmark/run | (re-)baseline the champion |
| GET | /api/audit | audit log tail |
| GET | /api/mcp/tools | MCP tool schemas |
| POST | /api/mcp/call | invoke MCP tool `{name, arguments}` |

Interactive docs at `/docs`.

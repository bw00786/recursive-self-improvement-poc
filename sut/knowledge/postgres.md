# PostgreSQL

PostgreSQL is an open-source relational database. A B-tree index speeds up
equality and range lookups; EXPLAIN ANALYZE shows the actual query plan and
execution time, which reveals sequential scans that an index could eliminate.

VACUUM reclaims storage from dead tuples left by updates and deletes, and
autovacuum runs it automatically. Full-text search uses tsvector and tsquery
with a GIN index for fast document matching.

A connection pooler such as PgBouncer reduces the cost of many short-lived
connections because each PostgreSQL connection is a separate process.

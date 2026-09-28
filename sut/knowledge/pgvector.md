# pgvector

pgvector adds vector similarity search to PostgreSQL. It stores embeddings in
a vector column and supports exact nearest neighbor search plus approximate
indexes: IVFFlat partitions vectors into lists and HNSW builds a navigable
small-world graph. HNSW usually gives better recall and query speed but uses
more memory and slower index builds than IVFFlat.

Distance operators include <-> for L2 distance and <=> for cosine distance.
Creating an index requires choosing lists or m parameters that trade recall
against build time and memory.

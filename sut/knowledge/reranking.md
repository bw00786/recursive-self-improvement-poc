# Reranking

A reranker rescores the top-k candidates from a fast first-stage retriever.
Cross-encoder rerankers process the query and one document together, which is
more accurate than bi-encoder retrieval but too slow to run over a whole
corpus, so rerankers are applied only to the top 20 to 100 candidates.

Reranking typically improves precision at the top of the list, which matters
when the generator only sees the first few chunks. A reranking stage usually
adds 50 to 300 milliseconds of latency per query.

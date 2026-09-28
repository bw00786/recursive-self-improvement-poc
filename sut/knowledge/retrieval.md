# Retrieval

Hybrid retrieval combines lexical retrieval (BM25 keyword matching) with
semantic vector retrieval (embedding similarity). BM25 ranks documents by
term frequency and inverse document frequency, so it excels at exact keyword
matches such as function names and error codes. Vector retrieval embeds the
query and documents into a dense vector space and ranks by cosine similarity,
so it excels at synonyms and paraphrases.

Reciprocal rank fusion (RRF) merges two ranked lists by summing 1/(k + rank)
across the lists, typically with k = 60. RRF requires no score normalization,
which makes it a robust default for combining BM25 and vector rankings.

A common hybrid failure mode is vocabulary mismatch: a user asks about
"speeding up queries" while the document says "indexing". Vector retrieval
handles this better than pure BM25.

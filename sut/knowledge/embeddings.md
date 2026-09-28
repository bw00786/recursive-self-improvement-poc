# Embeddings

A vector embedding maps text to a dense vector of floating-point numbers so
that semantically similar texts have high cosine similarity. Cosine similarity
measures the angle between two vectors and ranges from -1 to 1; values near 1
indicate strong similarity.

Embedding models are sensitive to domain shift: a model trained on general
web text may rank technical jargon poorly. Normalizing vectors to unit length
makes cosine similarity equivalent to a dot product, which is faster to
compute in approximate nearest neighbor indexes.

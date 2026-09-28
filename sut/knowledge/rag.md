# Retrieval-Augmented Generation

Retrieval-augmented generation (RAG) retrieves relevant documents and inserts
them into the prompt so the language model grounds its answer in supplied
context rather than parametric memory. Grounding reduces hallucination because
the model can quote provided text.

Citations make RAG answers auditable: the model marks each claim with the
source document it came from. Citation accuracy measures whether the cited
sources actually contain the answer.

A RAG pipeline is evaluated on retrieval recall (did we fetch the right
documents), answer accuracy (is the answer correct), and citation accuracy
(are claims properly attributed).

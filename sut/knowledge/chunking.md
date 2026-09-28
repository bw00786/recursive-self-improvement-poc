# Chunking

Chunking splits documents into passages small enough to embed and retrieve.
Chunk sizes between 256 and 1024 characters are common; smaller chunks improve
retrieval precision because each chunk contains one idea, while larger chunks
preserve more surrounding context for the generator.

Chunk overlap of 10 to 15 percent prevents facts that span a boundary from
being split in half. Overlap that is too large wastes the context window with
duplicated text.

Splitting on paragraph or section boundaries produces more coherent chunks
than splitting at fixed character offsets.

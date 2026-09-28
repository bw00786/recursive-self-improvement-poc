# Python

The GIL (global interpreter lock) allows only one thread to execute Python
bytecode at a time in CPython, so threads do not speed up CPU-bound work;
multiprocessing or native extensions bypass the GIL.

asyncio runs many I/O-bound coroutines on one thread using an event loop,
which suits high-concurrency network services. A generator yields values
lazily with the yield keyword and keeps its state between yields, which saves
memory on large sequences.

Type hints are optional annotations checked by tools like mypy; they have no
runtime cost and no runtime enforcement by default.

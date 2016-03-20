# Sampling in a race detector #

The idea to use sampling during race detection was (first?) [introduced](http://www.cs.ucla.edu/~dlmarino/pubs/pldi09.pdf) at PLDI'09 by Marino et al.

This idea is very simple: instead of analyzing all memory accesses, we do sampling.
For each memory access (or a set of accesses) we maintain a counter of
executions. If a memory access (set of accesses) has been executed more than a certain threshold, we start skipping this access sometimes.
The main question (discussed in the paper) is when to analyze the access and when not.

We are experimenting with this approach in ThreadSanitizer and it shows very nice results (up to 4x speedup w/o loosing too many races).

With the current version of ThreadSanitizer you may try the **experimental** flag `--sampling=<N>` where `N` is a number between 1 and 31.
31 means very aggressive sampling (i.e. very fast, looses races) and
1 means very little sampling (almost as slow as w/o sampling).
Reasonable values lie somewhere between 15 and 25.

Please try the flag and let us know what you think:
```
tsan --sampling=20 your-test
```

Note: the annotation `ANNOTATE_PUBLISH_MEMORY` does not work with sampling. :(
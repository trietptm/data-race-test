#summary Details about ThreadSanitizer's memory usage

# Introduction #

ThreadSanitizer requires a lot of memory to operate.

Here we describe how to optimize ThreadSanitizer's memory usage.


# Segments #

One of the key data structures in ThreadSanitizer is a **segment**
(see ThreadSanitizerAlgorithm for more details).
Each segment occupies just about 100 bytes (or even less), but the number of segments can be huge.

Currently, we allocate a fixed array of segments at startup (for performance reasons),
but this may change in future. At startup, ThreadSanitizer will print a line like this:
```
INFO: Allocating 939,524,096 (112 * 8,388,608) bytes for Segments.
```
This means that the number of segments is `8,388,608` and each occupy `112` bytes.
If you have plenty of memory, you may increase this number by using `--max-sid=<n>` switch.

When possible, ThreadSanitizer tries to reuse segments, but still it may run out of vacant
segments from time to time. When this happens, ThreadSanitizer will issue a message like this:
```
INFO: ThreadSanitizer has run out of segment IDs. Flushing state.
```
If you see this report very often, you may want to use `--max-sid` with a greater value (also, read further).


# Previous accesses #
Each segment stores a stack trace, which is used to show the **previous** accesses when reporting a race.
By default, 10 stack frames are stored, making it occupy 80 bytes of memory for each segment (40 bytes on a 32-bit system).
You can control this value by `--num-callers-in-history=<n>`.

For a continuous build, you may use a mode which does not keep these stack traces at all (`--keep-history=no`).
This will decrease the memory usage (and run-time) by a factor of 1.5x-2x, but the reports will be less informative.

# Memory limits #

ThreadSanitizer tries to guess the amount of memory available to it by reading `/proc/self/limits`
(i.e. the `ulimit` value, when available)
and it also reads `/proc/self/status` to figure out how much memory has already been taken.
You can also set the memory limit explicitly by using the `--max_mem_in_mb=<n>` switch or the
`VALGRIND_MEMORY_LIMIT_IN_MB` environment variable.
When ThreadSanitizer is close to its memory limit it may start printing messages like this:
```
INFO: ThreadSanitizer is running close to its memory limit. Flushing state.
```
If you see such message, you better give more memory to the tool. :)

# Using Ignore files #
As a black belt technique you can tell ThreadSanitizer to ignore certain functions in your program or create less segments.
If you ignore some hotspots ThreadSanitizer will consume less memory (and improve performance).
See ThreadSanitizerIgnores.
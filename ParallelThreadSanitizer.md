# Introduction #
When ThreadSanitizer was initially designed in 2008,
the ThreadSanitizerAlgorithm was made and tuned to be single-threaded
because at that time
the only front-end for it was Valgrind, which is itself single-threaded.
Now, with all other front-ends we have (such as PIN, LLVM,
and potentially some other), the time has come to make ThreadSanitizer
core parallel.

As of Dec 2010, this work is in progress.

# Algorithm #

When running with parallel front-end, ThreadSanitizer receives events
from different threads w/o any synchronization.

Several events only touch thread-local data and do not generally require locking:
  * `RTN_EXIT` event is purely thread-local -- it simply pops the shadow call stack of a given thread.
  * `RTN_CALL` event is also thread-local in most cases  (on a rare occasion when it needs to compute the "ignore below" property it may still need to acquire a lock).
  * `IGNORE_READS_BEGIN` and similar events are thread-local.

Most other events touch too many global objects in ThreadSanitizer,
so we acquire a global lock right away. This may be optimized further
in future.

The most frequent event is a [TRACE](ThreadSanitizerAlgorithm#Instrumentation:_TRACEs.md),
which consists of one `SBLOCK_ENTER` followed by one or more `READ` or `WRITE` events.
This is what requires most attention.

`SBLOCK_ENTER` is used to maintain nearly-precise information
about previous accesses. So, on every `SBLOCK_ENTER` a new segment
has to be created. The vacant segments reside in a global pool, so, to
avoid frequent accesses to the global pool each thread caches a number
of vacant (fresh) segments.

The `READ` and `WRITE` events may access all kinds of global objects,
however on the [fast path](ThreadSanitizerAlgorithm#Fast_path.md)
almost none of these objects are needed. So, for every `READ`/`WRITE` event
ThreadSanitizer tries to acquire a cache line slot using
one **atomic exchange instruction** (`xchg` on x86).
If the acquisition fails or if the cache line in the given slot is
wrong, we fall back to the slow path (under the lock).
Otherwise we try the
[fast path state machine](ThreadSanitizerAlgorithm#Fast_path.md); if it fails, we again fall back to the path under the lock.

# Debugging #
We need to make sure that the parallel ThreadSanitizer does not have
harmful races. The least painful way of checking ThreadSanitizer
for races is to build a test with the
[compiler-based ThreadSanitizer](CompileTimeInstrumentation.md) and run it
under a regular (PIN- or Valgrind- based) ThreadSanitizer.

# Performance #
While tuning the parallel version for performance, we eliminated
a number of global statistic counters and other less trivial
sources of cache line ping-pong.
The Linux tool [perf](https://perf.wiki.kernel.org/index.php/Main_Page)
helped us a lot.

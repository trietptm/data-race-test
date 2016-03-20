#summary Ignores mechanism in ThreadSanitizer

Besides ThreadSanitizerSuppressions,
ThreadSanitizer supports yet another machinery for suppressing reports. It is complementary to valgrind suppressions.

You can use a `--ignore=<filename>` flag to pass a file which contains lines like this:
```
# specifies object file name using a wildcard.
# All functions in this object will not be instrumented.
obj:*/libpthread-*.so
obj:*/ld-*.so
# all functions in this source file will be ignored
src:*file_with_some_tricky_code.cc

# These functions will be ignored as well
fun:*_ZN4base6subtle*
# These functions will be ignored together with other functions they call
fun_r:random_r

# These functions will be instrumented BUT no new segments will be
# created in their superblocks with --keep-history=1.
# As a result, it improves performance at the cost of the precision of the
# "concurrent accesses" stacktraces in the race reports.
# This can be very useful if you have a large number of tiny functions
# which do a lot of calculations but don't do anything threaded.
fun_hist:*v8*internal*
fun_hist:*unicode_conversion*
```

Such file lists the functions (either by object file name, source file name or directly by function name) that will not be instrumented by tsan.
This means, that these functions will be executed much faster and all memory accesses there will be ignored.
Functions that are called by the ignored functions are not affected.

This feature is used for two things:

First, it allows to suppress warnings that are caused by code in specified functions/files/objects,
which is not always possible with regular suppressions.
(for example, a racey write we want to suppress is in function FOO, and the concurrent reads are all over the program.
The reports may show the stack that belong to reads, thus you will have to write many suppressions).
Ignore file is also used to suppress warnings from libpthread and ld.so

Second, the ignore file allows to **speed up tsan by a large factor** (several times in some cases).

(**Black belt**): By using `--sample-events=<N>` you can collect the hotspots of the program
(those that slowdown ThreadSanitizer the most) and put them into the ignore file.
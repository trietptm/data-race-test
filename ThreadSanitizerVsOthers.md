#summary Comparison of ThreadSanitizer, Helgrind, Drd and Intel Thread Checker

**UNDER CONSTRUCTION!**

Some features that differ ThreadSanitizer from Helgrind (and also from DRD and Intel Thread Checker).

ThreadSanitizer has both **hybrid** and **pure happens-before** state machines
while such detectors as Helgrind (3.4), DRD, and Intel Thread Checker use only pure happens-before machine.

> The pure happens-before mode will not report false positives
> (unless your program uses lock-less synchronization), but it may miss races and is less predictable.

> The hybrid machine may give more false positives, but is much faster, more predictable and find more real races.

ThreadSanitizer supports DynamicAnnotations which can make any tricky synchronization
(including lock-less synchronization) to be ThreadSanitizer-friendly.

ThreadSanitizer prints all accesses involved in a data race and also all locks held during each access.
For details see ThreadSanitizerAlgorithm and the screenshot at the main ThreadSanitizer page.

ThreadSanitizer has an [\*ignore\* feature](ThreadSanitizerIgnores.md) which is complementary to valgrind suppressions.

ThreadSanitizer does not replace the application's **malloc**, but gently instruments it.
This is usefull if the application uses a custom malloc function
(e.g. [Google's TCMalloc](http://goog-perftools.sourceforge.net/doc/tcmalloc.html))
which has important side effects.

ThreadSanitizer is written in C++ with STL.
This is, AFAIK, the first valgrind tool written in C++.
Not a big deal otherwise. :)
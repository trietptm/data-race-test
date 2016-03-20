

# Introduction #

Various detectors of data races (such as  [Helgrind](http://valgrind.org/docs/manual/hg-manual.html), [DRD](http://valgrind.org/docs/manual/drd-manual.html), [Intel Parallel Inspector](http://software.intel.com/en-us/intel-parallel-inspector/),
[Sun Studio Thread Analyzer](http://developers.sun.com/sunstudio/downloads/ssx/tha/tha_getting_started.html) or ThreadSanitizer) rely on their ability to intercept and interpret synchronization events of the analyzed program. For example, all these race detectors know the semantics of `pthread_mutex_lock` and similar functions. However, it is hard or impossible to interpret raw atomic instructions as synchronization (e.g. treating every compare-and-exchange instruction or every instruction with lock prefix as a synchronization event will make the analysis very slow and conservative).

One of the most frequent patterns of lock-free synchronization is **atomic reference counting**.
```
class RefCounted {
 public:
  Ref() {
    AtomicIncrement(&ref);
  }
  Unref() {
    if (AtomicDecrement(&ref_) == 0) {
      delete this;
    }
  }
 private:
  AtomicInt ref_;
}
```

In order to avoid false warnings, race detectors need to understand that the reference counting implements correct synchronization.
Namely, the tools need to understand that every event occurred before the decrement **happens-before** the events that occur after the reference counter became zero.

With the DynamicAnnotations the most straightforward way to explain this to the tool
is to annotated the code of `Unref()`:
```
  Unref() {
    ANNOTATE_HAPPENS_BEFORE(&ref_);
    if (AtomicDecrement(&ref_) == 0) {
      ANNOTATE_HAPPENS_AFTER(&ref_);
      delete this;
    }
  }
```

This syntax is supported by ThreadSanitizer, [Helgrind](http://valgrind.org/docs/manual/hg-manual.html), [DRD](http://valgrind.org/docs/manual/drd-manual.html) (though they currently require different header files to be included). 

&lt;BR&gt;


The [Intel Parallel Inspector](http://software.intel.com/en-us/intel-parallel-inspector/) supports equivalent callbacks:  `itt_notify_sync_releasing(void*)` and  `itt_notify_sync_acquired(void*)`. 

&lt;BR&gt;


The [Sun Studio Thread Analyzer](http://developers.sun.com/sunstudio/downloads/ssx/tha/tha_getting_started.html) [supports](http://developers.sun.com/sunstudio/downloads/ssx/tha/tha_using.html)
`tha_notify_sync_post_begin(id)` / `tha_notify_sync_post_end(id)`	/ `tha_notify_sync_wait_begin(id)`	 / `tha_notify_sync_wait_end(id)`.


# Reference counting in basic\_string<> (libstdc++) #
Reference counting in C++ string<> ([libstdc++](http://gcc.gnu.org/onlinedocs/libstdc++/libstdc++-html-USERS-4.4/a01068.html#l00224)) is implemented in the following way:
```
     _M_dispose(const _Alloc& __a)
     {
         //...
         if (__gnu_cxx::__exchange_and_add_dispatch(&this->_M_refcount,
                                -1) <= 0)
           _M_destroy(__a);
     }  // XXX MT
```

This is the correct and the most common way of implementing atomic reference counting.
The problem is that the race detectors do no understand it because `__gnu_cxx::__exchange_and_add_dispatch` ends up compiling into one atomic instruction.
Generally, race detectors can not distinguish when such atomic instructions are used for decrementing reference counters or when they are used for other purposes (e.g. maintaining a thread-safe counter which is not used to synchronize anything but itself).

**NEW**: As of Aug 13, 2010, libstdc++ contains the annotations for race detectors.
See http://gcc.gnu.org/viewcvs?view=revision&revision=163210 and http://gcc.gnu.org/bugzilla/show_bug.cgi?id=45276

# Reference counting in foo #
TODO: please fill this section if you know about atomic reference counting in other common libraries.

# Proposal for library developers #
If you develop or maintain any widely used C/C++ library which works in multi-threaded context, it is in your best interest to support dynamic race detectors.

If you library does not itself use synchronization, or if it uses only standard `pthread_*` functions, you don't need to do anything else.
If your library does use some custom synchronization based on atomic instructions, we ask you to help the race detectors understand this code.

In many cases, the simplest way to explain custom synchronization to the race detectors is to use DynamicAnnotations (as shown above) or equivalent [Helgrind client requests](http://valgrind.org/docs/manual/hg-manual.html#hg-manual.client-requests) , but we expect that for some libraries this will be unacceptable due to additional dependency.


# How to try #
You can try ThreadSanitizer yourself and see what reports appear due to unannotated reference counting.

```
# Get ThreadSanitizer. Assumes you are on x86_64 Linux. Tested on Ubuntu 8.04
wget http://build.chromium.org/buildbot/tsan/binaries/tsan-r2280-amd64-linux-self-contained.sh
cp tsan-r2280-amd64-linux-self-contained.sh tsan.sh 
chmod +x tsan.sh 
```

```
# Build the example and run it under ThreadSanitizer.
cat > string_test.cc << EOF
#include <pthread.h>
#include <string>
#include <unistd.h>
using namespace std;

string *s;

pthread_mutex_t mu;
pthread_cond_t cv;
int done = 0;

void *Thread(void*) {
  string x = *s;  // calls _M_refcopy().

  pthread_mutex_lock(&mu);
  done++;
  pthread_cond_signal(&cv);
  pthread_mutex_unlock(&mu);
  // x is destructed, calls _M_dispose
}

const int kNThreads = 3;

int main() {
  s = new string("foo");
  pthread_t t[kNThreads];
  pthread_mutex_init(&mu, 0);
  pthread_cond_init(&cv, 0);
  // start threads.
  for (int i = 0; i < kNThreads; i++) {
    pthread_create(&t[i], 0, Thread, 0);
  }
  // wait for threads to copy 's', but don't wait for threads to exit.
  pthread_mutex_lock(&mu);
  while (done != kNThreads)
    pthread_cond_wait(&cv, &mu);
  pthread_mutex_unlock(&mu);
  // s has been copied few times, now delete it.
  // Last of the destructors (either here ot in Thread() will call _M_destroy).
  delete s;  // calls _M_dispose.
}
EOF
/usr/bin/g++ -g -lpthread string_test.cc
./tsan.sh ./a.out 

```

You should get the following race report (false warning):
```
==14051== WARNING: Possible data race during write of size 8 at 0x421F040: {{{
==14051==    T0 (locks held: {}):
==14051==     #0  operator delete(void*) /b/slave/full_linux_build/build/tsan/ts_valgrind_intercepts.c:495
==14051==     #1  std::basic_string<char, std::char_traits<char>, std::allocator<char> >::~basic_string() /usr/lib/libstdc++.so.6.0.9
==14051==     #2  main /tmp/refc/string_test.cc:40
==14051==   Concurrent read(s) happened at (OR AFTER) these points:
==14051==    T1 (locks held: {}):
==14051==     #0  std::basic_string<char, std::char_traits<char>, std::allocator<char> >::~basic_string() /usr/lib/libstdc++.so.6.0.9
==14051==     #1  Thread(void*) /tmp/refc/string_test.cc:18
==14051==     #2  ThreadSanitizerStartThread /b/slave/full_linux_build/build/tsan/ts_valgrind_intercepts.c:607
==14051==    T2 (locks held: {}):
==14051==     #0  std::basic_string<char, std::char_traits<char>, std::allocator<char> >::~basic_string() /usr/lib/libstdc++.so.6.0.9
==14051==     #1  Thread(void*) /tmp/refc/string_test.cc:18
==14051==     #2  ThreadSanitizerStartThread /b/slave/full_linux_build/build/tsan/ts_valgrind_intercepts.c:607
==14051==    T3 (locks held: {}):
==14051==     #0  std::basic_string<char, std::char_traits<char>, std::allocator<char> >::~basic_string() /usr/lib/libstdc++.so.6.0.9
==14051==     #1  Thread(void*) /tmp/refc/string_test.cc:18
==14051==     #2  ThreadSanitizerStartThread /b/slave/full_linux_build/build/tsan/ts_valgrind_intercepts.c:607
==14051==   Location 0x421F040 is 16 bytes inside a block starting at 0x421F030 of size 28 allocated by T0 from heap:
==14051==     #0  operator new(unsigned long) /b/slave/full_linux_build/build/tsan/ts_valgrind_intercepts.c:425
==14051==     #1  std::string::_Rep::_S_create(unsigned long, unsigned long, std::allocator<char> const&) /usr/lib/libstdc++.so.6.0.9
==14051==     #2  ???//usr/lib/libstdc++.so.6.0.9 /usr/lib/libstdc++.so.6.0.9
==14051==     #3  std::basic_string<char, std::char_traits<char>, std::allocator<char> >::basic_string(char const*, std::allocator<char> const&) /usr/lib/libstdc++.so.6.0.9
==14051==     #4  main /tmp/refc/string_test.cc:25
==14051== }}}
```
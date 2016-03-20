﻿#summary How to understand the reports produced by ThreadSanitizer



# Simple example #
## Example code ##
Let's consider the simplest example,
[RaceReportDemoTest](http://www.google.com/codesearch/p?hl=en#Xcie8cMcE6E/trunk/unittest/demo_tests.cc&q=RaceReportDemoTest&type=cs&exact_package=http://data-race-test.googlecode.com/svn&l=41)
from RacecheckUnittest.

```
Mutex mu1;  // This Mutex guards var.
Mutex mu2;  // This Mutex is not related to var.
int   var;  // GUARDED_BY(mu1)

void Thread1() {  // Runs in thread named 'test-thread-1'.
  MutexLock lock(&mu1);  // Correct Mutex.
  var = 1; 
}

void Thread2() {  // Runs in thread named 'test-thread-2'.
  MutexLock lock(&mu2);  // Wrong Mutex.
  var = 2; 
}
```

## Running the tool on demo test ##
First, get and build unittests (see RacecheckUnittest). Now you can run ThreadSanitizer on the example. The report is dumped to `demo.log`
### Linux ###
```
# notice that we run test compiled for amd64 platform, with O0
valgrind --tool=tsan --log-file="demo.log" ./bin/demo_tests-linux-amd64-O0 --gtest_filter="DemoTests.RaceReportDemoTest"
```
### Windows ###
(assuming you unpacked ThreadSanitizer to C:\)
```
C:\tsan-x86-windows\tsan.bat --log-file="demo.log" bin\demo_tests-windows-x86-O0.exe --gtest_filter="DemoTests.RaceReportDemoTest"
```

## The report ##
The report in `demo.log` will look like this:
```
==16898== INFO: T1 has been created by T0. Use --announce-threads to see the creation stack.
==16898== INFO: T2 has been created by T0. Use --announce-threads to see the creation stack.
==16898== WARNING: Possible data race during write of size 4 at 0x6457E0: {{{
==16898==    T2 (test-thread-2) (L{L3}):
==16898==     #0  RaceReportDemoTest::Thread2 demo_tests.cc:53
==16898==     #1  MyThread::ThreadBody thread_wrappers_pthread.h:341
==16898==   Concurrent write(s) happened at (OR AFTER) these points:
==16898==    T1 (test-thread-1) (L{L2}):
==16898==     #0  RaceReportDemoTest::Thread1 demo_tests.cc:48
==16898==     #1  MyThread::ThreadBody thread_wrappers_pthread.h:341
==16898==   Address 0x6457E0 is 0 bytes inside data symbol "_ZN18RaceReportDemoTest3varE"
==16898==   Locks involved in this report (reporting last lock sites): {L2, L3}
==16898==    L2 (0x645720)
==16898==     #0  pthread_mutex_lock ts_valgrind_intercepts.c:935
==16898==     #1  Mutex::Lock thread_wrappers_pthread.h:147
==16898==     #2  MutexLock::MutexLock thread_wrappers.h:286
==16898==     #3  RaceReportDemoTest::Thread1 demo_tests.cc:47
==16898==     #4  MyThread::ThreadBody thread_wrappers_pthread.h:341
==16898==    L3 (0x645780)
==16898==     #0  pthread_mutex_lock ts_valgrind_intercepts.c:935
==16898==     #1  Mutex::Lock thread_wrappers_pthread.h:147
==16898==     #2  MutexLock::MutexLock thread_wrappers.h:286
==16898==     #3  RaceReportDemoTest::Thread2 demo_tests.cc:52
==16898==     #4  MyThread::ThreadBody thread_wrappers_pthread.h:341
==16898== }}}
```

## GUI ##
You can view this report together with the sources using your favourite editor.
Here is an example using ThreadSanitizerAndVim:
the window at left shows the ThreadSanitizer's output, the two windows at right
display the two racey accesses.

> ![http://data-race-test.googlecode.com/svn/trunk/images/tsan-in-vim-three-windows.png](http://data-race-test.googlecode.com/svn/trunk/images/tsan-in-vim-three-windows.png)

## Details ##
Let us now describe each section of the report.

```
==16898== INFO: T1 has been created by T0. Use --announce-threads to see the creation stack.
==16898== INFO: T2 has been created by T0. Use --announce-threads to see the creation stack.
```
Each race report mentions two or more threads, e.g. `T1` and `T2`.
Note that the main thread of the program is called `T0`. Each thread is announced only once.
If you use the flag `--announce-threads` you will get the context where this thread has been created.

```
==16898== WARNING: Possible data race during write of size 4 at 0x6457E0: {{{
```

This is the header of the report.
It mentions the address of the racey memory, the size of the racey access and whether it was a read or a write.

```
==16898==    T2 (test-thread-2) (L{L3}):
```
This is the information about the last observed access which is considered to be racey.
  * `T2` is the thread where this access happened.
  * `test-thread-2` is the name of the thread. The threads are named using `ANNOTATE_THREAD_NAME(name)` from DynamicAnnotations.
  * `(L{L3})`: this is the list of all locks held during this access.
> > If some locks are held in reader mode, the reader and writer locks will be shown separately.

```
==16898==     #0  RaceReportDemoTest::Thread2 demo_tests.cc:53
==16898==     #1  MyThread::ThreadBody thread_wrappers_pthread.h:341
```
And here is the exact stack trace of the last observed access.

```
==16898==   Concurrent write(s) happened at (OR AFTER) these points:
```
Following are the sections that represent the accesses that are concurrent to the access above.
These accesses are not necessary concurrent to each other.


```
==16898==    T1 (test-thread-1) (L{L2}):
```
Again: the information about the thread and the locks.

```
==16898==     #0  RaceReportDemoTest::Thread1 demo_tests.cc:48
==16898==     #1  MyThread::ThreadBody thread_wrappers_pthread.h:341
```
This stack trace points to the concurrent access.
  * With `--keep-history=0` this section will not be shown (fastest).
  * With `--keep-history=1` (default) this section will be shown, but the stack trace may be not exact. The only difference from the actual stack trace is in the line number of the frame #0. In most cases, however, this line number is exact or within few lines from the actual one.
  * With `--keep-history=2` this stack trace is exact (slowest).


```
==16898==   Address 0x6457E0 is 0 bytes inside data symbol "_ZN18RaceReportDemoTest3varE"
```
Description of the racey memory location.
For heap-allocated objects we will see the allocation context.

```
==16898==   Locks involved in this report (reporting last lock sites): {L2, L3}
==16898==    L2 (0x645720)
==16898==     #0  pthread_mutex_lock ts_valgrind_intercepts.c:935
==16898==     #1  Mutex::Lock thread_wrappers_pthread.h:147
==16898==     #2  MutexLock::MutexLock thread_wrappers.h:286
==16898==     #3  RaceReportDemoTest::Thread1 demo_tests.cc:47
==16898==     #4  MyThread::ThreadBody thread_wrappers_pthread.h:341
==16898==    L3 (0x645780)
==16898==     #0  pthread_mutex_lock ts_valgrind_intercepts.c:935
==16898==     #1  Mutex::Lock thread_wrappers_pthread.h:147
==16898==     #2  MutexLock::MutexLock thread_wrappers.h:286
==16898==     #3  RaceReportDemoTest::Thread2 demo_tests.cc:52
==16898==     #4  MyThread::ThreadBody thread_wrappers_pthread.h:341
```

This gives us the information about all locks involved in this report.
For each lock ThreadSanitizer shows the context where this lock was acquired last.

# More complex example #
For a more complex example see the [test 311](http://www.google.com/codesearch/p?hl=en#Xcie8cMcE6E/trunk/unittest/demo_tests.cc&q=test311&type=cs&exact_package=http://data-race-test.googlecode.com/svn&l=384) from RacecheckUnittest.
We use `--pure-happens-before=no` since a pure happens-before detector can not detect the race on this test.
```
valgrind --tool=tsan  --pure-happens-before=no \
./bin/demo_tests-linux-amd64-O0 --gtest_filter="DemoTests.test311"
```


> ![http://data-race-test.googlecode.com/svn/trunk/images/tsan-in-vim3.png](http://data-race-test.googlecode.com/svn/trunk/images/tsan-in-vim3.png)
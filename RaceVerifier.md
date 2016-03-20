# Introduction #

ThreadSanitizer supports a RaceVerifier mode in which it takes an output of normal ThreadSanitizer run and attempt to verify all the race reports in it. It uses the same approach as RaceCheckerClass, inserting short sleeps immediately after (possibly) racey instructions. If at least two such sleeps happen simultaneously for the same data address, and at least of them is a write at that address - we've got a 100% race.

Keep in mind that RaceVerifier can not tell a harmful race from a benign one. It reports any pair of unsynchronized accesses (at least one of which is a write) as a race.

In practice, delays added by RaceVerifier at (or near) racy instructions often change the program behavior, if the race is harmful. Of course, this effect is not guaranteed, but, if happens, presents a proof that a race exists and it is harmful.

Also keep in mind that RaceVerifier can not verify races that are not there. For example, see [unsafe publishing](http://code.google.com/p/data-race-test/wiki/PopularDataRaces#Publishing_objects_without_synchronization):
```
MyType* obj = NULL;

void Thread1() {
  obj = new MyType();
}

void Thread2() {
  while(obj == NULL)
    yield();
  obj->DoSomething();
}
```
Compiler can transform this code in such a way, that the resulting binary will contain a data race. But, depending on the optimization options, compiler version and other factors, it may choose not to do so. In that latter case RaceVerifier will not be able to detect the problem.

The above code snippet, even if compiled in a non-racy way, still contains a race on weakly-ordered CPU architectures: some memory writes in MyType() constructor can be reordered with obj assignment. This race can not be verified by RaceVerifer, because delays that is it inserts do not affect this reordering in any way. RaceVerifier can only detect races that happen because of **variations in thread interleaving**.

# Usage #

RaceVerifier works with both Pin and Valgrind tools.

Run ThreadSanitizer as usual, and redirect stderr to a file. Or, even better, use --log-file option. Then run ThreadSanitizer the second time in RaceVerifier mode, using the log of the first run.

```
tsan/tsan_pin.sh --log-file=race.log program_binary
tsan/tsan_pin.sh --race-verifier=race.log program_binary
```

With Valgrind:
```
valgrind --tool=tsan --log-file=race.log program_binary
valgrind --tool=tsan --race-verifier=race.log program_binary
```

The second run will print only those reports from the first run that have been verified to be a 100% data race.

# Command line flags #
| Flag name | default | description |
|:----------|:--------|:------------|
| --race-verifier=filename[,filename...] | ""      | Run in race verification mode for the given log files. |
| --race-verifier-extra=race | ""      | Run in race verification mode for the given race description. This is meant mostly for debugging. Race description syntax can be checked in TSan log, "Race verifier data:" lines. |
| --race-verifier-sleep-ms=delay | 100     | Sleep duration in ms. Increasing this number might verify more races. |

# Example #
```

$ tsan/tsan_pin.sh unittest/bin/output_test1-linux-amd64-O0 2>log


$ cat log


ThreadSanitizer running in Race Verifier mode.
==11793== INFO: Allocating 939524096 (112 * 8388608) bytes for Segments.
sizeof(CacheLine) = 552
==11793== ThreadSanitizerPin r2088M: hybrid=no
==11793== INFO: Debug build
==11793== INFO: T1 has been created by T0. Use --announce-threads to see the creation stack.
==11793== INFO: T2 has been created by T0. Use --announce-threads to see the creation stack.
==11793== WARNING: Possible data race during write of size 4 at 0x602a20:
==11793==    T2 (locks held: {L2}):
==11793==     #0  Thread2() /src/data-race-test/unittest/output_test1.cc:13
==11793==     #1  MyThread::ThreadBody(MyThread*) /src/data-race-test/unittest/thread_wrappers_pthread.h:329
==11793==     #2  start_thread /lib/libpthread.so.0
==11793==   Concurrent write(s) happened at (OR AFTER) these points:
==11793==    T1 (locks held: {L1}):
==11793==     #0  Thread1() /src/data-race-test/unittest/output_test1.cc:8
==11793==     #1  MyThread::ThreadBody(MyThread*) /src/data-race-test/unittest/thread_wrappers_pthread.h:329
==11793==     #2  start_thread /lib/libpthread.so.0
==11793==   Locks involved in this report (reporting last lock sites): {L1, L2}
==11793==    L1
==11793==     #0  pthread_mutex_lock /lib/libpthread.so.0
==11793==     #1  Mutex::Lock() /src/data-race-test/unittest/thread_wrappers_pthread.h:135
==11793==     #2  MutexLock::MutexLock(Mutex*) /src/data-race-test/unittest/thread_wrappers.h:286
==11793==     #3  Thread1() /src/data-race-test/unittest/output_test1.cc:7
==11793==     #4  MyThread::ThreadBody(MyThread*) /src/data-race-test/unittest/thread_wrappers_pthread.h:329
==11793==     #5  start_thread /lib/libpthread.so.0
==11793==    L2
==11793==     #0  pthread_mutex_lock /lib/libpthread.so.0
==11793==     #1  Mutex::Lock() /src/data-race-test/unittest/thread_wrappers_pthread.h:135
==11793==     #2  MutexLock::MutexLock(Mutex*) /src/data-race-test/unittest/thread_wrappers.h:286
==11793==     #3  Thread2() /src/data-race-test/unittest/output_test1.cc:12
==11793==     #4  MyThread::ThreadBody(MyThread*) /src/data-race-test/unittest/thread_wrappers_pthread.h:329
==11793==     #5  start_thread /lib/libpthread.so.0
==11793==    Race verifier data: 0x400d16,0x400d42
==11793==
==11793== ThreadSanitizer summary: reported 1 warning(s) (1 race(s))


$ tsan/tsan_pin.sh --race-verifier=log --race-verifier-sleep-ms=100 unittest/bin/output_test1-linux-amd64-O0


ThreadSanitizer running in Race Verifier mode.
==11808== INFO: Allocating 939524096 (112 * 8388608) bytes for Segments.
sizeof(CacheLine) = 552
==11808== ThreadSanitizerPin r2088M: hybrid=no
==11808== INFO: Debug build
Possible race: 0x400d16,0x400d42
Confirmed race:
==11793== WARNING: Possible data race during write of size 4 at 0x602a20:
==11793==    T2 (locks held: {L2}):
==11793==     #0  Thread2() /src/data-race-test/unittest/output_test1.cc:13
==11793==     #1  MyThread::ThreadBody(MyThread*) /src/data-race-test/unittest/thread_wrappers_pthread.h:329
==11793==     #2  start_thread /lib/libpthread.so.0
==11793==   Concurrent write(s) happened at (OR AFTER) these points:
==11793==    T1 (locks held: {L1}):
==11793==     #0  Thread1() /src/data-race-test/unittest/output_test1.cc:8
==11793==     #1  MyThread::ThreadBody(MyThread*) /src/data-race-test/unittest/thread_wrappers_pthread.h:329
==11793==     #2  start_thread /lib/libpthread.so.0
==11793==   Locks involved in this report (reporting last lock sites): {L1, L2}
==11793==    L1
==11793==     #0  pthread_mutex_lock /lib/libpthread.so.0
==11793==     #1  Mutex::Lock() /src/data-race-test/unittest/thread_wrappers_pthread.h:135
==11793==     #2  MutexLock::MutexLock(Mutex*) /src/data-race-test/unittest/thread_wrappers.h:286
==11793==     #3  Thread1() /src/data-race-test/unittest/output_test1.cc:7
==11793==     #4  MyThread::ThreadBody(MyThread*) /src/data-race-test/unittest/thread_wrappers_pthread.h:329
==11793==     #5  start_thread /lib/libpthread.so.0
==11793==    L2
==11793==     #0  pthread_mutex_lock /lib/libpthread.so.0
==11793==     #1  Mutex::Lock() /src/data-race-test/unittest/thread_wrappers_pthread.h:135
==11793==     #2  MutexLock::MutexLock(Mutex*) /src/data-race-test/unittest/thread_wrappers.h:286
==11793==     #3  Thread2() /src/data-race-test/unittest/output_test1.cc:12
==11793==     #4  MyThread::ThreadBody(MyThread*) /src/data-race-test/unittest/thread_wrappers_pthread.h:329
==11793==     #5  start_thread /lib/libpthread.so.0
==11808==
==11808== ThreadSanitizer summary: reported 0 warning(s) (0 race(s))
```
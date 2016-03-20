#summary Dynamic Annotations are used to annotate custom synchronization utilities


# Introduction #

Dynamic annotation is a source code annotation that affects
the generated code (that is, the annotation is not a comment).
Each such annotation is attached to a particular
instruction and/or to a particular object (address) in the program.

Dynamic annotations could be used to pass various kinds of information to dynamic analysis tools,
such as Memcheck, Helgrind or ThreadSanitizer.

In order to use the dynamic annotations in your program you need to include
[dynamic\_annotations.h](http://code.google.com/p/data-race-test/source/browse/trunk/dynamic_annotations/dynamic_annotations.h),
define cpp macro `DYNAMIC_ANNOTATIONS_ENABLED=1`
and link with
[dynamic\_annotations.c](http://code.google.com/p/data-race-test/source/browse/trunk/dynamic_annotations/dynamic_annotations.c).

You can find examples of the annotations in RacecheckUnittest.

**TODO**: add more examples.

# Custom memory allocation #
Use `ANNOTATE_NEW_MEMORY(mem, size)` inside custom memory allocators.

# pthread\_cond\_wait loop #

We need to establish a happens-before relation between `CondVar::Signal()` and `CondVar::Wait()`.
In other words, we need to tell the detector that a pair of matching `CondVar::Signal()` and `CondVar::Wait()` perform correct synchronization.

There's a problem when `CondVar::Signal()` gets called before we enter `CondVar::Wait()` while loop.
In some cases we may have to annotate user code with `ANNOTATE_CONDVAR_LOCK_WAIT(&CV, &MU)` (or `ANNOTATE_CONDVAR_WAIT(&CV)`)
If we do not annotate a conditional critical section, there is a chance that a false data race will be reported.

```
Mutex mu;
CondVar cv;

// In this example, a false data race on 'GLOB' may be reported if we don't 
// insert ANNOTATE_CONDVAR_LOCK_WAIT(&cv, &mu);
void Thread1() {
  GLOB = 1;  // Access1
  mu.Lock();
  COND = 1;
  cv.Signal();        // <<<<<<<<<<<<<<<<< Does ANNOTATE_CONDVAR_SIGNAL(&cv)
  mu.Unlock();
}

void Thread2() {
  mu.Lock();
  while(COND != 1)
	cv.Wait(&mu);
  // W/o this annotation the race detector may report 
  // a false race between Access1 and Access2
  // This annotation should be placed rigth after the while loop
  ANNOTATE_CONDVAR_LOCK_WAIT(&cv, &mu);  // <<<<<<< Matches SIGNAL in Thread1()
  mu.Unlock();
  GLOB = 2; // Access2
}
```


Pure happens-before detectors do not suffer from this issue and do not require this annotation.

# Custom synchronization #
## Message queue ##
Message queues that use lock require annotations to avoid false positives in the Hybrid mode
(pure happens-before detector will be silent).
If a message queue is implemented w/o a lock, an annotations may be required even for a pure happens-before detector.
```
// Putter 
void MyCoolMessageQueue::Put(Type *e) {
  MutexLock lock(&mu_);
  ANNOTATE_HAPPENS_BEFORE(e);   //<<<< SIGNAL right before doing Put().
  PutElementIntoMyQueue(e);
}

// Getter
Type *MyCoolMessageQueue::Get() {
  MutexLock lock(&mu_);
  Type *e = GetElementFromMyQueue(e);
  ANNOTATE_HAPPENS_AFTER(e);     //<<<<< WAIT right after Get()
  return e;
}
```
## Free lists ##
Free lists are usually implemented in the same manner as message queues. So, see above.
## FIFO queues ##
A FIFO message queue (as any other message queue) could be annotated using `ANNOTATE_HAPPENS_BEFORE` / `ANNOTATE_HAPPENS_AFTER`.
But the specific `ANNOTATE_PCQ_*` annotations are a bit more race-detector-friendly.
The main difference is that if we put a same element into the queue several times, the `HAPPENS_BEFORE` / `HAPPENS_AFTER` annotations will make race detectors too conservative
(i.e. will create too many wrong happens-before arcs).
  * `ANNOTATE_PCQ_CREATE(pcq)`
  * `ANNOTATE_PCQ_DESTROY(pcq)`
  * `ANNOTATE_PCQ_PUT(pcq)`
  * `ANNOTATE_PCQ_GET(pcq)`

(PCQ stands for Producer Consumer Queue. The name of these annotations is subject to change).

## Reference counting ##
Reference counting using lock. Need to annotate to avoid false positives in Hybrid detector.
```
void Unref() {
  MU.Lock();
  bool do_delete = (--ref_ == 0);
  ANNOTATE_HAPPENS_BEFORE(&ref_);
  MU.Unlock();
  if (do_delete) {
    ANNOTATE_HAPPENS_AFTER(&ref_);
    delete this;
  } 
}
```

In case of lock-less reference counting, the annotation is required even for pure happens-before detectors.
```
void Unref() {
  ANNOTATE_HAPPENS_BEFORE(&refcount_);
  if (!AtomicDecrementByOne(&refcount_)) {
    // refcount_ is now 0
    ANNOTATE_HAPPENS_AFTER(&refcount_);
    delete this;
  }
}
```

# Pure happens-before Mutex #
If you annotate a mutex `mu` with `ANNOTATE_PURE_HAPPENS_BEFORE_MUTEX(&mu)`,
the Hybrid detector will treat this particular mutex as in pure happens-before mode.


# Benign races #
Use `ANNOTATE_BENIGN_RACE(addr, "Description")` to annotate an expected benign race on the address range `[addr, addr+sizeof(*addr))`. 

&lt;BR&gt;


An alternative form is `ANNOTATE_BENIGN_RACE_SIZED(addr, size, "Description")` 

&lt;BR&gt;


In C++ you can apply `ANNOTATE_BENIGN_RACE_STATIC(static_var, "Description")` to racy static variables.

# Racey reads #
It is often the case that we want to protect updates of some value, but can tolerate unsynchronized reads of that value.
For this kind of benign race we have special annotations:
  * `ANNOTATE_IGNORE_READS_BEGIN()`, `ANNOTATE_IGNORE_READS_END()`
  * `ANNOTATE_UNPROTECTED_READ(mem)`

These annotations allow us to ignore certain racey reads, while still checking all other accesses.

# Enable/disable analysis #
Sometimes you may need to disable race detection for the entire program (e.g. to go through a slow initialization step quickly). In this case call `ANNOTATE_ENABLE_RACE_DETECTION(0)` before you enter the slow part of code and `ANNOTATE_ENABLE_RACE_DETECTION(1)` when you are done. This annotation affects all threads.

# Custom locks #

If you implement your own locking primitive, you have to annotate it in order to make it ThreadSanitizer-friendly.

  * `ANNOTATE_RWLOCK_CREATE(lock)`
  * `ANNOTATE_RWLOCK_DESTROY(lock)`
  * `ANNOTATE_RWLOCK_ACQUIRED(lock, is_w)`
  * `ANNOTATE_RWLOCK_RELEASED(lock, is_w)`

# Expected races in unittests #
Data race that happens on address mem will not be reported.
In contrary, if the race detector does not find a race for that address, a warning message will be printed at the end.

# Naming Threads #
Use `ANNOTATE_THREAD_NAME(name)` do name a thread.
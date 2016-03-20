#summary Comparison of pure happens-before and hybrid modes

ThreadSanitizer has two major modes of operation:
  * Hybrid (--hybrid=yes)
  * Pure happens-before (default).

The example below is the simplest way to show the difference between these modes.

```
static Mutex mu;
static bool flag = flag_init_value; 
static int var;

void Thread1() {  // Runs in thread1.
   var = 1;  // << First access.
   mu.Lock();
   flag = true;
   mu.Unlock();
}

void Thread2() {  // Runs in thread2.
   bool f;
   do {
     mu.Lock();
     f = flag;
     mu.Unlock();
   } while(!f);
   var = 2; // << Second access.
}
```

So, is there a race between the two accesses to `var`?
Depends on the value of `flag_init_value`.
If it is false, the code is perfectly synchronized; if it is true, the code has a race.
But ThreadSanitizer has no way to distinguish between these two cases.

In the Hybrid mode, ThreadSanitizer will always report a data race on such code.
If this code is correct, you may help ThreadSanitizer to avoid this report by using DynamicAnnotations.

In the pure happens-before mode, ThreadSanitizer will behave differently.
If the race is real (`flag_init_value = true`), the race may or may not be reported (depends on timing).
This is why the pure happens-before mode is less predicatble.
If there is no race (`flag_init_value = false`), ThreadSanitizer will be silent.

Q. How do I choose between these two modes? 

&lt;BR&gt;


A. We suggest to use the Hybrid mode whenever possible. It is faster, finds more real races and is more predicatble. But if the Hybrid mode gives too many reports and you have no time to master the Dynamic Annotations, try the pure happens-before mode.

Q. Are there races detectable by the pure happens-before mode and not detectable by Hybrid. 

&lt;BR&gt;


A. The hybrid mode will find all races detectable by the pure happens-before mode and, maybe, some more.

Q. Does the pure happens-before mode have false positives? 

&lt;BR&gt;


A. Only if you have custom lock-free synchronization.

Q. Can we selectively apply the pure happens-before mode to one Mutex? 

&lt;BR&gt;


A. Yes, use `ANNOTATE_PURE_HAPPENS_BEFORE_MUTEX` from DynamicAnnotations.

Q. What is the technical difference between these two modes? 

&lt;BR&gt;


A. In the pure happens-before mode ThreadSanitizer treats `Mutex::Lock()` as `Wait` and `Mutex::Unlock()` as `Signal` and thus creates a happens-before arc between an `Unlock()` and the following `Lock()`. In the example above, the happens-before arc will be created between `mu.Unlock()` in Thread1 and `mu.Lock()` in Thread2.
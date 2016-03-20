﻿#summary Data race detection algorithm used by ThreadSanitizer.

The [ThreadSanitizer paper](http://data-race-test.googlecode.com/files/ThreadSanitizer.pdf) was presented at [WBIA'09](http://www.dyninst.org/wbia09/) (see also  http://pintool.org/wbia09.pdf, pages 62-71).



# Definitions #

**Tid** (thread id): a unique number identifying a thread of the running program.

**Addr** (address):  a pointer to the memory of the running program (a 64-bit number on a 64-bit system).

**Event-Type**: one of  `Read`, `Write` (memory access events),
`Wrlock`, `Rdlock`, `Wrunlock`, `Rdunlock` (locking events),
`Signal`, `Wait` (happens-before events).

**Event**: a triple `{Event-Type, Tid, Addr}`.
We will write `Event-Type(Tid,Addr)` or `Event-Type(Addr)` if `Tid` is obvious from the context.

**Lock**: an  address that appeared in a locking event. 

&lt;BR&gt;


A lock `L` is **wr-held** by a thread `T` at a given point of time if the number of events
`Wrlock(T,L)` observed so far is greater than the number of events `Wrunlock(T,L)`. 

&lt;BR&gt;


A lock `L` is **rd-held** by thread `T` if it is wr-held by `T` or if the
number of events `Rdlock(T,L)` is greater than the number of events `Rdunlock(T,L)`.

**Lock Set**: (`LS`) a set of locks. 

&lt;BR&gt;


**Writer Lock Set** (`LSwr`): the set of all wr-held locks of a given thread. 

&lt;BR&gt;


**Reader Lock Set** (`LSrd`): the set of all rd-held locks of a given thread. 

&lt;BR&gt;


**Event Lock Set**:  `LSwr` for a `Write` event and `LSrd` for a `Read` event.


**Happens-before arc**: a pair of events `X=Signal(Tx,Ax)` and `Y=Wait(Ty,Ay)` such that   `Ax = Ay`, `Tx != Ty` and `X` is observed first.



**Happens-before**: a partial order on the set of events. 

&lt;BR&gt;


Given two events `X=TypeX(Tx,Ax)` and `Y=TypeY(Ty,Ay)`
the event `X` **happens-before** or **precedes** the event `Y` (in short, `X < Y`) if `X` has been observed before `Y` and at least one of the following statements is true:
  * `Tx = Ty`
  * `{X,Y}` is a happens-before arc.
  * There exist two events `E1` and `E2`, such that `X <= E1 < E2 <= Y` (i.e. happens-before is transitive).

**Context of event**: information that allows the users to understand where the given event has appeared.
Usually, the context is a stack trace of the event.

**Segment**: a sequence of events of one thread that contains no
synchronization events. The context of a segment is the context of the
first event in the segment. Each segment has it's writer and reader Lock Sets.

![http://data-race-test.googlecode.com/svn/trunk/msm/exa3.png](http://data-race-test.googlecode.com/svn/trunk/msm/exa3.png)

The figure above shows three different threads divided into segments.
  * `S1 < S4` because these segments are in the same thread.
  * `S1 < S5` due to happens-before arc created by `Signal(T1,H1)` and `Wait(T2,H2)`.
  * `S1 < S7` because happens-before is transitive.
  * `!(S4 < S2)` (`S4` does not happen-before `S2`)

We will write `(S1 <= S2)` instead of `(S1 < S2 or S1 == S2)`.


**Segment Set**: a set of segments such that none of the segments in the set happens-before another segment.

**Concurrent**: two memory access events are **concurrent** if none of them happens-before another one and the intersection of the lock sets of these events is empty.

**Data Race**: a situation where there are two concurrent memory access events
with the same address and at least one of the events is `Write`.


# State machine #
The state of ThreadSanitizer consists of global and per-byte states.
Global state is the information about synchronization events that were observed
so far (lock sets, happens-before arcs). Per-byte state (also called
Shadow memory or metadata) is the information about each address (one byte of memory) of the running program. It consists of two segment sets: writer
segment set `SSwr` and reader segment set `SSrd`.
`SSwr` of a given address is a set of segments where the writes to this address
appeared. `SSrd` is a set of all segments where the reads from the given
address appeared, such that for every segment `Sr` in `SSrd` and segment `Sw` in `SSwr`,
`Sr` does not happen-before `Sw`.

The state machine updates the state on each event and reports a
possible data race if needed.

```
# Handle a memory access event (either read or write)
# that happened in thread 'tid' on address 'addr'.
def HandleMemoryAccess(is_write, tid, addr):
  (SSwr, SSrd) = GetPerByteState(addr)
  seg = GetCurrentSegment(tid)
  if (is_write): # Write event
    # Remove 'seg' and those that happen-before 'seg' from SSrd.
    SSrd = UpdateSegmentSet(SSrd, {}, seg)
    # Remove segments that happen-before 'seg' from SSwr and add 'seg'.
    SSwr = UpdateSegmentSet(SSwr, {seg}, seg)
  else: # Read event
    # Just add 'seg' to SSrd.
    SSrd = UpdateSegmentSet(SSrd, {seg}, seg)
  # Update the state.
  SetPerByteState(SSwr, SSrd)
  # Check if there is a race and report it.
  if (IsRace(SSwr, SSrd)): 
    ReportRace(is_write, tid, seg, addr)
```

```
# Return a new segment set constructed as follows: 
# take all segments from 'seg_set' that do not happen-before or equal to 'seg'
# and join them with 'init'.
def UpdateSegmentSet(seg_set, init, seg):
  new_seg_set = init
  foreach s in seg_set: 
    if (not (s <= seg)): 
       new_seg_set = union(new_seg_set, s)
  return new_seg_set
```

```
# Return true if the state {SSwr,SSrd} represents a race.
def IsRace(SSwr, SSrd): 
  for i in range(1, SSwr.size()):
    W1 = SSwr[i]
    LS1 = W1.LockSet()
    for j in range(i + 1, SSwr.size()):
      W2 = SSwr[j]
      LS2 = W2.LockSet()
      assert (not (W1 <= W2) and not (W2 <= W1))
      if (IntersectionIsEmpty(LS1, LS2)): 
        return True
    foreach R in SSrd: 
      LS3 = R.LockSet()
      if (not (W1 <= R) and IntersectionIsEmpty(LS1, LS3)):
        return True
  return False
```

# Reporting races #

While reporting a race we want to show all accesses involved in it and all locks held during each of the accesses.

```
def ReportRace(is_write, tid, seg, addr):
  (SSwr, SSrd) = GetPerByteState(addr)
  Printf("Possible data race during %s at address %p\n", 
    is_write ? "write" : "read", addr)
  PrintCurrentContext(tid)
  PrintCurrentLockSets(tid)
  foreach S in (SSwr w/o seg): 
    Printf("Concurrent write(s):\n")
    PrintSegmentContext(S) 
    PrintSegmentLockSets(S)
  if not is_write:
    return
  foreach S in (SSrd w/o seg): 
    if not (S <= seg):
      Printf("Concurrent read(s):\n")
      PrintSegmentContext(S) 
      PrintSegmentLockSets(S)
```


**The context of the concurrent accesses printed here is not precise** because
we print the context of a segment containing the concurrent access.
However, if ThreadSanitizer is used with `--keep-history=1` (which is the default),
the tool will create new segment each time the code enters a new super block.
As the result, the concurrent accesses will always have **almost** precise stack trace.

In practice, this means that in 50% cases the stack trace is precise and in other 49.9% cases
the printed stack is **nearly precise** (i.e. the top frame differs by few lines, the other frames are precise).



# Pure happens-before mode #
If we treat the following event pairs as happens-before arcs (in addition to `Signal`/`Wait` pairs), we will get a pure happens-before detector:
  * `Wrunlock(T1,A)` and `Wrlock(T2,A)`
  * `Rdunlock(T1,A)` and `Wrlock(T2,A)`
  * `Wrunlock(T1,A)` and `Rdlock(T2,A)`

# Pure happens-before vs Hybrid #
Unless your code uses lock-less synchronization, the pure happens-before
mode will never report a false race. So, why bother with hybrid then?

Let's look at this example:
```
void Thread1() {
  X = 1;
  mu.Lock(); // E1
  mu.Unlock(); // E2
}
void Thread2() {
  mu.Lock(); // E3
  mu.Unlock(); // E4
  X = 2;
}
```

Here we have a race between `Thread1` and `Thread2` on the variable `X`. 

&lt;BR&gt;


The order in which events E1 and E3 are actually executed depends on the scheduler (i.e. quite random). 

&lt;BR&gt;



If E1 is executed first, than a happens-before arc E2->E3 will be created. 

&lt;BR&gt;


![http://data-race-test.googlecode.com/svn/trunk/msm/purehb1.png](http://data-race-test.googlecode.com/svn/trunk/msm/purehb1.png)

Otherwise (E3 is executed first), an arc E4->E1 will be created.  

&lt;BR&gt;


![http://data-race-test.googlecode.com/svn/trunk/msm/purehb2.png](http://data-race-test.googlecode.com/svn/trunk/msm/purehb2.png)

So, the ability of the pure happens-before race detector to detect this race depends on the scheduler,
in other words the pure happens-before detector is less predictable. 

&lt;BR&gt;




LockSet-based or Hybrid detectors do not suffer from this unpredictability and are much faster, but on downside they have false positives, for example this one:
```
static int COND = 0;
void Thread1() {
  X = 1;
  mu.Lock(); // E1
  COND = 1
  mu.Unlock(); // E2
}
void Thread2() {
  int c;
  do {
    mu.Lock(); // E3
    c = COND;
    mu.Unlock(); // E4
    sleep(1);
  } while(c != 1);
  if (c) {
    X = 2;
  }
}
```
This code (though weird) is correct, but a Hybrid detector will report a false positive.
A pure happens-before detector will be silent. DynamicAnnotations can be used to make
such code friendly to Hybrid detectors.



# Instrumentation: TRACEs #
We instrument the memory accesses in the following way:
when compiling a [TRACE](http://www.pintool.org/docs/33586/Pin/html/group__TRACE__BASIC__API.html)
(which is an **acyclic** single-entry-multiple-exit region of code, in Valgrind it is called **IRSB**)
we create a passport for a TRACE. Since the TRACE is acyclic, the upper
bound of the number of memory operations (NMops) is known at instrumentation time.
So, the passport for a TRACE contains NMops passports of memory operations: `{pc, size, is_write}`.
For each Mop we know its position in a TRACE (`mop_index`).
For each thread we maintain a thread-local buffer which is long enough to hold all Mops of any TRACE.
When we enter a trace (at run-time), we zero first NMops elements of this buffer.
The instrumentation function for a memory access does
`thread_local_buffer[mop_index] = actual_address`,
which is simply one assembly instruction on x86.
When we enter the next TRACE, we flush the contents of the buffer.


The idea of this optimization is taken from `./MemTrace/memtrace.cpp` in PIN distribution.

# Shadow state cache #
Every time ThreadSanitizer analyzes a memory access it needs to get
the shadow state (`GetPerByteState()` above).
The shadow state for every byte of memory is encoded in 8 bytes.
We use a simple software cache and a backing store based
on a hash table to store the shadow state.
The shadow states are grouped into **cache lines**, each line contains
`2^N` shadow states for memory locations `[T*2^N, T*2^N+2^N)`
(`T` is called the **tag** of this cache line).
The **cache** is an array of `2^K` pointers to cache lines.

When we need to get the shadow state for a given address `A`, we first compute
the cache line tag by discarding the `N` least significant bits from `A`:
```
T=A >> N
```
Then we compute the **cache line slot index** `S` by taking `K`
least significant bits of the tag
```
S=T & ((1 << K) - 1).
```
The cache element with the index `S` contains a line
which has this slot index.
If the tag of the stored cache line is `T`, this cache line is what we need.
If the tag is different (or if no cache line is stored at this slot),
we fall back to the slow backing store based on a hash table.




# Fast path #
The state machine described above handles the general case when a
memory location has already been accessed by an arbitrary number
of threads. However the most frequent case is when a memory location
is never shared between threads (i.e. it is always accessed by a single thread).
For this case the implementation of the state machine could be optimized:
it first executes a very simple and fast code which attempts
to update the shadow state as if the memory has not been shared between
threads. If it fails, the original full state machine is then executed.
Our experiments show that on most programs 90%-98% of memory accesses
are never shared between threads. The fast path optimization
improves the performance by 1.5x-2x.


# Events #
The core of the algorithm handles only few types of events (memory accesses and synchronization).
But the real implementation of the detector needs to handle more events.
Below is the list of events which are processed with the Valgrind-based implementation of ThreadSanitizer.

Each of these events contains `tid` (the id of the current thread)
and `pc` (the program counter, aka `ip`, the instruction pointer).
Some events may contain: `id`, which is usually a memory address and `size`, which is `size_t`;

  * Memory access events:
    * `READ(tid, pc, id, size)`
    * `WRITE(tid, pc, id, size)`
  * Control flow events:
    * `RTN_CALL(tid, pc)` and `RTN_EXIT(tid, pc)` -- routine call and exit events.  ThreadSanitizer uses them to maintain the call stack for each thread. These events should match, otherwise the tool will get confused.
    * `SBLOCK_ENTER(tid, pc)` -- entry to a superblock. Optional.  Used to generate nearly-precise information about previous accesses.
  * Memory allocation events:
    * `MALLOC(tid, pc, id, size)` -- allocated memory `[id, id+size)`.
    * `FREE(tid, pc, id)` -- freeing memory at `id` (which was previsouly allocated with `MALLOC`).
  * Thread events:
    * `THR_CREATE(tid, pc, child_tid)` -- the current thread `tid` has created a child thread `child_tid`.
    * `THR_START(tid, pc, parent_tid)` -- this current thread `tid` has started; its parent ir `parent_tid`.
    * `THR_END(tid, pc)` -- the current thread has ended.
    * `THR_JOIN(tid, pc, child_tid)` -- the current thread `tid` has joined thread `child_tid`.
  * Events from a reader-writer lock. `id` is the address of the lock.
    * `LOCK_CREATE(tid, pc, id)`
    * `LOCK_DESTROY(tid, pc, id)`
    * `WR_LOCK(tid, pc, id)`
    * `RD_LOCK(tid, pc, id)`
    * `UNLOCK(tid, pc, id)`
  * Events from other synchronization utilities (e.g. conditional variable or semaphore). `id` is the address of the sync object.
    * `SIGNAL(tid, pc, id)`
    * `WAIT(tid, pc, id)`
  * Events from DynamicAnnotations. Optional
    * `PURE_HAPPENS_BEFORE_MUTEX(tid, pc, id)`,
    * `IGNORE_WRITES_BEGIN(tid, pc)`, `IGNORE_WRITES_END(tid, pc)`, `IGNORE_READS_BEGIN(tid, pc)`, `IGNORE_READ_END(tid, pc)`
    * `SET_THREAD_NAME(tid, pc, name)` -- set the thread name (`name` is `const char*`).
    * `TRACE_MEM(tid, pc, id)`
    * few more...
  * Events from atomic instructions are currently ignored.
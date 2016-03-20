

We've implemented an experimental compile-time instrumentation pass for LLVM that allows us to directly link ThreadSanitizer against the client code instead of using binary instrumentation frameworks.

An instrumented program collects the events (memory accesses, routine calls/exits) and passes them to the runtime library that serves as a proxy between the client code and ThreadSanitizer. The RTL also provides wrappers for functions that ThreadSanitizer should know about (synchronization primitives, allocation routines, [dynamic annotations](DynamicAnnotations.md)

The runtime library is also used by our GCC plugin, see GccInstrumentation.


# Usage and current status #
See the code in http://code.google.com/p/data-race-test/source/browse/#svn/trunk/llvm

We integrate our instrumentation plugin with Clang (http://clang.llvm.org), so you'll need to get, patch and build it.
```
llvm/scripts/clang/get_clang.sh
llvm/scripts/clang/patch_clang.sh
llvm/scripts/clang/build_clang.sh
```

Now build the runtime library:
```
cd tsan_rtl
make # This will build both 32-bit and 64-bit runtime libraries
make install_llvm
```

To compile a small test containing one file:

`$ clang_build_Linux/Release+Asserts/bin/clang -fthread-sanitizer  path/to/program.c -o program` -- produces a binary with builtin ThreadSanitizer

To build a larger program with `make` you'll need to override CC and CXX (and maybe LD) for it.

To run the tests, just execute the resulting binary. Additional flags for ThreadSanitizer can be supplied via the TSAN\_ARGS env variable.

**Obsolete note**: at the moment racecheck\_unittest doesn't pass when linked against ThreadSanitizer.

# Pros and Cons #
Possible advantages:
  * no binary translation and instrumentation overhead at runtime
  * at compile time we know the semantic information that allows us to ignore accesses to thread-local memory (e.g. unescaped stack allocations)

Possible drawbacks:
  * we'll need to recompile libc and other system libraries or somehow hardcode the knowledge about their functions in order to find races on the memory passed to library functions

# How it is done #
The wrappers for `gcc` and `g++` translate C/C++ code into LLVM assembly code using `llvm-gcc`. It is then instrumented using `opt`, which invokes `ThreadSanitizer.so` as a plugin. The instrumented code contains calls to the functions provided by the runtime library. If `gcc`/`g++` is used to link an executable binary, it is additionally linked with the ThreadSanitizer runtime (`tsan_rtl32.a` or `tsan_rtl64.a` depending on the word length)

## Instrumenting the client code ##
Each client module is instrumented independently, no link-time instrumentation is performed. For each module the following steps are done:
  * external declarations are inserted for the functions and global variables provided by the RTL
  * trace (superblock) instrumentation is done
  * each function call/exit is instrumented
  * debug info is written into the `tsan_rtl_debug_info` section

At the moment there are three external functions used by the client code. Those are: `bb_flush()` (used for flushing the thread-local event buffers, see below), `rtl_memcpy()` and `rtl_memmove()` (used to replace the [llvm.memcpy.\*](http://llvm.org/docs/LangRef.html#int_memcpy) and [llvm.memmove.\*](http://llvm.org/docs/LangRef.html#int_memmove) intrinsics). The thread-local global variables used to share the state between the instrumentation code and the runtime library are:
  * ShadowStack -- keeps the shadow stack of the current thread
  * LTID -- contains the literace thread ID (see below)
  * thread\_local\_ignore -- the integer flag used to tell that the current function is ignored
  * TLEB, or thread-local event buffer -- contains the READ/WRITE events to be passed to ThreadSanitizer

During the instrumentation each function is divided into traces (also known as superblocks), which are pieces of the call graph with a single entry and (possibly) multiple exits containing no cycles. For each trace the maximum possible number of memory operations is known at compile time, so it is possible to create a static record containing the following information about the trace:
```
struct TraceInfoPOD {
  enum { kLiteRaceNumTids = 8 };  // takes zero bytes
  size_t n_mops_;
  size_t pc_;
  size_t counter_;
  uint32_t literace_counters[kLiteRaceNumTids];
  int32_t literace_num_to_skip[kLiteRaceNumTids];
  MopInfo mops_[1];
};
```
, where `MopInfo` is defined as follows:
```
struct MopInfo {
  uintptr_t pc;
  uint32_t  size;
  bool      is_write;
};
```

Each trace exit is instrumented with the call to `bb_flush(&current_trace_info)` (typically 2 instructions on x64), which flushes the events collected executing the current trace. Each memory operation ([load](http://llvm.org/docs/LangRef.html#i_load) or [store](http://llvm.org/docs/LangRef.html#i_store)) is instrumented with an LLVM `store` instruction that puts the memory address being accessed into a thread-local buffer (at offset known at compile time). So the following code:
```
  store %dyn_value, %dyn_address
```

is transformed into:
```
  getelementptr @TLEB, i32 0, i64 <static_tleb_offset>
  store %dyn_address, %tleb_address
  store %dyn_value, %dyn_address
```

If the` --workaround-vptr-race` flag is set to true, the first trace of each object's destructor is instrumented in a way that replaces the memory address with NULL if and only if the memory operation is a store and it rewrites the current memory contents with the same value. For example, for following code:
```
  store %new, %a
```
the %ptr to be put into TLEB is calculated as follows:
```
  %old      = load %a
  %destcast = ptrtoint %a to i32
  %neq      = icmp ne %old, %new
  %neqcast  = zext %neq to i32
  %intptr   = mul %destcast, %neqcast
  %ptr      = inttoptr %intptr to i32
```

### Instrumenting the functions ###
After all traces are instrumented each function is furnished with a prologue and an epilogue that maintain the ThreadSanitizer shadow stack. The shadow stack is provided by the RTL and is a thread-local variable of the following type:
```
const size_t kMaxCallStackSize = 1 << 12;
struct CallStackPod {
  uintptr_t *end_;
  uintptr_t pcs_[kMaxCallStackSize];
};
```

Upon each function entry the following instructions are executed:
```
  %end_ptr = getelementptr %1* @ShadowStack, i64 0, i32 0
  %end = load i64** %0
  store i64 %addr, i64* %end
  %new_end = getelementptr i64* %end, i32 1
  store i64* %new_end, i64** %end_ptr
```

, effectively pushing the function address into the stack:
```
  *ShadowStack.end_ = (uintptr_t)addr;
  ShadowStack.end_++;
```

Before leaving the function the original stack top is restored:
```
  store i64* %end, i64** %end_ptr
```

The instrumentation plugin supports blacklists that can be used to ignore distinct functions. A function can be ignored solely, i.e. it won't be instrumented and won't send any messages to ThreadSanitizer or modify the shared state. Another option is to ignore recursively -- then the function is ignored itself, and the `thread_local_ignore` flag is incremented to indicate that ThreadSanitizer should drop all events from the nested functions at runtime.

### Sampling ###
Basically, the idea behind sampling is the following one: if the memory acces is hot, we can omit a portion of reports on it, and still have high probability of reporting a race. So keeping the number of executions for each trace and skipping some of the flushes if this number is high may speed up the detection drastically.

For each trace we store an array of 8 trace counters -- the **i** th counter is updated if the trace is executed on a thread with LTID==i, where LTID is just a cached version of TID modulo 8. We didn't want to keep only one counter per trace, because it could hide races between concurrent executions of the same trace. On the other hand, keeping a per-thread counter for each trace is unacceptably expensive. The trace counters are stored separately from the trace passports in order to keep the former ones cacheline-aligned.

Each trace exit is instrumented with the code that decrements the corresponding trace counter and checks whether it is greater than 0. If yes, the TLEB is flushed, otherwise it is cleared by calling llvm.memset() for the first n records in the buffer, where n is the size of the current trace. Clearing the TLEB is vital: consider that the current trace contains a conditional branch, and the TLEB was not cleared by the previous trace execution. Then, regardless of what branch was taken, all the buffer records would be filled, as if **both** branches were executed by the same thread simultaneously. This may obviously lead to false positives.

```
void Increment() {
  i++;  /* READ &i, WRITE &i */
  j++;  /* READ &j, WRITE &j */
  h++;  /* READ &h, WRITE &h */
}

void Branch() {
  Increment();
  if (i > 0) {   /* READ &i */
    j++;    /* READ &j, WRITE &j */
  } else {
    h++;    /* READ &h, WRITE &h */
  }
}
```

As the trace size is usually rather small, it doesn't always require a call to memset() to do the cleanup -- often a couple of movq instructions is enough.

A tradeoff between the overhead in a normal mode and using sampling is worth noticing. As shown above, it's better to make less calls to `bb_flush()` from the client code, that's why we try to organize more basic blocks together and flush the bunch of them at once. On the other hand, if the cleanup path is taken often, zeroing the TLEB requires much time, which we wouldn't have needed if none of the traces contained conditional branches. That's why one might want to compile her code with a trace size of one basic block, so that the cleanup is unnecessary.

### Debug information ###
The client code instrumentation is done on the SSA level, so the real symbol addresses are unknown at instrumentation time. To solve this problem each memory operation and each function call are assigned synthetic program counter values that depend on the current memory operations and call counters. The assumption is that the number of memory operations and function calls within a function is always less then the size of that function in bytes. Unfortunately this is not always right because of tail-call optimizations (we've found only a single collision in the Chromium binary so far, but it is enough to invalidate this approach). The synthetic addresses are stored along with their location in the source code (path, filename, line) in the `tsan_rtl_debug_info` section of the binary, which is read by ThreadSanitizer at runtime to provide the exact debug info.

### Instrumentation example ###
Here we show a simple C function and the instrumented x86\_64 code (added instructions are prefixed with `*`)
```
void foo(int *a, int *b, int *c, int i) {
  if (a) {
    *a = *b + c[i];
  } else {
    bar();
  }
}
```

```
  push   %r14                # prologue
  push   %rbx                # prologue
  sub    $8,%rsp             # prologue
* mov    TLSOFF(Stack),%rax  #
* mov    %fs:(%rax),%rbx     # rbx=Stack.top
* lea    8(%rbx),%r8         #
* mov    %r8,%fs:(%rax)      # Stack.top++
  test   %rdi,%rdi           # a > 0 ?
  je     <call_bar>          # yes - jump down
* mov    TLSOFF(TLEB),%rax   #
* mov    %rsi,%fs:(%rax)     # TLEB[0] = b
  movslq %ecx,%rcx           # sign-extend i
* lea    (%rdx,%rcx,4),%r8   # t1 = &c[i]
* mov    (%rsi),%esi         # t2 = *b
* mov    %r8,%fs:8(%rax)     # TLEB[1] = t1
  mov    (%rdx,%rcx,4),%ecx  # t3 = c[i]
* mov    %rdi,%fs:16(%rax)   # TLEB[2] = a
* add    %esi,%ecx           # t4 = t3 + t2
  mov    %ecx,(%rdi)         # *a = t4
* mov    <bb_passport>,%edi  #
* callq  <bb_flush_current>  # flush
* mov    TLSOFF(Stack),%rax  #
* mov    %rbx,%fs:(%rax)     # Stack.top--
  end:
  add    $8,%rsp             # epilogue
  pop    %rbx                # epilogue
  pop    %r14                # epilogue
  retq                       # return
  call_bar:
* mov    TLSOFF(Stack),%r14  #
* mov    %fs:(%r14),%rax     #
* movq   PC,(%rax)           # *Stack.top = PC
  callq  <bar>               # call bar()
* mov    %rbx,%fs:(%r14)     # Stack.top--
  jmp    <end>               # go to epilogue
```


### Code speed vs race detection precision ###
## ThreadSanitizer runtime library ##
## gcc/g++ wrappers ##
To build large projects, we use two handy Python scripts that interpose `gcc` and `g++` to do the instrumentation.



# Useful ThreadSanitizer flags #
  * `--suppressions=<filename>`
  * `--ignore=<filename>`
  * `--literace_sampling`
  * `--v`

# Building and testing Chromium #
## Building Chromium ##
  * set up a client and check out the source code following the instruction at http://code.google.com/p/chromium/wiki/LinuxBuildInstructions
  * patch the client with the patch from http://codereview.chromium.org/6524008 , which contains the necessary changes:
    * the default implementation of dynamic\_annotations is not linked with Chromium, because the RTL already provides its own
    * the OVERRIDE macro is expanded to no-op, because llvm-gcc doesn't seem to support it
    * the overridden versions of system allocation functions are disabled (we want to use our wrappers, not those from Chromium)
    * .gyp/include.gypi has some valuable GYP settings
  * run `gclient runhooks`:
```
HOME=`pwd` gclient runhooks
```
  * build `yasm` using `gcc`. Due to some problems the yasm binary doesn't work if built with `llvm-gcc`:
```
make BUILDTYPE=Release out/Release/yasm
```
  * build Chromium:
```
export SCRIPT_PATH=/path/to/data-race-test/llvm/scripts/
TSAN_IGNORE=`pwd`/tools/valgrind/tsan/ignores.txt \
 make -j16 -e CXX="$SCRIPT_PATH/g++" CC="$SCRIPT_PATH/gcc" PATH="$SCRIPT_PATH:$PATH" \
 BUILDTYPE=Release out/Release/chrome
```

## Running Chromium ##
```
TSAN_ARGS="--suppressions=`pwd`/tools/valgrind/tsan/suppressions.txt --show-pc --num_callers=15 --num_callers_in_history=15 --literace-sampling=25"  \
  out/Release/chrome --user-data-dir=./tmp --disable-popup-blocking 2>&1 | tee "llvm-log-`date +'%Y%m%d-%H%M%S'`" | grep race
```

=== Chromium tests used in the (upcoming) MSPC paper

To build and install Valgrind, refer to either the [official site](http://valgrind.org) or the forked version at http://code.google.com/p/valgrind-variant/

Running net\_unittests:
```
valgrind --tool=memcheck --trace-children=yes ~/net_self_cont/out/Release/net_unittests --gtest_filter=-*V8*
valgrind --tool=helgrind --trace-children=yes ~/net_self_cont/out/Release/net_unittests --gtest_filter=-*V8*
valgrind --tool=tsan --trace-children=yes ~/net_self_cont/out/Release/net_unittests --gtest_filter=-*V8*
```

# Future development #
## Short term ##
  * make racecheck\_unittest pass (see http://code.google.com/p/data-race-test/issues/detail?id=52 for the status)
  * try this on something big (Chromium?)
  * finish integration with Clang, fix the hacks
  * update the documentation
  * run CPU2006 and add the results
  * remove the --workaround-vptr-race flag, consult the VPTR symbol names instead
  * use LLVM debug info to get better stack traces for inlined function calls (store several nested symbols for a single pc)
  * read the debug info lazily
  * obtain original pc values (could be done after linking)
  * print symbol names/offsets for races on globals

## Long term ##
  * make it possible to switch between instrumented and uninstrumented versions at runtime
  * use escape analysis to reduce the number of instrumented operations
  * use PIN or other lightweight instrumentation framework to handle uninstrumented libraries
  * address the possible unwinding issues brought by exception handling
  * implement **fast** event logging in the RTL for offline mode
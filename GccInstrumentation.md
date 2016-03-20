# Usage #
First, you obtain and build gcc either version 4.5.2 or 4.5.3. Main steps required for that are outlined [here](http://code.google.com/p/data-race-test/source/browse/trunk/third_party/gcc_install.sh). If you have any problems with the build process, please, refer to http://gcc.gnu.org/.

Now checkout ThreadSanitizer sources:
```
export TSAN_ROOT=<tsan_root_directory>
svn checkout http://data-race-test.googlecode.com/svn/trunk $TSAN_ROOT
```

Build ThreadSanitizer run-time library:
```
cd $TSAN_ROOT/tsan_rtl
make
```

Build the instrumentation plugin (assuming you are using gcc 4.5.3):
```
$ cd $TSAN_ROOT/gcc/plg
$ GCC_VER=4.5.3 GCC_DIR=<gcc_install_path> make
```

Set the following environment variables:
```
$ export GCCTSAN_GCC_VER=4.5.3
$ export GCCTSAN_GCC_DIR=<gcc_install_path>
```

Now you use $TSAN\_ROOT/gcc/scripts/{gcc,g++} as the compiler front-end and $TSAN\_ROOT/gcc/scripts/ld as the linker.
[An ignore file](http://code.google.com/p/data-race-test/wiki/ThreadSanitizerIgnores) may be specified with GCCTSAN\_IGNORE environment variable. Other ThreadSanitizer [flags](http://code.google.com/p/data-race-test/wiki/ThreadSanitizer#Command_line_flags) may be specified with TSAN\_ARGS environment variable.

For example, here is how one builds and executes ThreadSanitizer unittests:
```
$ cd $TSAN_ROOT/unittest
$ GCCTSAN_GCC_VER=4.5.3 GCCTSAN_GCC_DIR=<gcc_install_path> GCCTSAN_IGNORE=$TSAN_ROOT/unittest/racecheck_unittest.ignore make CC=$TSAN_ROOT/gcc/scripts/gcc CXX=$TSAN_ROOT/gcc/scripts/g++ LD=$TSAN_ROOT/gcc/scripts/ld
$TSAN_ARGS="--suppressions=racecheck_unittest.supp --show_pc" ./bin/racecheck_unittest-linux-amd64-O0
```

# Building and Running Chromium #
## Building Chromium ##
  * Set up a client and check out the source code following the instruction at http://code.google.com/p/chromium/wiki/LinuxBuildInstructions
  * Specify the following rule in your .glient custom\_deps section of your src client:
```
  { "name"        : "src",
    "url"         : <...>,
    "custom_deps" : {
      <your old custom_deps here>
      "src/third_party/compiler-tsan": "http://src.chromium.org/svn/trunk/deps/third_party/compiler-tsan"
    },
  }
```
  * Execute:
```
  gclient sync
```
  * Execute:
```
  export CHROME_ROOT=chrome root dir *without* src
  cd $CHROME_ROOT/src/third_party/compiler-tsan
  tar xf gcc-4.5.3.tar
```
  * Execute:
```
  cd $CHROME_ROOT/src
  GYP_DEFINES="linux_use_tcmalloc=0 disable_nacl=1 release_valgrind_build=1 target_arch=x64" gclient runhooks
```
or:
```
  GYP_DEFINES="linux_use_tcmalloc=0 disable_nacl=1 release_valgrind_build=1 target_arch=ia32 chromeos=1" gclient runhooks
```
  * Build base\_unittests to test the whole thing:
```
  GCCTSAN_GCC_DIR=$CHROME_ROOT/src/third_party/compiler-tsan/gcc-4.5.3 GCCTSAN_GCC_VER=4.5.3 GCCTSAN_IGNORE=$CHROME_ROOT/src/tools/valgrind/tsan/ignores.txt GCCTSAN_ARGS="-DADDRESS_SANITIZER -DWTF_USE_DYNAMIC_ANNOTATIONS=1 -DWTF_USE_DYNAMIC_ANNOTATIONS_NOIMPL=1" make CC=$CHROME_ROOT/src/third_party/compiler-tsan/gcc-tsan/scripts/gcc CXX=$CHROME_ROOT/src/third_party/compiler-tsan/gcc-tsan/scripts/g++ LD=$CHROME_ROOT/src/third_party/compiler-tsan/gcc-tsan/scripts/g++ BUILDTYPE=Release -j8 base_unittests
```
  * Run base\_unittests:
```
  LD_LIBRARY_PATH=$CHROME_ROOT/src/third_party/compiler-tsan/gcc-4.5.3/lib32:$CHROME_ROOT/src/third_party/compiler-tsan/gcc-4.5.3/lib64 TSAN_ARGS="--sched_shake=1 --api_ambush=1 --full_stack_frames=1" $CHROME_ROOT/src/out/Release/base_unittests --gtest_filter=ToolsSanityTest.DataRace
```

> You should see a data race report in the console.
  * Build chrome itself:
> `GCCTSAN_GCC_DIR=$CHROME_ROOT/src/third_party/compiler-tsan/gcc-4.5.3 GCCTSAN_GCC_VER=4.5.3 GCCTSAN_IGNORE=$CHROME_ROOT/src/tools/valgrind/tsan/ignores.txt GCCTSAN_ARGS="-DADDRESS_SANITIZER -DWTF_USE_DYNAMIC_ANNOTATIONS=1 -DWTF_USE_DYNAMIC_ANNOTATIONS_NOIMPL=1" make CC=$CHROME_ROOT/src/third_party/compiler-tsan/gcc-tsan/scripts/gcc CXX=$CHROME_ROOT/src/third_party/compiler-tsan/gcc-tsan/scripts/g++ LD=$CHROME_ROOT/src/third_party/compiler-tsan/gcc-tsan/scripts/g++ BUILDTYPE=Release -j8 chrome`
  * Run chrome:
> `LD_LIBRARY_PATH=$CHROME_ROOT/src/third_party/compiler-tsan/gcc-4.5.3/lib32:$CHROME_ROOT/src/third_party/compiler-tsan/gcc-4.5.3/lib64 TSAN_ARGS="--sched_shake=1 --api_ambush=1 --full_stack_frames=1 --suppressions=$CHROME_ROOT/src/tools/valgrind/tsan/suppressions.txt" G_SLICE=always-malloc NSS_DISABLE_ARENA_FREE_LIST=1 NSS_DISABLE_UNLOAD=1 $CHROME_ROOT/src/out/Release/chrome`

> If the program is a way too slow set sched\_shake parameter to 0.
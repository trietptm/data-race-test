#summary ThreadSanitizer is a Valgrind-based detector of data races
#labels Featured

This page is about ThreadSanitizer version 1.
For the new (and better supported) version go to
http://code.google.com/p/thread-sanitizer


ThreadSanitizer paper was presented at [WBIA'09](http://dl.acm.org/citation.cfm?id=1791203): [PDF](http://webcluster.cs.columbia.edu/~junfeng/reliable-software/papers/thread-sanitizer.pdf)




# Introduction #

**ThreadSanitizer** (aka **tsan**, **not** "Thread Sanitizer") is a data race detector for C/C++ programs. 

&lt;BR&gt;


The Linux and Mac versions are based on [Valgrind](http://www.valgrind.org). 

&lt;BR&gt;


The Windows version is based on [PIN](http://www.pintool.org). 

&lt;BR&gt;


ThreadSanitizer is similar to [Helgrind](http://valgrind.org/docs/manual/hg-manual.html) in many ways, but it also has several
[differences](ThreadSanitizerVsOthers.md). 

&lt;BR&gt;


The instrumentation code is partially taken from Helgrind;
but the [race detection machinery](ThreadSanitizerAlgorithm.md) is absolutely new (the code is written in C++). 

&lt;BR&gt;


The source code is published under BSD-like licence (except for valgrind-related modules which are GPLv2+).

ThreadSanitizer is being actively developed and used at [Google](http://www.google.com).

See also:
  * ThreadSanitizerAlgorithm
  * MemoryUsage
  * ThreadSanitizerSuppressions
  * ThreadSanitizerIgnores
  * ThreadSanitizerVsOthers
  * UnderstandingThreadSanitizerReports
  * RacecheckUnittest
  * DynamicAnnotations
  * RaceCheckerClass
  * RaceDetectionLinks: links to other materials related to race detection
  * PopularDataRaces
  * ThreadSanitizerOffline: offline race detector
  * ThreadSanitizerPin: [PIN](http://www.pintool.org)-based variant

Contacts: **data-race-test(#)googlegroups.com**

# How to get #
You may download the pre-built binaries from the ThreadSanitizerBuildBot

If you want to build ThreadSanitizer youself, refer to BuildingThreadSanitizer.

ThreadSanitizer is supported on the following platforms:
  * Linux x86\_64 and x86. Tested on Ubuntu 8.04 and 9.10.
  * Darwin i386 (MacOS X 10.5).
  * Windows i386 (Tested on 7, Vista and XP)
  * In progress:
    * ARM Linux

# Using ThreadSanitizer #
### on Linux and Mac ###
Just like any other valgrind-based tool:
```
valgrind [valgrind options] --tool=tsan [--tsan-options] your/program [program options]
```
or (if you are using the self-contained binary):
```
tsan.sh [--tsan-options] your/program [program options]
```
### on Windows ###
Run ThreadSanitizer like this (assuming you unpacked it in **C:\**):
```
C:\tsan-x86-windows\tsan.bat [--tsan-options] -- your\program.exe [program options]
```

# Command line flags #
| Flag name | default | description |
|:----------|:--------|:------------|
| **Analysis sensitivity flags:** |         | ThreadSanitizer can work in different modes that affect accuracy (number of detected bugs, number of false reports) and speed.|
| --keep-history=0|1          | 1       |  Keep the history of the previous accesses. By default, the stack traces of concurrent accesses are _almost_ precise. 

&lt;BR&gt;

 Setting this option to zero will make the tool run 10%-30% faster, but the concurrent accesses will not be printed. 

&lt;BR&gt;

 Use --keep-history=0 in continuous builds, and --keep-history=1 when analyzing reports. |
|  --hybrid=yes|no | no      | Act as a hybrid detector (PureHappensBeforeVsHybrid) |
|  --free-is-write=yes|no | no      | Treat `free()/delete/...` as a memory access (write), thus reporting races between `free()` and other memory accesses. **On by default since [r2273](https://code.google.com/p/data-race-test/source/detail?r=2273)**  |
|        **Interface flags:**     |         | Flags that affect the generated output. |
|  --log-file=filename        |  ""     | Dump the output to `filename`; if empty dump to `stderr`|
|  --color                      |  no     | Add colors to the output using [ANSI escape codes](http://en.wikipedia.org/wiki/ANSI_escape_code). |
|  --show-pc                    | no      | Show pc (program counter) in the stack traces. |
|  --announce-threads           | no      | Show the stack traces of thread creation . |
|  --fullpath-after=file\_prefix |         |   Remove `"^.*file_prefix"` from the printed file names.  You may pass this flag several times. |
| **Resource usage** |         |             |
| --max-sid |8388608 (2^23) | This number of unique Segment IDs. 

&lt;BR&gt;

 This reflects the amount of memory allocated by ThreadSanitizer at startup. One Segment ID requires ~100 bytes of memory, so by default approximately 800M of memory is allocated.

&lt;BR&gt;

 The higher this number the better. This number can not be very small (<100000). The upper bound depends on the amount of available memory.  |
| --num-callers | 12      | The size of the stack trace printed for the current access. Increasing this number does not affect performance. |
| --num-callers-in-history | 10      | The size of the stack trace stored for the concurrent accesses. <br> Increasing this number improves the reports but increases the memory footprint and slows down the execution. <br>
<tr><td> <b>Profiling</b> </td><td>         </td><td>             </td></tr>
<tr><td> --sample-events=N </td><td> 0       </td><td>  If non zero, ThreadSanitizer will sample one of 2^N events and at the end print the event profile. <br> This options could be used together with ThreadSanitizerIgnores. </td></tr></tbody></table>

# Screenshot #
ThreadSanitizer's output viewed in [vim](http://www.vim.org) with syntax highlightning and the [source code](RacecheckUnittest.md) in the second window:

> ![http://data-race-test.googlecode.com/svn/trunk/images/tsan-in-vim3.png](http://data-race-test.googlecode.com/svn/trunk/images/tsan-in-vim3.png)
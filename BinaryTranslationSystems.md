**UNDER CONSTRUCTION**

Here we attempt to compare the most popular binary translation systems:
  * [Valgrind](http://www.valgrind.org)
  * [PIN](http://www.pintool.org)
  * [DynamoRio](http://dynamorio.org/)
This comparison is by no means complete.
Your comments are welcome!


|  |[Valgrind](http://www.valgrind.org) |[PIN](http://www.pintool.org) | [DynamoRio](http://dynamorio.org/)|
|:-|:-----------------------------------|:-----------------------------|:----------------------------------|
|  license |  GPL                               |  [Proprietary](http://www.pintool.org/faq.html) |   BSD                             |
| source available |  yes                               |  no                          |   yes                             |
| cost |  free                              | free                         |  free                             |
| Windows (native) | no                                 |   x86/x86\_64                |  x86/x86\_64                      |
| Windows (Linux+wine)| [yes](http://build.chromium.org/buildbot/waterfall.fyi/builders/Chromium%20Linux%20Wine%20(valgrind)/builds/532) |   ?                          |  ?                                |
| Linux | x86/x86\_64/ARM/PPC                | x86/x86\_64                  |  x86/x86\_64                      |
| Mac  |  x86                               |  no                          |  no                               |
| support for static binaries | limited                            |  yes                         |  limited (?)                      |
| attach to process |  no                                |  yes                         | not yet                           |
| runs threads in parallel | no                                 | yes                          |  yes                              |
| Memory error detector(s) | Memcheck                           |  [Intel Inspector](http://software.intel.com/en-us/intel-parallel-inspector/) |  [DrMemory](http://dynamorio.org/drmemory.html) |
| Race detector(s) | Helgrind,DRD,ThreadSanitizer       |  [Intel Inspector](http://software.intel.com/en-us/intel-parallel-inspector/), ThreadSanitizerPin |  not yet                          |
| Other heavyweight tools  |  Callgrind, Massif, etc            | ?                            |  ?                                |
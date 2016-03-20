# Please HELP!!! #

Reader, we need your help!
We want to collect an exhaustive and well annotated list of links to all materials related to race detection.

## Race detectors ##

  * Intel Thread Checker
    * Pure happens-before race detector, available on both Windows and Linux
    * Supports annotations (**TODO**: find a link to help/manual!)
    * Supports both compile-time and run-time instrumentation
    * A couple of papers are available:
      1. [U. Banerjee, B. Bliss, Z. Ma, and P. Petersen - A theory of data race detection](http://portal.acm.org/citation.cfm?id=1147416)
      1. [U. Banerjee, B. Bliss, Z. Ma, and P. Petersen - Unraveling Data Race Detection in the Intel® Thread Checker](http://software.intel.com/file/6311)
    * [Product homepage](http://software.intel.com/en-us/intel-thread-checker/)
    * Available for download the Linux version for noncommercial use
  * Sun Thread Analyzer
    * Hyrbid race detector, available on Solaris, SuSE Linux Enterprise Server 9 and the Red Hat Enterprise Linux 4
    * Supports annotations ([documentation](http://developers.sun.com/sunstudio/downloads/tha/tha_using.html#User%20APIs))
    * Requires compile-time instrumentation
    * TODO: download site, link to paper (any available?), comments
  * Helgrind
    * Pure happens-before race detector (since 3.4), available on Linux and Mac
    * Doesn't support annotations (as of August 14, work in progress)
    * Based on Valgrind run-time instrumentation framework
    * Open sourced as a part of Valgrind ([download](http://valgrind.org/downloads/), [manual](http://valgrind.org/docs/manual/hg-manual.html))
    * TODO: paper (any available?), comments
  * DRD
    * Pure happens-before race detector, available on Linux and Mac
    * Annotations are (partly?) supported (as of August 14, work in progress)
    * Based on Valgrind run-time instrumentation framework
    * Open sourced as a part of Valgrind ([download](http://valgrind.org/downloads/), [manual](http://valgrind.org/docs/manual/drd-manual.html))
    * TODO: paper (any available?), comments
  * MTRAT/MSDK: http://www.alphaworks.ibm.com/tech/msdk
    * IBM's Race detector for Java
    * Article: http://portal.acm.org/citation.cfm?doid=1639622.1639627
  * Lamport's paper
    * [L. Lamport, Time, clocks, and the ordering of events in a distributed system](http://portal.acm.org/citation.cfm?id=359563)
    * TODO: link to a paper
  * Eraser
    * Lockset-based race detector
    * [S. Savage , M. Burrows , G. Nelson , P. Sobalvarro, T. Anderson - Eraser: a dynamic data race detector for multithreaded programs](http://portal.acm.org/citation.cfm?id=265927)
    * TODO: comments
  * ThreadSanitizer: valgrind-based race detector. Supports both hybrid and pure happens-before modes.
    * Supports both hybrid and pure happens-before modes, available on Linux and Mac
    * Support annotations
    * Based on Valgrind run-time instrumentation framework
    * Open sourced ([download instructions, manual](http://code.google.com/p/data-race-test/wiki/ThreadSanitizer))
    * Paper presented at [WBIA'09](http://www.dyninst.org/wbia09/): http://pintool.org/wbia09.pdf, pages 62-71.

## Articles on race detection ##
**TODO** (add more)

  * [ConMem: Detecting Severe Concurrency Bugs through an Effect-Oriented Approach](http://pages.cs.wisc.edu/~shanlu/paper/asplos184-zhang.pdf). Wei Zhang, Chong Sun, and Shan Lu. 15th International Conference on Architecture Support for Programming Languages and Operating Systems (ASPLOS'10).
  * [Conflict Exceptions: Simplifying Concurrent Language Semantics with Precise Hardware Exceptions for Data-Races](http://www.cs.washington.edu/homes/luisceze/publications/isca173-lucia.pdf) -- fast race detection which requires hardware support.
  * [Adversarial Memory for Detecting Destructive Races](http://slang.soe.ucsc.edu/cormac/papers/pldi10.pdf) -- automatically checking if a race is benign or harmful.
  * [Effective Data-Race Detection for the Kernel](http://www.usenix.org/events/osdi10/tech/full_papers/Erickson.pdf). John Erickson, Madanlal Musuvathi, Sebastian Burckhardt, and Kirk Olynyk, Microsoft Research. -- Using hardware break points and watch points to detect races at run-time. As ingenious as it is simple!

## General bug-finding links ##

  * http://cacm.acm.org/magazines/2010/2/69354-a-few-billion-lines-of-code-later/fulltext/ -- extremely entertaining reading about the "Coverity" static analysis tool.

## High-Level Data Races ##
  * [High-Level Data Races. Cyrille Artho, Klaus Havelund, Armin Biere.](http://staff.aist.go.jp/c.artho/papers/vveis03.pdf) Continuation Eraser approach. Basic examination object is set of access to variables near lock. Intersect of this sets for same lock produced view of variables - one of basic definition in this paper. Unhappily, this algorithm doesn't help us in [First motivational example](http://code.google.com/p/data-race-test/wiki/HighLevelDataRaces?ts=1280497301&updated=HighLevelDataRaces#First_motivational_example). It's cover [Inconsistent state](http://code.google.com/p/data-race-test/wiki/HighLevelDataRaces?ts=1280745577&updated=HighLevelDataRaces#Inconsistent_state). By the way, article describe high level data-race occurred in NASA spacecraft controller. Algorithm described in Section 3 and occupy only one page. **Large number of false positives** on the real-world applications state in MUVI paper. Implementation name is **Java PathExplorer**.

  * [MUVI: Automatically Inferring Multi-Variable Access Correlations and Detecting Related Semantic and Concurrency Bugs. Shan Lu, Soyeon Park, Chongfeng Hu, Xiao Ma, Weihang Jiang Zhenmin Li, Raluca A. Popa, Yuanyuan Zhou](http://web.mit.edu/ralucap/www/MUVI.pdf). Multi-Variable Race Detection. Introduce model of variable correlations basic on static analyse. Defines correlate-metrics in a source code. This approach can auto-determine correlated variables in reasonably mature programs. MUVI can generate annotation for other race detectors. Also develop multi-variable variant of lock-set and happens-before algorithms. Number of **false-positives is comparable with true-bugs** (13 false vs 8 true).
  * [Randomized Active Atomicity Violation Detection in Concurrent Programs. Chang-Seo Park, Koushik Sen](http://parlab.eecs.berkeley.edu/sites/all/parlab/files/Randomized%20Active%20Atomicity%20Violation%20Detection%20in%20Concurrent%20Programs.pdf). Suggest use own randomized scheduler with different seeds. If annotated 'atom' blocks interleaving then report existing atomicity violation. With stored seed it's easy to reproduce violation case. Number of **false-positives is comparable with true-bugs** (7 false vs 14 true). Author's Implementation for Java named **AtomFuzzer** (only prototype).
  * [CTrigger: Exposing Atomicity Violation Bugs from Their Hiding Places. Soyeon Park, Shan Lu, Yuanyuan Zhou](http://pages.cs.wisc.edu/~shanlu/paper/asplos092-zhou.pdf). Suggest two-phase algorithm to find Unserializable Interleavings. First phase identify target interleavings by 3 steps. Second phase - controlled testing, if exists bug. Generally approach same with _Randomized Active Atomicity Violation Detection in Concurrent Programs_: tricky scheduler. But unlikely previous work, CTrigger can identify potential dangerous regions without annotations, base on definition of Unserializable Interleavings.
  * [AVIO: Detecting Atomicity Violations via Access Interleaving Invariants. Shan Lu, Joseph Tucek, Feng Qin and Yuanyuan Zhou](http://www.google.ru/url?sa=t&source=web&cd=1&ved=0CBUQFjAA&url=http%3A%2F%2Fciteseerx.ist.psu.edu%2Fviewdoc%2Fdownload%3Fdoi%3D10.1.1.91.1388%26rep%3Drep1%26type%3Dpdf&ei=V7t7TNiZJ47Gswb4z8CyDQ&usg=AFQjCNHYCFY-_AGnRyfY1GmqGDV10sjfrg). Like CTrigger main idea of paper is automatically define atomicity regions, named Access Interleaving Invariants. Program running with same input about 100 times. Remember pairs of instruction from same thread without interleaving. And suggest they atomicity. After learning phase, information about atomicity regions can used for finding atomicity violations. Produce **a lot of false-positives** (16 false vs 4 true).
  * [Finding stale-value errors in concurrent programs. M. Burrows and K. R. M. Leino.](http://www.google.ru/url?sa=t&source=web&cd=1&ved=0CBUQFjAA&url=http%3A%2F%2Fresearch.microsoft.com%2Fen-us%2Fum%2Fpeople%2Fleino%2Fpapers%2Fkrml107.pdf&ei=3xiGTOPEG8q6ONCc6NAO&usg=AFQjCNF7oOz23Zu5Mu4uFMmt2GI5KlZv1Q) Suggest use instrumentation for add for every local variable _t_ boolean _stale\_t_ variable. Support invariant: _stale\_t_ is _true_ if and only if the value of _t_ is considered stale. For every read t _assert(!stale\_t)_ must passed, over wise we report stale-value error. Also bring in two other subsidiary invariants. Approach has problems with multi-locks and produce **many false-positives** (43 false alarm vs 4 true bugs).
  * [Atom-Aid: Detecting and Surviving Atomicity Violations. Brandon Lucia.](http://www.cs.washington.edu/homes/luisceze/publications/lucia-atomaid.pdf) Asseverates typical atomicity violation ranges from 500 to 750 dynamic instructions. Suggest sophisticated united code in chucks size about 2000. Thereby potentially atomicity violation regions are hidden in the same chunk. Chucks executes atomically and in isolation. Based on implicit atomicity systems (BulkSC, Atomic Sequence Ordering, Implicit Transactions). Hiding 99% of real atomicity violations (Apache, MySQL, XMMS).
  * [Type and Effect System for Atomicity. Cormac Flanagan, Shaz Qadeer.](http://portal.acm.org/ft_gateway.cfm?id=781169&type=pdf&CFID=115747275&CFTOKEN=66573491A) Introduced (static?) atomicity proof system. Demanded atomic annotations. Determined, when we can swap two adjacent instructions (For example: lock.acquire() - right mover, lock.release() - left mover). To check annotated method X system alternates X's instruction with another abstract instructions and tries bring to bay all X's instruction to makes they adjacent. Found new atomicity violations in java.lang.StringBuffer and java.lang.String. (JDK 1.4)
  * [Kivati: Fast Detection and Prevention of Atomicity Violations. Lee Chew, David Lie.](http://www.google.ru/url?sa=t&source=web&cd=2&ved=0CB8QFjAB&url=http%3A%2F%2Fwww.eecg.toronto.edu%2F~lie%2Fpapers%2Fchew-eurosys2010-web.pdf&rct=j&q=Atomicity%20violation%20detection&ei=HizuTPfTJMPFswayuoD6Cg&usg=AFQjCNFoe8qvj78cqXUH1nBZXkEbqPbdmg&cad=rja) Static DFA analyse determines pairs of consecutive memory access and define this section atomic. For DFA uses CIL (Intermediate Language and Tools for Analysis and Transformation of C Programs) framework. In runtime checks atomicity of region. Low overhead (18 - 30 %). Affirm founding 11 known bugs in 5 real applications. To determine atomicity violations in runtime, uses watchpoints (implementation on x86).
  * [Static Detection of Atomicity Violations in Object-Oriented Programs. Christoph von Praun and Thomas R. Gross](http://www.google.ru/url?sa=t&source=web&cd=1&ved=0CBcQFjAA&url=http%3A%2F%2Fciteseerx.ist.psu.edu%2Fviewdoc%2Fdownload%3Fdoi%3D10.1.1.58.3931%26rep%3Drep1%26type%3Dpdf&rct=j&q=Static%20Detection%20of%20Atomicity%20Violations%20in%20Object-Oriented%20Programs&ei=6RL4TNWcBIzzsgaasp3ZCA&usg=AFQjCNHybje4CMtkXtwx3EJ7wft-jM_ldQ&cad=rjt) Continuation PathExplorer _view consistency_ approach (paper "High-Level Data Races. Cyrille Artho, Klaus Havelund, Armin Biere"). Introduce new definition - _method consistency_. Just extends it to accommodate the scope of methods as consistency criterion. Author are honest: paper contains two examples, where algorithm gets wrong result: false positive and false negative.
  * [Runtime Analysis of Atomicity for Multithreaded Programs. Liqiang Wang and Scott D. Stoller](http://www.cs.sunysb.edu/~stoller/papers/runtime-atomicity-TSE-2006.pdf) Describes and comparisons different algorithms. Consider two analyse approaches for atomicity violation (and well-known happens-before and lockset for data races): REDUCTION-BASED ALGORITHM (online and offline), BLOCK-BASED ALGORITHM (runtime). First is improvement of _Lipton reduction_. Simple static analyse, demands user annotations about transaction regions. Second algorithm is just finding suspicious patterns in runtime instructions. Seems like this approach more closed to race detection.
  * [How to miscompile programs with “benign” data races, Hans-J. Boehm](http://www.usenix.org/event/hotpar11/tech/final_files/Boehm.pdf) The paper shows that all kinds of C or C++ source-level “benign” races discussed in the literature can in fact lead to incorrect execution as a result of perfectly reasonable compiler transformations, or when the program is moved to a different hardware platform. Thus there is no reason to believe that a currently working program with “benign races” will continue to work when it is recompiled. Perhaps most surprisingly, this includes even the case of potentially concurrent writes of the same value by different threads.

## TODO ##
**TODO** add all links we already have somewhere.

**TODO** find new interesting links.


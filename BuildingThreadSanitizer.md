# Valgrind-based version #

ThreadSanitizer is not a part of the official valgrind distribution, so you will
have to download valgrind and ThreadSanitizer separately. You will also have to
apply a small patch to valgrind.

To build both 32-bit and 64-bit versions of ThreadSanitizer on Ubuntu Lucid 64-bit, you will need to first install several additional packages:
```
apt-get install subversion automake libc6-dbg libc6-dev-i386 g++-multilib
```

Then, just run the [./get\_and\_build\_tsan.sh script](http://data-race-test.googlecode.com/svn/trunk/tsan/get_and_build_tsan.sh) in your terminal window.

```
wget http://data-race-test.googlecode.com/svn/trunk/tsan/get_and_build_tsan.sh  && \
  chmod +x ./get_and_build_tsan.sh && \
  ./get_and_build_tsan.sh `pwd`/tsan_inst_tmp
```

**Note:** valgrind crashes if linked using [gold](http://en.wikipedia.org/wiki/Gold_(linker)) (see [bug](https://bugs.kde.org/show_bug.cgi?id=193413))
```
valgrind: mmap(0x400000, 241664) failed in UME with error 22 (Invalid argument).
valgrind: this can be caused by executables with very large text, data or bss segments.
```
Please make sure you don't use gold as a linker before building ThreadSanitizer.
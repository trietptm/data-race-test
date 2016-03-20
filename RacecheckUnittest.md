﻿#summary Unit tests for data race detector.


# C++ #

We have many tests for data race detectors. You can find the source code [in the SVN](http://code.google.com/p/data-race-test/source/browse/#svn/trunk/unittest).

To get and compile the unittests:
```
svn checkout http://data-race-test.googlecode.com/svn/trunk tsan_test
cd tsan_test/unittest
make  # if you're on Windows, run this in a cygwin shell run from VS-enabled cmd
```

Run:
```
# Run only one test from the old test suite (test42): 
./bin/racecheck_unittest-linux-amd64-O0 42 --gtest_filter="*NonGtest*" 
# Run only one test from the new test suite: 
./bin/racecheck_unittest-linux-amd64-O0 --gtest_filter="NegativeTests.EmptyRepTest"
# Run the whole test suite: 
./bin/racecheck_unittest-linux-amd64-O0
```

For more options refer to `unittest/Makefile` and other source files.

# Java #
So far we have a very small set of tests for a Java race detector.
```
cd data-race-test/third_party
svn checkout http://java-thread-sanitizer.googlecode.com/svn/trunk/
cd java-thread-sanitizer
ant download
ant
ant test
```
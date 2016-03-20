#summary The RaceChecker class -- helps confirming data races.

The RaceChecker class helps confirming data races, e.g. those detected by Helgrind or ThreadSanitizer.

If RaceChecker detected a race it is a 100% proof of a race.
If it did not detect a race it proves nothing.

## How it works ##

When the program enters RaceChecker's constructor, it remembers the address of the racey object (e.g. `&foo`) and then sleeps. Then, in the destructor, it forgets `&foo`.

If Thread2 entered RaceChecker's constructor while Thread1 is sleeping in RaceChecker's constructor with the same racey object (`&foo`), there are two concurrent accesses to `&foo`. If one of them is write -- bingo, we found a race. The code is pretty simple, it might be better than my explanation :)

See [race\_checker.h](http://code.google.com/p/data-race-test/source/browse/trunk/race_checker/race_checker.h) and
[all race checker files](http://code.google.com/p/data-race-test/source/browse/trunk/race_checker) for details.

## Example ##
```
int foo = 0;  // The racey address.

// Several reads and writes, nested calls to RaceChecker.
void ReaderAndWriter() {
  for (int i = 0; i < 1000; i++) {
    RaceChecker read_checker(RaceChecker::READ, &foo);
    assert(foo >= 0);  // Just a read.
    if ((i % 10) == 0) {
      RaceChecker write_checker(RaceChecker::WRITE, &foo);
      foo++;
    }
    assert(foo >= 0);  // Just a read.
  }
}

// More functions to make the stack traces more interesting.
static void *Dummy3(void *x) { ReaderAndWriter(); return NULL; }
static void *Dummy2(void *x) { return Dummy3(x); }
static void *Dummy1(void *x) { return Dummy2(x); }

int main() {
  pthread_t threads[3];
  pthread_create(&threads[0], NULL, &Dummy1, NULL);
  pthread_create(&threads[1], NULL, &Dummy2, NULL);
  pthread_create(&threads[2], NULL, &Dummy3, NULL);

  pthread_join(threads[0], NULL);
  pthread_join(threads[1], NULL);
  pthread_join(threads[2], NULL);
}
```


```
% g++ -g race_checker.cc race_checker_unittest.cc -lpthread
```
```
% RACECHECKER=1 ./a.out 2>&1 | head -19  | ./symbolize.py | c++filt
Race found between these points
=== writer:
./a.out[0x40541a] <ReaderAndWriter()>
./a.out[0x4054a7] <Dummy3(void*)>
./a.out[0x4054c3] <Dummy2(void*)>
./a.out[0x4054db] <Dummy1(void*)>
/lib64/tls/libpthread.so.0[0x2aaaaacc7f9f] <_fini>
/lib64/tls/libc.so.6(clone+0x72)[0x2aaaab719ea2]
=== reader:
./a.out[0x4053ae] <ReaderAndWriter()>
./a.out[0x4054a7] <Dummy3(void*)>
./a.out[0x4054c3] <Dummy2(void*)>
/lib64/tls/libpthread.so.0[0x2aaaaacc7f9f] <_fini>
/lib64/tls/libc.so.6(clone+0x72)[0x2aaaab719ea2]
=== reader:
./a.out[0x4053ae] <ReaderAndWriter()>
./a.out[0x4054a7] <Dummy3(void*)>
/lib64/tls/libpthread.so.0[0x2aaaaacc7f9f] <_fini>
/lib64/tls/libc.so.6(clone+0x72)[0x2aaaab719ea2]
```
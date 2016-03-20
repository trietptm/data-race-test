# Definitions and types of High-Level Data Races #

**TODO** High-Level Data Race - potential dangerous concurrent code without regular data races.
[Links](http://code.google.com/p/data-race-test/wiki/RaceDetectionLinks#High-Level_Data_Races) to articles about HL data races detection.

**Atomicity** - also called as **serializability**, is a property for the concurrent execution of several operations when their data manipulation effect is equivalent to that of a serial execution of them.  The assumed atomicity can be broken when the code region is unserializably interleaved by accesses from another thread, which leads to an **atomicity violation bug**. _S. Lu, J. Tucek, F. Qin, and Y. Zhou. AVIO: Detecting atomicity violations via access interleaving invariants. In ASPLOS, 2006._

The basic type of **unserializable interleavings** is composed of three memory accesses. Two of them, referred to as p(receding)-access and c(urrent)-access, consecutively access a shared location from the same thread. The third one, referred to as r(emote)-access, accesses the same memory location in the middle of the previous two from a different thread. Unserializable interleaving space gives a good coverage for all potential atomicity violation bugs. _S. Park, S. Lu, and Y. Zhou. Ctrigger: exposing atomicity violation bugs from their hiding places. In Fourteenth International Conference on Architec- ture Support for Programming Languages and Op- erating Systems (ASPLOS ’09), pages 25–36, Mar. 2009._

**Multi-Variable Race** also called **inconsistent state**. There are correlated variables e.g. field of one object, describe same side of object. Concurrent bugs could occur when there is no race on each single variable. See examples: inconsistent state.

# Examples #

## First motivational example ##

Consider following **java** source

```
  public void arraySize() {
    new ThreadRunner(2) {
      private int uk;
      private int[] stack;

      public void setUp() {
        stack = new int[20];
      }

      synchronized int getSize() {
        return uk;
      }

      synchronized void push(int x) {
        stack[uk++] = x;
      }

      synchronized int pop() {
        return stack[--uk];
      }

      public void thread1() {
        for (int i = 0; i < 10; i++) {
          push(i);
        }
      }

      public void thread2() {
        while (getSize() > 0) {
          // BAD BAD BAD!
          pop();
        }
      }
    };
  }
```

We havn't tradition data race, but code is unsafe.

## Inconsistent state ##

Following example take from [this paper](http://staff.aist.go.jp/c.artho/papers/vveis03.pdf). Main idea: we have complicated object with several propertis. And we have several methods to prompt it to other state. Than, without explicit synchronization we can get inconsistent state of this object.

Example:

```

  public void pointInconsistentState() {
    new ThreadRunner(2) {
      class Point {
        private int x, y;

        public Point() {
          x = 0;
          y = 0;
        }

        public synchronized int getX() {
          return x;
        }

        public synchronized void setX(int nx) {
          x = nx;
        }

        public synchronized int getY() {
          return y;
        }

        public synchronized void setY(int ny) {
          y = ny;
        }

        public synchronized int[] getXY() {
          return new int[]{x, y};
        }

        public synchronized void setXY(int[] xy) {
          x = xy[0];
          y = xy[1];
        }
      }

      Point point;

      public void setUp() {
        point = new Point();
      }

      public void thread1() {
        point.setX(100);
        // BAD BAD BAD!
        point.setY(100);
      }

      public void thread2() {
        Point localPoint = new Point();
        int[] xy = point.getXY();
        localPoint.setXY(xy);
      }
    };
  }
```
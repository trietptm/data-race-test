//===-- tsan_thread.h -------------------------------------------*- C++ -*-===//
//
//                     The LLVM Compiler Infrastructure
//
// This file is distributed under the University of Illinois Open Source
// License. See LICENSE.TXT for details.
//
//===----------------------------------------------------------------------===//
//
// This file is a part of ThreadSanitizer (TSan), a race detector.
//
// TsanThread.
//===----------------------------------------------------------------------===//

#ifndef TSAN_THREAD_H
#define TSAN_THREAD_H

#include "tsan_rtl.h"

namespace __tsan {

class TsanThread {
 public:
  static TsanThread *Create(void *callback, void *param);
  void *ThreadStart();
 private:
  TsanThread() { }
  void *callback_;
  void *param_;
};

}  // namespace __tsan

#endif  // TSAN_THREAD_H
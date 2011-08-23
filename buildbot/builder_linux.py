from buildbot.process import factory
from buildbot.steps.source import SVN
from buildbot.steps.shell import Compile
from buildbot.steps.shell import Test
from buildbot.steps.shell import ShellCommand
from common import *

def generate(settings):
  f1 = factory.BuildFactory()

  addSetupTreeForTestsStep(f1)

  # Run thread_sanitizer and suppressions tests.
  addTsanTestsStep(f1, ['amd64-linux-debug', 'x86-linux-debug'])

  # Run output tests.
  f1.addStep(ShellCommand(command='make -C unittest OS=linux ARCH=amd64 TSAN="../tsan.sh" run_output_tests',
                          description="running output tests 64",
                          descriptionDone="output tests 64"))
  f1.addStep(ShellCommand(command='make -C unittest OS=linux ARCH=x86 TSAN="../tsan.sh" run_output_tests',
                          description="running output tests 32",
                          descriptionDone="output tests 32"))

  # Run unit tests.
  test_binaries = {} # (bits, opt, static) -> (binary, desc)
  os = 'linux'
  #                  test binary | tsan + run parameters
  #             bits, opt, static, tsan-debug, threaded, mode
  variants = [((  64,   1, False),(        True, False, 'hybrid')),
              ((  64,   1, False),(        True, False, 'phb')),
              ((  32,   1, False),(        True, False, 'hybrid')),
              ((  64,   0, False),(        True, False, 'hybrid')),
              ((  64,   1, False),(       False, False, 'phb')),
              ((  32,   0, False),(       False, False, 'hybrid')),
              ((  64,   1, False),(       False, True,  'phb'))]
  for (test_variant, run_variant) in variants:
    (tsan_debug, threaded, mode) = run_variant
    if not test_binaries.has_key(test_variant):
      (bits, opt, static) = test_variant
      test_desc = getTestDesc(os, bits, opt, static)
      test_binaries[test_variant] = test_desc
    test_binary = unitTestBinary(os, bits, opt, static)
    addTestStep(f1, tsan_debug, threaded, mode, test_binary, test_desc, extra_args=['--error_exitcode=1'])
    addTestStep(f1, tsan_debug, threaded, mode, test_binary, test_desc + ' RV 1st pass',
                extra_args=['--show-expected-races', '--error_exitcode=1'],
                extra_test_args=['--gtest_filter="RaceVerifierTests.*"'],
                append_command='2>&1 | tee raceverifier.log')
    addTestStep(f1, tsan_debug, threaded, mode, test_binary, test_desc + ' RV 2nd pass',
                extra_args=['--error_exitcode=1', '--race-verifier=raceverifier.log'],
                extra_test_args=['--gtest_filter="RaceVerifierTests.*"'],
                append_command='2>&1')

  # Run unit tests under TSan under Memcheck
  addTestStep(f1, True, False, 'phb', unitTestBinary(os, 32, 0, False),
              getTestDesc(os, 32, 0, False) + " (under Memcheck)",
              extra_args=['--error_exitcode=1'],
              prefix=["./memcheck64.sh"])


  # Run unit tests with 32-bit valgrind.
  test_desc = test_binaries[(32, 1, False)]
  test_binary = unitTestBinary(os, 32, 1, False)
  addTestStep(f1, False, False, 'fast', test_binary, test_desc + '(32-bit valgrind)',
              frontend_binary='./memcheck32.sh')

  b = {'name': 'linux',
        'slavename': 'vm44-m3',
        'builddir': 'full-linux',
        'factory': f1,
        }

  return [b]

from buildbot.process import factory
from buildbot.steps.source import SVN
from buildbot.steps.shell import Compile
from buildbot.steps.shell import Test
from buildbot.steps.shell import ShellCommand
from common import *


def runAllTests(factory, variants, os):
  test_variants = {} # (bits, opt, static, base_name) -> (binary, threaded, desc)
  for (test_variant, run_variant) in variants:
    (tsan_debug, mode, threaded, base_name) = run_variant
    if test_variants.has_key(test_variant):
      test_desc = test_variants[test_variant]
    else:
      (bits, opt, static) = test_variant
      test_desc = getTestDesc(os, bits, opt, static)
      test_variants[test_variant] = test_desc
    test_binary = unitTestBinary(os, bits, opt, static, test_base_name=base_name)
    if base_name == 'demo_tests':
      extra_args = []
    else:
      extra_args=["--error_exitcode=1"]
    addTestStep(factory, tsan_debug, threaded, mode, test_binary, test_desc, frontend='pin',
                pin_root='../../../third_party/pin', extra_args=extra_args, test_base_name=base_name)
    if base_name == 'racecheck_unittest' and not threaded:
      addTestStep(factory, tsan_debug, False, mode, test_binary, test_desc + ' RV 1st pass', frontend='pin',
                  pin_root='../../../third_party/pin',
                  extra_args=extra_args + ['--show-expected-races', '--error_exitcode=1'],
                  extra_test_args=['--gtest_filter="RaceVerifierTests.*"'],
                  append_command='2>&1 | tee raceverifier.log')
      addTestStep(factory, tsan_debug, False, mode, test_binary, test_desc + ' RV 2nd pass', frontend='pin',
                  pin_root='../../../third_party/pin',
                  extra_args=extra_args + ['--error_exitcode=1', '--race-verifier=raceverifier.log'],
                  extra_test_args=['--gtest_filter="RaceVerifierTests.*"'],
                  append_command='2>&1')


def generate(settings):
  f1 = factory.BuildFactory()

  addSetupTreeForTestsStep(f1)

  # Run thread_sanitizer and suppressions tests.
  addTsanTestsStep(f1, ['amd64-linux-debug', 'x86-linux-debug'])

  # Run unit tests.
  #                  test binary | tsan + run parameters
  #             bits, opt, static, tsan-debug, threaded, mode
  variants = [((  64,   0, False),(        True, 'phb',    False, 'racecheck_unittest')),
              ((  64,   1, False),(        True, 'hybrid', False, 'demo_tests')),
              ((  64,   0, False),(        True, 'phb',    True, 'racecheck_unittest'))]
  runAllTests(f1, variants, 'linux')


  b1 = {'name': 'buildbot-linux-pin',
        'slavename': 'vm43-m3',
        'builddir': 'full_linux_pin',
        'factory': f1,
        }

  return [b1]

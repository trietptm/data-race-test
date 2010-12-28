from buildbot.process import factory
from buildbot.steps.source import SVN
from buildbot.steps.shell import Compile
from buildbot.steps.shell import Test
from buildbot.steps.shell import ShellCommand
from buildbot.steps.transfer import FileUpload
from common import *
from common_perf import *

def generate(settings):
  compile_steps = [
    # Checkout sources.
    SVN(svnurl=settings['svnurl'], mode='copy'),

    # Build tsan + pin.
    Compile(command=['make', '-C', 'tsan', '-j4',
                     'VALGRIND_ROOT=', 'PIN_ROOT=c:/pin',
                     'w32o', 'w32d'],
            description='building tsan with pin',
            descriptionDone='build tsan with pin'),
    Compile(command=['make', '-C', 'tsan',
                     'VALGRIND_ROOT=', 'PIN_ROOT=c:/pin',
                     'w32-sfx'],
            description='packing sfx binary',
            descriptionDone='pack sfx binary'),
    ShellCommand(command="bash -c 'mkdir -p out; cd out; ../tsan/tsan-x86-windows-sfx.exe'",
                 description='extracting sfx',
                 descriptionDone='extract sfx')]

  f_tester = factory.BuildFactory()
  f_tester.addSteps(compile_steps)

  # Run thread_sanitizer and suppressions tests.
  addTsanTestsStep(f_tester, ['x86-windows-debug'])

  # Run tests.
  test_binaries = {} # (os, bits, opt, static, name) -> (binary, desc)
  os = 'windows'
  #                  test binary | tsan + run parameters
  #             bits, opt, static, tsan-debug, threaded, mode
  variants = [
    ((  32,   1, False),(        True, False, 'hybrid')),
    ((  32,   1, False),(        True, False, 'phb')),
    ((  32,   0, False),(       False, False, 'phb')),
    ((  32,   1, False),(        True, True,  'phb')), # Threaded!
    ]
  for (test_variant, run_variant) in variants:
    (tsan_debug, threaded, mode) = run_variant
    if not test_binaries.has_key(test_variant):
      (bits, opt, static) = test_variant
      test_desc = addBuildTestStep(f_tester, os, bits, opt, static)
      test_binaries[test_variant] = test_desc
    test_binary = unitTestBinary(os, bits, opt, static)
    addTestStep(f_tester, tsan_debug, threaded, mode, test_binary, test_desc, frontend='pin-win',
                pin_root='c:/pin', timeout=None, extra_args=['--error_exitcode=1'])
    if threaded:
      continue
    addTestStep(f_tester, tsan_debug, threaded, mode, test_binary, test_desc + ' RV 1st pass', frontend='pin-win',
                pin_root='c:/pin', timeout=None,
                extra_args=['--show-expected-races', '--error_exitcode=1'],
                extra_test_args=['--gtest_filter="RaceVerifierTests.*"'],
                append_command='2>&1 | tee raceverifier.log')
    addTestStep(f_tester, tsan_debug, threaded, mode, test_binary, test_desc + ' RV 2nd pass', frontend='pin-win',
                pin_root='c:/pin', timeout=None,
                extra_args=['--error_exitcode=1', '--race-verifier=raceverifier.log'],
                extra_test_args=['--gtest_filter="RaceVerifierTests.*"'],
                append_command='2>&1')


  binaries = {
    'tsan\\tsan-x86-windows-sfx.exe' : 'tsan-r%s-x86-windows-sfx.exe'}
  addUploadBinariesStep(f_tester, binaries)

  b1 = {'name': 'buildbot-winxp',
        'slavename': 'vm10-m3',
        'builddir': 'full_winxp',
        'factory': f_tester,
        }

  b2 = {'name': 'buildbot-vista',
        'slavename': 'vm50-m3',
        'builddir': 'full_vista',
        'factory': f_tester,
        }

  b3 = {'name': 'buildbot-win7',
        'slavename': 'vm51-m3',
        'builddir': 'full_win7',
        'factory': f_tester,
        }

  #######################
  # Performance bot
  f_perf = factory.BuildFactory()
  f_perf.addSteps(compile_steps)

  for opt in [0, 1]:
    addBuildTestStep(f_perf, os, 32, opt, False)

  platform = 'perf-win'  # will be in the URL of the results.
  benchmark_modes = {
    35:'phb',
    151:'phb',
    502:'phb',
    # 503:'phb', disabled for now - too slow
    512:'hybrid',
  }

  bigtest32_binary = unitTestBinary(os, 32, 0, False, test_base_name='bigtest')
  bigtest32_desc = getTestDesc(os, 32, 0, False)
  step_generator = chromium_utils.InitializePartiallyWithArguments(
      genBenchmarkStep, factory, platform, 'bigtest32')
  addTestStep(f_perf, False, False, 'phb', bigtest32_binary,
              bigtest32_desc,
              pin_root='c:/pin', frontend='pin-win', timeout=None,
              extra_args=["--error_exitcode=1", "--suppressions=unittest/bigtest.supp"],
              test_base_name='bigtest',
              step_generator=step_generator)

  racecheck32_binary = unitTestBinary(os, 32, 0, False, test_base_name='racecheck_unittest')
  racecheck32_desc = getTestDesc(os, 32, 0, False)
  step_generator = chromium_utils.InitializePartiallyWithArguments(
      genBenchmarkStep, factory, platform, 'racecheck_unittest32')
  for test_id, mode in benchmark_modes.items():
    addTestStep(f_perf, False, False, mode, racecheck32_binary,
                racecheck32_desc + ', test ' + str(test_id),
                pin_root='c:/pin', frontend='pin-win', timeout=None,
                extra_args=["--error_exitcode=1"],
                extra_test_args=["--gtest_filter=NonGtestTests*", str(test_id)],
                test_base_name='racecheck_unittest',
                step_generator=step_generator)

  bperf = {'name': 'perf-win',
           'slavename': 'chromeperf01',
           'builddir': 'full_perf_win',
           'factory': f_perf,
           }

  return [b1, b2, b3, bperf]

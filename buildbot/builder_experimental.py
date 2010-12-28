from buildbot.process import factory
from buildbot.steps.source import SVN
from buildbot.steps.shell import Compile
from buildbot.steps.shell import Test
from buildbot.steps.shell import ShellCommand
from common import *
from common_perf import *

def generate(settings):
  f1 = factory.BuildFactory()


  # Checkout sources.
  f1.addStep(SVN(svnurl=settings['svnurl'], mode='copy'))

  f1.addStep(ShellCommand(command='svnversion . >REVISION',
      description='getting revision',
      descriptionDone='get revision'))


  f1.addStep(ShellCommand(command='cd third_party && ./update_valgrind.sh && ' +
                          'cp -rv valgrind valgrind32 && cp -rv valgrind valgrind64',
                          description='unpacking valgrind',
                          descriptionDone='unpack valgrind'))

  # Build valgrind and install it to out/.
  f1.addStep(ShellCommand(command='cd third_party && ./build_and_install_valgrind.sh `pwd`/../out && ' +
                          'strip `pwd`/../out/lib/valgrind/memcheck-x86-linux && ' +
                          'strip `pwd`/../out/lib/valgrind/memcheck-amd64-linux',
                          description='building valgrind',
                          descriptionDone='build valgrind'))

  # Build tsan and install it to out/.
  path_flags = ['OFFLINE=',
                'VALGRIND_INST_ROOT=../out']
  f1.addStep(Compile(command=['make', '-C', 'tsan', '-j2'] + path_flags + ['lo'],
                     description='building tsan',
                     descriptionDone='build tsan'))

  # Build self-contained tsan binaries.
  f1.addStep(ShellCommand(command=['make', '-C', 'tsan'] + path_flags +
                          ['OS=linux', 'ARCH=amd64', 'DEBUG=1', 'self-contained'],
                          description='packing self-contained tsan (debug)',
                          descriptionDone='pack self-contained tsan (debug)'))

  f1.addStep(ShellCommand(command=['make', '-C', 'tsan'] + path_flags +
                          ['OS=linux', 'ARCH=amd64', 'DEBUG=0', 'self-contained-stripped'],
                          description='packing self-contained tsan',
                          descriptionDone='pack self-contained tsan'))


  f1.addStep(ShellCommand(command='ln -s tsan/bin/tsan-amd64-linux-self-contained.sh tsan.sh',
                          description='symlinking tsan',
                          descriptionDone='symlink tsan'))


  # Build tests.
  os = 'linux'
#  for bits in [32, 64]:
#    for opt in [0, 1]:
#      for static in [False, True]:
#        addBuildTestStep(f1, os, bits, opt, static)
#  for bits in [32, 64]:
#    for opt in [0, 1]:
#      for static in [False, True]:
  addBuildTestStep(f1, os, 32, 0, False)
  addBuildTestStep(f1, os, 64, 0, False)
  addBuildTestStep(f1, os, 32, 1, False)
  addBuildTestStep(f1, os, 64, 1, False)

  # addBuildTestStep(f1, os, 32, 1, False, pic=True)


  # Run benchmarks.
  platform = 'perf-linux'
  benchmark_modes = {
    35:'phb',
    72:'phb',
    73:'phb',
    151:'phb',
    502:'phb',
    503:'phb',
    512:'hybrid',
  }

  bigtest_binary = unitTestBinary('linux', 64, 0, False, test_base_name='bigtest')
  bigtest_desc = getTestDesc('linux', 64, 0, False)
  step_generator = chromium_utils.InitializePartiallyWithArguments(
      genBenchmarkStep, factory, platform, 'bigtest')
  addTestStep(f1, False, False, 'phb', bigtest_binary,
              bigtest_desc,
              extra_args=["--error_exitcode=1", "--suppressions=unittest/bigtest.supp"],
              test_base_name='bigtest',
              step_generator=step_generator)

  racecheck_binary = unitTestBinary('linux', 64, 0, False, test_base_name='racecheck_unittest')
  racecheck_desc = getTestDesc('linux', 64, 0, False)
  step_generator = chromium_utils.InitializePartiallyWithArguments(
      genBenchmarkStep, factory, platform, 'racecheck_unittest')
  for test_id, mode in benchmark_modes.items():
    addTestStep(f1, False, False, mode, racecheck_binary,
                racecheck_desc + ', test ' + str(test_id),
                extra_args=["--error_exitcode=1"],
                extra_test_args=["--gtest_filter=NonGtestTests*", str(test_id)],
                test_base_name='racecheck_unittest',
                step_generator=step_generator)

  # 32-bit benchmarks
  bigtest32_binary = unitTestBinary('linux', 32, 0, False, test_base_name='bigtest')
  bigtest32_desc = getTestDesc('linux', 32, 0, False)
  step_generator = chromium_utils.InitializePartiallyWithArguments(
      genBenchmarkStep, factory, platform, 'bigtest32')
  addTestStep(f1, False, False, 'phb', bigtest32_binary,
              bigtest32_desc,
              extra_args=["--error_exitcode=1", "--suppressions=unittest/bigtest.supp"],
              test_base_name='bigtest',
              step_generator=step_generator)

  racecheck32_binary = unitTestBinary('linux', 32, 0, False, test_base_name='racecheck_unittest')
  racecheck32_desc = getTestDesc('linux', 32, 0, False)
  step_generator = chromium_utils.InitializePartiallyWithArguments(
      genBenchmarkStep, factory, platform, 'racecheck_unittest32')
  for test_id, mode in benchmark_modes.items():
    addTestStep(f1, False, False, mode, racecheck32_binary,
                racecheck32_desc + ', test ' + str(test_id),
                extra_args=["--error_exitcode=1"],
                extra_test_args=["--gtest_filter=NonGtestTests*", str(test_id)],
                test_base_name='racecheck_unittest',
                step_generator=step_generator)




  b1 = {'name': 'perf-linux',
        'slavename': 'chromeperf05',
        'builddir': 'full_perf_linux',
        'factory': f1,
        }

  return [b1]

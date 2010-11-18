from buildbot.process import factory
from buildbot.steps.source import SVN
from buildbot.steps.shell import Compile
from buildbot.steps.shell import Test
from buildbot.steps.shell import ShellCommand
from common import *

def generate(settings):
  f1 = factory.BuildFactory()

  # Checkout sources.
  f1.addStep(SVN(svnurl=settings['svnurl'], mode='copy'))

  # Build tsan and install it to out/.
  f1.addStep(Compile(command=['make', '-C', 'llvm/opt/ThreadSanitizer'],
                     description='building opt module',
                     descriptionDone='build opt module'))
  f1.addStep(Compile(command=['make', '-C', 'llvm/tsan_rtl'],
                     description='building RTL',
                     descriptionDone='build RTL'))
  cflags = '-DDYNAMIC_ANNOTATIONS_WANT_ATTRIBUTE_WEAK '
  cflags += '-DRACECHECK_UNITTEST_WANT_ATTRIBUTE_WEAK'
  path = '`pwd`/llvm/scripts'
  flags = ['OMIT_CPP0X=1', 'CXXFLAGS="%s"' % cflags, 'CFLAGS="%s"' % cflags,
           'CC=%s/gcc.sh' % path, 'CXX=%s/gcc.sh' % path,
           'LD=%s/ld.sh' % path,  'AR=%s/ar.sh' % path]
  flags = ['OMIT_CPP0X=1', 'EXTRA_CXXFLAGS="%s"' % cflags,
           'EXTRA_CFLAGS="%s"' % cflags,
           'PATH="%s:$PATH"' % path]
  f1.addStep(ShellCommand(command=['/bin/sh', '-c'] + [' '.join([ 'make'] + flags + ['-C', 'unittest', 'l32'])],
                     description='building racecheck_unittest (32-bit)',
                     descriptionDone='build racecheck_unittest (32-bit)'))

  f1.addStep(ShellCommand(command=['/bin/sh', '-c'] + [' '.join([ 'make'] + flags + ['-C', 'unittest', 'l64'])],
                     description='building racecheck_unittest (64-bit)',
                     descriptionDone='build racecheck_unittest (64-bit)'))


  tsan_args = ['--ignore=unittest/racecheck_unittest.ignore',
               '--suppressions=unittest/racecheck_unittest.supp',
               '--error-exitcode=1']
  f1.addStep(ShellCommand(command=['unittest/bin/racecheck_unittest-linux-x86-O0', '--gtest_filter=-PrintfTests.*:NegativeTests.test141'],
             description='running racecheck_unittest (32-bit)',
             descriptionDone='run racecheck_unittest (32-bit)',
             env={'TSAN_ARGS': ' '.join(tsan_args),
                  'TSAN_DBG_INFO': 'unittest/bin/racecheck_unittest-linux-x86-O0.dbg',
                 }))

  f1.addStep(ShellCommand(command=['unittest/bin/racecheck_unittest-linux-amd64-O0', '--gtest_filter=-PrintfTests.*:NegativeTests.test141'],
             description='running racecheck_unittest (64-bit)',
             descriptionDone='run racecheck_unittest (64-bit)',
             env={'TSAN_ARGS': ' '.join(tsan_args),
                  'TSAN_DBG_INFO': 'unittest/bin/racecheck_unittest-linux-amd64-O0.dbg',
                 }))


  b1 = {'name': 'buildbot-llvm',
        'slavename': 'vm45-m3',
        'builddir': 'llvm',
        'factory': f1,
        }


  return [b1]

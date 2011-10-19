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
  f1.addStep(Compile(command=['make', '-C', 'tsan_rtl', 'DEBUG=1', "NO_BFD=1"],
                     description='building RTL',
                     descriptionDone='build RTL'))
  path = '`pwd`/llvm/scripts'
  ignore_path = '`pwd`/unittest/racecheck_unittest.ignore'
  flags = ['OMIT_DYNAMIC_ANNOTATIONS_IMPL=1', 
           'OMIT_CPP0X=1',
           'PATH="%s:$PATH"' % path,
           'TSAN_IGNORE="%s"' % ignore_path ]
  gtest_filter='-PrintfTests.*:NegativeTests.test141'
  gtest_filter+=':PositiveTests.RepPositive*Test'

  f1.addStep(ShellCommand(command=['/bin/sh', '-c'] + [' '.join([ 'make'] + flags + ['-C', 'unittest', 'l32'])],
                     description='building racecheck_unittest (32-bit)',
                     descriptionDone='build racecheck_unittest (32-bit)'))

  f1.addStep(ShellCommand(command=['/bin/sh', '-c'] + [' '.join([ 'make'] + flags + ['-C', 'unittest', 'l64'])],
                     description='building racecheck_unittest (64-bit)',
                     descriptionDone='build racecheck_unittest (64-bit)'))


  tsan_args = ['--ignore=unittest/racecheck_unittest.ignore',
               '--suppressions=unittest/racecheck_unittest.supp',
               '--error-exitcode=1']
  f1.addStep(ShellCommand(command=['unittest/bin/racecheck_unittest-linux-x86-O0', '--gtest_filter=%s' % gtest_filter],
             description='running racecheck_unittest (32-bit)',
             descriptionDone='run racecheck_unittest (32-bit)',
             env={'TSAN_ARGS': ' '.join(tsan_args),
                 }))

  f1.addStep(ShellCommand(command=['unittest/bin/racecheck_unittest-linux-amd64-O0', '--gtest_filter=%s' % gtest_filter],
             description='running racecheck_unittest (64-bit)',
             descriptionDone='run racecheck_unittest (64-bit)',
             env={'TSAN_ARGS': ' '.join(tsan_args),
                 }))


  b1 = {'name': 'buildbot-llvm',
        'slavename': 'vm45-m3',
        'builddir': 'llvm',
        'factory': f1,
        }


  return [b1]

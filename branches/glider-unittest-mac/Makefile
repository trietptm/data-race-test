CXX=g++

SUFFIX=
PLATFORM_FLAGS=
CXXFLAGS=

all: racecheck_unittest${SUFFIX} bigtest${SUFFIX}

mac:
	make all PLATFORM_FLAGS="-D_APPLE_"

# + false_sharing_unittest${SUFFIX}
O1: 
	make SUFFIX=.O1 CXXFLAGS="-O1 -fno-inline"
O2: 
	make SUFFIX=.O2 CXXFLAGS="-O2 -fno-inline"
all_opt: all O1 O2

%${SUFFIX}: %.cc dynamic_annotations.h thread_wrappers_pthread.h
	${CXX} ${CXXFLAGS} $< -Wall -Werror -Wno-sign-compare -Wshadow 	dynamic_annotations.cc ${PLATFORM_FLAGS} -lpthread -g -DDYNAMIC_ANNOTATIONS=1 -o $@

clean:
	rm -f racecheck_unittest bigtest *.O1 *.O2

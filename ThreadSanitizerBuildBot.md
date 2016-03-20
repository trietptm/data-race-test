# Buildbot location #
We have a [continuous build of ThreadSanitizer](http://build.chromium.org/p/client.tsan/waterfall) where the fresh binaries are built regularly.<br />
Please make sure the bots are green for the given revision when downloading a TSan binary.

# Downloading TSan binaries #
You may download the latest ThreadSanitizer binaries at
http://build.chromium.org/p/client.tsan/binaries.<br>

<h3>for Linux and Mac</h3>
For example, to get the <a href='https://code.google.com/p/data-race-test/source/detail?r=4356'>r4356</a> build for x86_64 Linux you will need to do:<br>
<pre><code>wget http://build.chromium.org/p/client.tsan/binaries/tsan-r4356-amd64-linux-self-contained.sh<br>
chmod +x tsan-r4356-amd64-linux-self-contained.sh<br>
</code></pre>

<h3>for Windows</h3>
For Windows, we store the binaries as self-extracting <a href='http://www.7-zip.org/'>7z</a> archives<br>
For example, to get the <a href='https://code.google.com/p/data-race-test/source/detail?r=4356'>r4356</a> package, please download and run<br> <a href='http://build.chromium.org/p/client.tsan/binaries/tsan-r4356-x86-windows-sfx.exe'>http://build.chromium.org/p/client.tsan/binaries/tsan-r4356-x86-windows-sfx.exe</a><br>
This will extract the binaries into a <code>tsan-x86-windows</code> subdirectory, <code>tsan.bat</code> is what you want.<br>
<br>
<b>Regarding Licensing on Windows</b><br>
ThreadSanitizer itself is published under <a href='http://www.gnu.org/licenses/old-licenses/gpl-2.0.html'>GPLv2</a>.<br>
The binaries for Windows depend on third party software,<br>see <a href='http://code.google.com/p/data-race-test/source/browse/trunk/tsan/license_for_windows.txt'>http://code.google.com/p/data-race-test/source/browse/trunk/tsan/license_for_windows.txt</a> for the details.
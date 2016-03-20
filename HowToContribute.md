#summary Instructions on how to contribute to this project

  * If you are not listed as 'Project committers', please write to **data-race-test(#)googlegroups.com**.
  * Checkout the code: `svn checkout https://data-race-test.googlecode.com/svn/trunk/ data-race-test --username your-user-name`.
  * Edit the code.
  * Send a code review to **data-race-test(#)googlegroups.com** using [Reitveld's upload.py](http://codereview.appspot.com/static/upload.py)<br>(see <a href='http://code.google.com/p/rietveld/wiki/CodeReviewHelp'>http://code.google.com/p/rietveld/wiki/CodeReviewHelp</a>).<br>
<ul><li>Once you've got LGTM (looks good to me) from someone, <code>svn commit</code>.<br>
</li><li>Please check the <a href='http://code.google.com/p/data-race-test/wiki/ThreadSanitizerBuildBot'>buildbot</a> status in a few minutes after commiting, especially the Windows bots.
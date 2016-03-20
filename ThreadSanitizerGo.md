# Data Race Detector for Go language #

The race detector is currently integrated into the Go trunk. It works for linux/amd64 and darwin/amd64.

Just add -race flag to go test/run/install:
```
go test -race net/http
```

If the tool finds a data race it prints the report like this:
```
WARNING: DATA RACE
Read by goroutine 98:
  net/http.(*bodyEOFSignal).Close()
      src/pkg/net/http/transport.go:813 +0x41
  net/http.(*persistConn).readLoop()
      src/pkg/net/http/transport.go:558 +0x450

Previous write by goroutine 147:
  net/http.(*bodyEOFSignal).Close()
      src/pkg/net/http/transport.go:816 +0x78
  net/http_test.func·098()
      src/pkg/net/http/transport_test.go:894 +0x4d1

Goroutine 98 (running) created at:
  net/http.(*Transport).getConn()
      src/pkg/net/http/transport.go:390 +0x920
  net/http.(*Transport).RoundTrip()
      src/pkg/net/http/transport.go:156 +0x35e
  net/http.send()
      src/pkg/net/http/client.go:141 +0x4e1
  net/http.(*Client).doFollowingRedirects()
      src/pkg/net/http/client.go:254 +0x93d
  net/http.(*Client).Get()
      src/pkg/net/http/client.go:201 +0xc1
  net/http_test.func·098()
      src/pkg/net/http/transport_test.go:878 +0xec

Goroutine 147 (running) created at:
  net/http_test.TestTransportConcurrency()
      src/pkg/net/http/transport_test.go:896 +0x463
  testing.tRunner()
      src/pkg/testing/testing.go:297 +0xc9
```

Currently the tool has found [27 data races](http://code.google.com/p/go/issues/list?can=1&q=label%3AThreadSanitizer) in the standard library and 60+ data races elsewhere. The tool significantly slowdowns programs (~2-10x) and has high memory overhead (~5-10x).
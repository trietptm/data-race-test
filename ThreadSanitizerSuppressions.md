ThreadSanitizer supports suppression mechanism, which extends [regular valgrind suppressions](http://valgrind.org/docs/manual/manual-core.html#manual-core.suppress)

Our extensions:
  * Multiple stack traces for one suppression rule are supported. Each stack trace must be enclosed by curly braces. As always, { and } should be on lines of their own.
  * Demangled C++ function names are supported.

Example of new syntax:
```
{
  suppression_name
  tool_name:warning_name
  {
    fun:mangled_function_name_wildcard
    obj:object_name_wildcard
    ...
    fun:demangled_function_name_wildcard
  }
  {
    ...
    fun:another_mangled_function_name_wildcard
  }
}
```

Specify it with `--suppressions=<filename>` flag.

See also ThreadSanitizerIgnores
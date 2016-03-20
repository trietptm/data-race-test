#summary Viewing ThreadSanitizer's output in Vim

You can do magic things with [Vim](http://vim.org).<br />
One of such things is that you can use Vim as a GUI for ThreadSanitizer.

Here is an example:
> ![http://data-race-test.googlecode.com/svn/trunk/images/tsan-in-vim-three-windows.png](http://data-race-test.googlecode.com/svn/trunk/images/tsan-in-vim-three-windows.png)


## Colors in vim ##
First, you need to teach Vim to identify the ThreadSanitizer output.<br />
You may do it by putting this code to **$HOME/.vim/scripts.vim**:
```
if did_filetype()  " filetype already set..
  finish           " ..don't do these checks
endif
" scan first 100 lines, to see if this is a ThreadSanitizer's output
let lnum = 1
while lnum < 100
  if (getline(lnum) =~ 'ThreadSanitizerValgrind')
    setfiletype tsan
  endif
  set foldlevel=1
  let lnum = lnum + 1
endwhile
```

Now, create a file **$HOME/.vim/syntax/tsan.vim** and define ThreadSanitizer (tsan) syntax there.
```
" define the syntax groups for ThreadSanitizer's output
sy match TS_Head              /Possible data race during.*:/
sy match TS_Concurrent        /Concurrent .* happened at or after these points:/
sy match TS_MemoryDescr       /Address .* is .* bytes inside data symbol.*/
sy match TS_MemoryDescr       /Location .* bytes inside a block starting at .* of size .* allocated.*/
sy match TS_Locks             /Locks involved in this report.*/
sy match TS_Fold              /{{{/
sy match TS_Fold              /}}}/
sy match TS_FirstFunc         /#0  0x[0-9A-F]\+: .*/

" define the colors for the groups
hi TS_Head          ctermfg=Red
hi TS_Concurrent    ctermfg=Magenta
hi TS_MemoryDescr   ctermfg=Cyan
hi TS_Locks         ctermfg=Green
hi TS_Fold          cterm=bold
hi TS_FirstFunc     cterm=bold

" vim: fdl=1
```

## Folds ##
Note, that tsan output has `{{{` and `}}}` markers in it. They are for [vim folds](http://www.vim.org/htmldoc/fold.html).<br />
In short, you can open and close sections of the log file.

## Viewing logs with frames ##
We find it very convenient to analyze ThreadSanitizer logs while viewing the source of the program being tested in a different frame.<br />
In vim, you can do it like this:

Put this text into your **$HOME/.vimrc** :
```
set path=,,.,../include
function! Gfw()
  let b = bufnr('')
  normal mz
  let b = bufnr('')
  wincmd w
  exe "b " . b
  normal `zgF
endfun
nnoremap ;f :call Gfw()<cr>
```

  * Open the tsan log file while standing in the source directory.
  * Type **:vsplit** (this will split your vim window vertically into two)
  * Move the cursor to the text like **some/path/file\_name.c:123**
  * Type **;f**

**TODO(all):** does anyone know how to do the same with Emacs? With Eclipse?
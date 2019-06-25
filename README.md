# Main statements

1. File is identified by its md5 hash
2. File might be included in another file (archive, encrypted tar, etc.)
3. We can have VFS as a result of this projets. In this VFS we will be able to set the
   way of how we "store" a file. For example: "%(year)s/%(year)s-%(month)s-%(day)s/%(n)d".
4. For archives we need to process all files within them recursively.


If we have more than 1 copy of original file, we should store all of its original names (?)

Files should be added/updated/removed from archive via HTTP REST API.

https://archive-service.parselab.ru/api/<method>

Methods are:

1. add
2. get
3. delete
4. info

# TODO

1. pcp hash calculation for animated GIFs. `convert` produces multiple images for animated GIFs,
how to calculate pcp hash for them?
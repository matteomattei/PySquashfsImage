PySquashfsImage is a lightweight library for reading squashfs image files in Python.
It provides a way to read squashfs images header and to retrieve encapsulated binaries.
It is compatible with Python 2 and Python 3.

## Use as a library

### List all elements in the image:
-------------------------------
```python
from PySquashfsImage import SquashFsImage

image = SquashFsImage('/path/to/my/image.img')
for i in image.root.findAll():
    print(i.getName())
image.close()
```

### Print all files and folder with human readable path:
----------------------------------------------------
```python
from PySquashfsImage import SquashFsImage

image = SquashFsImage('/path/to/my/image.img')
for i in image.root.findAllPaths():
    print(i)
image.close()
```

### Print only files:
-----------------
```python
from PySquashfsImage import SquashFsImage

image = SquashFsImage('/path/to/my/image.img')
for i in image.root.findAll():
    if not i.isFolder():
        print(i.getPath())
image.close()
```

### Save the content of a file:
---------------------------
```python
from PySquashfsImage import SquashFsImage

image = SquashFsImage('/path/to/my/image.img')
for i in image.root.findAll():
    if i.getName() == 'myfilename':
        with open('/tmp/' + i.getName(), 'wb') as f:
            print('Saving original ' + i.getPath() + ' in /tmp/' + i.getName())
            f.write(i.getContent())
image.close()
```

## Use as a command

```
$ pysquashfsimage -h
usage: pysquashfsimage [-h] [-V] file paths [paths ...]

positional arguments:
  file           squashfs filesystem
  paths          directories or files to print information about

options:
  -h, --help     show this help message and exit
  -V, --version  show program's version number and exit
```

For each path, if it is a directory it will print the mode and name of each
contained file, with sizes and symlinks.

If a path is a file, print its content.

Example command:
```
$ pysquashfsimage myimage.img /bin /etc/passwd
```
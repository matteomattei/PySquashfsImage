PySquashfsImage is a lightweight library for reading squashfs image files in Python.
It provides a way to read squashfs images header and to retrieve encapsulated binaries.
It is compatible with Python 2 and Python 3.

## Use as a library

### List all elements in the image:
-------------------------------
```python
from PySquashfsImage import SquashFsImage

image = SquashFsImage('/path/to/my/image.img')
for i in image.root.find_all():
    print(i.name)
image.close()
```

### Print all files and folder with human readable path:
----------------------------------------------------
```python
from PySquashfsImage import SquashFsImage

image = SquashFsImage('/path/to/my/image.img')
for i in image.root.find_all_paths():
    print(i)
image.close()
```

### Print only files:
-----------------
```python
from PySquashfsImage import SquashFsImage

image = SquashFsImage('/path/to/my/image.img')
for i in image.root.find_all():
    if not i.is_dir:
        print(i.path)
image.close()
```

### Save the content of a file:
---------------------------
```python
from PySquashfsImage import SquashFsImage

image = SquashFsImage('/path/to/my/image.img')
for i in image.root.find_all():
    if i.name == 'myfilename':
        with open('/tmp/' + i.name, 'wb') as f:
            print('Saving original ' + i.path + ' in /tmp/' + i.name)
            f.write(i.read_bytes())
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
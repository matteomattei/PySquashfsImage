PySquashfsImage is a lightweight library for reading squashfs image files in Python.
It provides a way to read squashfs images header and to retrieve encapsulated binaries.
It is compatible with Python 2.6, 2.7 and Python 3.1+.

## Installation

```
pip install PySquashfsImage
```

If you are using Python <= 3.2 and need LZMA decompression, install
[backports.lzma](https://pypi.org/project/backports.lzma/).

For LZ4 decompression, install [lz4](https://pypi.org/project/lz4/) (Python 3.7+).

For Zstandard decompression install [zstandard](https://pypi.org/project/zstandard/) (Python 3.7+).

## Use as a library

### List all elements in the image:
```python
from PySquashfsImage import SquashFsImage

image = SquashFsImage('/path/to/my/image.img')
for item in image.root.find_all():
    print(item.name)
image.close()
```

### Print all files and folder with human readable path:
```python
from PySquashfsImage import SquashFsImage

image = SquashFsImage('/path/to/my/image.img')
for path in image.root.find_all_paths():
    print(path)
image.close()
```

### Print only files:
```python
from PySquashfsImage import SquashFsImage

image = SquashFsImage('/path/to/my/image.img')
for item in image.root.find_all():
    if not item.is_dir:
        print(item.path)
image.close()
```

### Save the content of a file:
```python
from PySquashfsImage import SquashFsImage

image = SquashFsImage('/path/to/my/image.img')
for item in image.root.find_all():
    if item.name == 'myfilename':
        with open('/tmp/' + item.name, 'wb') as f:
            print('Saving original ' + item.path + ' in /tmp/' + item.name)
            f.write(item.read_bytes())
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
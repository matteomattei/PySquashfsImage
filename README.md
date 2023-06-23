PySquashfsImage is a lightweight library for reading squashfs 4.0 image files in Python.
It provides a way to read squashfs images header and to retrieve encapsulated binaries.
It is compatible with Python 2.7 and Python 3.1+.

## Installation

```
pip install PySquashfsImage
```

### Compression

Supported compression methods:

- Gzip
- [LZO](https://pypi.org/project/python-lzo/)
- [LZ4](https://pypi.org/project/lz4/)
- [XZ](https://pypi.org/project/backports.lzma/) (only for Python < 3.3)
- [Zstandard](https://pypi.org/project/zstandard/)

Some of them require a third-party library that you'll need to install
separately if needed.

## Use as a library

### List all elements in the image:
```python
from PySquashfsImage import SquashFsImage

image = SquashFsImage.from_file('/path/to/my/image.img')
for item in image:
    print(item.name)
image.close()
```

### Print all files and folder with human readable path:
```python
from PySquashfsImage import SquashFsImage

# Use with a context manager (recommended).
with SquashFsImage.from_file('/path/to/my/image.img') as image:
    for file in image:
        print(file.path)
```

### Print only files:
```python
from PySquashfsImage import SquashFsImage

with open('/path/to/my/image.img', "rb") as f:
    imgbytes = f.read()

# Create an image from bytes.
with SquashFsImage.from_bytes(imgbytes) as image:
    for item in image:
        if not item.is_dir:
            print(item.path)
```

### Save the content of a file:
```python
from PySquashfsImage import SquashFsImage

with SquashFsImage.from_file('/path/to/my/image.img') as image:
    myfile = image.find('myfilename')
    if myfile is not None:
        with open('/tmp/' + myfile.name, 'wb') as f:
            print('Saving original ' + myfile.path + ' in /tmp/' + myfile.name)
            f.write(myfile.read_bytes())

    # If the file is large it's preferable to iterate over its content.
    hugefile = image.select("/hugedir/myhugefile.big")
    with open("myhugefile.big", "wb") as f:
        for block in hugefile.iter_bytes():
            f.write(block)
```

## Use as a command

### List

```
$ pysquashfs list -h
usage: pysquashfs list [-h] [-o OFFSET] [-p PATH] [-r] [-t TYPE [TYPE ...]] file

List the contents of the file system

positional arguments:
  file                        squashfs filesystem

optional arguments:
  -h, --help                  show this help message and exit
  -o OFFSET, --offset OFFSET  absolute position of file system's start. Default: 0
  -p PATH, --path PATH        absolute path of directory or file to list. Default: '/'
  -r, --recursive             whether to list recursively. For the root directory the value is inverted. Default: False
  -t TYPE [TYPE ...], --type TYPE [TYPE ...]
                              when listing a directory, filter by file type with f, d, l, p, s, b, c
```

Similar to `unsquashfs -ll -full`.

Example that only lists directories under the root directory:
```
$ pysquashfs list myimage.img -r -t d
drwxrwxrwx 1049/1049               468 2018-10-10 08:14:16 /bin
drwxrwxrwx 1049/1049                 3 2021-05-14 18:46:17 /dev
drwxrwxrwx 1049/1049               869 2019-11-12 09:31:30 /etc
drwxrwxrwx 1049/1049                 3 2021-05-14 18:46:17 /home
drwxrwxrwx 1049/1049               406 2017-12-11 08:14:16 /lib
drwxrwxrwx 1049/1049                98 2021-05-14 18:46:17 /mnt
drwxrwxrwx 1049/1049                 3 2021-05-14 15:12:17 /proc
drwxrwxrwx 1049/1049                 3 2021-05-14 15:12:17 /root
drwxrwxrwx 1049/1049               690 2021-05-14 12:11:44 /sbin
drwxrwxrwx 1049/1049                 3 2021-05-14 15:12:17 /sys
drwxrwxrwx 1049/1049                 3 2021-05-14 18:46:17 /tmp
drwxrwxrwx 1049/1049               364 2021-05-14 18:46:17 /usr
drwxrwxrwx 1049/1049                60 2018-11-09 05:38:43 /var
13 file(s) found
```

### Extract

```
$ pysquashfs extract -h
usage: pysquashfs extract [-h] [-o OFFSET] [-d DEST] [-p PATH] [-f] [-q] file

Extract files from the file system

positional arguments:
  file                        squashfs filesystem

optional arguments:
  -h, --help                  show this help message and exit
  -o OFFSET, --offset OFFSET  absolute position of file system's start. Default: 0
  -d DEST, --dest DEST        directory that will contain the extracted file(s). If it doesn't exist it will be created. Default: current directory
  -p PATH, --path PATH        absolute path of directory or file to extract. Default: '/'
  -f, --force                 overwrite files that already exist. Default: False
  -q, --quiet                 don't print extraction status. Default: False
```

On Unix, this command tries to give the same output as `unsquashfs`, but should
not be preferred over it. Some features like extended attributes are missing.

On Windows, you might create symlinks with a privileged account or with an
unprivileged one if Developer Mode is enabled.
Otherwise, a regular file containing the target will be created.
Special files are ignored.

Example command that will extract `/bin` under `/tmp`:
```
$ pysquashfs extract myimage.img -p /bin -d /tmp
```

### Scan

```
$ pysquashfs scan -h
usage: pysquashfsimage scan [-h] file

Find and show all the superblocks that can be found in a file

positional arguments:
  file        squashfs filesystem

optional arguments:
  -h, --help  show this help message and exit
```

Output is similar to `unsquashfs -s`.

Example:
```
$ pysquashfs scan myimage.img
Superblock #1
Magic:                        0x73717368
Major:                        4
Minor:                        0
Creation or last append time: 2018-06-16 16:46:23
Size:                         7864320
Compression:                  XZ
Block size:                   524288
Flags:                        192
Number of fragments:          27
Number of inodes:             361
Number of ids:                1
Inode table start:            0x77E924
Directory table start:        0x77FAF2
Fragment table start:         0x781448
Lookup table start:           0x7817C6
ID table start:               0x7817D4
xattr ID table start:         0xFFFFFFFFFFFFFFFF
Offset:                       161843
```
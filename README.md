PySquashfsImage is a lightweight library for reading squashfs image files in Python.
It provides a way to read squashfs images header and to retrieve encapsulated binaries.
It is compatible with Python2 and Python3.

Examples:
---------

List all elements in the image:
-------------------------------
```
from PySquashfsImage import SquashFsImage

image = SquashFsImage('/path/to/my/image.img')
for i in image.root.findAll():
    print(i.getName())
image.close()
```

Print all files and folder with human readable path:
----------------------------------------------------
```
from PySquashfsImage import SquashFsImage

image = SquashFsImage('/path/to/my/image.img')
for i in image.root.findAllPaths():
    print(i)
image.close()
```

Print only files:
-----------------
```
from PySquashfsImage import SquashFsImage

image = SquashFsImage('/path/to/my/image.img')
for i in image.root.findAll():
    if not i.isFolder():
        print(i.getPath())
image.close()
```

Save the content of a file:
---------------------------
```
from PySquashfsImage import SquashFsImage

image = SquashFsImage('/path/to/my/image.img')
for i in image.root.findAll():
    if i.getName() == b'myfilename':
        with open(b'/tmp/'+i.getName(),'wb') as f:
            print(b'Saving original '+i.getPath().encode()+b' in /tmp/'+i.getName())
            f.write(i.getContent())
image.close()
```


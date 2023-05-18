from enum import IntEnum

SQUASHFS_INVALID_FRAG = 0xFFFFFFFF
SQUASHFS_INVALID_XATTR = 0xFFFFFFFF


class Type(IntEnum):
    DIR = 1
    FILE = 2
    SYMLINK = 3
    BLKDEV = 4
    CHRDEV = 5
    FIFO = 6
    SOCKET = 7
    LDIR = 8
    LREG = 9
    LSYMLINK = 10
    LBLKDEV = 11
    LCHRDEV = 12
    LFIFO = 13
    LSOCKET = 14

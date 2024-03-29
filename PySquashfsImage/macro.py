from .const import SQUASHFS_CHECK, SQUASHFS_COMPRESSED_BIT, SQUASHFS_COMPRESSED_BIT_BLOCK, SQUASHFS_METADATA_SIZE


def SQUASHFS_COMPRESSED_SIZE(B):
    if B & ~SQUASHFS_COMPRESSED_BIT:
        return B & ~SQUASHFS_COMPRESSED_BIT
    else:
        return SQUASHFS_COMPRESSED_BIT


def SQUASHFS_BIT(flag, bit):
    return ((flag >> bit) & 1) != 0


def SQUASHFS_CHECK_DATA(flags):
    return SQUASHFS_BIT(flags, SQUASHFS_CHECK)


def SQUASHFS_COMPRESSED(B):
    return (B & SQUASHFS_COMPRESSED_BIT) == 0


def SQUASHFS_COMPRESSED_SIZE_BLOCK(B):
    return B & ~SQUASHFS_COMPRESSED_BIT_BLOCK


def SQUASHFS_COMPRESSED_BLOCK(B):
    return (B & SQUASHFS_COMPRESSED_BIT_BLOCK) == 0


def SQUASHFS_INODE_BLK(a):
    return (a >> 16) & 0xFFFFFFFF


def SQUASHFS_INODE_OFFSET(a):
    return a & 0xFFFF


def SQUASHFS_MKINODE(A, B):
    return ((A << 16) + B) & 0xFFFFFFFFFFFFFFFF


def SQUASHFS_MK_VFS_INODE(a, b):
    return ((a << 8) + (b >> 2) + 1) & 0xFFFFFFFF


def SQUASHFS_MODE(a):
    return a & 0xFFF


def SQUASHFS_FRAGMENT_BYTES(A):
    return A * 16


def SQUASHFS_FRAGMENT_INDEX(A):
    return SQUASHFS_FRAGMENT_BYTES(A) // SQUASHFS_METADATA_SIZE


def SQUASHFS_FRAGMENT_INDEX_OFFSET(A):
    return SQUASHFS_FRAGMENT_BYTES(A) % SQUASHFS_METADATA_SIZE


def SQUASHFS_FRAGMENT_INDEXES(A):
    return (SQUASHFS_FRAGMENT_BYTES(A) + SQUASHFS_METADATA_SIZE - 1) // SQUASHFS_METADATA_SIZE


def SQUASHFS_FRAGMENT_INDEX_BYTES(A):
    return SQUASHFS_FRAGMENT_INDEXES(A) * 8


def SQUASHFS_LOOKUP_BYTES(A):
    return A * 8


def SQUASHFS_LOOKUP_BLOCK(A):
    return SQUASHFS_LOOKUP_BYTES(A) // SQUASHFS_METADATA_SIZE


def SQUASHFS_LOOKUP_BLOCK_OFFSET(A):
    return SQUASHFS_LOOKUP_BYTES(A) % SQUASHFS_METADATA_SIZE


def SQUASHFS_LOOKUP_BLOCKS(A):
    return (SQUASHFS_LOOKUP_BYTES(A) + SQUASHFS_METADATA_SIZE - 1) // SQUASHFS_METADATA_SIZE


def SQUASHFS_LOOKUP_BLOCK_BYTES(A):
    return SQUASHFS_LOOKUP_BLOCKS(A) * 8


def SQUASHFS_ID_BYTES(A):
    return A * 4


def SQUASHFS_ID_BLOCK(A):
    return SQUASHFS_ID_BYTES(A) // SQUASHFS_METADATA_SIZE


def SQUASHFS_ID_BLOCK_OFFSET(A):
    return SQUASHFS_ID_BYTES(A) % SQUASHFS_METADATA_SIZE


def SQUASHFS_ID_BLOCKS(A):
    return (SQUASHFS_ID_BYTES(A) + SQUASHFS_METADATA_SIZE - 1) // SQUASHFS_METADATA_SIZE


def SQUASHFS_ID_BLOCK_BYTES(A):
    return SQUASHFS_ID_BLOCKS(A) * 8


def SQUASHFS_XATTR_BYTES(A):
    return A * 16


def SQUASHFS_XATTR_BLOCK(A):
    return SQUASHFS_XATTR_BYTES(A) // SQUASHFS_METADATA_SIZE


def SQUASHFS_XATTR_BLOCK_OFFSET(A):
    return SQUASHFS_XATTR_BYTES(A) % SQUASHFS_METADATA_SIZE


def SQUASHFS_XATTR_BLOCKS(A):
    return (SQUASHFS_XATTR_BYTES(A) + SQUASHFS_METADATA_SIZE - 1) // SQUASHFS_METADATA_SIZE


def SQUASHFS_XATTR_BLOCK_BYTES(A):
    return SQUASHFS_XATTR_BLOCKS(A) * 8


def SQUASHFS_XATTR_BLK(A):
    return (A >> 16) & 0xFFFFFFFF


def SQUASHFS_XATTR_OFFSET(A):
    return A & 0xFFFF


def LOOKUP_INDEX(NUMBER):
    return NUMBER >> 12


def LOOKUP_OFFSET(NUMBER):
    return NUMBER & 0xFFF

from io import BufferedIOBase
from . import STREAM_BLOCKSIZE


def snappy_compress(source : BufferedIOBase, destination : BufferedIOBase) -> None:
    """
    Compresses source into destination using Google's Snappy algorithm.
    """
    if (not isinstance(source, BufferedIOBase) and (not hasattr(source, "read") or not callable(source.read))) or (not isinstance(destination, BufferedIOBase) and (not hasattr(destination, "write") or not callable(destination.write))):
        raise TypeError("Expected BufferedIOBase for source and destination, got " + repr(source.__class__.__name__) + " and " + repr(destination.__class__.__name__))

    from snappy.snappy import compress
    blocksize = STREAM_BLOCKSIZE
    block = source.read(blocksize)

    while len(block) == blocksize:

        comp = compress(block)

        destination.write(int.to_bytes(len(comp), 4, "little", signed = False))

        destination.write(comp)

        block = source.read(blocksize)
    
    comp = compress(block)

    destination.write(int.to_bytes(len(comp), 4, "little", signed = False))

    destination.write(comp)


from snappy import UncompressError

class StreamSnappyVersionError(UncompressError):

    pass

del UncompressError

def snappy_decompress(source : BufferedIOBase, destination : BufferedIOBase, *, old : bool = False) -> None:
    """
    Decompresses source into destination using Google's Snappy algorithm.
    """
    if (not isinstance(source, BufferedIOBase) and (not hasattr(source, "read") or not callable(source.read))) or (not isinstance(destination, BufferedIOBase) and (not hasattr(destination, "write") or not callable(destination.write))):
        raise TypeError("Expected BufferedIOBase for source and destination, got " + repr(source.__class__.__name__) + " and " + repr(destination.__class__.__name__))

    from snappy.snappy import decompress, stream_decompress, UncompressError

    if not old:
        try:

            while True:

                size_b = source.read(4)

                if not size_b:
                    return
                elif len(size_b) != 4:
                    raise ValueError("Compressed data was truncated")

                size = int.from_bytes(size_b, "little", signed = False)

                destination.write(decompress(source.read(size)))
        except UncompressError:
            raise StreamSnappyVersionError("Source was compressed with the old version of stream-snappy")
    else:
        stream_decompress(source, destination, STREAM_BLOCKSIZE)

    



def bz2_compress(source : BufferedIOBase, destination : BufferedIOBase) -> None:
    """
    Compresses source into destination using bzip2 algorithm.
    """
    if (not isinstance(source, BufferedIOBase) and (not hasattr(source, "read") or not callable(source.read))) or (not isinstance(destination, BufferedIOBase) and (not hasattr(destination, "write") or not callable(destination.write))):
        raise TypeError("Expected BufferedIOBase for source and destination, got " + repr(source.__class__.__name__) + " and " + repr(destination.__class__.__name__))

    from bz2 import BZ2Compressor
    comp = BZ2Compressor(9)
    
    blocksize = STREAM_BLOCKSIZE
    block = source.read(blocksize)

    while len(block) == blocksize:

        destination.write(comp.compress(block))

        block = source.read(blocksize)
    
    destination.write(comp.compress(block) + comp.flush())


def bz2_decompress(source : BufferedIOBase, destination : BufferedIOBase) -> None:
    """
    Decompresses source into destination using bzip2 algorithm.
    """
    if (not isinstance(source, BufferedIOBase) and (not hasattr(source, "read") or not callable(source.read))) or (not isinstance(destination, BufferedIOBase) and (not hasattr(destination, "write") or not callable(destination.write))):
        raise TypeError("Expected BufferedIOBase for source and destination, got " + repr(source.__class__.__name__) + " and " + repr(destination.__class__.__name__))

    from bz2 import BZ2Decompressor
    comp = BZ2Decompressor()
    
    blocksize = STREAM_BLOCKSIZE
    block = source.read(blocksize)

    while len(block) == blocksize:

        destination.write(comp.decompress(block))

        block = source.read(blocksize)
    
    destination.write(comp.decompress(block))
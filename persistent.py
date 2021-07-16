from io import BytesIO, RawIOBase
from threading import RLock
from typing import Any, Dict, Iterable, List, Optional, Tuple
from os import urandom

# encoding : 0 : None, 1 : snappy, 2 : bz2

class BufferedQueue(RawIOBase):

    def __init__(self) -> None:
        from io import BytesIO
        self._buffer = BytesIO()
        self._nr = 0
        self._lock = RLock()

    def read(self, size: int = -1) -> Optional[bytes]:
        with self._lock:
            self._buffer.seek(self._nr)
            data = self._buffer.read(size)
            self._nr += len(data)
            self._buffer.seek(0, 2)
        with self._lock:
            if self._buffer.tell() == self._nr:
                from io import BytesIO
                self._buffer = BytesIO()
                self._nr = 0
        return data
    
    def write(self, b: bytes) -> Optional[int]:
        with self._lock:
            self._buffer.seek(0, 2)
            self._buffer.write(b)
    
    def flush(self) -> None:
        with self._lock:
            self._buffer.flush()
    
    def seek(self, offset: int, whence: int = 0) -> int:
        with self._lock:
            return self._buffer.seek(offset, whence)
    
    def close(self) -> None:
        with self._lock:
            self._buffer.close()
    
    @property
    def closed(self) -> bool:
        return self._buffer.closed
    
    def fileno(self) -> int:
        raise OSError("No fileno for BufferedQueue")
    
    def isatty(self) -> bool:
        return self._buffer.isatty()
    
    def readable(self) -> bool:
        return True
    
    def readline(self, size: Optional[int] = -1) -> bytes:
        with self._lock:
            self._buffer.seek(self._nr)
            data = self._buffer.readline(size)
            self._nr += len(data)
            self._buffer.seek(0, 2)
        with self._lock:
            if self._buffer.tell() == self._nr:
                from io import BytesIO
                self._buffer = BytesIO()
                self._nr = 0
        return data
    
    def readlines(self, hint: int = -1) -> List[bytes]:
        with self._lock:
            self._buffer.seek(self._nr)
            data = self._buffer.readlines(hint)
            self._nr += len(data)
            self._buffer.seek(0, 2)
        with self._lock:
            if self._buffer.tell() == self._nr:
                from io import BytesIO
                self._buffer = BytesIO()
                self._nr = 0
        return data
    
    def seekable(self) -> bool:
        return True
    
    def tell(self) -> int:
        with self._lock:
            return self._buffer.tell()
    
    def truncate(self, size: Optional[int] = None) -> int:
        with self._lock:
            self._nr = min(self._nr, size if size != None else float("inf"))
            return self._buffer.truncate(size)
    
    def writable(self) -> bool:
        return True
    
    def writelines(self, lines: Iterable[bytes]) -> None:
        with self._lock:
            self._buffer.seek(0, 2)
            self._buffer.writelines(lines)
    
    def readall(self) -> bytes:
        with self._lock:
            self._buffer.seek(self._nr)
            data = self._buffer.read()
            self._nr += len(data)
            self._buffer.seek(0, 2)
        with self._lock:
            if self._buffer.tell() == self._nr:
                from io import BytesIO
                self._buffer = BytesIO()
                self._nr = 0
        return data
    
    def readinto(self, buffer: memoryview) -> Optional[int]:
        with self._lock:
            self._buffer.seek(self._nr)
            l = self._buffer.readinto(buffer)
            self._nr += l
            self._buffer.seek(0, 2)
        with self._lock:
            if self._buffer.tell() == self._nr:
                from io import BytesIO
                self._buffer = BytesIO()
                self._nr = 0
        return l



def AES_encrypt(source : BytesIO, destination : BytesIO, key : bytes) -> None:
    """
    Encrypts the source into the destination using an AES cipher in CBC mode.
    Both source and destination must have read and write methods
    """
    if not isinstance(source, BytesIO) or not isinstance(destination, BytesIO) or not isinstance(key, bytes):
        raise TypeError("Expected BytesIO for source and destination, bytes for key, got " + repr(source.__class__.__name__) + ", " + repr(destination.__class__.__name__) + " and " + repr(key.__class__.__name__))
    if len(key) not in (16, 24, 32):
        raise IndexError("Key must be of 16, 24 or 32 bytes")

    from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
    from cryptography.hazmat.primitives import padding

    IV = urandom(algorithms.AES.block_size // 8)

    encryptor = Cipher(algorithms.AES(key), modes.CBC(IV)).encryptor()
    padder = padding.PKCS7(algorithms.AES.block_size).padder()

    destination.write(IV)

    blocksize = 2 ** 16
    block = block = source.read(blocksize)
    
    while len(block) == blocksize:
        
        destination.write(encryptor.update(padder.update(block)))

        block = source.read(blocksize)

    destination.write(encryptor.update(padder.update(block) + padder.finalize()) + encryptor.finalize())


def AES_decrypt(source : BytesIO, destination : BytesIO, key : bytes) -> None:
    """
    Decrypts the source into the destination using an AES cipher. The Initialization Vector must be the first 16 bytes (automatic if AES_encrypt was used).
    """
    if not isinstance(source, BytesIO) or not isinstance(destination, BytesIO) or not isinstance(key, bytes):
        raise TypeError("Expected BytesIO for source and destination, bytes for key, got " + repr(source.__class__.__name__) + ", " + repr(destination.__class__.__name__) + " and " + repr(key.__class__.__name__))
    if len(key) not in (16, 24, 32):
        raise IndexError("Key must be of 16, 24 or 32 bytes")
    
    from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
    from cryptography.hazmat.primitives import padding

    IV = source.read(algorithms.AES.block_size // 8)
    
    decryptor = Cipher(algorithms.AES(key), modes.CBC(IV)).decryptor()
    unpadder = padding.PKCS7(algorithms.AES.block_size).unpadder()

    blocksize = 2 ** 16
    block = source.read(blocksize)

    while len(block) == blocksize:

        destination.write(unpadder.update(decryptor.update(block)))

        block = source.read(blocksize)
    
    destination.write(unpadder.update(decryptor.update(block) + decryptor.finalize()) + unpadder.finalize())



def snappy_compress(source : BytesIO, destination : BytesIO) -> None:
    """
    Compresses source into destination using Google's Snappy algorithm.
    """
    if not isinstance(source, BytesIO) or not isinstance(destination, BytesIO):
        raise TypeError("Expected BytesIO for source and destination, got " + repr(source.__class__.__name__) + " and " + repr(destination.__class__.__name__))

    from snappy.snappy import stream_compress
    stream_compress(source, destination)


def snappy_decompress(source : BytesIO, destination : BytesIO) -> None:
    """
    Decompresses source into destination using Google's Snappy algorithm.
    """
    if not isinstance(source, BytesIO) or not isinstance(destination, BytesIO):
        raise TypeError("Expected BytesIO for source and destination, got " + repr(source.__class__.__name__) + " and " + repr(destination.__class__.__name__))

    from snappy.snappy import stream_decompress
    stream_decompress(source, destination)



def bz2_compress(source : BytesIO, destination : BytesIO) -> None:
    """
    Compresses source into destination using bzip2 algorithm.
    """
    if not isinstance(source, BytesIO) or not isinstance(destination, BytesIO):
        raise TypeError("Expected BytesIO for source and destination, got " + repr(source.__class__.__name__) + " and " + repr(destination.__class__.__name__))

    from bz2 import BZ2Compressor
    comp = BZ2Compressor(9)
    
    blocksize = 2 ** 16
    block = source.read(blocksize)

    while len(block) == blocksize:

        destination.write(comp.compress(block))

        block = source.read(blocksize)
    
    destination.write(comp.compress(block) + comp.flush())


def bz2_decompress(source : BytesIO, destination : BytesIO) -> None:
    """
    Decompresses source into destination using bzip2 algorithm.
    """
    if not isinstance(source, BytesIO) or not isinstance(destination, BytesIO):
        raise TypeError("Expected BytesIO for source and destination, got " + repr(source.__class__.__name__) + " and " + repr(destination.__class__.__name__))

    from bz2 import BZ2Decompressor
    comp = BZ2Decompressor(9)
    
    blocksize = 2 ** 16
    block = source.read(blocksize)

    while len(block) == blocksize:

        destination.write(comp.compress(block))

        block = source.read(blocksize)
    
    destination.write(comp.compress(block) + comp.flush())




def save(path : str, *obj : Any, compression : str = "snappy", **kwobj : Any) -> None:
    """
    Saves python object(s) at given file path. Also saves their variable's name if given with keywords.
    Compression method can be "snappy", "bz2" or "None".
    """
    if compression not in ("snappy", "bz2", "None"):
        raise ValueError('Expected compression in ("snappy", "bz2", "None")')
    if not obj and not kwobj:
        raise ValueError("Expected at least one object")
    with open(path, "wb") as file:
        if compression == "snappy":
            from pickle import dump
            from snappy.snappy import stream_compress
            file.write(b"\01")
            tmp = BufferedQueue()
            dump((tuple(obj), dict(kwobj)), tmp)
            stream_compress(tmp, file)
        elif compression == "bz2":
            from pickle import dumps
            from bz2 import compress
            file.write(b"\02")
            tmp = dumps((tuple(obj), dict(kwobj)))
            file.write(compress(tmp))
        else:
            from pickle import dump
            file.write(b"\00")
            dump((tuple(obj), dict(kwobj)), file)



def save_env(path : str, glob : dict) -> None:
    """
    Saves the interpreter global variables at given file path.
    """
    save(path, *(), **glob)



def load(path : str, old : bool = False, safeguard : bool = False) -> Tuple[Tuple[Any], Dict[str, Any]]:
    """
    Loads and return python object(s) stored at file path.
    """
    from pickle import load
    with open(path, "rb") as file:
        if not old:
            mode = file.read(1)
        else:
            mode = b"\00"
        if mode == b"\00": # No compression
            l, d = load(file)
        elif mode == b"\01": # snappy compression
            from snappy.snappy import stream_decompress
            tmp = BufferedQueue()
            stream_decompress(file, tmp)
            tmp.seek(0)
            l, d = load(tmp)
        elif mode == b"\02": # bz2 compression
            from bz2 import BZ2File
            file = BZ2File(file, 'rb')
            l, d = load(file)
        else:
            raise UnicodeError("Could not read encoding method")
    if not safeguard and len(l) == 1 and len(d) == 0:
        return l[0]
    return l, d
    


def load_env(path : str, glob : dict) -> Tuple[Any]:
    """
    Loads and returns unnamed object. Loads named object into the correponding global names.
    """
    from pickle import load
    with open(path, "rb") as file:
        l, d = load(file)
        glob.update(d)
        return l
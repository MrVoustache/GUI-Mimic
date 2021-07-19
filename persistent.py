from io import BufferedIOBase
from typing import Any, Dict, Iterable, List, Optional, Tuple, Union


class BufferedQueue(BufferedIOBase):


    """
    A readable and writable bytes buffer. Write data and read it in the order FIFO (First In - First Out). It is a queue for bytes.
    maxsize defines the maximum amount of space allocated for storage. If more than possible needs to be written, the current Thread pauses until space has been freed.
    Use the method has_space() to check if data can be written.
    blocking (default True) indicates if the reader should wait for content to be written before returning. Otherwise, read might not return as much bytes as requested but more might come later.
    Closing the buffer is done (automatically) in two steps.
    Upon calling close(), writting becomes impossible. The buffer actually closes afterwards, when all of its content has been read.
    """


    def __init__(self, maxsize : int = -1, blocking : bool = True) -> None:
        if not isinstance(maxsize, int) or not isinstance(blocking, bool):
            raise TypeError("Expected int, bool, got " + repr(maxsize.__class__.__name__) + "and " + repr(blocking.__class__.__name__))
        if maxsize < -1 or maxsize == 0:
            raise ValueError("maxsize must be a positive nonzero integer")
        if maxsize == -1:
            maxsize = float("inf")
        from io import BytesIO
        from threading import RLock
        self._buffer = BytesIO()
        self._nr = 0
        self._lock = RLock()
        self._maxsize = maxsize
        self._closed = False
        self._len = 0
        self._blocking = blocking
        

    def __len__(self) -> int:
        """
        Returns the space used by the buffer (in bytes).
        """
        return self._len
    

    def has_space(self) -> bool:
        with self._lock:
            return len(self) < self._maxsize


    def read(self, size: int = -1) -> Optional[bytes]:
        with self._lock:
            if self._buffer.closed:
                return b""
        if not self._blocking:
            with self._lock:
                self._buffer.seek(self._nr)
                data = self._buffer.read(size)
                self._nr += len(data)
                self._buffer.seek(0, 2)
            with self._lock:
                self._buffer.seek(0, 2)
                if self._buffer.tell() == self._nr:
                    if self._closed:
                        self._buffer.close()
                    else:
                        from io import BytesIO
                        self._buffer = BytesIO()
                    self._nr = 0
                    self._len = 0
            return data
        else:
            from time import sleep
            block = b""
            remaining = size
            if size == -1:
                size = float("inf")
            while len(block) < size:
                while len(self) == 0:
                    if self._buffer.closed:
                        return block
                    sleep(0.001)
                with self._lock:
                    self._buffer.seek(self._nr)
                    data = self._buffer.read(remaining)
                    self._nr += len(data)
                    remaining -= len(data)
                    block += data
                    self._buffer.seek(0, 2)
                with self._lock:
                    self._buffer.seek(0, 2)
                    if self._buffer.tell() == self._nr:
                        if self._closed:
                            self._buffer.close()
                            self._nr = 0
                            self._len = 0
                            break
                        else:
                            from io import BytesIO
                            self._buffer = BytesIO()
                            self._nr = 0
                            self._len = 0
            return block
    

    def write(self, b: bytes) -> Optional[int]:
        if self._closed:
            raise IOError("BuffuredQueue is closed")
        from time import sleep
        while len(self) >= self._maxsize:
            sleep(0.001)
        with self._lock:
            self._buffer.seek(0, 2)
            self._buffer.write(b)
            self._len += len(b)
    

    def flush(self) -> None:
        if self._closed:
            raise IOError("BuffuredQueue is closed")
        with self._lock:
            self._buffer.flush()
    

    def seek(self, offset: int, whence: int = 0) -> int:
        with self._lock:
            return self._buffer.seek(offset, whence)
    

    def close(self) -> None:
        with self._lock:
            self._closed = True
            if len(self) == 0:
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
            if self._buffer.closed:
                return b""
        if not self._lock:
            with self._lock:
                self._buffer.seek(self._nr)
                data = self._buffer.readline(size)
                self._nr += len(data)
                self._buffer.seek(0, 2)
            with self._lock:
                self._buffer.seek(0, 2)
                if self._buffer.tell() == self._nr:
                    if self._closed:
                        self._buffer.close()
                    else:
                        from io import BytesIO
                        self._buffer = BytesIO()
                    self._nr = 0
                    self._len = 0
        else:
            block = b""
            remaining = size
            if size < 0:
                size = float("inf")
            while block[-1] != "\n" and len(block) < size:
                with self._lock:
                    self._buffer.seek(self._nr)
                    data = self._buffer.readline(remaining)
                    self._nr += len(data)
                    remaining -= len(data)
                    block += data
                    self._buffer.seek(0, 2)
                with self._lock:
                    self._buffer.seek(0, 2)
                    if self._buffer.tell() == self._nr:
                        if self._closed:
                            self._buffer.close()
                            self._nr = 0
                            self._len = 0
                            break
                        else:
                            from io import BytesIO
                            self._buffer = BytesIO()
                            self._nr = 0
                            self._len = 0
            data = block
        return data
    

    def readlines(self, hint: int = -1) -> List[bytes]:
        with self._lock:
            if self._buffer.closed:
                return b""
        if not self._blocking:
            with self._lock:
                self._buffer.seek(self._nr)
                data = self._buffer.readlines(hint)
                self._nr += sum(len(di) for di in data)
                self._buffer.seek(0, 2)
            with self._lock:
                self._buffer.seek(0, 2)
                if self._buffer.tell() == self._nr:
                    if self._closed:
                        self._buffer.close()
                    else:
                        from io import BytesIO
                        self._buffer = BytesIO()
                    self._nr = 0
                    self._len = 0
        else:
            block = []
            remaining = hint
            if hint < 0:
                hint = float("inf")
            while sum(len(di) for di in block) < hint:
                with self._lock:
                    self._buffer.seek(self._nr)
                    data = self._buffer.readlines(remaining)
                    dlen = sum(len(di) for di in data)
                    self._nr += dlen
                    remaining -= dlen
                    if block[-1][-1] != b"\n":
                        block[-1] += data.pop(0)
                    block.extend(data)
                    self._buffer.seek(0, 2)
                with self._lock:
                    self._buffer.seek(0, 2)
                    if self._buffer.tell() == self._nr:
                        if self._closed:
                            self._buffer.close()
                            self._nr = 0
                            self._len = 0
                            break
                        else:
                            from io import BytesIO
                            self._buffer = BytesIO()
                            self._nr = 0
                            self._len = 0
            data = block
        return data
    

    def seekable(self) -> bool:
        return True
    

    def tell(self) -> int:
        with self._lock:
            return self._buffer.tell()
    

    def truncate(self, size: Optional[int] = None) -> int:
        if self._closed:
            raise IOError("BuffuredQueue is closed")
        with self._lock:
            self._nr = min(self._nr, size if size != None else float("inf"))
            return self._buffer.truncate(size)
    

    def writable(self) -> bool:
        return True
    

    def writelines(self, lines: Iterable[bytes]) -> None:
        if self._closed:
            raise IOError("BuffuredQueue is closed")
        from time import sleep
        while len(self) >= self._maxsize:
            sleep(0.0001)
        with self._lock:
            self._buffer.seek(0, 2)
            for line in lines:
                self._buffer.write(line)
                self._len += len(line)
    

    def readall(self) -> bytes:
        with self._lock:
            if self._buffer.closed:
                return b""
        data = b""
        from time import sleep
        while not self.closed:
            data += self.read()
            sleep(0.001)
        return data
    
    
    


STREAM_BLOCKSIZE = 2 ** 20




def AES_encrypt(source : BufferedIOBase, destination : BufferedIOBase, key : bytes) -> None:
    """
    Encrypts the source into the destination using an AES cipher in CBC mode.
    Both source and destination must have read and write methods
    """
    if not isinstance(source, BufferedIOBase) or not isinstance(destination, BufferedIOBase) or not isinstance(key, bytes):
        raise TypeError("Expected BufferedIOBase for source and destination, bytes for key, got " + repr(source.__class__.__name__) + ", " + repr(destination.__class__.__name__) + " and " + repr(key.__class__.__name__))
    if len(key) not in (16, 24, 32):
        raise IndexError("Key must be of 16, 24 or 32 bytes")

    from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
    from cryptography.hazmat.primitives import padding
    from os import urandom

    IV = urandom(algorithms.AES.block_size // 8)

    encryptor = Cipher(algorithms.AES(key), modes.CBC(IV)).encryptor()
    padder = padding.PKCS7(algorithms.AES.block_size).padder()

    destination.write(IV)

    blocksize = STREAM_BLOCKSIZE
    block = block = source.read(blocksize)
    
    while len(block) == blocksize:
        
        destination.write(encryptor.update(padder.update(block)))

        block = source.read(blocksize)

    destination.write(encryptor.update(padder.update(block) + padder.finalize()) + encryptor.finalize())


def AES_decrypt(source : BufferedIOBase, destination : BufferedIOBase, key : bytes) -> None:
    """
    Decrypts the source into the destination using an AES cipher. The Initialization Vector must be the first 16 bytes (automatic if AES_encrypt was used).
    """
    if not isinstance(source, BufferedIOBase) or not isinstance(destination, BufferedIOBase) or not isinstance(key, bytes):
        raise TypeError("Expected BufferedIOBase for source and destination, bytes for key, got " + repr(source.__class__.__name__) + ", " + repr(destination.__class__.__name__) + " and " + repr(key.__class__.__name__))
    if len(key) not in (16, 24, 32):
        raise IndexError("Key must be of 16, 24 or 32 bytes")
    
    from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
    from cryptography.hazmat.primitives import padding

    IV = source.read(algorithms.AES.block_size // 8)
    
    decryptor = Cipher(algorithms.AES(key), modes.CBC(IV)).decryptor()
    unpadder = padding.PKCS7(algorithms.AES.block_size).unpadder()

    blocksize = STREAM_BLOCKSIZE
    block = source.read(blocksize)

    while len(block) == blocksize:

        destination.write(unpadder.update(decryptor.update(block)))

        block = source.read(blocksize)
    
    destination.write(unpadder.update(decryptor.update(block) + decryptor.finalize()) + unpadder.finalize())



def snappy_compress(source : BufferedIOBase, destination : BufferedIOBase) -> None:
    """
    Compresses source into destination using Google's Snappy algorithm.
    """
    if not isinstance(source, BufferedIOBase) or not isinstance(destination, BufferedIOBase):
        raise TypeError("Expected BufferedIOBase for source and destination, got " + repr(source.__class__.__name__) + " and " + repr(destination.__class__.__name__))

    from snappy.snappy import stream_compress
    stream_compress(source, destination, blocksize = STREAM_BLOCKSIZE)


def snappy_decompress(source : BufferedIOBase, destination : BufferedIOBase) -> None:
    """
    Decompresses source into destination using Google's Snappy algorithm.
    """
    if not isinstance(source, BufferedIOBase) or not isinstance(destination, BufferedIOBase):
        raise TypeError("Expected BufferedIOBase for source and destination, got " + repr(source.__class__.__name__) + " and " + repr(destination.__class__.__name__))

    from snappy.snappy import stream_decompress
    stream_decompress(source, destination, blocksize = STREAM_BLOCKSIZE)



def bz2_compress(source : BufferedIOBase, destination : BufferedIOBase) -> None:
    """
    Compresses source into destination using bzip2 algorithm.
    """
    if not isinstance(source, BufferedIOBase) or not isinstance(destination, BufferedIOBase):
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
    if not isinstance(source, BufferedIOBase) or not isinstance(destination, BufferedIOBase):
        raise TypeError("Expected BufferedIOBase for source and destination, got " + repr(source.__class__.__name__) + " and " + repr(destination.__class__.__name__))

    from bz2 import BZ2Decompressor
    comp = BZ2Decompressor()
    
    blocksize = STREAM_BLOCKSIZE
    block = source.read(blocksize)

    while len(block) == blocksize:

        destination.write(comp.decompress(block))

        block = source.read(blocksize)
    
    destination.write(comp.decompress(block))




def save(path : Union[str, BufferedIOBase], *obj : Any, snappy : bool = True, bz2 : bool = False, key : Optional[bytes] = None, **kwobj : Any) -> None:
    """
    Saves python object(s) at given file path. Also saves their variable's name if given with keywords.
    path can also be any writable buffer.
    snappy indicates if Google's fast compression algorithm should be used.
    bz2 indicates if bzip2 strong compression should be used.
    If given, key will be used to encrypt the data using AES with CBC mode.
    """
    if not isinstance(snappy, bool) or not isinstance(bz2, bool) or (key != None and not isinstance(key, bytes)):
        raise TypeError("Expected bool, bool, bytes for snappy, bz2 and key, got " + repr(snappy.__class__.__name__) + ", " + repr(bz2.__class__.__name__) + " and " + repr(key.__class__.__name__))
    if isinstance(path, str):
        try:
            path = open(path, "wb")
            close = True
        except:
            raise FileNotFoundError("Could not open given file path")
    elif isinstance(path, BufferedIOBase):
        close = False
    else:
        raise TypeError("Expected str (path) or BufferedIOBase got " + repr(path.__class__.__name__))
    if isinstance(key, bytes) and len(key) not in (16, 24, 32):
        raise ValueError("When using a cipher key, the key must be of lenght 16, 24 or 32 bytes")
    

    def dump_func(source : Any, destination : BufferedIOBase, close_destination : bool):
        from pickle import dump
        dump(source, destination)
        if close_destination:
            destination.close()
    
    def snappy_func(source : BufferedIOBase, destination : BufferedIOBase, close_destination : bool):
        snappy_compress(source, destination)
        if close_destination:
            destination.close()
    
    def bz2_func(source : BufferedIOBase, destination : BufferedIOBase, close_destination : bool):
        bz2_compress(source, destination)
        if close_destination:
            destination.close()
    
    def aes_func(source : BufferedIOBase, destination : BufferedIOBase, close_destination : bool):
        AES_encrypt(source, destination, key)
        if close_destination:
            destination.close()


    transforms = [dump_func]

    info_int = 0

    if snappy:
        transforms.append(snappy_func)
        info_int |= 1
    if bz2:
        transforms.append(bz2_func)
        info_int |= 2
    if key:
        transforms.append(aes_func)
        info_int |= 4
    
    info_byte = info_int.to_bytes(1, "little", signed = False)
    path.write(info_byte)

    if len(transforms) > 1:
        queue_memory = 2 ** 24 // (len(transforms) - 1)
    else:
        queue_memory = 1
    
    pipes = [BufferedQueue(queue_memory, True) for i in range(len(transforms) - 1)]

    from threading import Thread
    threads = []
    
    for i, ti in enumerate(transforms):
        if i:
            source = pipes[i - 1]
        else:
            source = (tuple(obj), dict(kwobj))
        if i < len(transforms) - 1:
            close_i = True
            destination = pipes[i]
        else:
            destination = path
            close_i = close
        threads.append(Thread(target = ti, args = (source, destination, close_i)))
    
    for ti in threads:
        ti.start()
        
    for ti in threads:
        ti.join()





def save_env(path : str, glob : dict, *, snappy : bool = True, bz2 : bool = False, key : Optional[bytes] = None) -> None:
    """
    Saves the interpreter global variables at given file path.
    Same parameters as save.
    """
    try:
        save(path, *(), **glob, snappy = snappy, bz2 = bz2, key = key)
    except:
        raise


def load(path : Union[str, BufferedIOBase], *, safeguard : bool = False, key : Optional[bytes] = None) -> Tuple[Tuple[Any], Dict[str, Any]]:
    """
    Loads the object(s) stored at path. Returns a tuple containing the unnamed objects and a dictionary containing the named ones.
    path can also be any kind of readable buffer.
    If the file is encrypted, the cipher key should be given.
    If the safeguard is disabled (default) and the object has no named objects, the tuple will be expanded. In the case of a single object, it will be directly returned.
    """
    if not isinstance(safeguard, bool) or key != None and not isinstance(key, bytes):
        raise TypeError("Expected bool for safeguard and bytes for key, got " + repr(safeguard.__class__.__name__) + " and " + repr(key.__class__.__name__))
    if isinstance(path, str):
        try:
            path = open(path, "wb")
            close = True
        except:
            raise FileNotFoundError("Could not open given file path")
    elif isinstance(path, BufferedIOBase):
        close = False
    else:
        raise TypeError("Expected str (path) or BufferedIOBase got " + repr(path.__class__.__name__))
    if isinstance(key, bytes) and len(key) not in (16, 24, 32):
        raise ValueError("When using a cipher key, the key must be of lenght 16, 24 or 32 bytes")
    

    def load_func(source : BufferedQueue, destination : list, close_destination : bool, close_source : bool):
        from pickle import load
        destination.append(load(source))
        if close_source:
            source.close()
        
    
    def snappy_func(source : BufferedIOBase, destination : BufferedIOBase, close_destination : bool, close_source : bool):
        snappy_decompress(source, destination)
        if close_destination:
            destination.close()
        if close_source:
            source.close()
    
    def bz2_func(source : BufferedIOBase, destination : BufferedIOBase, close_destination : bool, close_source : bool):
        bz2_decompress(source, destination)
        if close_destination:
            destination.close()
        if close_source:
            source.close()
    
    def aes_func(source : BufferedIOBase, destination : BufferedIOBase, close_destination : bool, close_source : bool):
        AES_decrypt(source, destination, key)
        if close_destination:
            destination.close()
        if close_source:
            source.close()


    info_int = int.from_bytes(path.read(1), "little", signed = False)

    snappy = info_int & 1
    bz2 = info_int & 2
    ciphered = info_int & 4
    if ciphered and not key:
        raise ValueError("Content of buffer is encrypted, but no key was given")

    transforms = [load_func]

    if snappy:
        transforms.insert(0, snappy_func)
    if bz2:
        transforms.insert(0, bz2_func)
    if ciphered:
        transforms.insert(0, aes_func)
    

    if len(transforms) > 1:
        queue_memory = 2 ** 24 // (len(transforms) - 1)
    else:
        queue_memory = 1
    
    pipes = [BufferedQueue(queue_memory, True) for i in range(len(transforms) - 1)]

    from threading import Thread
    threads = []
    result = []
    
    for i, ti in enumerate(transforms):
        if i:
            source = pipes[i - 1]
            close_s = False
        else:
            source = path
            close_s = close
        if i < len(transforms) - 1:
            destination = pipes[i]
            close_i = True
        else:
            destination = result
            close_i = False
        threads.append(Thread(target = ti, args = (source, destination, close_i, close_s)))
    
    for ti in threads:
        ti.start()
    
        
    for ti in threads:
        ti.join()
                
    r = result.pop()

    if not safeguard and len(r[1]) == 0:
        if len(r[0]) == 1:
            return r[0][0]
        return r[0]
    
    return r




def load_env(path : str, glob : dict, *, safeguard : bool = False, key : Optional[bytes] = None) -> Tuple[Any]:
    """
    Loads and returns unnamed object. Loads named object into the correponding global names.
    Same parameters as load.
    """
    try:
        l, d = load(path, safeguard = True, key = key)
    except:
        raise
    glob.update(d)
    if not safeguard and len(l) == 1:
        return l[0]
    return l


__all__ = ["save", "save_env", "load", "load_env"]
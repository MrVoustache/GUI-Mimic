from io import BufferedIOBase, UnsupportedOperation
from typing import Iterable, Iterator, List, Optional


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
        from threading import RLock
        from io import BytesIO
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
    

    def __str__(self) -> str:
        return "BufferedQueue with {} bytes allocated".format(len(self))
    

    def __iter__(self) -> Iterator[bytes]:
        line = self.readline()
        while line:
            yield line
            line = self.readline()


    def available(self) -> int:
        """
        Returns the amount of data available in the buffer.
        """
        return self._len - self._nr
     

    def has_space(self) -> bool:
        with self._lock:
            return len(self) < self._maxsize


    def read(self, size: int = -1) -> Optional[bytes]:
        # print("Reading {} bytes".format(size))
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
        # print("Writing {} bytes".format(len(b)))
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

    
    def readinto(self, buffer: memoryview) -> int:
        with self._lock:
            if self._buffer.closed:
                return None
        if not isinstance(buffer, memoryview) and not isinstance(buffer, bytearray):
            raise TypeError("Expected writable bytes buffer, like bytearray or memoryview, got " + repr(buffer.__class__.__name__))
        if isinstance(buffer, memoryview) and len(buffer):
            fixed = True
        else:
            fixed = False
        if not self._blocking:
            if fixed:
                maxsize = len(buffer)
            else:
                maxsize = -1
            with self._lock:
                self._buffer.seek(self._nr)
                data = self._buffer.read(maxsize)
                self._nr += len(data)
                self._buffer.seek(0, 2)
                buffer[:len(data)] = data
                read = len(data)
                if not read:
                    read = None
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
            read = 0
            if fixed:
                remaining = len(buffer)
            else:
                remaining = -1
            while remaining:
                with self._lock:
                    self._buffer.seek(self._nr)
                    data = self._buffer.read(remaining)
                    self._nr += len(data)
                    remaining -= len(data)
                    buffer[read : read + len(data)] = data
                    self._buffer.seek(0, 2)
                    read += len(data)
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
        return read
    

    def read1(self, size: int) -> bytes:
        with self._lock:
            if self._buffer.closed:
                return b""
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
    

    def detach(self) -> None:
        raise UnsupportedOperation("Cannot detach BufferedQueue")


del BufferedIOBase, UnsupportedOperation
del Iterable, List, Optional
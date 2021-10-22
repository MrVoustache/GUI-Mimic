from io import BufferedIOBase
from typing import Any, Dict, Optional, Tuple, Union





def save(path : Union[str, BufferedIOBase], *obj : Any, snappy : bool = True, bz2 : bool = False, key : Optional[Union[bytes, str]] = None, **kwobj : Any) -> None:
    """
    Saves python object(s) at given file path. Also saves their variable's name if given with keywords.
    path can also be any writable buffer.
    snappy indicates if Google's fast compression algorithm should be used.
    bz2 indicates if bzip2 strong compression should be used.
    If given, key will be used to encrypt the data using AES with CBC mode.
    """
    from io import BufferedIOBase
    from typing import Any
    if not isinstance(snappy, bool) or not isinstance(bz2, bool) or (key != None and not isinstance(key, (bytes, str))):
        raise TypeError("Expected bool, bool, bytes for snappy, bz2 and key, got " + repr(snappy.__class__.__name__) + ", " + repr(bz2.__class__.__name__) + " and " + repr(key.__class__.__name__))
    if isinstance(path, str):
        try:
            path = open(path, "wb")
            close = True
        except:
            raise FileNotFoundError("Could not open given file path")
    elif isinstance(path, BufferedIOBase) or (hasattr(path, "write") and callable(path.write)):
        close = False
    else:
        raise TypeError("Expected str (path) or BufferedIOBase got " + repr(path.__class__.__name__))
    if isinstance(key, bytes) and len(key) not in (16, 24, 32):
        raise ValueError("When using a cipher key, the key must be of lenght 16, 24 or 32 bytes")
    
    from io_tools.utils import BufferedQueue
    

    def dump_func(source : Any, destination : BufferedIOBase, close_destination : bool):
        from pickle import dump
        dump(source, destination)
        if close_destination:
            destination.close()
    
    def snappy_func(source : BufferedIOBase, destination : BufferedIOBase, close_destination : bool):
        from io_tools.compressors import snappy_compress
        snappy_compress(source, destination)
        if close_destination:
            destination.close()
    
    def bz2_func(source : BufferedIOBase, destination : BufferedIOBase, close_destination : bool):
        from io_tools.compressors import bz2_compress
        bz2_compress(source, destination)
        if close_destination:
            destination.close()
    
    def aes_func(source : BufferedIOBase, destination : BufferedIOBase, close_destination : bool):
        from io_tools.cipher import AES_encrypt
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

    from io_tools import STREAM_BLOCKSIZE

    if len(transforms) > 1:
        queue_memory = STREAM_BLOCKSIZE // (len(transforms) - 1)
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
        threads.append(Thread(target = ti, args = (source, destination, close_i), daemon = True))
    
    for ti in threads:
        ti.start()
    
    from time import sleep
    while threads:
        for i, ti in enumerate(threads[:]):
            if not ti.is_alive():
                if i:
                    raise RuntimeError("There was an ecoding error while performing one of the saving transformations.")
                else:
                    threads.pop(0)
                    break
        sleep(0.001)





def save_env(path : str, glob : dict, *, snappy : bool = True, bz2 : bool = False, key : Optional[Union[bytes, str]] = None) -> None:
    """
    Saves the interpreter global variables at given file path.
    Same parameters as save.
    """
    try:
        save(path, *(), **glob, snappy = snappy, bz2 = bz2, key = key)
    except:
        raise


def load(path : Union[str, BufferedIOBase], *, safeguard : bool = False, key : Optional[Union[bytes, str]] = None, old_snappy : bool = False) -> Tuple[Tuple[Any], Dict[str, Any]]:
    """
    Loads the object(s) stored at path. Returns a tuple containing the unnamed objects and a dictionary containing the named ones.
    path can also be any kind of readable buffer.
    If the file is encrypted, the cipher key should be given.
    If the safeguard is disabled (default) and the object has no named objects, the tuple will be expanded. In the case of a single object, it will be directly returned.
    """
    from io import BufferedIOBase
    from typing import Any
    path_cp = path
    if not isinstance(safeguard, bool) or key != None and not isinstance(key, (bytes, str)):
        raise TypeError("Expected bool for safeguard and bytes for key, got " + repr(safeguard.__class__.__name__) + " and " + repr(key.__class__.__name__))
    if isinstance(path, str):
        try:
            path = open(path, "rb")
            close = True
        except:
            raise FileNotFoundError("Could not open given file path")
    elif isinstance(path, BufferedIOBase) or (hasattr(path, "read") and callable(path.read) and hasattr(path, "readline") and callable(path.readline)):
        close = False
    else:
        raise TypeError("Expected str (path) or BufferedIOBase got " + repr(path.__class__.__name__))
    if isinstance(key, bytes) and len(key) not in (16, 24, 32):
        raise ValueError("When using a cipher key, the key must be of lenght 16, 24 or 32 bytes")
    
    from io_tools.utils import BufferedQueue    

    snappy_error = []

    def load_func(source : BufferedIOBase, destination : list, close_destination : bool, close_source : bool):
        from pickle import load
        try:
            destination.append(load(source))
        except:
            pass
        if close_source:
            source.close()
        
    
    def snappy_func(source : BufferedIOBase, destination : BufferedIOBase, close_destination : bool, close_source : bool):
        from io_tools.compressors import snappy_decompress, StreamSnappyVersionError
        try:
            snappy_decompress(source, destination, old = old_snappy)
        except StreamSnappyVersionError:
            snappy_error.append(True)
            destination.close()
            source.close()
            return
        if close_destination:
            destination.close()
        if close_source:
            source.close()
    
    def bz2_func(source : BufferedIOBase, destination : BufferedIOBase, close_destination : bool, close_source : bool):
        from io_tools.compressors import bz2_decompress
        try:
            bz2_decompress(source, destination)
        except:
            pass
        if close_destination:
            destination.close()
        if close_source:
            source.close()
    
    def aes_func(source : BufferedIOBase, destination : BufferedIOBase, close_destination : bool, close_source : bool):
        from io_tools.cipher import AES_decrypt
        try:
            AES_decrypt(source, destination, key)
        except:
            pass
        if close_destination:
            destination.close()
        if close_source:
            source.close()


    info_int = int.from_bytes(path.read(1), "little", signed = False)

    snappy = info_int & 1
    bz2 = info_int & 2
    ciphered = info_int & 4
    # if snappy:
    #     print("Content was compressed with snappy")
    # if bz2:
    #     print("Content was compressed with bz2")
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
        queue_memory = 2 ** 28 // (len(transforms) - 1)
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
        threads.append(Thread(target = ti, args = (source, destination, close_i, close_s), daemon = True))
    
    for ti in threads:
        ti.start()
    
        
    from time import sleep
    while threads:
        for i, ti in enumerate(threads[:]):
            if not ti.is_alive():
                if snappy_error:
                    if not old_snappy:
                        return load(path_cp, safeguard = safeguard, key = key, old_snappy = True)
                    else:
                        raise RuntimeError("Error while uncompressing data with snappy")
                if i:
                    raise RuntimeError("There was an ecoding error while performing one of the saving transformations.")
                else:
                    threads.pop(0)
                    break
        sleep(0.001)
    
    try:
        r = result.pop()
    except IndexError:
        raise RuntimeError("Error while loading object(s)")

    if not safeguard and len(r[1]) == 0:
        if len(r[0]) == 1:
            return r[0][0]
        return r[0]
    
    return r




def load_env(path : str, glob : dict, *, safeguard : bool = False, key : Optional[Union[bytes, str]] = None) -> Tuple[Any]:
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



def encoding(path : str) -> Tuple[bool, bool, bool]:
    """
    Returns bool values indicating if snappy, bzip2 and a cipher key have been used to encode the given file.
    """
    with open(path, "rb") as f:
        mark = int.from_bytes(f.read(1), "little", signed=False)
        snappy = bool(mark & 1)
        bz2 = bool(mark & 2)
        ciphered = bool(mark & 4)
        return snappy, bz2, ciphered


__all__ = ["save", "save_env", "load", "load_env", "encoding"]

del BufferedIOBase, Any, Dict, Optional, Tuple, Union
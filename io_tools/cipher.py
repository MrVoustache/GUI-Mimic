from io import BufferedIOBase
from typing import Union
from . import STREAM_BLOCKSIZE


def AES_encrypt(source : BufferedIOBase, destination : BufferedIOBase, key : Union[bytes, str]) -> None:
    """
    Encrypts the source into the destination using an AES cipher in CBC mode.
    Both source and destination must have read and write methods
    """
    if (not isinstance(source, BufferedIOBase) and (not hasattr(source, "read") or not callable(source.read))) or (not isinstance(destination, BufferedIOBase) and (not hasattr(destination, "write") or not callable(destination.write))) or not isinstance(key, (bytes, str)):
        raise TypeError("Expected BufferedIOBase for source and destination, bytes for key, got " + repr(source.__class__.__name__) + ", " + repr(destination.__class__.__name__) + " and " + repr(key.__class__.__name__))
    if isinstance(key, str):
        from hashlib import sha256      # I know there is no salt here. We'll see that later!
        key = sha256(bytes(key, encoding = "utf-8"), usedforsecurity=True).digest()
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


def AES_decrypt(source : BufferedIOBase, destination : BufferedIOBase, key : Union[bytes, str]) -> None:
    """
    Decrypts the source into the destination using an AES cipher. The Initialization Vector must be the first 16 bytes (automatic if AES_encrypt was used).
    """
    if (not isinstance(source, BufferedIOBase) and (not hasattr(source, "read") or not callable(source.read))) or (not isinstance(destination, BufferedIOBase) and (not hasattr(destination, "write") or not callable(destination.write))) or not isinstance(key, (bytes, str)):
        raise TypeError("Expected BufferedIOBase for source and destination, bytes for key, got " + repr(source.__class__.__name__) + ", " + repr(destination.__class__.__name__) + " and " + repr(key.__class__.__name__))
    if isinstance(key, str):
        from hashlib import sha256      # I know there is no salt here. We'll see that later!
        key = sha256(bytes(key, encoding = "utf-8"), usedforsecurity=True).digest()
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
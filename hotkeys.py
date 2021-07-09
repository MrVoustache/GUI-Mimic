from typing import Iterator
from pynput.keyboard import Key

class Hotkey:

    """
    Represents a hokeys combination.
    The release_order argument represents the order in which to release the keys. Can be "inverse", "same" or "random".
    """

    def __init__(self, *keys : Key, release_order : str = "inverse") -> None:
        keys = list(keys)
        for i, ki in enumerate(keys):
            if not isinstance(ki, (Key, str)):
                raise TypeError("Expected Keys or str, got " + repr(ki.__class__.__name__))
        if release_order not in ("same", "inverse", "random"):
            raise ValueError("Release order must be one of 'same', 'inverse' or 'random'.")
        self.keys = keys
        self.release_order = release_order
    

    def __iter__(self) -> Iterator[Key]:
        for k in self.keys:
            yield k
        if self.release_order == "same":
            for k in self.keys:
                yield k
        elif self.release_order == "inverse":
            for k in reversed(self.keys):
                yield k
        elif self.release_order == "random":
            from random import shuffle
            keys = list(self.keys)
            shuffle(keys)
            for k in keys:
                yield k
    

    def __str__(self) -> str:
        return " + ".join(str(k) for k in self.keys)
    
    
    __repr__ = __str__
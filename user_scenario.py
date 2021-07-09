from typing import Iterator, Tuple


class user_scenario:

    def __init__(self, *sequence : str) -> None:
        
        self._sequence = tuple(sequence)
    

    def __str__(self) -> str:
        return "user_scenario(" + ', '.join('"' + si + '"' for si in self._sequence) + ")"
    
    __repr__ = __str__

    def __iter__(self) -> Iterator[str]:
        return iter(self._sequence)
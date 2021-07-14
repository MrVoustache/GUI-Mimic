from typing import Any, Iterator, Tuple



class user_scenario:

    def __init__(self, *sequence : str, mouse_resolution : float = 0.01, smooth_mouse : bool = True) -> None:
        
        self._sequence = tuple(sequence)
        self._parameters = {"mouse_resolution" : mouse_resolution, "smooth_mouse" : smooth_mouse}

        if not isinstance(mouse_resolution, (float, int)) or not isinstance(smooth_mouse, bool):
            raise TypeError("Expected float, bool for mouse_resolution and smooth_mouse, got " + repr(mouse_resolution.__class__.__name__) + " and " + repr(smooth_mouse.__class__.__name__))

        from user_guide import user_guide
        self._guide : user_guide = None
    

    def __str__(self) -> str:
        return "user_scenario(" + ', '.join('"' + si + '"' for si in self._sequence) + ")"
    
    __repr__ = __str__

    def __iter__(self) -> Iterator[str]:
        return iter(self._sequence)
    
    def __call__(self) -> Any:
        if not self._guide:
            raise ValueError("Scenario has no been assigned to a user_guide")
        self._guide.simulate(self)
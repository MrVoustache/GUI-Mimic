from transforms import Transform
from events import Event, MouseMove
from typing import Any, Callable, Iterable, Iterator, List, Sequence, Tuple, Union


class user_sequence:

    def __init__(self, sequence : List[Tuple[str, int, Any]] = (),* , relativistic : bool = False) -> None:
        self._sequence : List[Event] = []

        last = 0
        for event in sequence:
            if not isinstance(event, MouseMove):
                if not relativistic:
                    event.time, last = event.time - last, event.time
                self._sequence.append(event)
        
        self._atRunTransforms : List[Transform] = []
    

    def apply_transform(self, transform : Union[Callable[[Event], Union[Event, Sequence[Event]]], Transform]) -> "user_sequence":

        if not isinstance(transform, Transform):
            try:
                transform = Transform(transform)
            except:
                raise TypeError("Expected Transform or tranform function, got " + repr(transform.__class__.__name__))
        
        new_sequence = []

        for event in self._sequence:
            ei = transform(event)
            if isinstance(ei, Event):
                new_sequence.append(ei)
            else:
                new_sequence.extend(ei)
        
        return new_sequence
    

    def schedule_transform(self, transform : Union[Callable[[Event], Union[Event, Sequence[Event]]], Transform]) -> None:

        if not isinstance(transform, Transform):
            try:
                transform = Transform(transform)
            except:
                raise TypeError("Expected Transform or tranform function, got " + repr(transform.__class__.__name__))
        
        self._atRunTransforms.append(transform)
    

    def cancel_transform(self) -> Transform:

        if self._atRunTransforms:
            return self._atRunTransforms.pop()
        else:
            raise IndexError("No scheduled transforms")
    

    def transforms(self) -> Iterator[Transform]:

        return iter(self._atRunTransforms)


    def play(self, mouse_resolution : float = 0.01, * , smooth_mouse : bool = True) -> "user_sequence":
        from pynput import mouse, keyboard
        Mc = mouse.Controller()
        Kc = keyboard.Controller()

        play_sequence = []

        for k, event in enumerate(self._sequence):

            current_sequence = [event]

            if event._generative:
                current_sequence = list(event.play(Mc, Kc, mouse_resolution=mouse_resolution, smooth_mouse=smooth_mouse))
            
            for ti in self._atRunTransforms:
                next_sequence = []
                for ej in current_sequence:
                    eij = ti(ej)
                    if isinstance(eij, Event):
                        current_subsequence = [eij]
                    else:
                        current_subsequence = list(eij)
                    next_sequence.extend(current_subsequence)
                current_sequence = next_sequence
            
            for ei in current_sequence:
                ei.play(Mc, Kc, mouse_resolution=mouse_resolution, smooth_mouse=smooth_mouse)
            
            play_sequence.extend(current_sequence)

        return user_sequence(play_sequence)


    def __call__(self, *args: Any, **kwds: Any) -> Any:
        self.play(*args, **kwds)
    

    def __iter__(self) -> Iterator[Event]:
        return iter(self._sequence)
    

    def append(self, event : Event) -> None:
        if not isinstance(event, Event):
            raise TypeError("Expected Event, got " + repr(event.__class__.__name__))
        self._sequence.append(event)
    
    def extend(self, iter : Iterable[Event]) -> None:
        l = list(iter)
        for ei in l:
            if not isinstance(ei, Event):
                raise TypeError("Expected Events, got " + repr(ei.__class__.__name__))
        self._sequence.extend(l)
    

    def pop(self, i : int = -1) -> Event:
        if not self._sequence:
            raise IndexError("Empty Event sequence")
        return self._sequence.pop(i)
from transforms import Transform, refine_phase_1, refine_phase_2
from events import Event, MouseMove
from typing import Any, Callable, Iterable, Iterator, List, Sequence, Tuple, Union


class user_sequence:

    """
    A representation of a sequence of events. Stores events, schedules transformations for execution, allows to apply transformations.
    """

    _default_transform = [Transform(refine_phase_1())]

    _default_transform.append(Transform(refine_phase_2(_default_transform[-1].function)))

    def __init__(self, sequence : Iterable[Event] = (), *, raw : bool = False) -> None:

        if not isinstance(sequence, Iterable):
            raise TypeError("Expected Iterable of Events, got " + repr(sequence.__class__.__name__))

        if not isinstance(raw, bool):
            raise TypeError("Expected bool, got " + repr(raw.__class__.__name__))

        self._sequence : List[Event] = list(sequence)

        for event in self._sequence:
            if not isinstance(event, Event):
                raise TypeError("Expected Iterable of Events, got " + repr(event.__class__.__name__) + " in the sequence")
            
        if not raw:
            for ti in self._default_transform:

                new_sequence = []

                for event in self._sequence:
                    ei = ti(event)
                    if isinstance(ei, Event):
                        new_sequence.append(ei)
                    elif isinstance(ei, list):
                        new_sequence.extend(ei)
                    else:
                        raise TypeError("Transform function must return Event or list of Events, got " + repr(ei.__class__.__name__))
                
                self._sequence = new_sequence
        
        self._atRunTransforms : List[Transform] = []
    

    def apply_transform(self, transform : Union[Callable[[Event], Union[Event, Sequence[Event]]], Transform]) -> "user_sequence":

        """
        Immediately applies a transformation and returns the transformed sequence.
        """

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
            elif isinstance(ei, list):
                new_sequence.extend(ei)
            else:
                raise TypeError("Transform function must return Event or list of Events, got " + repr(ei.__class__.__name__))
        
        return user_sequence(new_sequence, raw = True)

    apply = apply_transform
    

    def schedule_transform(self, transform : Union[Callable[[Event], Union[Event, Sequence[Event]]], Transform]) -> None:

        """
        Schedule a transformation for execution. The transformation will be executed when playing back this sequence.
        The order is important as transformation will be executed in the order they were scheduled.
        """

        if not isinstance(transform, Transform):
            try:
                transform = Transform(transform)
            except:
                raise TypeError("Expected Transform or tranform function, got " + repr(transform.__class__.__name__))
        
        self._atRunTransforms.append(transform)
    
    schedule = schedule_transform
    

    def cancel_transform(self) -> Transform:

        """
        Cancels the last scheduled transform and returns it.
        """

        if self._atRunTransforms:
            return self._atRunTransforms.pop()
        else:
            raise IndexError("No scheduled transforms")
        
    cancel = cancel_transform
    

    def transforms(self) -> Iterator[Transform]:

        """
        An iterator over the scheduled transforms.
        """

        return iter(self._atRunTransforms)


    def play(self, *, mouse_resolution : float = 0.01, smooth_mouse : bool = True) -> "user_sequence":

        """
        Takes control of the mouse and keyboard and plays the sequence back. Equivalent to directly calling the sequence.
        Returns the actual sequence of events that was played.
        mouse_resolution is the period of infinitesimal mouse moves.
        if smooth_moves is True, the mouse won't be moved at the recorded starting points and instead starts at the current position.
        """

        from pynput import mouse, keyboard
        Mc = mouse.Controller()
        Kc = keyboard.Controller()

        play_sequence = []

        for k, event in enumerate(self._sequence):

            current_sequence = [event]
            no_gen = not event._generative

            while not no_gen:
                no_gen = True
                new_sequence = []
                for event in current_sequence:
                    if event._generative:
                        new_sequence.extend(event.play(Mc, Kc, mouse_resolution=mouse_resolution, smooth_mouse=smooth_mouse))
                        no_gen = False
                    else:
                        new_sequence.append(event)
                current_sequence = new_sequence
            
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

        return user_sequence(play_sequence, raw = True)


    def __call__(self, *args: Any, **kwds: Any) -> "user_sequence":
        return self.play(*args, **kwds)
    

    def __iter__(self) -> Iterator[Event]:
        return iter(self._sequence)
    

    def __getitem__(self, index : Union[int, slice]) -> Union[Event, "user_sequence"]:
        if isinstance(index, int):
            try:
                return self._sequence[index]
            except IndexError:
                raise IndexError("Sequence index out of range")
        elif isinstance(index, slice):
            try:
                return user_sequence(self._sequence[index])
            except:
                raise
        else:
            raise TypeError("Sequence indices must be int or slice, not " + repr(index.__class__.__name__))
    

    def __delitem__(self, index : Union[int, slice]) -> None:
        try:
            del self._sequence[index]
        except:
            raise
    

    def __setitem__(self, index : Union[int, slice], value : Union[Event, Iterable[Event]]) -> None:
        if isinstance(index, int):
            if not isinstance(value, Event):
                raise TypeError("Expected Event, got " + repr(value.__class__.__name__))
            try:
                self._sequence[index] = value
            except IndexError:
                raise IndexError("Sequence index out of range")
        elif isinstance(index, slice):
            try:
                value = list(value)
            except:
                raise ValueError("Expected iterable of Events, got " + repr(value.__class__.__name__))
            for ei in value:
                if not isinstance(ei, Event):
                    raise TypeError("Expected iterable of Events, got a " + repr(ei.__class__.__name__))
            try:
                self._sequence[index] = value
            except:
                raise
        else:
            raise TypeError("Sequence indices must be int or slice, not " + repr(index.__class__.__name__))
    

    def append(self, event : Event) -> None:
        """
        Adds an event at the end of the sequence.
        """
        if not isinstance(event, Event):
            raise TypeError("Expected Event, got " + repr(event.__class__.__name__))
        self._sequence.append(event)
    

    def extend(self, iter : Iterable[Event]) -> None:
        """
        Extends the sequence with the events in the iterable.
        """
        l = list(iter)
        for ei in l:
            if not isinstance(ei, Event):
                raise TypeError("Expected Events, got " + repr(ei.__class__.__name__))
        self._sequence.extend(l)
    

    def pop(self, i : int = -1) -> Event:
        """
        Removes the event from the sequence at given index (default: last).
        """
        if not self._sequence:
            raise IndexError("Empty Event sequence")
        if i < 0:
            i += len(self._sequence)
        if i < 0 or i >= len(self._sequence):
            raise IndexError("Sequence index out of range")
        return self._sequence.pop(i)
    

    def clear(self) -> None:
        """
        Clears the event sequence.
        """
        self._sequence.clear()
    

    def copy(self) -> "user_sequence":
        """
        Returns a deepcopy of the event sequence.
        """
        from copy import deepcopy
        return user_sequence(deepcopy(e) for e in self._sequence)
    

    def insert(self, i : int, event : Event) -> None:
        """
        Inserts an event at the given position in the sequence.
        """
        if not isinstance(event, Event):
            raise TypeError("Expected Event, got " + repr(event.__class__.__name__))
        if i < 0:
            i += len(self._sequence)
        if i < 0 or i >= len(self._sequence):
            raise IndexError("Sequence index out of range")
        self._sequence.insert(i, event)
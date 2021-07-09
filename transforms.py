from events import Event
from typing import Any, Callable, List, Sequence, Union


class Transform:

    """
    A transformation class that enables to apply function to event sequences.
    A transformation requires a Callable that takes a single event as input and returns another event or a sequence of events (might be empty to delete the event).
    """

    def __init__(self, function : Callable[[Event, Any], Union[Event, Sequence[Event]]], *args : Any, **kwargs : Any) -> None:
        if not isinstance(function, Callable):
            raise TypeError("Expected Callable, got " + repr(function.__class__.__name__))
        self.function = function
        self.args = args
        self.kwargs = kwargs

    
    def set_arguments(self, *args : Any, **kwargs : Any) -> None:
        self.args = args
        self.kwargs = kwargs
    

    def __call__(self, event : Event) -> Union[Event, Sequence[Event]]:
        try:
            return self.function(event, *self.args, **self.kwargs)
        except:
            raise ValueError("Given function did not work for event " + str(event))




class time_dilation:

    """
    A simple time dilation function.
    A time dilation of 1.0 does nothing. 2.0 double the duration. 0.5 halves it...
    """

    def __init__(self, factor : float = 1.0) -> None:
        if not isinstance(factor, float) or factor <= 0:
            raise TypeError("Expected nonzero positive float, got " + repr(factor.__class__.__name__))
        self.factor = factor

    
    def __call__(self, event : Event) -> Event:
        from copy import deepcopy
        E = deepcopy(event)
        E.time *= self.factor
        return E



class time_noise:

    """
    A simple time noise function. Adds Guassian relative noise in the time stamps.
    Argument is the variance of the Gaussian distribution.
    The law is 𝒩(1.0, variance) and the samples of this law will stretch the time stamps.
    For example, is the law is 𝒩(1.0, 0.3) (default), and the sample is 1.25, then, the given event
    will have its duration multiplied by 1.25.
    """

    def __init__(self, variance : float = 0.3) -> None:
        if not isinstance(variance, float) or variance <= 0:
            raise TypeError("Expected nonzero positive float, got " + repr(variance.__class__.__name__))
        self.sigma = variance ** 0.5

    
    def __call__(self, event : Event) -> Event:
        from copy import deepcopy
        from random import gauss
        E = deepcopy(event)
        E.time *= max(gauss(1.0, self.sigma), 0) 
        return E


class filter_events:

    """
    A simple class-filter function for events.
    Just give it the classes of events you want to keep.
    The inverse keyword allowas you in inverse the filtering.
    """

    def __init__(self, *classes : type, inverse : bool = False) -> None:
        for cls in classes:
            if not isinstance(cls, type):
                raise TypeError("Expected classes, got " + repr(cls.__class__.__name__))
        if not isinstance(inverse, bool):
            raise TypeError("Expected bool for inverse, got " + repr(inverse.__class__.__name__))
        
        self.inverse = inverse
        self.classes = classes

    
    def __call__(self, event : Event) -> List[Event]:
        
        if isinstance(event, self.classes) != self.inverse:
            return [event]
        return []
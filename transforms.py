from events import Event, MouseEvent, MouseMove, MousePress, MouseRelease, MouseScroll, MouseStart, MouseStop
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
            import traceback
            raise ValueError("Given function did not work for " + str(event) + ":\n" + traceback.format_exc())




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
    The inverse keyword allows you in inverse the filtering.
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





class relativistic_time:

    """
    A simple transform to wind up times of event to local times, relative to the last event.
    """

    def __init__(self) -> None:
        self.total = None
        
    
    def __call__(self, event : Event) -> Event:
        from copy import deepcopy
        e = deepcopy(event)
        if self.total == None:
            e.time, self.total = 0, e.time
        else:
            e.time, self.total = e.time - self.total, e.time
        return e


class refine_phase_1:

    """
    Refines the sequence by marking the starts and stops of the mouse.
    """

    def __init__(self, *, inactivity : int = 100000000, max_duration : int = 2000000000) -> None:
        self.last_t = 0
        self.elapsed = 0
        self.moving = False
        self.last_ev = None

        if not isinstance(max_duration, int) or not isinstance(inactivity, int):
            raise TypeError("Expected int, int for inactivity and max_duration, got " + repr(inactivity.__class__.__name__) + " and " + repr(max_duration.__class__.__name__))

        self.inactivity = inactivity
        self.max_duration = max_duration

        self.starts, self.stops = {}, {}
    

    def __call__(self, event : Event) -> List[Event]:
        self.elapsed += event.time
        self.last_t += event.time

        if self.moving and self.last_t > self.inactivity:
            self.moving = False
            self.elapsed = self.last_t + event.time


        if isinstance(event, MouseEvent):

            self.last_t = 0

            if not self.moving and isinstance(event, (MouseMove, MousePress, MouseRelease, MouseScroll)):
                self.moving = True
                self.starts[event] = event.time
                self.stops[event] = 0
                self.elapsed = 0

            if self.moving and self.elapsed >= self.max_duration:
                self.moving = False
                self.elapsed = 0

            elif self.moving:
                t, ev = self.stops.popitem()
                self.stops[event] = self.elapsed
        
        self.last_ev = event

        return event



class refine_phase_2:

    """
    Refines the sequence by creating MouseStart and MouseStop events and by removing MouseMove events.
    """

    def __init__(self, last_phase : refine_phase_1) -> None:
        self.last = last_phase

    
    def clean(self):
        self.last.elapsed = 0
        self.last.last_t = 0
        self.last.moving = False
        self.last.last_ev = None
    

    def __call__(self, event : Event) -> List[Event]:
        if isinstance(event, MouseEvent):
            if event in self.last.starts:
                t = self.last.starts.pop(event)
                if not self.last.starts and not self.last.stops:
                    self.clean()
                if not isinstance(event, MouseMove):
                    l = [MouseStart(t, event.x, event.y), event]
                else:
                    l = [MouseStart(t, event.x, event.y)]
            elif event in self.last.stops:
                t = self.last.stops.pop(event)
                if not self.last.starts and not self.last.stops:
                    self.clean()
                if not isinstance(event, MouseMove):
                    l = [MouseStop(t, event.x, event.y), event]
                else:
                    l = [MouseStop(t, event.x, event.y)]
            else:
                if not isinstance(event, MouseMove):
                    l = [event]
                else:
                    l = []
        else:
            l = [event]

        if self.last.last_ev in l and self.last.stops:
            ev, t = self.last.stops.popitem()
            ev = MouseStop(t, ev.x, ev.y)
            l.append(ev)
        
        return l
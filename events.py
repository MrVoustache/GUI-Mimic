from abc import ABCMeta, abstractmethod
from hotkeys import Hotkey
from typing import Any, Callable, List, Sequence, Union

from pynput.keyboard import Key, KeyCode
from pynput.mouse import Button


class Event(metaclass = ABCMeta):

    """
    Abstract Base Class of events. Only has a time attribute representing how long to wait before executing the event in nanoseconds.
    """

    __slots__ = ("time")

    _generative = False

    @abstractmethod
    def __init__(self) -> None:
        self.time : int
        raise NotImplementedError
    
    def __str__(self) -> str:
        return self.__class__.__name__ + " event"
    
    def __repr__(self) -> str:
        return self.__class__.__name__ + "(" + ", ".join(ai + " = " + repr(getattr(self, ai)) for ai in self.__slots__) + ")"

    @abstractmethod
    def play(self, Mc, Kc, *, mouse_resolution : float = 0.01, smooth_mouse : bool = False) -> Union[None, List["Event"]]:
        """
        Plays the event. The given arguments are the mouse and keyboard controllers.
        Note that, if it is supposed to, the event must sleep.
        If the class attribute "_generative" is True, this event must instead return the generated event sequence that it is supposed to generate.
        """
        raise NotImplementedError
    

    def copy(self) -> "Event":
        from copy import deepcopy
        return deepcopy(self)
    


class KeyboardEvent(Event):

    """
    An Abstract Base Class for all keyboard events.
    """


class KeyboardPress(KeyboardEvent):

    """
    An event that indicates a key has been pressed on the keyboard. key attribute represents the corresponding key object.
    """

    __slots__ = ("time", "key")

    def __init__(self, time : int, key : Key) -> None:
        if not isinstance(time, int) or time < 0:
            raise TypeError("Expected positive integer for time, got " + repr(time.__class__.__name__))
        if not isinstance(key, (KeyCode, Key, str)) or (isinstance(key, str) and len(key) != 1):
            raise TypeError("Expected Key, Keycode or str of length 1, got " + repr(key.__class__.__name__))
        self.time = time
        self.key = key

    def play(self, Mc, Kc, *, mouse_resolution : float = 0.01, smooth_mouse : bool = False) -> Union[None, List["Event"]]:
        from time import sleep
        sleep(self.time / 1000000000)
        Kc.press(self.key)
    

class KeyboardRelease(KeyboardEvent):

    """
    An event that indicates a key has been released on the keyboard. key attribute represents the corresponding key object.
    """

    __slots__ = ("time", "key")

    def __init__(self, time : int, key : Key) -> None:
        if not isinstance(time, int) or time < 0:
            raise TypeError("Expected positive integer for time, got " + repr(time.__class__.__name__))
        if not isinstance(key, (KeyCode, Key, str)) or (isinstance(key, str) and len(key) != 1):
            raise TypeError("Expected Key, Keycode or str of length 1, got " + repr(key.__class__.__name__))
        self.time = time
        self.key = key
    
    def play(self, Mc, Kc, *, mouse_resolution : float = 0.01, smooth_mouse : bool = False) -> Union[None, List["Event"]]:
        from time import sleep
        sleep(self.time / 1000000000)
        Kc.release(self.key)


class MouseEvent(Event):

    """
    An Abstract Base Class for all mouse events.
    """

    x : int
    y : int


class MouseMove(MouseEvent):

    """
    An event that indicates a mouse move. Its x and y attributes indicate the final position of the mouse.
    """

    __slots__ = ("time", "x", "y")

    def __init__(self, time : int, x : int, y : int) -> None:
        if not isinstance(time, int) or time < 0:
            raise TypeError("Expected positive integer for time, got " + repr(time.__class__.__name__))
        if not isinstance(x, int) or x < 0 or not isinstance(y, int) or y < 0:
            raise TypeError("Expected positive integers for coordinates, got " + repr(x.__class__.__name__) + " and " + repr(y.__class__.__name__))
        self.time = time
        self.x = x
        self.y = y
    
    def play(self, Mc, Kc, *, mouse_resolution : float = 0.01, smooth_mouse : bool = False) -> Union[None, List["Event"]]:
        from time import sleep
        sleep(self.time / 1000000000)
        while Mc.position != (self.x, self.y):
            Mc.position = (self.x, self.y)


class MousePress(MouseEvent):

    """
    An event that indicates a mouse click. Its x and y attributes indicate the final position of the mouse.
    Its button attribute is the corresponding button object.
    """

    __slots__ = ("time", "x", "y", "button")

    def __init__(self, time : int, x : int, y : int, button : Button) -> None:
        if not isinstance(time, int) or time < 0:
            raise TypeError("Expected positive integer for time, got " + repr(time.__class__.__name__))
        if not isinstance(x, int) or x < 0 or not isinstance(y, int) or y < 0:
            raise TypeError("Expected positive integers for coordinates, got " + repr(x.__class__.__name__) + " and " + repr(y.__class__.__name__))
        if not isinstance(button, Button):
            raise TypeError("Expected Button, got " + repr(button.__class__.__name__))
        self.time = time
        self.x = x
        self.y = y
        self.button = button
    
    def play(self, Mc, Kc, *, mouse_resolution : float = 0.01, smooth_mouse : bool = False) -> Union[None, List["Event"]]:
        from time import sleep
        sleep(self.time / 1000000000)
        while Mc.position != (self.x, self.y):
            Mc.position = (self.x, self.y)
        Mc.press(self.button)


class MouseRelease(MouseEvent):

    """
    An event that indicates a mouse button release. Its x and y attributes indicate the final position of the mouse.
    Its button attribute is the corresponding button object.
    """

    __slots__ = ("time", "x", "y", "button")

    def __init__(self, time : int, x : int, y : int, button : Button) -> None:
        if not isinstance(time, int) or time < 0:
            raise TypeError("Expected positive integer for time, got " + repr(time.__class__.__name__))
        if not isinstance(x, int) or x < 0 or not isinstance(y, int) or y < 0:
            raise TypeError("Expected positive integers for coordinates, got " + repr(x.__class__.__name__) + " and " + repr(y.__class__.__name__))
        if not isinstance(button, Button):
            raise TypeError("Expected Button, got " + repr(button.__class__.__name__))
        self.time = time
        self.x = x
        self.y = y
        self.button = button
    
    def play(self, Mc, Kc, *, mouse_resolution : float = 0.01, smooth_mouse : bool = False) -> Union[None, List["Event"]]:
        from time import sleep
        sleep(self.time / 1000000000)
        while Mc.position != (self.x, self.y):
            Mc.position = (self.x, self.y)
        Mc.release(self.button)


class MouseScroll(MouseEvent):

    """
    An event that indicates a mouse scroll. Its x and y attributes indicate the final position of the mouse.
    Its dx and dy coordinates indicate the scroll direction and amount.
    """

    __slots__ = ("time", "x", "y", "dx", "dy")

    def __init__(self, time : int, x : int, y : int, dx : int, dy : int) -> None:
        if not isinstance(time, int) or time < 0:
            raise TypeError("Expected positive integer for time, got " + repr(time.__class__.__name__))
        if not isinstance(x, int) or x < 0 or not isinstance(y, int) or y < 0:
            raise TypeError("Expected positive integers for coordinates, got " + repr(x.__class__.__name__) + " and " + repr(y.__class__.__name__))
        if not isinstance(dx, int) or not isinstance(dy, int):
            raise TypeError("Expected integers for scrolling, got " + repr(dx.__class__.__name__) + " and " + repr(dy.__class__.__name__))
        self.time = time
        self.x = x
        self.y = y
        self.dx = dx
        self.dy = dy
    
    def play(self, Mc, Kc, *, mouse_resolution : float = 0.01, smooth_mouse : bool = False) -> Union[None, List["Event"]]:
        from time import sleep
        sleep(self.time / 1000000000)
        while Mc.position != (self.x, self.y):
            Mc.position = (self.x, self.y)
        Mc.scroll(self.dx, self.dy)


class MouseStart(MouseEvent):

    """
    An event that indicates the mouse started moving. Its x and y attributes indicate the starting of the mouse.
    """

    _generative = True

    __slots__ = ("time", "x", "y")

    def __init__(self, time : int, x : int, y : int) -> None:
        if not isinstance(time, int) or time < 0:
            raise TypeError("Expected positive integer for time, got " + repr(time.__class__.__name__))
        if not isinstance(x, int) or x < 0 or not isinstance(y, int) or y < 0:
            raise TypeError("Expected positive integers for coordinates, got " + repr(x.__class__.__name__) + " and " + repr(y.__class__.__name__))
        self.time = time
        self.x = x
        self.y = y
    
    def play(self, Mc, Kc, *, mouse_resolution : float = 0.01, smooth_mouse : bool = False) -> List["Event"]:
        if not smooth_mouse:
            return [MouseMove(self.time, self.x, self.y)]
        return []



class MouseStop(MouseEvent):

    """
    An event that indicates the mouse stopped moving. Its x and y attributes indicate the final position of the mouse.
    """

    _generative = True

    __slots__ = ("time", "x", "y")

    def __init__(self, time : int, x : int, y : int) -> None:
        if not isinstance(time, int) or time < 0:
            raise TypeError("Expected positive integer for time, got " + repr(time.__class__.__name__))
        if not isinstance(x, int) or x < 0 or not isinstance(y, int) or y < 0:
            raise TypeError("Expected positive integers for coordinates, got " + repr(x.__class__.__name__) + " and " + repr(y.__class__.__name__))
        self.time = time
        self.x = x
        self.y = y
    
    def play(self, Mc, Kc, *, mouse_resolution : float = 0.01, smooth_mouse : bool = False) -> List["Event"]:
        start, stop = Mc.position, (self.x, self.y)
        MR = max(int(self.time / 1000000000 / mouse_resolution), 1)
        dx = 1 / MR
        dt = round(max(self.time / MR, 100000))
        from Bezier import Bezier_curve, random_circle_point
        inter = random_circle_point(start, stop)
        C = Bezier_curve(start, inter, stop)
        l = []
        for i in range(MR):
            l.append(MouseMove(dt, *C(dx * i)))
        l.append(MouseMove(dt, *stop))
        return l



class KeyboardInput(KeyboardEvent):

    """
    A generative event that create a an input from the user.
    The input can be a string or a sequence of Keys/Hotkeys objects
    The speed is the number of keys pressed by second.
    """

    __slots__ = ("time", "input", "speed")

    _generative = True

    def __init__(self, time : int, input : Union[str, Sequence[Key], Hotkey, Callable[[], Union[str, Sequence[Key], Hotkey]]], speed : float = 8.0) -> None:
        if not isinstance(time, int) or time < 0:
            raise TypeError("Expected positive integer for time, got " + repr(time.__class__.__name__))
        if not isinstance(input, (Sequence, Hotkey, Callable)):
            raise TypeError("Expected Sequence of str, Keys, or Hotkey for input, got " + repr(input.__class__.__name__))
        if not isinstance(speed, (int, float)) or speed <= 0:
            raise TypeError("Expected nonzero positive float for speed, got " + repr(speed.__class__.__name__))
        self.time = time
        self.input = input
        self.speed = speed
    

    def play(self, Mc, Kc, *, mouse_resolution: float, smooth_mouse: bool) -> List["Event"]:
        dt = round(1 / self.speed / 2 * 1000000000)
        events = []

        if isinstance(self.input, Callable):
            input = self.input()
        else:
            input = self.input

        if isinstance(input, Sequence):
            for s in input:
                events.append(KeyboardPress(dt, s))
                events.append(KeyboardRelease(dt, s))
        
        elif isinstance(input, Hotkey):
            l = list(input)
            n = len(l)
            for s in l[:n // 2]:
                events.append(KeyboardPress(2 * dt, s))
            
            events.append(KeyboardRelease(4 * dt, l[n // 2]))

            for s in l[n // 2 + 1:]:
                events.append(KeyboardRelease(dt, s))


        events[0].time = self.time

        return events


class MouseClick(MouseEvent):

    """
    A generative event that represents moving the mouse to a certain place and clicking there.
    times indicates the number of clicks (default 1, 2 for double-click, 0 can actually be used to simply move the mouse...)
    """

    
    __slots__ = ("time", "dt", "x", "y", "button")

    _generative = True

    def __init__(self, time : int, dt : int, x : Union[int, Callable[[], int]], y : Union[int, Callable[[], int]], button : Button = Button.left, *, times : int = 1) -> None:
        if not isinstance(time, int) or time < 0:
            raise TypeError("Expected positàive integer for time, got " + repr(time.__class__.__name__))
        if not isinstance(dt, int) or dt < 0:
            raise TypeError("Expected positive integer for dt, got " + repr(dt.__class__.__name__))
        if not isinstance(button, Button):
            raise TypeError("Expected Button, got " + repr(button.__class__.__name__))
        if ((not isinstance(x, int) or x < 0) and not isinstance(x, Callable)) or ((not isinstance(y, int) or y < 0) and not isinstance(y, Callable)):
            raise TypeError("Expected positive integers or Callable for coordinates, got " + repr(x.__class__.__name__) + " and " + repr(y.__class__.__name__))
        if not isinstance(times, int) or times < 0:
            raise TypeError("Expected positive integer for times")
        self.time = time
        self.dt = dt
        self.button = button
        self.x = x
        self.y = y
        self.times = times
    
    def play(self, Mc, Kc, *, mouse_resolution: float, smooth_mouse: bool) -> List["Event"]:
        events = []

        events.append(MouseStop(self.time, self.x, self.y))

        for i in range(self.times):
            events.append(MousePress(self.dt, self.x, self.y, self.button))
            events.append(MouseRelease(self.dt // 2, self.x, self.y, self.button))
        
        return events
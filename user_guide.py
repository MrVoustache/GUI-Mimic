from user_sequence import user_sequence
from transforms import Transform
from events import Event
from typing import Any, Callable, Dict, Iterator, List, Optional, Sequence, Tuple, Union
from user_scenario import user_scenario

class user_guide:

    """
    A workbench for editing your sequences and scenarios (usually) for a given software.
    You can manage sequences and scenarios as attributes.
    """

    def __init__(self) -> None:
        self._functionalities = {}


    def __getstate__(self) -> Dict[str, Any]:
        return {"_functionalities" : self._functionalities}
    
    def __setstate__(self, state) -> None:
        self.__dict__.update(state)
    

    
    def __getattr__(self, name : str) -> Any:
        if name in self.__dict__ or name == "_functionalities":
            return self.__dict__[name]
        elif name in self._functionalities:
            return self._functionalities[name]
        else:
            raise AttributeError("'user_guide' has no attribute '{}'".format(name))
        
    def __setattr__(self, name: str, value: Any) -> None:
        if name in self.__dict__ or name == "_functionalities":
            return super().__setattr__(name, value)
        else:
            self._functionalities[name] = value
            if isinstance(value, user_scenario):
                value._guide = self
        
    def __delattr__(self, name: str) -> None:
        if name in self.__dict__:
            return super().__delattr__(name)
        elif name in self._functionalities:
            self._functionalities.pop(name)
        else:
            raise KeyError("'{}' not in user_guide".format(name))
    
    def __iter__(self) -> Iterator[Tuple[str, Union[user_sequence, user_scenario]]]:
        for k, v in self._functionalities.items():
            yield k, v
    
    def __contains__(self, key : str) -> bool:
        return key in self._functionalities
    
    def __call__(self) -> user_sequence:
        return self.simulate()

    def __str__(self) -> str:
        return "user_guide[" + ", ".join(k for k, v in self) + "]"
    
    __repr__ = __str__


    
    def sequences(self) -> Iterator[Tuple[str, user_sequence]]:
        for k, v in self._functionalities.items():
            if isinstance(v, user_sequence):
                yield k, v
    
    def scenarios(self) -> Iterator[Tuple[str, user_scenario]]:
        for k, v in self._functionalities.items():
            if isinstance(v, user_scenario):
                yield k, v
        
    def keys(self) -> List[str]:
        return [k for k, v in self]
    

    def simulate(self, *scenarios : Optional[Union[str, user_scenario]]) -> user_sequence:

        import re
        from random import choice

        if not scenarios:
            scenarios = []
            for k, v in self.scenarios():
                scenarios.append(v)
            
        else:
            scenarios = list(scenarios)
            for i, sci in enumerate(scenarios):
                if not isinstance(sci, (str, user_scenario)):
                    raise TypeError("Expected str or user_scenario, got " + repr(sci.__class__.__name__))
                if isinstance(sci, str) and sci in self and not isinstance(getattr(self, sci), user_scenario):
                    raise KeyError("No corresponding user_scenarion in user_guide : " + repr(sci))
                if isinstance(sci, str):
                    if sci in self:
                        scenarios[i] = getattr(self, sci)
                    else:
                        try:
                            sci = re.compile(sci)
                        except:
                            raise KeyError("No corresponding user_scenarion in user_guide : " + repr(sci))
                        matches = [vi for ki, vi in self.scenarios() if sci.fullmatch(ki)]
                        scenarios[i] = choice(matches)

                        
            
        scenario = choice(scenarios)
        mouse_resolution = scenario._parameters["mouse_resolution"]
        smooth_mouse = scenario._parameters["smooth_mouse"]

        result_sequence = []

        for sequence_name in scenario:
            if sequence_name in self:
                getattr(self, sequence_name).play(mouse_resolution = mouse_resolution, smooth_mouse = smooth_mouse)
            else:
                names = re.compile(sequence_name)
                matches = [seq for name, seq in self.sequences() if names.fullmatch(name)]
                seq = choice(matches)
                result_sequence.extend(seq.play(mouse_resolution = mouse_resolution, smooth_mouse = smooth_mouse))
        
        return user_sequence(result_sequence)
    
    
    def apply_transform(self, transform : Union[Callable[[Event], Union[Event, Sequence[Event]]], Transform]) -> None:
        
        if not isinstance(transform, Transform):
            try:
                transform = Transform(transform)
            except:
                raise TypeError("Expected Transform or tranform function, got " + repr(transform.__class__.__name__))
        

        for obj in dir(self):
            if isinstance(getattr(self, obj), user_sequence):
                setattr(self, obj, getattr(self, obj).apply_transform(transform))
    

    def schedule_transform(self, transform : Union[Callable[[Event], Union[Event, Sequence[Event]]], Transform]) -> None:

        if not isinstance(transform, Transform):
            try:
                transform = Transform(transform)
            except:
                raise TypeError("Expected Transform or tranform function, got " + repr(transform.__class__.__name__))
        
        for obj in dir(self):
            if isinstance(getattr(self, obj), user_sequence):
                getattr(self, obj).schedule_transform(transform)
            
from typing import Any, Dict, Iterator, List, Optional, Tuple
from user_scenario import user_scenario

class user_guide:

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
        
    def __delattr__(self, name: str) -> None:
        if name in self.__dict__:
            return super().__delattr__(name)
        elif name in self._functionalities:
            self._functionalities.pop(name)
        else:
            raise KeyError("'{}' not in user_guide".format(name))
    
    def __iter__(self) -> Iterator[Tuple[Any, Any]]:
        for k, v in self._functionalities.items():
            yield k, v
        
    def keys(self) -> List[str]:
        return [k for k, v in self]
        
    def __str__(self) -> str:
        return "user_guide[" + ", ".join(k for k, v in self) + "]"
    
    __repr__ = __str__

    def chain(self, sequence : List[str]) -> None:
        to_do = []
        import re
        from random import choice
        for si in sequence:
            try:
                if si in self._functionalities:
                    to_do.append(self._functionalities[si])
                else:
                    expr = re.compile(si)
                    possibilities = []
                    for sj in self._functionalities:
                        if expr.fullmatch(sj):
                            possibilities.append(sj)
                    if not possibilities:
                        raise KeyError("No matching name")
                    to_do.append(self._functionalities[choice(possibilities)])
            except KeyError:
                raise KeyError("Unknown functionality")
        

        for fi in to_do:
            fi.disturb()(smooth_mouse = True)
    

    def simulate(self, scenario : Optional[user_scenario] = None) -> None:
        if scenario == None:
            choices = []
            for k, v in self._functionalities.items():
                if isinstance(v, user_scenario):
                    choices.append(v)
                
            from random import choice
            self.chain(choice(choices))
        elif isinstance(scenario, user_scenario):
            self.chain(scenario)
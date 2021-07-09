from threading import Thread
from typing import Any, Callable, List
from user_scenario import user_scenario
from user_sequence import user_sequence
from user_guide import user_guide
from pynput import mouse, keyboard
from code import interact
from persistent import load, save
from time import sleep, time_ns
from events import *


event_list = []

listening = [False]
hotkeys = [False, False, False]

origin = [time_ns()]

def start_listening():
    listening[0] = True
    print("Started recording\n>>> ", end="")
    to_delete = [repr(i) for i in [keyboard.Key.ctrl_l, keyboard.Key.alt_l]]
    while event_list and isinstance(event_list[-1], (KeyboardPress, KeyboardRelease)) and repr(event_list[-1].key) in to_delete:
        to_delete.remove(repr(event_list[-1].key))
        event_list.pop()
    
    last_start[0] = len(event_list)
    origin[0] = time_ns()

def stop_listening():
    listening[0] = False
    print("Stopped recording\n>>> ", end="")
    to_delete = [repr(i) for i in [keyboard.Key.ctrl_l, keyboard.Key.alt_l]]
    while event_list and isinstance(event_list[-1], KeyboardPress) and repr(event_list[-1].key) in to_delete:
        event_list.pop()

last_start = [0]

Mc = mouse.Controller()


def on_move(x, y):
    if listening[0]:
        event_list.append(MouseMove(time_ns() - origin[0], *Mc.position))
        generate_artificial_events(event_list[-1])

def on_click(x, y, button, pressed):
    if listening[0]:
        if pressed:
            event_list.append(MousePress(time_ns() - origin[0], *Mc.position, button))
        else:
            event_list.append(MouseRelease(time_ns() - origin[0], *Mc.position, button))
        generate_artificial_events(event_list[-1])

def on_scroll(x, y, dx, dy):
    if listening[0]:
        event_list.append(MouseScroll(time_ns() - origin[0], *Mc.position, dx, dy))
        generate_artificial_events(event_list[-1])

def on_press(key):
    if key == keyboard.Key.ctrl_l:
        hotkeys[0] = True
    elif key == keyboard.Key.alt_l:
        hotkeys[1] = True
    elif repr(key) == repr(keyboard.KeyCode.from_vk(82)):
        hotkeys[2] = True
    if listening[0] and repr(key) != repr(keyboard.KeyCode.from_vk(82)):
        event_list.append(KeyboardPress(time_ns() - origin[0], key))
        generate_artificial_events(event_list[-1])
    if all(hotkeys):
        if listening[0]:
            stop_listening()
        else:
            start_listening()

def on_release(key):
    if key == keyboard.Key.ctrl_l:
        hotkeys[0] = False
    elif key == keyboard.Key.alt_l:
        hotkeys[1] = False
    elif repr(key) == repr(keyboard.KeyCode.from_vk(82)):
        hotkeys[2] = False
    if listening[0] and repr(key) != repr(keyboard.KeyCode.from_vk(82)):
        if last_start[0] != len(event_list) or repr(key) not in (repr(keyboard.Key.ctrl_l), repr(keyboard.Key.alt_l)):
            event_list.append(KeyboardRelease(time_ns() - origin[0], key))
            generate_artificial_events(event_list[-1])





artificial_events_generators = []

def generate_artificial_events(event):
    for gen in artificial_events_generators:
        gen(event)



inactivity = 100000000
max_duration = 3000000000
last_start = [-float("inf")]


def mouse_start(event : Event):       # When the mouse starts moving after a period of inactivity
    if isinstance(event, MouseMove):
        last = origin[0]
        for ei in event_list[:-1]:
            if isinstance(ei, MouseEvent):
                last = ei.time
        t = time_ns()
        if t - last - origin[0] >= inactivity or last == origin[0]:
            last_start[0] = time_ns()
            event_list.append(MouseStart(t - origin[0], *Mc.position))
            
artificial_events_generators.append(mouse_start)
move_id = [-1]

def mouse_stop(event : Event):      # When the mouse stops moving (beginning of a period of inactivity)
    if isinstance(event, MouseMove):
        if time_ns() - last_start[0] > max_duration:
            t = time_ns()
            last_start[0] = t
            event_list.append(MouseStop(t - origin[0], *Mc.position))
            event_list.append(MouseStart(t - origin[0], *Mc.position))
        ID = move_id[0] + 1
        move_id[0] = ID
        def wait_and_mark(ID):
            t = time_ns()
            while time_ns() - t < inactivity:
                if move_id[0] != ID:
                    return
                sleep(0.001)
            if move_id[0] == ID:
                i = event_list.index(event)
                event_list.insert(i + 1, MouseStop(event.time, event.x, event.y))
        t = Thread(target=wait_and_mark, args=(ID, ), daemon=False)
        t.start()

artificial_events_generators.append(mouse_stop)




k_listener = keyboard.Listener(
    on_press=on_press,
    on_release=on_release)

k_listener.start()


m_listener = mouse.Listener(
    on_move=on_move,
    on_click=on_click,
    on_scroll=on_scroll)

m_listener.start()



        

def show(ev = None):
    if ev == None:
        ev = event_list
    for event in ev:
        print(repr(event))


def extract(filter : Callable[[tuple], bool] = lambda x : True) -> List[tuple]:
    r = event_list.copy()
    event_list.clear()
    return user_sequence(list(ei for ei in r if filter(ei)))


def clear():
    event_list.clear()


from os import chdir


env = {
    "load" : load,
    "save" : save,
    "show" : show,
    "user_guide" : user_guide,
    "user_sequence" : user_sequence,
    "user_scenario" : user_scenario,
    "extract" : extract,
    "clear" : clear,
    "cd" : chdir,
    "Key" : Key,
    "Button" : Button
}

import events

for ni in dir(events):
    ei = getattr(events, ni)
    if isinstance(ei, type) and issubclass(ei, Event):
        env[ni] = ei

import transforms

env["Transform"] = transforms.Transform
env["time_dilation"] = transforms.time_dilation
env["time_noise"] = transforms.time_noise
env["filter_events"] = transforms.filter_events

import hotkeys as hk

env["Hotkey"] = hk.Hotkey

interact(local=env)
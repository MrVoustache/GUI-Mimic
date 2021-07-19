# GUI-Mimic
A GUI fuzzing tool that works by recording the user and making scenarios out of it

To make it work, you first need a few Python modules. You can get them with the following commands :

pip install pynput
pip install python-snappy       -> Default compression applied when saving objects
pip install cryptography        -> If you want to encrypt your files using a custom key

Once this is done, you just have to run recorder.py using Python. This will start and interactive Python prompt.
You can then press you recording hotkeys (default Ctrl+Alt+r) and your mouse and keyboard activity will be recorded.
Press these hotkeys again to stop recording.

Once a recording has been done, use the function extract() to retrieve the recorded sequence of events (user_sequence).

The recommended way to manage your recordings is with a "user_guide". For example, if I want to make scenarios for Notepad.exe, I can simply do:

>>> Notepad = user_guide()

Then I can add my recording to it:

>>> Notepad.rec_1 = extract()

You are also recommended to record specific use cases in the target application. For example, for Notepad, I would record a sequence to start the application, one to create a new file, save it, open another... All accessible under "Notepad.start", "Notepad.new", "Notepad.save", "Notepad.open".
You can - and you should - make multiple recordings for each action, but in different ways (for example, starting Notepad from the start menu as "start_1", from the explorer by opening a file as "start_2"...) since we will use them randomly later.

To make a scenario, you should use the "user_scenario" class:

>>> Notepad.scenario_1 = user_scenario("start", "write", "save", "close")

This scenario represents the chaining of the sequences named "start", "write", "save" and "close" in the user_guide "Notepad". But one more interesting way to use it is with regular expressions:

>>> Notepad.scenario_2 = user_scenario("start.*", "write.*", "save.*", "close_1")

In this scenario, I want to start a sequence which name starts with "start", chosen randomly, then with "write", then with "save", then I want specifically the sequence named "close_1".

Using sequences that are recordings of the basic action within an application, and by making randomized scenarios that describe all valid use cases, you can fuzz efficiently your target application.

Another important functionality to consider is transforms. Transform is a class that is used to apply a given function to all events in a specific sequence (or in all sequences in a user_guide).

A transform first needs a callable which takes an event as arguments and returns a single event, or a list of events (possibly empty). The transform will then be applied to a sequence by returning a new sequence in which each event has been replaced by the result(s) of the transform callable. For example, a very useful built-in callable is filter_events. Here I want to keep only mouse events in a specific sequence:

>>> transform = filter_events(Mouse_Event)
>>> Notepad.start_1 = Notepad.start_1.apply_transform(transform)

I also want to remove all Mouse_Move events from all the sequences:

>>> transform = filter_events(Mouse_Move, inverse = True)
>>> Notepad.apply_transform(transform)

Some built-in transformation are random, for example time_dilation and time_noise. time_noise for example, is used to add some gaussian randomness in the time stamps of all events. This is useful when your events are artificial and are spaced evenly in time. These king of transformation should instead be executed at execution, when you are playing the scenario, so that two repetitions of this scenario end up being different:

>>> Notepad.schedule_transform(time_noise(variance = 0.3))

I can also schedule these for a user_sequence. Here I want the closing sequence to last 20% longer:

>>> Notepad.close_1.schedule_transform(time_dilation(1.2))

One last thing to do with event sequences: you can directly add or remove events from them. Sequences are quite similar to Python lists and have similar functions. You can create your own events and append them to a sequence, pop certain events, replace entire pars of the sequence with a new sequence...
In particular there are some event classes that are made to describe complex events in a much simpler way. For example, I never described what the "write.*" sequences were. Let's declare them now:

>>> write = user_sequence()     # Empty sequence
>>> write.append(MouseClick(2000000000, 100000000, 900, 700))       # Move the mouse to the coordinates (900, 700), in two seconds, then click in 0.1 second
>>> write.append(KeyboardInput(3000000000, "This is a test sentence.\nDon't pay attention", 9)) #Wait 3 seconds, then write this text at a speed of 9 characters per second.
>>> Notepad.write_1 = write

These two event don't make sense all alone, but during playback, they will be replaced by "atomic" events (MouseMove, MousePress, MouseRelease, KeyboardPress, KeyboardRelease). This is just a simpler way to describe events. You might have remarked that upon reading an extracted event sequence (after recording), you won't see MouseMove events, but instead a MouseStart and a MouseStop events. These are the same kind of events, and they are replace by many MouseMove events during execution. If you want the raw, unrefined sequence, simply type:

>>> raw_sequence = extract(raw = True)

You can also apply a filter on events upon extraction. Here, for example, I want to keep only the events which time stamps (in nanoseconds) are even, for some reason...

>>> even_sequence = extract(lambda ev : ev.time % 2 == 0)

Finally, after a long job of editing and recording, you can play your sequence or scenario back.
To play a sequence, you can just call it:

>>> Notepad.start_1()

To play a given scenario, same thing...
And to play a random scenario, you can use the "simulate" method of user_guides:

>>> Notepad.simulate("scenario_1", "scenario_2")        # Randomly plays scenario 1 or 2
>>> Notepad.simulate()                                  # Randomly play a scenario

Note that these sequences can hold abstract events (KeyboardInput, MouseMoves...), some events might be random, some possibly random transformations can be applied at execution...and you might obtain an interesting result that you would want to reproduce. Luckyly, simulate (as well as calling a sequence or a scenario) returns the actual event sequence that was actually played:

>>> playback = Notepad.simulate()           # Plays a random scenario.
>>> playback()                              # Replays the exact same sequence of events.
>>> refined_playback = user_sequence(playback)  # Note that playback was a raw sequence. Now it contains abstract events.


One last thing to know is how to save and reload all of your work. For that, just use the two very simple functions "save" and "load":

>>> save("Notepad.pyt", Notepad)        # Saves the user_guide in the file "Notepad.pyt"
...
Another day
...
>>> Notepad = load("Notepad.pyt")       # All of your sequences, scenarios and transforms are back.


You now have most of the knowledge necessary to use this tool. If, however, you want to learn more, Python's help function works great with this tool. Juste type:

>>> help(Notepad)       # Same as help(user_guide)
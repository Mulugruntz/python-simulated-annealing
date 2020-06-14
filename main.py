# https://en.wikipedia.org/wiki/Simulated_annealing

"""
Let s = s[0]
For k = 0 through k[max] (exclusive):
    T ← temperature( (k+1)/k[max] )
    Pick a random neighbour, s[new] ← neighbour(s)
    If P(E(s), E(s[new]), T) ≥ random(0, 1):
        s ← s[new]
Output: the final state s
"""
import math
import random
from copy import deepcopy
from typing import TypeVar, List, Generic, Tuple

from kivy import Config
from kivy.clock import Clock
from kivy.input import MotionEvent
from kivy.metrics import Metrics

Config.set('graphics', 'resizable', 0)

from kivy.core.window import Window
Window.size = (500, 500)

from kivy.app import App
from kivy.properties import ListProperty
from kivy.uix.widget import Widget

S = TypeVar('S')
Nodes = List[Tuple[int, int]]


def swap_random(seq):
    idx = range(len(seq))
    i1, i2 = random.sample(idx, 2)
    seq[i1], seq[i2] = seq[i2], seq[i1]


def swap_random_neighbours(seq):
    idx = range(len(seq))
    i1 = random.choice(idx)
    i2 = 0 if i1+1 == len(seq) else i1+1
    seq[i1], seq[i2] = seq[i2], seq[i1]


class SimulatedAnnealing(Generic[S]):
    def __init__(self, state: S, k_max: int = 200, t_max: int = 200) -> None:
        self.__state: S = None
        self.history: List[S] = []
        self.k_max: int = k_max
        self.k: int = 0
        self.t_max = t_max
        self.state = state

    @property
    def state(self) -> S:
        return self.__state

    @state.setter
    def state(self, state: S) -> None:
        self.__state = state
        self.history.append(state)

    def neighbour(self, state: S) -> S:
        raise NotImplementedError

    def temperature(self, x: float) -> int:
        raise NotImplementedError

    def acceptance_prob(self, energy_state: int, energy_state_new: int, temperature: int) -> float:
        raise NotImplementedError

    def energy(self, state: S) -> int:
        raise NotImplementedError

    def start(self) -> None:
        for k in range(self.k_max):
            temp = self.temperature((k + 1) / self.k_max)
            if temp == 0:
                break
            state_new = self.neighbour(self.state)
            if self.acceptance_prob(self.energy(self.state), self.energy(state_new), temp) >= random.random():
                self.state = state_new


class TravelingSalesman(SimulatedAnnealing[Nodes]):

    def neighbour(self, state: Nodes) -> Nodes:
        out = deepcopy(state)
        swap_random(out)
        return out

    def temperature(self, x: float) -> int:
        return int(self.t_max * (x - 1)**2)

    def acceptance_prob(self, energy_state: int, energy_state_new: int, temperature: int) -> float:
        if energy_state_new < energy_state:
            return 1.
        return math.exp(-(energy_state_new - energy_state) / temperature)

    def energy(self, state: Nodes) -> int:
        total_distance = 0
        for start, end in zip(state, state[1:] + state[0:1]):
            total_distance += ((end[0] - start[0]) ** 2) ** 0.5 + ((end[1] - start[1]) ** 2) ** 0.5
        return int(total_distance)


class SimulatedAnnealingWidget(Widget):
    nodes = ListProperty()

    def __init__(self, **kwargs):
        super(SimulatedAnnealingWidget, self).__init__(**kwargs)
        self.salesman = TravelingSalesman(
            generate_cities(Window.system_size[0] * Metrics.density, Window.system_size[1] * Metrics.density, 20),
            k_max=2000, t_max=200
        )
        self.nodes = self.salesman.state
        self.salesman.start()
        self.ids.slider.max = len(self.salesman.history) - 1
        self.ids.slider.bind(on_touch_move=self.cb_slider_on_touch_move)
        self.salesman_callback = iter(self.salesman.history)
        self.event_clock_callback = None
        Clock.schedule_once(self.start_delayed_process, 2)

    def start_delayed_process(self, dt):
        self.event_clock_callback = Clock.schedule_interval(self.callback_next_state, 1 / 50.)

    def callback_next_state(self, dt):
        try:
            self.nodes = next(self.salesman_callback)
        except StopIteration:
            self.ids.energy_label.text = self.ids.energy_label.text[:-3] + '!'
            self.ids.slider.disabled = False
            self.event_clock_callback.cancel()
        else:
            self.ids.energy_label.text = str(self.salesman.energy(self.nodes)) + '...'
            self.ids.slider.value += 1
        print('My callback is called', dt)

    def cb_slider_on_touch_move(self, slider, event: MotionEvent) -> None:
        self.nodes = self.salesman.history[int(slider.value)]
        self.ids.energy_label.text = f'{int(slider.value)} => {str(self.salesman.energy(self.nodes))}'


class SimulatedAnnealingApp(App):
    def build(self):
        return SimulatedAnnealingWidget()


def generate_cities(width, height, nodes):
    return [(random.randint(0, width), random.randint(0, height)) for _ in range(nodes)]


def main():
    SimulatedAnnealingApp().run()


if __name__ == '__main__':
    main()

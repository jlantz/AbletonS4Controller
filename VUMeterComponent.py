import Live
import math
import logging
from _Framework.ControlSurfaceComponent import ControlSurfaceComponent
from _Framework.SliderElement import SliderElement
from _Framework.InputControlElement import *
CHANNEL_SCALE_MAX = .9
CHANNEL_SCALE_MIN = 0.4
CHANNEL_SCALE_INCREMENTS = 128
RMS_FRAMES = 10
USE_RMS = False

logger = logging.getLogger(__name__)

class VUMeterComponent(ControlSurfaceComponent):
    _active_instances = []

    def __init__(self, parent):
        ControlSurfaceComponent.__init__(self)
        VUMeterComponent._active_instances.append(self)
        self.slider = None
        self._parent = parent
        self._vu_meter = None
        self.frames = [0.0] * RMS_FRAMES
        self.increments = CHANNEL_SCALE_INCREMENTS
        self.top = CHANNEL_SCALE_MAX
        self.bottom = CHANNEL_SCALE_MIN
        self.multiplier = self.calculate_multiplier(self.top, self.bottom, self.increments)
        self.current_level = 0

    def disconnect(self):
        VUMeterComponent._active_instances.remove(self)
        if self.slider:
            self.slider.send_value(0, True)
        if self._vu_meter != None:
            self._vu_meter.remove_output_meter_left_listener(self.observe)
            self._vu_meter = None

    def observe(self):
        new_frame = self.mean_peak()
        self.store_frame(new_frame)
        self.level = self.scale(new_frame)
        if self.level != self.current_level:
            self.current_level = self.level
            self.send_vu_value(self.level)
        else:
            None

    def store_frame(self, frame):
        self.frames.pop(0)
        self.frames.append(frame)

    def rms(self, frames):
        return math.sqrt(sum((frame * frame for frame in frames)) / len(frames))

    def mean_peak(self):
        return (self._vu_meter.output_meter_left + self._vu_meter.output_meter_right) / 2

    def scale(self, value):
        if value > self.top:
            value = self.top
        elif value < self.bottom:
            value = self.bottom
        value = value - self.bottom
        value = value * self.multiplier
        return int(round(value))

    def calculate_multiplier(self, top, bottom, increments):
        return increments / (top - bottom)

    def set_vu_meter(self, track):
        self.set_led_slider(track)
        self._vu_meter = track
        if self._vu_meter != None:
            self._vu_meter.add_output_meter_left_listener(self.observe)
        else:
            None

    def set_led_slider(self, slider):
        self.slider = slider

    def send_vu_value(self, level):
        if level != None:
            if level < 0:
                None
            else:
                self.slider.send_value(level, True)
        else:
            None

    def update(self):
        pass

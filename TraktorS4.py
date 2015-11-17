from __future__ import with_statement
import logging
from itertools import izip
from itertools import repeat
from _Framework.ButtonElement import ButtonElement
from _Framework.ControlSurface import ControlSurface
from _Framework.InputControlElement import MIDI_CC_TYPE
from _Framework.Layer import Layer
from _Framework.MixerComponent import MixerComponent as BaseMixerComponent
from _Framework.SliderElement import SliderElement
from ChannelStripComponent import ChannelStripComponent
from VUMeterComponent import VUMeterComponent

logger = logging.getLogger(__name__)

NUM_TRACKS = 5

TRACK_VOLUME_SLIDERS = (
    (2,69),
    (0,69),
    (1,69),
    (3,69),
)
TRACK_CUE_BUTTONS = (
    (2,68),
    (0,68),
    (1,68),
    (3,68),
)
TRACK_FILTER_KNOBS = (
    (2,67),
    (0,67),
    (1,67),
    (3,67),
)
TRACK_EQ_LOW_KNOBS = (
    (2,66),
    (0,66),
    (1,66),
    (3,66),
)
TRACK_EQ_MID_KNOBS = (
    (2,65),
    (0,65),
    (1,65),
    (3,65),
)
TRACK_EQ_HIGH_KNOBS = (
    (2,64),
    (0,64),
    (1,64),
    (3,64),
)
TRACK_FX_1_BUTTONS = (
    (2,62),
    (0,62),
    (1,62),
    (3,62),
)
TRACK_FX_2_BUTTONS = (
    (2,63),
    (0,63),
    (1,63),
    (3,63),
)
TRACK_GAIN_KNOBS = (
    (2,60),
    (0,60),
    (1,60),
    (3,60),
)
TRACK_GAIN_BUTTONS = (
    (2,61),
    (0,61),
    (1,61),
    (3,61),
)
TRACK_METERS = (
    (2,70),
    (0,70),
    (1,70),
    (3,70),
)

BROWSE_KNOB = ((4,2),)
BROWSE_KNOB_PUSH = ((4,3),)
BROWSE_BUTTON = ((4,9),)

MASTER_LOOP_DRY_WET_KNOB = ((4,4),)
MASTER_LOOP_SIZE_BUTTON = ((4,5),)
MASTER_LOOP_UNDO_BUTTON = ((4,6),)
MASTER_LOOP_REC_BUTTON = ((4,7),)
MASTER_LOOP_PLAY_BUTTON = ((4,8),)

CROSSFADER_SLIDER = ((4,10),)

class ChannelStripLayer(Layer):

    def __init__(self, priority = None, **controls):
        super(Layer, self).__init__()
        self._priority = priority
        self._name_to_controls = dict(izip(controls.iterkeys(), repeat(None)))
        self._control_to_names = dict()
        self._control_clients = dict()
        for name, control in controls.iteritems():
            if isinstance(control, tuple):
                for c in control:
                    self._control_to_names.setdefault(c, []).append(name)
            else:
                self._control_to_names.setdefault(control, []).append(name)

    def on_received(self, client, *a, **k):
        """ Override from ExclusiveResource """
        for controls in self._control_to_names.iterkeys():
            k.setdefault('priority', self._priority)
            if not isinstance(controls, tuple):
                controls = (controls,)
            for control in controls:
                if hasattr(control, 'resource'):
                    control.resource.grab(self._get_control_client(client), *a, **k)

    def on_lost(self, client):
        """ Override from ExclusiveResource """
        for controls in self._control_to_names.iterkeys():
            if not isinstance(controls, tuple):
                controls = (controls,)
            for control in controls:
                if hasattr(control, 'resource'):
                    control.resource.release(self._get_control_client(client))


class S4MixerComponent(BaseMixerComponent):

    def _create_strip(self):
        return ChannelStripComponent()

    def set_vu_meter_controls(self, controls):
        for strip, control in map(None, self._channel_strips, controls or []):
            strip.set_vu_meter_control(control)

    def set_filter_controls(self, controls):
        for strip, control in map(None, self._channel_strips, controls or []):
            strip.set_filter_control(control)

    def set_send_controls(self, controls):
        self._send_controls = controls
        for strip, control in map(None, self._channel_strips, controls or []):
            if self._send_index is None:
                strip.set_send_controls(None)
            else:
                # NOTE: I'm not sure why this had to be changed but the ChannelStrip
                # was getting a double wrapped tuple causing errors in the ChannelStrip's
                # update method without this change
                strip_controls = (None,) * self._send_index + (control,)
                strip.set_send_controls(strip_controls[0])

class TraktorS4(ControlSurface):

    def __init__(self, c_instance=None, *args, **kwargs):
        super(TraktorS4, self).__init__(c_instance=c_instance, *args, **kwargs)

        logger.info('TraktorS4: Base ControlSurface.__init__() completed')
        with self.component_guard():
            logger.info('TraktorS4: Initializing 4 track mixer')
            self._create_components()
            logger.info('TraktorS4: Initialization complete!')

    def _create_components(self):
        self._init_mixer()

    def _create_mixer(self):
        return S4MixerComponent(
            num_tracks=NUM_TRACKS,
        )
   
    def _init_mixer(self):
        self._mixer = self._create_mixer()
        self._set_mixer_volume_controls()
        #self._set_mixer_send_controls()
        #self._set_mixer_fx_macro1_controls()
        self._set_mixer_strip_modes()
        self._set_mixer_vu_meter_controls()

    def _set_mixer_vu_meter_controls(self):
        controls = []
        for strip_id in range(4):
            controls.append(SliderElement(MIDI_CC_TYPE, TRACK_METERS[strip_id][0], TRACK_METERS[strip_id][1]))
        
        self._mixer.set_vu_meter_controls(controls)

    def _set_mixer_volume_controls(self):
        controls = []
        for slider in TRACK_VOLUME_SLIDERS + MASTER_LOOP_DRY_WET_KNOB:
            controls.append(
                SliderElement(MIDI_CC_TYPE, slider[0], slider[1])
            )
        
        self._mixer.set_volume_controls(controls)

    def _set_mixer_strip_modes(self):
        for strip_index in range(4):
            strip = self._mixer._channel_strips[strip_index]
            sends_layer = ChannelStripLayer(
                send1_control = SliderElement(MIDI_CC_TYPE, TRACK_EQ_HIGH_KNOBS[strip_index][0], TRACK_EQ_HIGH_KNOBS[strip_index][1]),
                send2_control = SliderElement(MIDI_CC_TYPE, TRACK_EQ_MID_KNOBS[strip_index][0], TRACK_EQ_MID_KNOBS[strip_index][1]),
                send3_control = SliderElement(MIDI_CC_TYPE, TRACK_EQ_LOW_KNOBS[strip_index][0], TRACK_EQ_LOW_KNOBS[strip_index][1]),
                fx1_macro1_control = SliderElement(MIDI_CC_TYPE, TRACK_FILTER_KNOBS[strip_index][0], TRACK_FILTER_KNOBS[strip_index][1]),
                fx1_macro2_control = None,
                fx1_macro3_control = None,
                fx1_macro4_control = None,
                fx2_macro1_control = None,
                fx2_macro2_control = None,
                fx2_macro3_control = None,
                fx2_macro4_control = None,
                fx3_macro1_control = None,
                fx3_macro2_control = None,
                fx3_macro3_control = None,
                fx3_macro4_control = None,
            )
            fx1_layer = ChannelStripLayer(
                send1_control = None,
                send2_control = None,
                send3_control = None,
                fx1_macro1_control = SliderElement(MIDI_CC_TYPE, TRACK_FILTER_KNOBS[strip_index][0], TRACK_FILTER_KNOBS[strip_index][1]),
                fx1_macro2_control = SliderElement(MIDI_CC_TYPE, TRACK_EQ_LOW_KNOBS[strip_index][0], TRACK_EQ_LOW_KNOBS[strip_index][1]),
                fx1_macro3_control = SliderElement(MIDI_CC_TYPE, TRACK_EQ_MID_KNOBS[strip_index][0], TRACK_EQ_MID_KNOBS[strip_index][1]),
                fx1_macro4_control = SliderElement(MIDI_CC_TYPE, TRACK_EQ_HIGH_KNOBS[strip_index][0], TRACK_EQ_HIGH_KNOBS[strip_index][1]),
                fx2_macro1_control = None,
                fx2_macro2_control = None,
                fx2_macro3_control = None,
                fx2_macro4_control = None,
                fx3_macro1_control = None,
                fx3_macro2_control = None,
                fx3_macro3_control = None,
                fx3_macro4_control = None,
            )
            fx2_layer = ChannelStripLayer(
                send1_control = None,
                send2_control = None,
                send3_control = None,
                fx1_macro1_control = None,
                fx1_macro2_control = None,
                fx1_macro3_control = None,
                fx1_macro4_control = None,
                fx2_macro1_control = SliderElement(MIDI_CC_TYPE, TRACK_FILTER_KNOBS[strip_index][0], TRACK_FILTER_KNOBS[strip_index][1]),
                fx2_macro2_control = SliderElement(MIDI_CC_TYPE, TRACK_EQ_LOW_KNOBS[strip_index][0], TRACK_EQ_LOW_KNOBS[strip_index][1]),
                fx2_macro3_control = SliderElement(MIDI_CC_TYPE, TRACK_EQ_MID_KNOBS[strip_index][0], TRACK_EQ_MID_KNOBS[strip_index][1]),
                fx2_macro4_control = SliderElement(MIDI_CC_TYPE, TRACK_EQ_HIGH_KNOBS[strip_index][0], TRACK_EQ_HIGH_KNOBS[strip_index][1]),
                fx3_macro1_control = None,
                fx3_macro2_control = None,
                fx3_macro3_control = None,
                fx3_macro4_control = None,
            )
            fx3_layer = ChannelStripLayer(
                send1_control = None,
                send2_control = None,
                send3_control = None,
                fx1_macro1_control = None,
                fx1_macro2_control = None,
                fx1_macro3_control = None,
                fx1_macro4_control = None,
                fx2_macro1_control = None,
                fx2_macro2_control = None,
                fx2_macro3_control = None,
                fx2_macro4_control = None,
                fx3_macro1_control = SliderElement(MIDI_CC_TYPE, TRACK_FILTER_KNOBS[strip_index][0], TRACK_FILTER_KNOBS[strip_index][1]),
                fx3_macro2_control = SliderElement(MIDI_CC_TYPE, TRACK_EQ_LOW_KNOBS[strip_index][0], TRACK_EQ_LOW_KNOBS[strip_index][1]),
                fx3_macro3_control = SliderElement(MIDI_CC_TYPE, TRACK_EQ_MID_KNOBS[strip_index][0], TRACK_EQ_MID_KNOBS[strip_index][1]),
                fx3_macro4_control = SliderElement(MIDI_CC_TYPE, TRACK_EQ_HIGH_KNOBS[strip_index][0], TRACK_EQ_HIGH_KNOBS[strip_index][1]),
            )
            strip.set_modes(sends_layer, fx1_layer, fx2_layer, fx3_layer)

            strip._modes.set_mode_button('sends',
                ButtonElement(False, MIDI_CC_TYPE, TRACK_GAIN_BUTTONS[strip_index][0], TRACK_GAIN_BUTTONS[strip_index][1])
            )
            strip._modes.set_mode_button('fx1',
                ButtonElement(False, MIDI_CC_TYPE, TRACK_CUE_BUTTONS[strip_index][0], TRACK_CUE_BUTTONS[strip_index][1])
            )
            strip._modes.set_mode_button('fx2',
                ButtonElement(False, MIDI_CC_TYPE, TRACK_FX_1_BUTTONS[strip_index][0], TRACK_FX_1_BUTTONS[strip_index][1])
            )
            strip._modes.set_mode_button('fx3',
                ButtonElement(False, MIDI_CC_TYPE, TRACK_FX_2_BUTTONS[strip_index][0], TRACK_FX_2_BUTTONS[strip_index][1])
            )

    def _set_mixer_fx_macro1_controls(self):
        for strip_index in range(4):
            strip = self._mixer._channel_strips[strip_index]
            strip.set_fx_macro1_control(SliderElement(MIDI_CC_TYPE, TRACK_FILTER_KNOBS[strip_index][0], TRACK_FILTER_KNOBS[strip_index][1]))

    def _set_mixer_send_controls(self):
        for strip_index in range(4):
            strip = self._mixer._channel_strips[strip_index]
            controls = (
                SliderElement(MIDI_CC_TYPE, TRACK_EQ_HIGH_KNOBS[strip_index][0], TRACK_EQ_HIGH_KNOBS[strip_index][1]),
                SliderElement(MIDI_CC_TYPE, TRACK_EQ_MID_KNOBS[strip_index][0], TRACK_EQ_MID_KNOBS[strip_index][1]),
                SliderElement(MIDI_CC_TYPE, TRACK_EQ_LOW_KNOBS[strip_index][0], TRACK_EQ_LOW_KNOBS[strip_index][1]),
            )
            logger.info('Send controls for strip %s = %s' % (strip_index, str(controls)))
            strip.set_send_controls(controls)

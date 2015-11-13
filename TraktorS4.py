from __future__ import with_statement
import logging
from _Framework.ButtonElement import ButtonElement
from _Framework.ControlSurface import ControlSurface
from _Framework.InputControlElement import MIDI_CC_TYPE
from _Framework.MixerComponent import MixerComponent as BaseMixerComponent
from _Framework.SliderElement import SliderElement
from ChannelStripComponent import HiLoFilterSliderElement
from ChannelStripComponent import ChannelStripComponent

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

class S4MixerComponent(BaseMixerComponent):

    def _create_strip(self):
        return ChannelStripComponent()

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
        self._set_mixer_filter_controls()
        self._set_mixer_send_controls()

    def _set_mixer_volume_controls(self):
        controls = []
        for slider in TRACK_VOLUME_SLIDERS + MASTER_LOOP_DRY_WET_KNOB:
            controls.append(
                SliderElement(MIDI_CC_TYPE, slider[0], slider[1])
            )
        
        self._mixer.set_volume_controls(controls)

    def _set_mixer_filter_controls(self):
        controls = []
        for knob in TRACK_FILTER_KNOBS:
            controls.append(
                HiLoFilterSliderElement(MIDI_CC_TYPE, knob[0], knob[1])
            )
        
        self._mixer.set_filter_controls(controls)

    def _set_mixer_send_controls(self):
        controls = []

        for track in range(4):
            track_controls = (
                SliderElement(MIDI_CC_TYPE, TRACK_EQ_HIGH_KNOBS[track][0], TRACK_EQ_HIGH_KNOBS[track][1]),
                SliderElement(MIDI_CC_TYPE, TRACK_EQ_MID_KNOBS[track][0], TRACK_EQ_MID_KNOBS[track][1]),
                SliderElement(MIDI_CC_TYPE, TRACK_EQ_LOW_KNOBS[track][0], TRACK_EQ_LOW_KNOBS[track][1]),
            )
            controls.append(track_controls)

        self._mixer.set_send_controls(controls)

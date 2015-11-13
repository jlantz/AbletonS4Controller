import logging
from _Framework.ChannelStripComponent import ChannelStripComponent as BaseChannelStripComponent
from _Framework.SliderElement import SliderElement
from _Generic.Devices import get_parameter_by_name
from InputControlMultiElement import InputControlMultiElement
logger = logging.getLogger(__name__)


FILTER_DEVICES = {
    'AudioEffectGroupDevice|HiLo Filter': {
        'highpass': 'Macro 1',
        'lowpass': 'Macro 2',
        'resonance': 'Macro 3',
        'lfo': 'Macro 4',
    },
}

class HiLoFilterSliderElement(InputControlMultiElement, SliderElement):
    pass

class ChannelStripComponent(BaseChannelStripComponent):
    """ A custom channel strip with support for filter knobs and LED level meters """

    def __init__(self):
        self._filter_control = None
        self._filter_device = None
        super(ChannelStripComponent, self).__init__()

    def disconnect(self):
        """ releasing references and removing listeners"""
        super(ChannelStripComponent, self).disconnect()
        self._filter_control = None
        self._filter_device = None

    def set_filter_control(self, control):
        if control != self._filter_control:
            if self._filter_control:
                self._filter_control.release_parameter()
            self._filter_control = control
            self.update()

    def _connect_parameters(self):
        if self._pan_control != None:
            self._pan_control.connect_to(self._track.mixer_device.panning)
        if self._volume_control != None:
            self._volume_control.connect_to(self._track.mixer_device.volume)
        if self._filter_control != None and self._filter_device != None:
            self._filter_control.connect_to(self._filter_device['lowpass'], *(
                self._filter_device['highpass'],
                self._filter_device['resonance'],
                self._filter_device['lfo'],
            ))
        if self._send_controls != None:
            index = 0
            for send_control in self._send_controls:
                if send_control != None:
                    if index < len(self._track.mixer_device.sends):
                        send_control.connect_to(self._track.mixer_device.sends[index])
                    else:
                        send_control.release_parameter()
                        self._empty_control_slots.register_slot(send_control, nop, 'value')
                index += 1

    def _all_controls(self):
        return [self._pan_control, self._volume_control, self._filter_control] + list(self._send_controls or [])

    def set_track(self, track):
        super(ChannelStripComponent, self).set_track(track)
        self._set_filter_device()
        self.update()
    
    def _set_filter_device(self):
        self._filter_device = None
        if self._track != None:
            for index in range(len(self._track.devices)):
                device = self._track.devices[-1 * (index + 1)]
                device_key = '%s|%s' % (device.class_name, device.name)
                if device_key in FILTER_DEVICES.keys():
                    device_dict = FILTER_DEVICES[device_key]
                    self._filter_device = {
                        'device': device,
                        'lowpass': get_parameter_by_name(device, device_dict['lowpass']),
                        'highpass': get_parameter_by_name(device, device_dict['highpass']),
                        'resonance': get_parameter_by_name(device, device_dict['resonance']),
                        'lfo': get_parameter_by_name(device, device_dict['lfo']),
                    }


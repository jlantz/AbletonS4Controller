import logging
from _Framework.ChannelStripComponent import ChannelStripComponent as BaseChannelStripComponent
from _Framework.ModesComponent import LayerMode
from _Framework.ModesComponent import ModesComponent
from _Framework.SliderElement import SliderElement
from _Framework.Util import nop
from _Generic.Devices import get_parameter_by_name
from VUMeterComponent import VUMeterComponent
logger = logging.getLogger(__name__)


FX_DEVICES = {
    'AudioEffectGroupDevice': {
        'macro1': 'Macro 1',
        'macro2': 'Macro 2',
        'macro3': 'Macro 3',
        'macro4': 'Macro 4',
    },
}

fx_mode_group = 'fx_mode_group'

class ChannelStripModesComponent(ModesComponent):

    def __init__(self, *a, **k):
        super(ChannelStripModesComponent, self).__init__(*a, **k)

    def _do_enter_mode(self, name):
        changed = False
        if name != self._get_selected_mode():
            changed = True
        super(ChannelStripModesComponent, self)._do_enter_mode(name)
        mode = self.get_mode(name)
        #if mode and hasattr(mode, '_component'):
            #mode._component._set_fx_devices()
            #mode._component.update()

    def _do_leave_mode(self, name):
        super(ChannelStripModesComponent, self)._do_leave_mode(name)

class set_send_control(object):
    def __init__(self, parent, send_num):
        self._parent = parent
        self._send_num = send_num

    def __call__(self, control):
        self._parent.set_send_control(self._send_num, control)

class set_fx_control(object):
    def __init__(self, parent, fx_num, macro_num):
        self._parent = parent
        self._fx_num = fx_num
        self._macro_num = macro_num

    def __call__(self, control):
        self._parent.set_fx_control(self._fx_num, self._macro_num, control)
        

class ChannelStripComponent(BaseChannelStripComponent):
    """ A custom channel strip with support for fx knobs and LED level meters """

    def __init__(self):
        for send_num in range(1,4):
            send_key = '_send%s_control' % send_num
            setattr(self, send_key, None)
            setattr(self, 'set%s' % send_key, set_send_control(self, send_num))

        for fx_num in range(1,4):
            fx_device_key = '_fx%s_device' % fx_num
            setattr(self, fx_device_key, None)
            for macro_num in range(1,5):
                fx_macro_key = '_fx%s_macro%s_control' % (fx_num, macro_num)
                setattr(self, fx_macro_key, None)
                setattr(self, 'set%s' % fx_macro_key, set_fx_control(self, fx_num, macro_num))

        self._vu_meter_control = None

        super(ChannelStripComponent, self).__init__()

    def disconnect(self):
        """ releasing references and removing listeners"""
        super(ChannelStripComponent, self).disconnect()
        for send_num in range(1,4):
            send_key = '_send%s_control' % send_num
            setattr(self, send_key, None)
        for fx_num in range(1,4):
            fx_device_key = '_fx%s_device' % fx_num
            setattr(self, fx_device_key, None)
            for macro_num in range(1,5):
                fx_macro_key = '_fx%s_macro%s_control' % (fx_num, macro_num)
                setattr(self, fx_macro_key, None)

    def set_modes(self, sends_layer, fx1_layer, fx2_layer, fx3_layer):
        if hasattr(self, '_modes'):
            self._modes.disconnect()
        self._modes = ModesComponent()
        self._modes.add_mode('sends', [LayerMode(self, sends_layer)])
        self._modes.add_mode('fx1', [LayerMode(self, fx1_layer)])
        self._modes.add_mode('fx2', [LayerMode(self, fx2_layer)])
        self._modes.add_mode('fx3', [LayerMode(self, fx3_layer)])
        self._modes._set_selected_mode('sends')

    def set_send_control(self, send_num, control):
        current = getattr(self, '_send%s_control' % send_num)
        if control != current:
            changed = True
            if current:
                current.release_parameter()
            setattr(self, '_send%s_control' % send_num, control)
            self.update()

    def set_fx_control(self, fx_num, macro_num, control):
        current = getattr(self, '_fx%s_macro%s_control' % (fx_num, macro_num))
        if control != current:
            changed = True
            if current:
                current.release_parameter()
            setattr(self, '_fx%s_macro%s_control' % (fx_num, macro_num), control)
            self.update()

    def set_vu_meter_control(self, control):
        try:
            current = self._vu_meter_control.slider
        except AttributeError:
            current = None

        if current != control:
            if control is None:
                self._vu_meter_control = None
            else:
                self._vu_meter_control = VUMeterComponent(self)
                if self._track:
                    self._vu_meter_control.set_vu_meter(self._track)
                    self._vu_meter_control.set_led_slider(control)
            self.update()

    def _connect_parameters(self):
        current_mode = self._get_current_mode_index()
        if self._pan_control != None:
            self._pan_control.connect_to(self._track.mixer_device.panning)
        if self._volume_control != None:
            self._volume_control.connect_to(self._track.mixer_device.volume)
        if self._send1_control != None:
            self._send1_control.connect_to(self._track.mixer_device.sends[0])
        if self._send2_control != None:
            self._send2_control.connect_to(self._track.mixer_device.sends[1])
        if self._send3_control != None:
            self._send3_control.connect_to(self._track.mixer_device.sends[2])
        self._set_fx_devices()
        for fx_num in range(1,4):
            for macro_num in range(1,5):
                control_key = '_fx%s_macro%s_control' % (fx_num, macro_num)
                fx_control = getattr(self, control_key)
                if fx_control:
                    fx_device = getattr(self, '_fx%s_device' % fx_num)
                    if fx_device:
                        fx_control.connect_to(fx_device['macro%s' % macro_num])

    def _all_controls(self):
        return [
            self._pan_control, 
            self._volume_control, 
            self._fx1_macro1_control, 
            self._fx1_macro2_control, 
            self._fx1_macro3_control, 
            self._fx1_macro4_control,
            self._fx2_macro1_control, 
            self._fx2_macro2_control, 
            self._fx2_macro3_control, 
            self._fx2_macro4_control,
            self._fx3_macro1_control, 
            self._fx3_macro2_control, 
            self._fx3_macro3_control, 
            self._fx3_macro4_control,
            self._send1_control, 
            self._send2_control, 
            self._send3_control, 
        ]

    def set_track(self, track):
        super(ChannelStripComponent, self).set_track(track)
        self._set_fx_devices()
        self.update()

    def _get_current_mode_index(self):
        if hasattr(self, '_modes') and self._modes.selected_mode:
            return self._modes._mode_list.index(self._modes.selected_mode)
    
    def _set_fx_devices(self):
        self._fx1_device = None
        self._fx2_device = None
        self._fx3_device = None
        if self._track != None:
            matched_devices = []
            for device in self._track.devices:
                if device.class_name in FX_DEVICES.keys():
                     matched_devices.append(device)

            if not matched_devices:
                return

            device = None

            # FX1 Device (required)
            device = matched_devices[0]
            device_dict = FX_DEVICES[device.class_name]
            self._fx1_device = {
                'device': device,
                'macro1': get_parameter_by_name(device, device_dict['macro1']),
                'macro2': get_parameter_by_name(device, device_dict['macro2']),
                'macro3': get_parameter_by_name(device, device_dict['macro3']),
                'macro4': get_parameter_by_name(device, device_dict['macro4']),
            }
            
            # FX2 Device (optional)
            try:
                device = matched_devices[1]
                device_dict = FX_DEVICES[device.class_name]
                self._fx2_device = {
                    'device': device,
                    'macro1': get_parameter_by_name(device, device_dict['macro1']),
                    'macro2': get_parameter_by_name(device, device_dict['macro2']),
                    'macro3': get_parameter_by_name(device, device_dict['macro3']),
                    'macro4': get_parameter_by_name(device, device_dict['macro4']),
                }
            except IndexError:
                pass

            # FX3 Device (optional)
            try:
                device = matched_devices[2]
                device_dict = FX_DEVICES[device.class_name]
                self._fx3_device = {
                    'device': device,
                    'macro1': get_parameter_by_name(device, device_dict['macro1']),
                    'macro2': get_parameter_by_name(device, device_dict['macro2']),
                    'macro3': get_parameter_by_name(device, device_dict['macro3']),
                    'macro4': get_parameter_by_name(device, device_dict['macro4']),
                }
            except IndexError:
                pass



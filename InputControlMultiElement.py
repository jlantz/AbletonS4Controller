import logging
from _Framework.InputControlElement import InputControlElement
logger = logging.getLogger(__name__)

class InputControlMultiElement(InputControlElement):

    def install_connections(self, install_translation, install_mapping, install_forwarding):
        self._send_delayed_messages_task.kill()
        self._is_mapped = False
        self._is_being_forwarded = False
        if self._msg_channel != self._original_channel or self._msg_identifier != self._original_identifier:
            install_translation(self._msg_type, self._original_identifier, self._original_channel, self._msg_identifier, self._msg_channel)
        if self._parameter_to_map_to != None:
            # Install mapping for each parameter
            for parameter in self._parameter_to_map_to:
                self._is_mapped = install_mapping(self, parameter, self._mapping_feedback_delay, self._mapping_feedback_values())
        if self.script_wants_forwarding():
            self._is_being_forwarded = install_forwarding(self)
            if self._is_being_forwarded and self.send_depends_on_forwarding:
                self._send_delayed_messages_task.restart()

    def begin_gesture(self):
        """
        Begins a modification on the input control element,
        meaning that we should consider the next flow of input data as
        a consistent gesture from the user.
        """
        if self._parameter_to_map_to and not self._in_parameter_gesture:
            self._in_parameter_gesture = True
            # Loop through all parameters
            for parameter in self._parameter_to_map_to:
                parameter.begin_gesture()

    def end_gesture(self):
        """
        Ends a modification of the input control element. See
        begin_gesture.
        """
        if self._parameter_to_map_to and self._in_parameter_gesture:
            self._in_parameter_gesture = False
            # Loop through all parameters
            for parameter in self._parameter_to_map_to:
                parameter.end_gesture()

    def connect_to(self, parameter, *args):
        """ parameter is a Live.Device.DeviceParameter, *args is any additional parameters to control """
        parameters = [parameter] + list(args)
        if self._parameter_to_map_to != parameters:
            if parameter == None:
                self.release_parameter()
            else:
                self._parameter_to_map_to = parameters
                self._request_rebuild()

    def release_parameter(self):
        if self._parameter_to_map_to != None:
            self.end_gesture()
            self._parameter_to_map_to = None
            self._request_rebuild()

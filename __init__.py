from TraktorS4 import TraktorS4
def create_instance(c_instance):
    return TraktorS4(c_instance)

from _Framework.Capabilities import *

def get_capabilities():
    return {CONTROLLER_ID_KEY: controller_id(vendor_id=6092, product_ids=[47871], model_name='Traktor Kontrol S4'),
     PORTS_KEY: [inport(props=[NOTES_CC, REMOTE, SCRIPT]),
                 outport(props=[NOTES_CC, REMOTE, SCRIPT])]}

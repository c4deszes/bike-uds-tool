from .loader import load_profile
from line_protocol.protocol import LineMaster
import time
from .constants import *

class UdsSetPropertyException(Exception):

    def __init__(self, *args: object) -> None:
        super().__init__(*args)

class UdsGetPropertyException(Exception):

    def __init__(self, *args: object) -> None:
        super().__init__(*args)

class UdsRawTool():
    def __init__(self, master: LineMaster):
        self.master = master

    def get_property(self, address: int, prop_id: int, delay: float = 0.05, timeout: float = 1):
        self.master.send_data(UDS_PROPERTY_GET_CALL_REQUEST_ID | address, [prop_id.to_bytes(2, 'big')])
        time.sleep(delay)

        start = time.time()
        while time.time() - start < timeout:
            response = self.master.request(UDS_PROPERTY_GET_RETURN_REQUEST_ID | address)
            if len(response) != 3:
                raise UdsGetPropertyException("Invalid response length")
            response_addr = response[0] << 8 | response[1]
            if response_addr & UDS_PROPERTY_STATUS_MASK:
                if response[2] == UDS_PROPERTY_GET_RETURN_NO_REQUEST:
                    return UdsGetPropertyException("No request was scheduled")
                elif response[2] == UDS_PROPERTY_GET_RETURN_NOT_READY:
                    time.sleep(delay)
                elif response[2] == UDS_PROPERTY_GET_RETURN_NO_SUCH_PROPERTY:
                    raise UdsGetPropertyException("Property not found")
                elif response[2] == UDS_PROPERTY_GET_RETURN_READ_FAILURE:
                    raise UdsGetPropertyException("Read failure")
                elif response[2] == UDS_PROPERTY_GET_RETURN_BAD_REQUEST:
                    raise UdsGetPropertyException("Bad request")
                else:
                    raise UdsGetPropertyException("Unknown error")
            else:
                return response[2:]

class UdsTool():
    
    def __init__(self, master):
        super().__init__(master)
        self.profiles = {}

    def load_profile(self, node, addr, profile):
        profile = load_profile(profile)
        self.profiles[node] = (addr, profile)
    
    def get_property(self, node, prop):
        
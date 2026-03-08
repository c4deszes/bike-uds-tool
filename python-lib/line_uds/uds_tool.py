from typing import Dict, List, Union
from line_protocol.protocol.master import LineMaster
from .constants import *
import time
from .loader import load_profile, UdsProfile
from queue import Queue, Empty
from threading import Thread, Event
from dataclasses import dataclass

from line_uds.profile import UdsProperty
from line_protocol.network.nodes import NodeRef

class UdsSetPropertyException(Exception):

    def __init__(self, *args: object) -> None:
        super().__init__(*args)

class UdsGetPropertyException(Exception):

    def __init__(self, *args: object) -> None:
        super().__init__(*args)

@dataclass
class UdsGetPropertyRequest():
    address: int
    prop_id: int
    delay: float
    timeout: float

@dataclass
class UdsSetPropertyRequest():
    address: int
    prop_id: int
    value: bytes
    delay: float
    timeout: float

@dataclass
class UdsGetPropertyEvent():
    prop: UdsGetPropertyRequest
    event_id: int
    event: Event
    # Filled out after event is set
    response: bytes
    exception: Exception

    def __init__(self, prop: UdsGetPropertyRequest, event_id: int, event: Event):
        self.prop = prop
        self.event_id = event_id
        self.event = event
        self.response = None
        self.exception = None

@dataclass
class UdsSetPropertyEvent():
    prop: UdsSetPropertyRequest
    event_id: int
    event: Event
    # Filled out after event is set
    exception: Exception

    def __init__(self, prop: UdsSetPropertyRequest, event_id: int, event: Event):
        self.prop = prop
        self.event_id = event_id
        self.event = event
        self.exception = None

@dataclass
class UdsPropertyValue:
    buffer: bytearray
    value: any

class UdsPropertyStatus:

    def __init__(self, prop: UdsProperty, data: UdsPropertyValue):
        self.prop = prop
        self.data = data
        self.exception: Exception | None = None

@dataclass
class UdsNodeStatus():
    _ref: NodeRef
    profile: UdsProfile
    properties: Dict[int, UdsPropertyStatus]

class UdsTool():

    def __init__(self, master: 'LineMaster'):
        self._master = master
        self._queue = Queue(100)
        self._event_id = 0
        self._running = False

        self.nodes = {x: UdsNodeStatus(NodeRef(x, None), None, {}) for x in range(1, 15)}

    def load_profile(self, node: Union[int, str], profile: Union[str, UdsProfile]):
        if isinstance(profile, str):
            profile = load_profile(profile)
        if isinstance(node, str):
            if self._master.network is None:
                raise ValueError("Master device has no network configured, cannot resolve node name")
            node = self._master.network.get_node(node).address

        self.nodes[node].profile = profile
        for prop in profile.properties:
            # TODO: initialize default values for properties
            self.nodes[node].properties[prop.prop_id] = UdsPropertyStatus(prop, UdsPropertyValue(None, None))

        return profile

    def __enter__(self):
        self._running = True
        self._thread = Thread(target=self._run)
        self._thread.start()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self._running = False
        self._thread.join()

    def _process_getevent(self, response, event: UdsGetPropertyEvent) -> bool:
        # TODO: in all cases update the properties of the node
        if len(response) < 3:
            event.exception = UdsGetPropertyException("Invalid response length")
            return True

        response_addr = response[0] << 8 | response[1]
        if response_addr & UDS_PROPERTY_STATUS_MASK:
            if response[2] == UDS_PROPERTY_GET_RETURN_NOT_READY:
                return False
            if response[2] == UDS_PROPERTY_GET_RETURN_NO_REQUEST:
                event.exception = UdsGetPropertyException("No request was scheduled")
            elif response[2] == UDS_PROPERTY_GET_RETURN_NO_SUCH_PROPERTY:
                event.exception = UdsGetPropertyException("Property not found")
            elif response[2] == UDS_PROPERTY_GET_RETURN_READ_FAILURE:
                event.exception = UdsGetPropertyException("Read failure")
            elif response[2] == UDS_PROPERTY_GET_RETURN_BAD_REQUEST:
                event.exception = UdsGetPropertyException("Bad request")
            else:
                event.exception = UdsGetPropertyException("Unknown error")
            return True
        else:
            event.response = response[2:]

            if event.prop.prop_id in self.nodes[event.prop.address].properties:
                property_status = self.nodes[event.prop.address].properties[event.prop.prop_id]
                property_status.data.buffer = bytearray(event.response)
                if property_status.prop is not None:
                    property_status.data.value = property_status.prop.decode(property_status.data.buffer)

            return True
        
    def _process_setevent(self, response, event: UdsSetPropertyEvent) -> bool:
        # TODO: in all cases update the properties of the node
        if len(response) != 3:
            event.exception = UdsSetPropertyException("Invalid response length")
            return True
        if response[2] == UDS_PROPERTY_SET_RETURN_SUCCESS:

            if event.prop.prop_id in self.nodes[event.prop.address].properties:
                property_status = self.nodes[event.prop.address].properties[event.prop.prop_id]
                property_status.data.buffer = bytearray(event.prop.value)
                if property_status.prop is not None:
                    property_status.data.value = property_status.prop.decode(property_status.data.buffer)

            return True
        elif response[2] == UDS_PROPERTY_SET_RETURN_NOT_READY:
            return False
        elif response[2] == UDS_PROPERTY_SET_RETURN_NO_SUCH_PROPERTY:
            event.exception = UdsSetPropertyException("Property not found")
            return True
        elif response[2] == UDS_PROPERTY_SET_RETURN_NO_REQUEST:
            event.exception = UdsSetPropertyException("No request was scheduled")
            return True
        else:
            event.exception = UdsSetPropertyException("Unknown error")
            return True

    def _run(self):
        while self._running:
            try:
                event = self._queue.get(timeout=1)
                if isinstance(event, UdsGetPropertyEvent):
                    start = time.time()
                    timeout = event.prop.timeout
                    self._master.send_request(UDS_PROPERTY_GET_CALL_REQUEST_ID | event.prop.address,
                                              list(event.prop.prop_id.to_bytes(2, 'big')),
                                              wait=True, timeout=timeout)
                    timeout -= time.time() - start
                    try:
                        while timeout > 0:
                            time.sleep(event.prop.delay)
                            timeout -= event.prop.delay
                            start = time.time()
                            response = self._master.request(UDS_PROPERTY_GET_RETURN_REQUEST_ID | event.prop.address,
                                                            wait=True, timeout=timeout)
                            timeout -= time.time() - start
                            if self._process_getevent(response, event):
                                event.event.set()
                                break
                        if timeout <= 0:
                            raise UdsGetPropertyException("Timeout")
                    except Exception as e:
                        event.exception = e
                        event.event.set()
                elif isinstance(event, UdsSetPropertyEvent):
                    start = time.time()
                    timeout = event.prop.timeout
                    self._master.send_request(UDS_PROPERTY_SET_CALL_REQUEST_ID | event.prop.address,
                                              list(event.prop.prop_id.to_bytes(2, 'big')) + list(event.prop.value),
                                              wait=True, timeout=timeout)
                    timeout -= time.time() - start
                    try:
                        while timeout > 0:
                            time.sleep(event.prop.delay)
                            timeout -= event.prop.delay
                            start = time.time()
                            response = self._master.request(UDS_PROPERTY_SET_RETURN_REQUEST_ID | event.prop.address,
                                                            wait=True, timeout=timeout)
                            timeout -= time.time() - start
                            if self._process_setevent(response, event):
                                event.event.set()
                                break
                        if timeout <= 0:
                            raise UdsSetPropertyException("Timeout")
                    except Exception as e:
                        event.exception = e
                        event.event.set()
            except Empty as e:
                pass

    def get_property_raw(self, address: int, prop_id: int, delay: float = 0.05, wait: bool = False,
                         timeout: float = 1):
        event = UdsGetPropertyEvent(UdsGetPropertyRequest(address, prop_id, delay, timeout), self._event_id, Event())
        self._queue.put(event)
        self._event_id += 1

        if wait:
            event.event.wait(timeout)
            if event.exception:
                raise event.exception
            return event.response

    def set_property_raw(self, address: int, prop_id: int, value: bytes, delay: float = 0.05,
                         wait: bool = False, timeout: float = 1):
        event = UdsSetPropertyEvent(UdsSetPropertyRequest(address, prop_id, value, delay, timeout), self._event_id, Event())
        self._queue.put(event)
        self._event_id += 1

        if wait:
            event.event.wait(timeout)
            if event.exception:
                raise event.exception

    def get_property(self, address: Union[int, str], prop_id: Union[int, str], delay: float = 0.05,
                     wait: bool = False, timeout: float = 1):
        if isinstance(address, str):
            address = self._master.network.get_node(address)
        if isinstance(prop_id, str):
            prop_id = self.nodes[address].profile.get_property(prop_id).prop_id
        # TODO: decode value
        return self.get_property_raw(address, prop_id, delay, wait, timeout)
    
    def set_property(self, address: Union[int, str], prop_id: Union[int, str], value, delay: float = 0.05,
                        wait: bool = False, timeout: float = 1):
        if isinstance(address, str):
            address = self._master.network.get_node(address).address
        if isinstance(prop_id, str):
            prop_id = self.nodes[address].profile.get_property(prop_id).prop_id

        prop_value = self.nodes[address].profile.get_property(prop_id).encode(value)
        return self.set_property_raw(address, prop_id, prop_value, delay, wait, timeout)

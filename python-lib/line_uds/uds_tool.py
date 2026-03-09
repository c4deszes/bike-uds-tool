from typing import Dict, List, Union
from line_protocol.protocol.master import LineMaster
from .constants import *
import time
from .loader import load_profile, UdsProfile
from queue import Queue, Empty
from threading import Thread, Event
from dataclasses import dataclass

from line_uds.profile import UdsProperty
from line_protocol.network.nodes import Node, NodeRef

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
    _node: Node
    profile: UdsProfile
    properties: Dict[int, UdsPropertyStatus]

class UdsNodeStatusListener():

    def on_property_change(self, node: Node, prop: UdsProperty, value: UdsPropertyValue):
        pass

class UdsTool():

    def __init__(self, master: 'LineMaster'):
        self._master = master
        self._queue = Queue[Union[UdsGetPropertyEvent, UdsSetPropertyEvent]](100)
        self._event_id = 0
        self._running = False

        self._listeners: List[UdsNodeStatusListener] = []
        self._nodes: Dict[int, UdsNodeStatus] = {}

    def load_profile(self, node: Node, profile: Union[str, UdsProfile]):
        if isinstance(profile, str):
            profile = load_profile(profile)

        self._nodes[node.address] = UdsNodeStatus(node, profile, {})
        for prop in profile.properties:
            # TODO: initialize default values for properties
            self._nodes[node.address].properties[prop.prop_id] = UdsPropertyStatus(prop, UdsPropertyValue(None, None))

        return profile
    
    def add_listener(self, listener: UdsNodeStatusListener):
        self._listeners.append(listener)

    def __enter__(self):
        self._running = True
        self._thread = Thread(target=self._run)
        self._thread.start()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self._running = False
        self._thread.join()

    def _update_property(self, address: int, prop_id: int, value: bytes):
        if address in self._nodes and prop_id in self._nodes[address].properties:
            property_status = self._nodes[address].properties[prop_id]
            property_status.data.buffer = bytearray(value)
            if property_status.prop is not None:
                property_status.data.value = property_status.prop.decode(property_status.data.buffer)

            for listener in self._listeners:
                listener.on_property_change(self._nodes[address]._node, property_status.prop, property_status.data)

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

            self._update_property(event.prop.address, event.prop.prop_id, event.response)

            return True
        
    def _process_setevent(self, response, event: UdsSetPropertyEvent) -> bool:
        # TODO: in all cases update the properties of the node
        if len(response) != 3:
            event.exception = UdsSetPropertyException("Invalid response length")
            return True
        if response[2] == UDS_PROPERTY_SET_RETURN_SUCCESS:

            self._update_property(event.prop.address, event.prop.prop_id, event.prop.value)

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
            
    def _find_node_by_name(self, name: str) -> Node:
        for node in self._master.network.nodes:
            if node.name == name:
                return node
        raise ValueError(f"Node with name {name} not found")

    def get_property(self, address: Union[int, str], prop_id: Union[int, str], delay: float = 0.05,
                     wait: bool = False, timeout: float = 1):
        if isinstance(address, str):
            address = self._find_node_by_name(address).address
        if isinstance(prop_id, str):
            prop_id = self._nodes[address].profile.get_property(prop_id).prop_id
        # TODO: decode value
        return self.get_property_raw(address, prop_id, delay, wait, timeout)
    
    def set_property(self, address: Union[int, str], prop_id: Union[int, str], value, delay: float = 0.05,
                        wait: bool = False, timeout: float = 1):
        if isinstance(address, str):
            address = self._find_node_by_name(address).address
        if isinstance(prop_id, str):
            prop_id = self._nodes[address].profile.get_property(prop_id).prop_id

        prop_value = self._nodes[address].profile.get_property(prop_id).encode(value)
        return self.set_property_raw(address, prop_id, prop_value, delay, wait, timeout)

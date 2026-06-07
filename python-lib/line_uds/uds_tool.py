from typing import Dict, List, Union, Any
from line_protocol.protocol.master import LineMaster
from .constants import *
import time
from .loader import load_profile, UdsProfile
from queue import Queue, Empty
from threading import Thread, Event
from dataclasses import dataclass

from line_uds.profile import UdsProperty, UdsService
from line_protocol.network.nodes import Node, NodeRef

class UdsSetPropertyException(Exception):

    def __init__(self, status_code: int, *args: object) -> None:
        super().__init__(*args)
        self.status_code = status_code

class UdsGetPropertyException(Exception):

    def __init__(self, status_code: int, *args: object) -> None:
        super().__init__(*args)
        self.status_code = status_code

class UdsServiceCallException(Exception):

    def __init__(self, status_code: int, *args: object) -> None:
        super().__init__(*args)
        self.status_code = status_code

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
class UdsServiceRequest():
    address: int
    service_id: int
    data: bytes
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
class UdsServiceEvent():
    service: UdsServiceRequest
    event_id: int
    event: Event
    # Filled out after event is set
    response: bytes
    exception: Exception

    def __init__(self, service: UdsServiceRequest, event_id: int, event: Event):
        self.service = service
        self.event_id = event_id
        self.event = event
        self.response = None
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
class UdsServiceReturn:
    buffer: bytearray
    value: any

class UdsServiceStatus:

    def __init__(self, service: UdsService, data: UdsServiceReturn):
        self.service = service
        # TODO: status code
        self.data = data
        self.exception: Exception | None = None

@dataclass
class UdsNodeStatus():
    _node: Node
    profile: UdsProfile
    properties: Dict[int, UdsPropertyStatus]
    services: Dict[int, UdsServiceStatus]

class UdsNodeStatusListener():

    def on_property_change(self, node: Node, prop: UdsProperty, value: UdsPropertyValue):
        pass

    # TODO: status code
    def on_service_finish(self, node: Node, service: UdsService, result: UdsServiceReturn):
        pass

    def on_service_failure(self, node: Node, service: UdsService, exception: Exception):
        pass

class UdsTool():

    def __init__(self, master: 'LineMaster'):
        self._master: 'LineMaster' = master
        self._queue = Queue[Union[UdsGetPropertyEvent, UdsSetPropertyEvent]](100)
        self._event_id = 0
        self._running = False

        self._listeners: List[UdsNodeStatusListener] = []
        self._nodes: Dict[int, UdsNodeStatus] = {}

    def load_profile(self, node: Node, profile: Union[str, UdsProfile]):
        if isinstance(profile, str):
            profile = load_profile(profile)

        self._nodes[node.address] = UdsNodeStatus(node, profile, {}, {})
        for prop in profile.properties:
            # TODO: initialize default values for properties
            self._nodes[node.address].properties[prop.prop_id] = UdsPropertyStatus(prop, UdsPropertyValue(None, None))

        for service in profile.services:
            # TODO: initialize default values
            self._nodes[node.address].services[service.service_id] = UdsServiceStatus(service, UdsServiceReturn(None, None))

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

    def _update_service(self, address: int, service_id: int, status_code: int, value: bytes):
        if address in self._nodes and service_id in self._nodes[address].services:
            service_status = self._nodes[address].services[service_id]
            service_status.data.buffer = bytearray(value)
            if service_status.service is not None:
                service_status.data.value = service_status.service.decode_return_value(service_status.data.buffer)

                for listener in self._listeners:
                    listener.on_service_finish(self._nodes[address]._node, service_status.service, service_status.data)

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
                event.exception = UdsGetPropertyException(UDS_PROPERTY_GET_RETURN_NO_REQUEST, "No request was scheduled")
            elif response[2] == UDS_PROPERTY_GET_RETURN_NO_SUCH_PROPERTY:
                event.exception = UdsGetPropertyException(UDS_PROPERTY_GET_RETURN_NO_SUCH_PROPERTY, "Property not found")
            elif response[2] == UDS_PROPERTY_GET_RETURN_READ_FAILURE:
                event.exception = UdsGetPropertyException(UDS_PROPERTY_GET_RETURN_READ_FAILURE, "Read failure")
            elif response[2] == UDS_PROPERTY_GET_RETURN_BAD_REQUEST:
                event.exception = UdsGetPropertyException(UDS_PROPERTY_GET_RETURN_BAD_REQUEST, "Bad request")
            else:
                event.exception = UdsGetPropertyException(response[2], "Unknown error")
            return True
        else:
            event.response = response[2:]

            self._update_property(event.prop.address, event.prop.prop_id, event.response)

            return True
        
    def _process_setevent(self, response, event: UdsSetPropertyEvent) -> bool:
        # TODO: in all cases update the properties of the node
        if len(response) != 3:
            event.exception = UdsSetPropertyException(UDS_PROPERTY_SET_RETURN_BAD_RESPONSE, "Invalid response length")
            return True
        if response[2] == UDS_PROPERTY_SET_RETURN_SUCCESS:

            self._update_property(event.prop.address, event.prop.prop_id, event.prop.value)

            return True
        elif response[2] == UDS_PROPERTY_SET_RETURN_NOT_READY:
            return False
        elif response[2] == UDS_PROPERTY_SET_RETURN_NO_SUCH_PROPERTY:
            event.exception = UdsSetPropertyException(UDS_PROPERTY_SET_RETURN_NO_SUCH_PROPERTY, "Property not found")
            return True
        elif response[2] == UDS_PROPERTY_SET_RETURN_NO_REQUEST:
            event.exception = UdsSetPropertyException(UDS_PROPERTY_SET_RETURN_NO_REQUEST, "No request was scheduled")
            return True
        else:
            event.exception = UdsSetPropertyException(response[2], "Unknown error")
            return True
        
    def _process_serviceevent(self, response, event: UdsServiceEvent) -> bool:
        if len(response) < 3:
            raise UdsServiceCallException(UDS_SERVICE_CALL_BAD_RESPONSE, "Invalid response length")
        
        status_code = response[2]

        if status_code == UDS_SERVICE_CALL_SUCCESS:
            if len(response) == 3:
                event.response = []
            else:
                event.response = response[3:]

            self._update_service(event.service.address, event.service.service_id, status_code, event.response)
            return True
        elif status_code == UDS_SERVICE_CALL_NOT_READY:
            return False
        else:
            raise UdsServiceCallException(status_code, "Service call failed")

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
                                                            wait=True, timeout=event.prop.delay)
                            timeout -= time.time() - start
                            if self._process_getevent(response, event):
                                event.event.set()
                                break
                        if timeout <= 0:
                            raise UdsGetPropertyException(UDS_PROPERTY_GET_RETURN_TIMEOUT, "Timeout")
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
                                                            wait=True, timeout=event.prop.delay)
                            timeout -= time.time() - start
                            if self._process_setevent(response, event):
                                event.event.set()
                                break
                        if timeout <= 0:
                            raise UdsSetPropertyException(UDS_PROPERTY_SET_RETURN_TIMEOUT, "Timeout")
                    except Exception as e:
                        event.exception = e
                        event.event.set()
                elif isinstance(event, UdsServiceEvent):
                    start = time.time()
                    timeout = event.service.timeout
                    self._master.send_request(UDS_SERVICE_CALL_REQUEST_ID | event.service.address,
                                              list(event.service.service_id.to_bytes(2, 'big')) + list(event.service.data),
                                              wait=True, timeout=timeout)
                    timeout -= time.time() - start
                    try:
                        while timeout > 0:
                            time.sleep(event.service.delay)
                            timeout -= event.service.delay
                            start = time.time()
                            response = self._master.request(UDS_SERVICE_RETURN_REQUEST_ID | event.service.address,
                                                            wait=True, timeout=event.service.delay)
                            timeout -= time.time() - start
                            if self._process_serviceevent(response, event):
                                event.event.set()
                                break
                        if timeout <= 0:
                            raise UdsServiceCallException(UDS_SERVICE_CALL_TIMEOUT, "Timeout")
                    except Exception as e:
                        event.exception = e
                        event.event.set()

                        for listener in self._listeners:
                            listener.on_service_failure(self._nodes[event.service.address]._node, self._nodes[event.service.address].services[event.service.service_id].service, e)
            except Empty as e:
                pass

    def get_property_raw(self, address: int, prop_id: int, delay: float = 0.05, wait: bool = False,
                         timeout: float = 1) -> list[int] | UdsGetPropertyEvent:
        event = UdsGetPropertyEvent(UdsGetPropertyRequest(address, prop_id, delay, timeout), self._event_id, Event())
        self._queue.put(event)
        self._event_id += 1

        if wait:
            # TODO: find a solution
            event.event.wait(timeout + 1)
            if event.exception:
                raise event.exception
            return event.response
        return event

    def set_property_raw(self, address: int, prop_id: int, value: bytes, delay: float = 0.05,
                         wait: bool = False, timeout: float = 1) -> None | UdsSetPropertyEvent:
        event = UdsSetPropertyEvent(UdsSetPropertyRequest(address, prop_id, value, delay, timeout), self._event_id, Event())
        self._queue.put(event)
        self._event_id += 1

        if wait:
            # TODO: find a solution
            event.event.wait(timeout + 1)
            if event.exception:
                raise event.exception
            return None
        return event

    def call_service_raw(self, address: int, service_id: int, data: bytes, delay: float = 0.05,
                         wait: bool = False, timeout: float = 1):
        event = UdsServiceEvent(UdsServiceRequest(address, service_id, data, delay, timeout), self._event_id, Event())
        self._queue.put(event)
        self._event_id += 1

        if wait:
            # TODO: find a solution
            event.event.wait(timeout + 1)
            if event.exception:
                raise event.exception
            return event.response
            
    def _find_node_by_name(self, name: str) -> Node:
        # if self._master.network is not None:
        #     for node in self._master.network.nodes:
        #         if node.name == name:
        #             return node
        for node_status in self._nodes.values():
            if node_status._node.name == name:
                return node_status._node
        raise ValueError(f"Node with name {name} not found")

    def get_property(self, address: Union[int, str], prop_id: Union[int, str], delay: float = 0.05,
                     wait: bool = False, timeout: float = 1) -> Any | UdsGetPropertyEvent:
        if isinstance(address, str):
            address = self._find_node_by_name(address).address
        if isinstance(prop_id, str):
            prop_id = self._nodes[address].profile.get_property(prop_id).prop_id

        result = self.get_property_raw(address, prop_id, delay, wait, timeout)
        if wait:
            return self._nodes[address].properties[prop_id].prop.decode(result)
        return result
    
    def set_property(self, address: Union[int, str], prop_id: Union[int, str], value, delay: float = 0.05,
                        wait: bool = False, timeout: float = 1):
        if isinstance(address, str):
            address = self._find_node_by_name(address).address
        if isinstance(prop_id, str):
            prop_id = self._nodes[address].profile.get_property(prop_id).prop_id

        prop_value = self._nodes[address].profile.get_property(prop_id).encode(value)
        return self.set_property_raw(address, prop_id, prop_value, delay, wait, timeout)
    
    def call_service(self, address: Union[int, str], service_id: Union[int, str], params: Dict[str, any], delay: float = 0.05,
                        wait: bool = False, timeout: float = 1):
        if isinstance(address, str):
            address = self._find_node_by_name(address).address
        service = self._nodes[address].profile.get_service(service_id)

        data = service.encode_parameters(params)

        return self.call_service_raw(address, service_id, data, delay, wait, timeout)

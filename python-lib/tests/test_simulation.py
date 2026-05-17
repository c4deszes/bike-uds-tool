# pylint: disable=missing-function-docstring, missing-class-docstring, missing-module-docstring
# pylint: disable=invalid-name
import pytest
import time

from line_protocol.network import load_network, Node
from line_protocol.network.request import SignalValueContainer
from line_protocol.protocol.master import LineMaster, LineTransportTimeout, RequestListener, NodeStatusListener, NodeStatusProperty
from line_protocol.protocol.simulation import SimulatedPeripheral
from unittest.mock import Mock

from line_uds.uds_tool import (UdsServiceCallException, UdsTool, UdsProfile,
                               UdsGetPropertyException, UdsSetPropertyException,
                               UdsGetPropertyEvent, UdsSetPropertyEvent,
                               UdsNodeStatusListener)
from line_uds.profile import UdsProperty, UdsService, UdsServiceParam, UdsIntTypeDefinition, UdsBoolTypeDefinition, UdsEnumTypeDefinition, UdsVoidTypeDefinition, UdsStructTypeDefinition
from line_uds.simulation import SimulatedUdsExtension, UdsExtensionListener

@pytest.fixture()
def node():
    yield Node('TestNode', 0x01)

@pytest.fixture()
def uds_profile():
    profile = UdsProfile()

    numeric_prop = UdsProperty('NumericProperty', 0x0001, '', 'Default', 'volatile', UdsIntTypeDefinition('uint16_t', 2, False))
    numeric_prop.min = 0
    numeric_prop.max = 65535
    numeric_prop.default_value = 0
    profile.properties.append(numeric_prop)

    bool_prop = UdsProperty('BooleanProperty', 0x0002, '', 'Default', 'volatile', UdsBoolTypeDefinition('bool'))
    bool_prop.default_value = False
    profile.properties.append(bool_prop)
    
    enum_prop = UdsProperty('EnumProperty', 0x0003, '', 'Default', 'volatile', UdsEnumTypeDefinition('TestEnum', ['Value1', 'Value2', 'Value3']))
    enum_prop.default_value = 'Value1'
    profile.properties.append(enum_prop)

    # TODO: add struct property
    
    void_noparams = UdsService('VoidNoParams', 0x100, '', 'Default', [], UdsVoidTypeDefinition('void'))

    profile.services.append(void_noparams)

    yield profile

@pytest.fixture()
def simulated_extension(uds_profile):
    yield SimulatedUdsExtension(uds_profile)

class UdsHandler(UdsExtensionListener):

    def __init__(self):
        pass

    def on_property_change(self, property_id: int, buffer: bytearray, value: any) -> None:
        pass

    def on_service_call(self, service_id: int, request_data: list[int]) -> None:
        pass

@pytest.fixture()
def peripheral(node, simulated_extension):
    peripheral = SimulatedPeripheral(node)
    peripheral.add_extension(simulated_extension)
    peripheral.op_status = 'Ok'
    peripheral.software_version = '1.0.0'
    peripheral.serial_number = 0x12345678
    yield peripheral

@pytest.fixture()
def master(peripheral):
    with LineMaster() as master:
        master.virtual_bus.add(peripheral)
        yield master

@pytest.fixture()
def uds_tool(master, node, uds_profile):
    with UdsTool(master) as uds_tool:
        uds_tool.load_profile(node, uds_profile)
        yield uds_tool

class TestSimulationUdsExtension_PropertyAccess_SyncRaw:

    def test_PropertyAccess_SyncRaw_GetInvalidProperty(self, uds_tool, peripheral):
        with pytest.raises(UdsGetPropertyException):
            uds_tool.get_property_raw(0x01, 0xFFFF, wait=True, timeout=1)

    def test_PropertyAccess_SyncRaw_SetInvalidProperty(self, uds_tool, peripheral):
        with pytest.raises(UdsSetPropertyException):
            uds_tool.set_property_raw(0x01, 0xFFFF, bytes([0x00]), wait=True, timeout=1)

    def test_PropertyAccess_SyncRaw_GetNumericProperty(self, uds_tool, peripheral):
        value = uds_tool.get_property_raw(0x01, 0x0001, wait=True, timeout=1)
        assert value == [0x00, 0x00]

    def test_PropertyAccess_SyncRaw_SetNumericProperty(self, uds_tool, peripheral):
        uds_tool.set_property_raw(0x01, 0x0001, bytes([0x34, 0x12]), wait=True, timeout=1)
        value = uds_tool.get_property_raw(0x01, 0x0001, wait=True, timeout=1)
        assert value == [0x34, 0x12]

    def test_PropertyAccess_SyncRaw_GetBooleanProperty(self, uds_tool, peripheral):
        value = uds_tool.get_property_raw(0x01, 0x0002, wait=True, timeout=1)
        assert value == [0x00]

    def test_PropertyAccess_SyncRaw_SetBooleanProperty(self, uds_tool, peripheral):
        uds_tool.set_property_raw(0x01, 0x0002, bytes([0x01]), wait=True, timeout=1)
        value = uds_tool.get_property_raw(0x01, 0x0002, wait=True, timeout=1)
        assert value == [0x01]

    def test_PropertyAccess_SyncRaw_GetEnumProperty(self, uds_tool, peripheral):
        value = uds_tool.get_property_raw(0x01, 0x0003, wait=True, timeout=1)
        assert value == [0x00]

    def test_PropertyAccess_SyncRaw_SetEnumProperty(self, uds_tool, peripheral):
        uds_tool.set_property_raw(0x01, 0x0003, bytes([0x02]), wait=True, timeout=1)
        value = uds_tool.get_property_raw(0x01, 0x0003, wait=True, timeout=1)
        assert value == [0x02]

class TestSimulationUdsExtension_PropertyAccess_Sync:

    def test_PropertyAccess_Sync_GetInvalidProperty(self, uds_tool, peripheral):
        with pytest.raises(UdsGetPropertyException):
            uds_tool.get_property('TestNode', 0xFFFF, wait=True, timeout=1)

    def test_PropertyAccess_Sync_SetInvalidProperty(self, uds_tool, peripheral):
        with pytest.raises(LookupError):
            uds_tool.set_property('TestNode', 0xFFFF, 0, wait=True, timeout=1)

    def test_PropertyAccess_Sync_GetNumericProperty(self, uds_tool, peripheral):
        value = uds_tool.get_property('TestNode', 'NumericProperty', wait=True, timeout=1)
        assert value == 0

    def test_PropertyAccess_Sync_SetNumericProperty(self, uds_tool, peripheral):
        uds_tool.set_property('TestNode', 'NumericProperty', 0x1234, wait=True, timeout=1)
        value = uds_tool.get_property('TestNode', 'NumericProperty', wait=True, timeout=1)
        assert value == 0x1234

    def test_PropertyAccess_Sync_GetBooleanProperty(self, uds_tool, peripheral):
        value = uds_tool.get_property('TestNode', 'BooleanProperty', wait=True, timeout=1)
        assert value == False

    def test_PropertyAccess_Sync_SetBooleanProperty(self, uds_tool, peripheral):
        uds_tool.set_property('TestNode', 'BooleanProperty', True, wait=True, timeout=1)
        value = uds_tool.get_property('TestNode', 'BooleanProperty', wait=True, timeout=1)
        assert value == True

    def test_PropertyAccess_Sync_GetEnumProperty(self, uds_tool, peripheral):
        value = uds_tool.get_property('TestNode', 'EnumProperty', wait=True, timeout=1)
        assert value == 'Value1'

    def test_PropertyAccess_Sync_SetEnumProperty(self, uds_tool, peripheral):
        uds_tool.set_property('TestNode', 'EnumProperty', 'Value3', wait=True, timeout=1)
        value = uds_tool.get_property('TestNode', 'EnumProperty', wait=True, timeout=1)
        assert value == 'Value3'

class TestSimulationUdsExtension_PropertyAccess_Async:

    @pytest.fixture()
    def listener(self, uds_tool):
        listener = Mock(spec=UdsNodeStatusListener)
        uds_tool.add_listener(listener)
        yield listener

    def test_PropertyAccess_Async_GetNumericProperty(self, uds_tool, listener):
        event = uds_tool.get_property_raw(0x01, 0x0001, wait=False)
        assert isinstance(event, UdsGetPropertyEvent)

        event.event.wait(1)
        
        #assert listener.on_property_change.assert_called_once()
        assert event.response == [0x00, 0x00]

    def test_PropertyAccess_Async_SetNumericProperty(self, uds_tool, peripheral):
        event = uds_tool.set_property_raw(0x01, 0x0001, bytes([0x34, 0x12]), wait=False)
        assert isinstance(event, UdsSetPropertyEvent)

        event.event.wait(1)
        value = uds_tool.get_property_raw(0x01, 0x0001, wait=True, timeout=1)
        # TODO: assert listener called with correct value
        assert value == [0x34, 0x12]

class TestSimulationUdsExtension_ServiceCall_SyncRaw:

    def test_ServiceCall_SyncRaw_InvalidService(self, uds_tool, peripheral):
        with pytest.raises(UdsServiceCallException):
            response = uds_tool.call_service_raw(0x01, 0x5555, [], wait=True, timeout=1)

    def test_ServiceCall_SyncRaw_VoidNoParams(self, uds_tool, peripheral):
        response = uds_tool.call_service_raw(0x01, 0x100, [], wait=True)
        assert response == []

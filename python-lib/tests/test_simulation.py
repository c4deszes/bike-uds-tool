# pylint: disable=missing-function-docstring, missing-class-docstring, missing-module-docstring
# pylint: disable=invalid-name
import pytest
import time

from line_protocol.network import load_network, Node
from line_protocol.network.request import SignalValueContainer
from line_protocol.protocol.master import LineMaster, LineTransportTimeout, RequestListener, NodeStatusListener, NodeStatusProperty
from line_protocol.protocol.simulation import SimulatedPeripheral
from unittest.mock import Mock

from line_uds.uds_tool import UdsTool, UdsProfile
from line_uds.profile import UdsNumericProperty, UdsBooleanProperty, UdsEnumProperty
from line_uds.simulation import SimulatedUdsExtension

class TestSimulationUdsExtension:

    @pytest.fixture()
    def node(self):
        yield Node('RotorSensor', 0x01)

    @pytest.fixture()
    def uds_profile(self):
        profile = UdsProfile()
        profile.properties.append(UdsNumericProperty('NumericProperty', 0x0001, 2, False, 0))
        yield profile

    @pytest.fixture()
    def simulated_extension(self, uds_profile):
        yield SimulatedUdsExtension(uds_profile)

    @pytest.fixture()
    def peripheral(self, node, simulated_extension):
        peripheral = SimulatedPeripheral(node)
        peripheral.add_extension(simulated_extension)
        peripheral.op_status = 'Ok'
        peripheral.software_version = '1.0.0'
        peripheral.serial_number = 0x12345678
        yield peripheral

    @pytest.fixture()
    def master(self, peripheral):
        with LineMaster() as master:
            master.virtual_bus.add(peripheral)
            yield master

    @pytest.fixture()
    def uds_tool(self, master):
        with UdsTool(master) as uds_tool:
            yield uds_tool

    def test_PropertyAccess(self, uds_tool, peripheral):
        uds_tool.set_property_raw(0x01, 0x0001, bytes([0x34, 0x12]), wait=True, timeout=1)
        value = uds_tool.get_property_raw(0x01, 0x0001, wait=True, timeout=1)
        assert value == [0x34, 0x12]

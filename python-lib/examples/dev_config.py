from line_flash.flash import FlashTool
from line_protocol.protocol.master import LineMaster
from line_protocol.protocol.transport import LineSerialTransport
import logging
from line_uds.uds_tool import UdsRawTool, UdsTool

logging.basicConfig(level=logging.DEBUG)

with LineSerialTransport('COM9', baudrate=19200, one_wire=True) as transport:
    master = LineMaster(transport)
    uds_raw_tool = UdsRawTool(master)
    uds_tool = UdsTool(uds_raw_tool)

    # "Brightness_Safety_Level": {
    #         "id": "0x4023",
    #         "type": "uint16",
    #         "min": 10,
    #         "max": 1000
    #     },

    #value = uds_raw_tool.get_property(0x03, prop_id=0x4023)

    #value = uds_raw_tool.set_property(0x03, prop_id=0x4023, value=int.to_bytes(200, 2, byteorder='little'))

    uds_tool.load_profile(node='RearLight', addr=0x03, profile="C:/Workspace/bicycle/rear-light/sw/tools/line/uds_profile.json")

    level = uds_tool.get_property('RearLight', prop='Brightness_Safety_Level')
    uds_tool.set_property('RearLight', prop='Brightness_Safety_Level', value=300)

    uds_tool.call_service('RearLight', service='CalibrateBrightness', Brightness=100)

    #value = uds_tool.get_property(0x03, prop_id=0x4090)

    # uds_tool = UdsTool(master)
    # uds_tool.load_profile(node='RotorSensor', addr=0x01, profile="uds_profile.json")

    # uds_tool.set_property('RotorSensor', prop='Example_Property', value=0x01)
    # uds_tool.set_property('RotorSensor', prop='Example_Option', value=True)
    # uds_tool.set_property('RotorSensor', prop='Example_Choice', value='Two')
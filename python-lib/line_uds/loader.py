import json
import os

from line_uds.profile import UdsProfile, UdsNumericProperty, UdsBooleanProperty, UdsEnumProperty

def load_profile(profile):
    with open(profile, 'r') as f:
        data = json.load(f)

        profile = UdsProfile()
        profile.services = []

        properties = []
        for (name, prop) in data['properties'].items():
            if prop['type'] in ['uint8', 'uint16', 'uint32', 'uint64']:
                byte_size = int(prop['type'][4:]) // 8
                properties.append(UdsNumericProperty(name, prop['id'], byte_size, False))
            if prop['type'] in ['int8', 'int16', 'int32', 'int64']:
                byte_size = int(prop['type'][3:]) // 8
                properties.append(UdsNumericProperty(name, prop['id'], byte_size, True))
            elif prop['type'] == 'bool':
                properties.append(UdsBooleanProperty(name, prop['id']))
            elif prop['type'] == 'enum':
                properties.append(UdsEnumProperty(name, prop['id'], prop['values']))

        profile.properties = properties

        return profile
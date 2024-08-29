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
                properties.append(UdsNumericProperty(name, int(prop['id'], 0), byte_size, False, prop['default'] if 'default' in prop else 0))
            if prop['type'] in ['int8', 'int16', 'int32', 'int64']:
                byte_size = int(prop['type'][3:]) // 8
                properties.append(UdsNumericProperty(name, int(prop['id'], 0), byte_size, True, prop['default'] if 'default' in prop else 0))
            elif prop['type'] == 'bool':
                properties.append(UdsBooleanProperty(name, int(prop['id'], 0), prop['default'] if 'default' in prop else False))
            elif prop['type'] == 'enum':
                properties.append(UdsEnumProperty(name, int(prop['id'], 0), prop['values'], prop['default'] if 'default' in prop else None))

            # TODO: warning for unknown property type

        profile.properties = properties

        return profile
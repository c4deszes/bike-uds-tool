import json
import os

from line_uds.profile import (
    UdsProfile, UdsNumericProperty, UdsBooleanProperty, UdsEnumProperty,
    UdsService, UdsServiceParam
)

def get_int_size(type_str) -> int:
    """Returns the size in bits of the given integer type."""
    if type_str == 'uint8_t' or type_str == 'int8_t':
        return 8
    elif type_str == 'uint16_t' or type_str == 'int16_t':
        return 16
    elif type_str == 'uint32_t' or type_str == 'int32_t':
        return 32
    elif type_str == 'uint64_t' or type_str == 'int64_t':
        return 64
    else:
        raise ValueError(f"Unknown integer type: {type_str}")

def load_profile(profile):
    with open(profile, 'r') as f:
        data = json.load(f)

        profile = UdsProfile()

        services = []
        for name, service in data['services'].items():
            params = []
            for param in service['params']:
                params.append(UdsServiceParam(
                    param['name'],
                    param['type'],
                ))
            svc = UdsService(
                name,
                int(service['id'], 0),
                params,
                service['return']
            )
            services.append(svc)

        profile.services = services

        properties = []
        for (name, prop) in data['properties'].items():
            property_id = int(prop['id'], 0)
            description = prop['description'] if 'description' in prop else ""
            group = prop['group'] if 'group' in prop else "Default"
            if prop['type'] in ['uint8_t', 'uint16_t', 'uint32_t', 'uint64_t']:
                byte_size = get_int_size(prop['type']) // 8
                numeric_prop = UdsNumericProperty(name, property_id, description, group, byte_size, False, prop['default'] if 'default' in prop else 0)
                if 'min' in prop:
                    numeric_prop.min = prop['min']
                if 'max' in prop:
                    numeric_prop.max = prop['max']
                properties.append(numeric_prop)
            elif prop['type'] in ['int8_t', 'int16_t', 'int32_t', 'int64_t']:
                byte_size = get_int_size(prop['type']) // 8
                numeric_prop = UdsNumericProperty(name, property_id, description, group, byte_size, True, prop['default'] if 'default' in prop else 0)
                if 'min' in prop:
                    numeric_prop.min = prop['min']
                if 'max' in prop:
                    numeric_prop.max = prop['max']
                properties.append(numeric_prop)
            elif prop['type'] == 'bool':
                properties.append(UdsBooleanProperty(name, property_id, description, group, prop['default'] if 'default' in prop else False))
            elif prop['type'] == 'enum':
                properties.append(UdsEnumProperty(name, property_id, description, group, prop['values'], prop['default'] if 'default' in prop else None))

            # TODO: warning for unknown property type

        profile.properties = properties

        return profile
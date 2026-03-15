import json
import os

from line_uds.profile import (
    UdsEnumTypeDefinition, UdsProfile, UdsProperty,
    UdsService, UdsServiceParam, UdsTypeDefinition, UdsStructTypeDefinition,
        UdsIntTypeDefinition, UdsBoolTypeDefinition,
    BUILTIN_TYPES
)

def auto_int(x):
    if isinstance(x, int):
        return x
    return int(x, 0)

def lookup_type_definition(type_definitions: list[UdsTypeDefinition], type_name: str) -> UdsTypeDefinition:
    if type_name in BUILTIN_TYPES:
        return BUILTIN_TYPES[type_name]
    for type_def in type_definitions:
        if type_def.name == type_name:
            return type_def
    raise ValueError(f"Type definition not found for type name: {type_name}")

def load_profile(profile):
    with open(profile, 'r') as f:
        data = json.load(f)

        profile = UdsProfile()

        type_definitions = []
        for name, type_def in data['types'].items():
            if type_def['type'] == 'struct':
                members = {}
                for member_name, member in type_def['fields'].items():
                    members[member_name] = lookup_type_definition(type_definitions, member['type'])
                type_definitions.append(UdsStructTypeDefinition(name, members))
            elif type_def['type'] == 'enum':
                type_definitions.append(UdsEnumTypeDefinition(name, type_def['values']))
            else:
                raise ValueError(f"Unknown type definition type: {type_def['type']} for type {name}")
        profile.type_definitions = type_definitions

        services = []
        for name, service in data['services'].items():
            params = []
            for param_name, param in service['params'].items():
                params.append(UdsServiceParam(
                    param_name,
                    lookup_type_definition(type_definitions, param['type']),
                ))
            svc = UdsService(
                name,
                int(service['id'], 0),
                params,
                lookup_type_definition(type_definitions, service['return']) if service['return'] != 'void' else 'void'
            )
            services.append(svc)

        profile.services = services

        properties = []
        for (name, prop) in data['properties'].items():
            property_id = int(prop['id'], 0)
            description = prop['description'] if 'description' in prop else ""
            group = prop['group'] if 'group' in prop else "Default"
            storage_class = prop['storage_class'] if 'storage_class' in prop else "volatile"

            if prop['type'] in BUILTIN_TYPES:
                prop_type = BUILTIN_TYPES[prop['type']]
                property = UdsProperty(name, property_id, description, group, storage_class, prop_type)

                if isinstance(prop_type, UdsIntTypeDefinition):
                    if 'min' in prop:
                        property.min = auto_int(prop['min'])
                    else:
                        property.min = -(2 ** (prop_type.size * 8 - 1)) if prop_type.signed else 0
                    if 'max' in prop:
                        property.max = auto_int(prop['max'])
                    else:
                        property.max = (2 ** (prop_type.size * 8 - 1) - 1) if prop_type.signed else (2 ** (prop_type.size * 8) - 1)
                    property.default_value = auto_int(prop['default']) if 'default' in prop else 0
                elif isinstance(prop_type, UdsBoolTypeDefinition):
                    property.default_value = prop['default'] if 'default' in prop else False

                properties.append(property)
            else:
                prop_type = lookup_type_definition(type_definitions, prop['type'])
                property = UdsProperty(name, property_id, description, group, storage_class, prop_type)

                if isinstance(prop_type, UdsEnumTypeDefinition):
                    property.default_value = prop['default'] if 'default' in prop else prop_type.values[0]
                elif isinstance(prop_type, UdsStructTypeDefinition):
                    # TODO: support for default values of struct properties
                    pass

                properties.append(property)

        profile.properties = properties

        return profile
class UdsTypeDefinition():
    def __init__(self, name: str) -> None:
        self.name = name

    def encode(self, value) -> bytearray:
        raise NotImplementedError()

    def decode(self, data: bytearray) -> any:
        raise NotImplementedError()
    
class UdsVoidTypeDefinition(UdsTypeDefinition):
    def __init__(self, name: str) -> None:
        super().__init__(name)

    def encode(self, value) -> bytearray:
        return bytearray()

    def decode(self, data: bytearray) -> any:
        return None
    
    def get_ctype(self) -> str:
        return 'void'
    
class UdsIntTypeDefinition(UdsTypeDefinition):
    def __init__(self, name: str, size: int, signed: bool) -> None:
        super().__init__(name)
        self.size = size
        self.signed = signed

    def encode(self, value: int) -> bytearray:
        if isinstance(value, str):
            value = int(value)
        return bytearray(value.to_bytes(self.size, 'little', signed=self.signed))

    def decode(self, data: bytearray) -> int:
        return int.from_bytes(data, 'little', signed=self.signed)
    
    def get_ctype(self) -> str:
        if self.signed:
            return f'int{self.size * 8}_t'
        return f'uint{self.size * 8}_t'
    
class UdsBoolTypeDefinition(UdsTypeDefinition):
    def __init__(self, name: str) -> None:
        super().__init__(name)

    def encode(self, value: bool) -> bytearray:
        if value:
            return bytearray([0x01])
        return bytearray([0x00])

    def decode(self, data: bytearray) -> bool:
        if data[0] == 0x00:
            return False
        return True
    
    def get_ctype(self) -> str:
        return 'bool'

class UdsStructTypeDefinition(UdsTypeDefinition):
    def __init__(self, name: str, fields: dict[str, UdsTypeDefinition]) -> None:
        super().__init__(name)
        self.fields = fields

    def encode(self, value) -> bytearray:
        data = bytearray()
        for field_name, field_type in self.fields.items():
            data.extend(field_type.encode(value[field_name]))
        return data

    def decode(self, data: bytearray) -> any:
        value = {}
        offset = 0
        for field_name, field_type in self.fields.items():
            field_value = field_type.decode(data[offset:])
            value[field_name] = field_value
            offset += len(field_type.encode(field_value))
        return value
    
    def get_ctype(self) -> str:
        return f"uds_{self.name}_t"

class UdsEnumTypeDefinition(UdsTypeDefinition):
    def __init__(self, name: str, values: list[str]) -> None:
        super().__init__(name)
        self.values = values

    def encode(self, value) -> bytearray:
        return bytearray([self.values.index(value)])

    def decode(self, data: bytearray) -> any:
        return self.values[data[0]]
    
    def get_ctype(self) -> str:
        return f"uds_{self.name}_t"
    
BUILTIN_TYPES = {
    'uint8_t': UdsIntTypeDefinition('uint8_t', 1, False),
    'uint16_t': UdsIntTypeDefinition('uint16_t', 2, False),
    'uint32_t': UdsIntTypeDefinition('uint32_t', 4, False),
    'uint64_t': UdsIntTypeDefinition('uint64_t', 8, False),
    'int8_t': UdsIntTypeDefinition('int8_t', 1, True),
    'int16_t': UdsIntTypeDefinition('int16_t', 2, True),
    'int32_t': UdsIntTypeDefinition('int32_t', 4, True),
    'int64_t': UdsIntTypeDefinition('int64_t', 8, True),
    'bool': UdsBoolTypeDefinition('bool'),
    'void': UdsVoidTypeDefinition('void')
}

####################

class UdsServiceParam():
    def __init__(self, param_name: str, param_type: UdsTypeDefinition) -> None:
        self.param_name = param_name
        self.param_type = param_type

class UdsService():
    def __init__(self, name: str, service_id: int, description: str, group: str, params: list[UdsServiceParam], return_type: UdsTypeDefinition) -> None:
        self.name = name
        self.service_id = service_id
        self.description = description
        self.group = group
        self.params = params
        self.return_type = return_type

    def encode_parameters(self, param_values: dict[str, any]) -> bytearray:
        data = bytearray()
        for param in self.params:
            value = param_values[param.param_name]
            data.extend(param.param_type.encode(value))
        return data
    
    def decode_return_value(self, data: bytearray) -> any:
        return self.return_type.decode(data)

class UdsProperty():

    def __init__(self, name: str, prop_id: int, description: str, group: str, storage_class: str, typedef: UdsTypeDefinition) -> None:
        self.prop_name = name
        self.prop_id = prop_id
        self.description = description
        self.group = group
        self.storage_class = storage_class
        self.typedef = typedef

    def encode(self, value) -> bytearray:
        return self.typedef.encode(value)

    def decode(self, data: bytearray) -> any:
        return self.typedef.decode(data)

class UdsProfile():

    def __init__(self) -> None:
        self.name = None
        self.channel: int = None
        self.type_definitions: list[UdsTypeDefinition] = []
        self.services: list[UdsService] = []
        self.properties: list[UdsProperty] = []

    def get_property(self, prop_name) -> UdsProperty:
        for prop in self.properties:
            if prop.prop_name == prop_name or prop.prop_id == prop_name:
                return prop
        raise LookupError(f"Property {prop_name} not found")
    
    def get_property_groups(self) -> list[str]:
        groups = set()
        for prop in self.properties:
            groups.add(prop.group)
        return list(groups)

    def get_properties_by_group(self, group_name) -> list[UdsProperty]:
        return [prop for prop in self.properties if prop.group == group_name]

    def get_service(self, service_name) -> UdsService:
        for service in self.services:
            if service.service_name == service_name or service.service_id == service_name:
                return service
        raise LookupError(f"Service {service_name} not found")
    
    def get_service_groups(self) -> list[str]:
        groups = set()
        for service in self.services:
            groups.add(service.group)
        return list(groups)
    
    def get_services_by_group(self, group_name) -> list[UdsService]:
        return [service for service in self.services if service.group == group_name]

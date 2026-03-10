class UdsServiceParam():
    def __init__(self, param_name: str, param_type: str) -> None:
        self.param_name = param_name
        self.param_type = param_type

class UdsService():
    def __init__(self, name: str, service_id: int, params: list[UdsServiceParam], return_type: str) -> None:
        self.name = name
        self.service_id = service_id
        self.params = params
        self.return_type = return_type

class UdsProperty():

    def __init__(self, name: str, prop_id: int, description: str = "", group: str = "Default") -> None:
        self.prop_name = name
        self.prop_id = prop_id
        self.description = description
        self.group = group

    def encode(self, value) -> bytearray:
        raise NotImplementedError()

    def decode(self, data: bytearray) -> any:
        raise NotImplementedError()

class UdsNumericProperty(UdsProperty):

    def __init__(self, name, prop_id, description, group, size, signed, default: int=0) -> None:
        super().__init__(name, prop_id, description, group)
        self.size = size
        self.signed = signed
        self.default_value = default
        self.min = -(2 ** (self.size * 8 - 1)) if self.signed else 0
        self.max = (2 ** (self.size * 8 - 1)) - 1 if self.signed else (2 ** (self.size * 8)) - 1

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

class UdsBooleanProperty(UdsProperty):

    def __init__(self, name, prop_id, description="", group="Default", default=False) -> None:
        super().__init__(name, prop_id, description, group)
        self.default_value = default

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

class UdsEnumProperty(UdsProperty):

    def __init__(self, name, prop_id, description="", group="Default", values=None, default=None) -> None:
        super().__init__(name, prop_id, description, group)
        self.values = values if values is not None else []
        self.default_value = default

    def encode(self, value) -> bytearray:
        # todo: error handling (value not in values)
        return bytearray([self.values.index(value)])

    def decode(self, data: bytearray) -> any:
        # todo: error handling (index out of range)
        return self.values[data[0]]

    def get_ctype(self) -> str:
        return 'uint8_t'

class UdsProfile():

    def __init__(self) -> None:
        self.name = None
        self.channel: int = None
        self.services = []
        self.properties: list[UdsProperty] = []

    def get_property(self, prop_name) -> UdsProperty:
        for prop in self.properties:
            if prop.prop_name == prop_name or prop.prop_id == prop_name:
                return prop
        raise LookupError(f"Property {prop_name} not found")

    def get_service(self, service_name) -> UdsService:
        for service in self.services:
            if service.service_name == service_name or service.service_id == service_name:
                return service
        raise LookupError(f"Service {service_name} not found")

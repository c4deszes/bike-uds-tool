

class UdsProperty():

    def __init__(self, name: str, prop_id: int) -> None:
        self.prop_name = name
        self.prop_id = prop_id

    def encode(self, value) -> bytearray:
        raise NotImplementedError()

    def decode(self, data: bytearray) -> any:
        raise NotImplementedError()

class UdsNumericProperty(UdsProperty):

    def __init__(self, name, prop_id, size, signed) -> None:
        super().__init__(name, prop_id)
        self.size = size
        self.signed = signed

    def encode(self, value: int) -> bytearray:
        return bytearray(value.to_bytes(self.size, 'little', signed=self.signed))

    def decode(self, data: bytearray) -> int:
        return int.from_bytes(data, 'little', signed=self.signed)

    def get_ctype(self) -> str:
        if self.signed:
            return f'int{self.size * 8}_t'
        return f'uint{self.size * 8}_t'

class UdsBooleanProperty(UdsProperty):

    def __init__(self, name, prop_id) -> None:
        super().__init__(name, prop_id)

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

    def __init__(self, name, prop_id, values) -> None:
        super().__init__(name, prop_id)
        self.values = values

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
        self.services = []
        self.properties = []

    def get_property(self, prop_name) -> UdsProperty:
        for prop in self.properties:
            if prop.prop_name == prop_name or prop.prop_id == prop_name:
                return prop
        raise LookupError(f"Property {prop_name} not found")

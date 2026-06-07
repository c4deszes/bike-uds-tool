from line_protocol.protocol.simulation import SimulatedDiagnosticExtension
from line_uds.profile import UdsProfile
from line_uds.constants import *

class UdsExtensionPropertyListener():
    pass

class UdsExtensionListener():

    def on_property_change(self, property_id: int, buffer: bytearray, value: any) -> None:
        pass

    def on_service_call(self, service_id: int, buffer: list[int], request: any) -> None:
        pass

class SimulatedUdsExtension(SimulatedDiagnosticExtension):

    def __init__(self, profile: UdsProfile):
        super().__init__()
        self.profile = profile
        self.properties = {}
        self.subscriber(UDS_PROPERTY_GET_CALL_REQUEST_ID, self.uds_get_request)
        self.publisher(UDS_PROPERTY_GET_RETURN_REQUEST_ID, self.uds_get_response)

        self.subscriber(UDS_PROPERTY_SET_CALL_REQUEST_ID, self.uds_set_request)
        self.publisher(UDS_PROPERTY_SET_RETURN_REQUEST_ID, self.uds_set_response)

        self.subscriber(UDS_SERVICE_CALL_REQUEST_ID, self.uds_call_service)
        self.publisher(UDS_SERVICE_RETURN_REQUEST_ID, self.uds_call_response)

        self._get_property_id = None
        self._set_property_id = None
        self._set_property_status = None
        self._service_id = None
        self._service_data = None
        self._service_status = None
        self._service_response_data = None

        self.reset_properties()

        self.listener: UdsExtensionListener = None

    def reset_properties(self) -> None:
        self.properties = {}
        for prop in self.profile.properties:
            self.properties[prop.prop_id] = prop.default_value

    @staticmethod
    def _create_response(property_id: int, data: list[int]) -> list[int]:
        response = [(property_id >> 8) & 0xFF, property_id & 0xFF]
        response.extend(data)
        return response

    def uds_get_request(self, data: list[int]) -> None:
        self._get_property_id = (data[0] << 8) | data[1]

    def uds_get_response(self) -> list[int]:
        if self._get_property_id is None:
            return SimulatedUdsExtension._create_response(0x0000 | UDS_PROPERTY_STATUS_MASK, [UDS_PROPERTY_GET_RETURN_NO_REQUEST])
        elif self._get_property_id in self.properties:
            value = self.properties[self._get_property_id]
            prop = self.profile.get_property(self._get_property_id)
            encoded_value = prop.encode(value)
            response = SimulatedUdsExtension._create_response(self._get_property_id, list(encoded_value))
            self._get_property_id = None
            return response
        else:
            response = SimulatedUdsExtension._create_response(self._get_property_id | UDS_PROPERTY_STATUS_MASK, [UDS_PROPERTY_GET_RETURN_NO_SUCH_PROPERTY])
            self._get_property_id = None
            return response

    def uds_set_request(self, data: list[int]) -> None:
        property_id = (data[0] << 8) | data[1]
        if property_id in self.properties:
            prop = self.profile.get_property(property_id)
            value_data = bytearray(data[2:])
            value = prop.decode(value_data)
            self.properties[property_id] = value

            if self.listener is not None:
                self.listener.on_property_change(property_id, value_data, value)

            self._set_property_id = property_id
            self._set_property_status = UDS_PROPERTY_SET_RETURN_SUCCESS
        else:
            self._set_property_id = property_id
            self._set_property_status = UDS_PROPERTY_SET_RETURN_NO_SUCH_PROPERTY

    def uds_set_response(self) -> list[int]:
        if self._set_property_id is None:
            return SimulatedUdsExtension._create_response(0x0000 | UDS_PROPERTY_STATUS_MASK, [UDS_PROPERTY_SET_RETURN_NO_REQUEST])
        else:
            response = SimulatedUdsExtension._create_response(self._set_property_id, [self._set_property_status])
            self._set_property_id = None
            self._set_property_status = None
            return response

    def has_pending_service_call(self) -> bool:
        return self._service_id is not None
    
    def get_pending_service_call(self) -> tuple[int, list[int]] | None:
        if self._service_id is not None:
            return self._service_id, self._service_data
        else:
            return None

    def set_service_call_response(self, response_data: list[int]) -> None:
        if self._service_id is not None:
            self._service_response_data = response_data

    def finish_service_call(self, status: int) -> None:
        if self._service_id is not None:
            self._service_status = status

    def uds_call_service(self, data: list[int]) -> None:
        if self._service_id is not None:
            # Previous service call still pending, ignore new request
            return
        self._service_id = (data[0] << 8) | data[1]

        try:
            self.profile.get_service(self._service_id)  # Validate service ID

            self._service_data = data[2:] if len(data) > 2 else []
            self._service_status = UDS_SERVICE_CALL_NOT_READY
            self._service_response_data = []
        except LookupError:
            self._service_status = UDS_SERVICE_CALL_NO_SUCH_SERVICE

    def uds_call_response(self) -> list[int]:
        if self._service_id is None:
            return SimulatedUdsExtension._create_response(0x0000, [UDS_SERVICE_CALL_NO_REQUEST])

        if self._service_status == UDS_SERVICE_CALL_NOT_READY:
            response = SimulatedUdsExtension._create_response(self._service_id, [UDS_SERVICE_CALL_NOT_READY])
            return response
        elif self._service_status == UDS_SERVICE_CALL_SUCCESS:
            response = SimulatedUdsExtension._create_response(self._service_id, [UDS_SERVICE_CALL_SUCCESS] + self._service_response_data)
            self._service_id = None
            self._service_data = None
            self._service_status = None
            self._service_response_data = None
            return response
        else:
            response = SimulatedUdsExtension._create_response(self._service_id, [self._service_status])
            self._service_id = None
            self._service_data = None
            self._service_status = None
            self._service_response_data = None
            return response

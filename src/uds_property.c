#include "uds_diag.h"
#include "uds_api.h"

#include <stdbool.h>
#include <stdint.h>

static bool UDS_GetProperty_RequestReceived = false;
static bool UDS_GetProperty_ResponseSet = false;
static uint16_t UDS_GetProperty_PropertyId = UDS_PROPERTY_ID_RESERVED;
static uint8_t UDS_GetProperty_Status = UDS_PROPERTY_GET_RETURN_NOT_READY;
static uint8_t UDS_GetProperty_ResponseSize = 0;
static uint8_t UDS_GetProperty_Response[32];

void UDS_EnqueueGetPropertyResponse(uint16_t property_id, uint8_t size, uint8_t* response) {
    UDS_GetProperty_PropertyId = property_id;
    UDS_GetProperty_ResponseSize = size;
    for (int i = 0; i < size; i++) {
        UDS_GetProperty_Response[i] = response[i];
    }
    UDS_GetProperty_Status = UDS_PROPERTY_GET_RETURN_PREPARED;
    UDS_GetProperty_ResponseSet = true;
}

void UDS_EnqueueGetPropertyError(uint16_t property_id, uint8_t error_code) {
    UDS_GetProperty_PropertyId = property_id;
    UDS_GetProperty_Status = error_code;
    UDS_GetProperty_ResponseSet = true;
}

static void UDS_ResetGetPropertyResponse() {
    UDS_GetProperty_ResponseSet = false;
    UDS_GetProperty_PropertyId = UDS_PROPERTY_ID_RESERVED;
    UDS_GetProperty_Status = UDS_PROPERTY_GET_RETURN_NOT_READY;
}

void UDS_LINE_GetCallHandler(uint16_t request, uint8_t size, uint8_t* payload) {
    UDS_GetProperty_RequestReceived = true;

    if (size == 2) {
        uint16_t property_id = (((uint16_t)payload[0]) << 8) | payload[1];
        UDS_OnGetProperty(property_id);
    }
    else {
        UDS_EnqueueGetPropertyError(UDS_PROPERTY_ID_RESERVED, UDS_PROPERTY_GET_RETURN_BAD_REQUEST);
    }
}

bool UDS_LINE_GetReturnHandler(uint16_t request, uint8_t* size, uint8_t* payload) {
    if (UDS_GetProperty_ResponseSet) {
        if (UDS_GetProperty_Status == UDS_PROPERTY_GET_RETURN_PREPARED) {
            // respond with prepared data
            payload[0] = (UDS_GetProperty_PropertyId >> 8) & 0xFF;
            payload[1] = UDS_GetProperty_PropertyId & 0xFF;
            for (int i = 0; i < UDS_GetProperty_ResponseSize; i++) {
                payload[2 + i] = UDS_GetProperty_Response[i];
            }
            *size = 2 + UDS_GetProperty_ResponseSize;

            UDS_ResetGetPropertyResponse();
            return true;
        }
        else {
            payload[0] = (UDS_GetProperty_PropertyId >> 8) & 0xFF | 0x80;
            payload[1] = UDS_GetProperty_PropertyId & 0xFF;
            payload[2] = UDS_GetProperty_Status;
            *size = 3;

            UDS_ResetGetPropertyResponse();
            return true;
        }
    }
    else {
        if (UDS_GetProperty_RequestReceived) {
            payload[0] = (UDS_GetProperty_PropertyId >> 8) & 0xFF | 0x80;
            payload[1] = UDS_GetProperty_PropertyId & 0xFF;
            payload[2] = UDS_PROPERTY_GET_RETURN_NOT_READY;
            *size = 3;
            return true;
        }
        else {
            payload[0] = (UDS_GetProperty_PropertyId >> 8) & 0xFF | 0x80;
            payload[1] = UDS_GetProperty_PropertyId & 0xFF;
            payload[2] = UDS_PROPERTY_GET_RETURN_NO_REQUEST;
            *size = 3;
            return true;
        }
    }
    // should never reach here
    return false;
}

// TODO: later change this to an actual queue
static bool UDS_SetProperty_RequestReceived = false;
static bool UDS_SetProperty_ResponseSet = false;
static uint16_t UDS_SetProperty_PropertyId = UDS_PROPERTY_ID_RESERVED;
static uint8_t UDS_SetProperty_Status = UDS_PROPERTY_SET_RETURN_NO_REQUEST;

void UDS_EnqueueSetPropertyResponse(uint16_t property_id, uint8_t status) {
    UDS_SetProperty_PropertyId = property_id;
    UDS_SetProperty_Status = status;
    UDS_SetProperty_ResponseSet = true;
}

void UDS_ResetSetPropertyResponse() {
    UDS_SetProperty_ResponseSet = false;
    UDS_SetProperty_PropertyId = UDS_PROPERTY_ID_RESERVED;
    UDS_SetProperty_Status = UDS_PROPERTY_SET_RETURN_NO_REQUEST;
}

void UDS_LINE_SetCallHandler(uint16_t request, uint8_t size, uint8_t* payload) {
    UDS_SetProperty_RequestReceived = true;
    if (size >= 3) {
        uint16_t property_id = (((uint16_t)payload[0]) << 8) | payload[1];
        UDS_SetProperty_PropertyId = property_id;
        UDS_OnSetProperty(property_id, size - 2, payload + 2);
    }
    else {
        UDS_EnqueueSetPropertyResponse(UDS_PROPERTY_ID_RESERVED, UDS_PROPERTY_SET_RETURN_BAD_REQUEST);
    }
}

bool UDS_LINE_SetReturnHandler(uint16_t request, uint8_t* size, uint8_t* payload) {
    if (UDS_SetProperty_ResponseSet) {
        payload[0] = (UDS_SetProperty_PropertyId >> 8) & 0xFF | 0x80;
        payload[1] = UDS_SetProperty_PropertyId & 0xFF;
        payload[2] = UDS_SetProperty_Status;
        *size = 3;

        UDS_SetProperty_RequestReceived = false;
        UDS_ResetSetPropertyResponse();
        return true;
    }
    else {
        if (UDS_SetProperty_RequestReceived) {
            payload[0] = (UDS_SetProperty_PropertyId >> 8) & 0xFF | 0x80;
            payload[1] = UDS_SetProperty_PropertyId & 0xFF;
            payload[2] = UDS_PROPERTY_SET_RETURN_NOT_READY;
            *size = 3;
            return true;
        }
        else {
            payload[0] = (UDS_SetProperty_PropertyId >> 8) & 0xFF | 0x80;
            payload[1] = UDS_SetProperty_PropertyId & 0xFF;
            payload[2] = UDS_PROPERTY_SET_RETURN_NO_REQUEST;
            *size = 3;
            return true;
        }
    }
    return false;
}
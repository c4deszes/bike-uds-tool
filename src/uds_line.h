#if !defined(UDS_LINE_H_)
#define UDS_LINE_H_

#include <stdint.h>
#include <stdbool.h>

void UDS_LINE_GetCallHandler(uint16_t request, uint8_t size, uint8_t* payload);

bool UDS_LINE_GetReturnHandler(uint16_t request, uint8_t* size, uint8_t* payload);

void UDS_EnqueueGetPropertyResponse(uint16_t property_id, uint8_t size, uint8_t* response);

void UDS_EnqueueGetPropertyError(uint16_t property_id, uint8_t error_code);



void UDS_LINE_SetCallHandler(uint16_t request, uint8_t size, uint8_t* payload);

bool UDS_LINE_SetReturnHandler(uint16_t request, uint8_t* size, uint8_t* payload);

void UDS_EnqueueSetPropertyResponse(uint16_t property_id, uint8_t status);

#endif // UDS_LINE_H_

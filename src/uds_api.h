#if !defined(UDS_API_H_)
#define UDS_API_H_

#include <stdint.h>

void UDS_Init();

void UDS_LINE_Init();

// Generated code interfaces
void UDS_OnSetProperty(uint16_t property_id, uint8_t size, uint8_t* data);

/**
 * @brief Called when a property read is requested, this function shall prepare the response to the
 *        request, by calling 
 * 
 * @param property_id 
 * @param size 
 * @param data 
 * @return true 
 * @return false 
 */
void UDS_OnGetProperty(uint16_t property_id);

void UDS_OnServiceCall(uint16_t service_id, uint8_t size, uint8_t* data);

#endif // UDS_API_H_

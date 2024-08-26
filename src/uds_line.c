
#include "uds_diag.h"
#include "uds_line.h"

#include "line_diagnostics.h"

void UDS_LINE_Init() {
    // LINE_Diag_RegisterUnicastListener(UDS_SERVICE_CALL_REQUEST_ID, _FLASH_LINE_OnPageWriteHandler);
    // LINE_Diag_RegisterUnicastPublisher(UDS_SERVICE_RETURN_REQUEST_ID, _FLASH_LINE_GetWriteStatusHandler);

    LINE_Diag_RegisterUnicastListener(UDS_PROPERTY_GET_CALL_REQUEST_ID, UDS_LINE_GetCallHandler);
    LINE_Diag_RegisterUnicastPublisher(UDS_PROPERTY_GET_RETURN_REQUEST_ID, UDS_LINE_GetReturnHandler);

    LINE_Diag_RegisterUnicastListener(UDS_PROPERTY_SET_CALL_REQUEST_ID, UDS_LINE_SetCallHandler);
    LINE_Diag_RegisterUnicastPublisher(UDS_PROPERTY_SET_RETURN_REQUEST_ID, UDS_LINE_SetReturnHandler);
}

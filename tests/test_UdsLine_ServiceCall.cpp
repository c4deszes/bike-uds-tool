#include "gtest/gtest.h"
#include "fff.h"

extern "C" {
    #include "uds_diag.h"
    #include "uds_gen.h"

    #include "line_protocol.h"
    #include "line_tester.h"
}

DEFINE_FFF_GLOBALS;

// Diagnostic callbacks
FAKE_VALUE_FUNC0(uint32_t, LINE_Diag_GetSerialNumber);
FAKE_VALUE_FUNC0(LINE_Diag_SoftwareVersion_t*, LINE_Diag_GetSoftwareVersion);
FAKE_VALUE_FUNC0(LINE_Diag_PowerStatus_t*, LINE_Diag_GetPowerStatus);
FAKE_VALUE_FUNC0(uint8_t, LINE_Diag_GetOperationStatus);

// Transport callbacks
FAKE_VOID_FUNC4(LINE_Transport_OnError, uint8_t, bool, uint16_t, line_transport_error);
FAKE_VOID_FUNC4(LINE_Transport_WriteResponse, uint8_t, uint8_t, uint8_t*, uint8_t);
FAKE_VOID_FUNC2(LINE_Transport_WriteRequest, uint8_t, uint16_t);

// Adapters to enable diagnostics over the transport layer
bool LINE_Transport_RespondsTo(uint8_t channel, uint16_t request) {
    return LINE_Diag_RespondsTo(channel, request);
}

bool LINE_Transport_PrepareResponse(uint8_t channel, uint16_t request, uint8_t* size, uint8_t* payload) {
    return LINE_Diag_PrepareResponse(channel, request, size, payload);
}

void LINE_Transport_OnData(uint8_t channel, bool response, uint16_t request, uint8_t size, uint8_t* payload) {
    if (!response) {
        LINE_Diag_OnRequest(channel, request, size, payload);
    }
}

#define UINT16_L(x) ((uint8_t)(x & 0xFF))
#define UINT16_H(x) ((uint8_t)((x >> 8) & 0xFF))

#define TEST_NODE_ADDRESS 0x5

LINE_Diag_Config_t diag_config = {
    .transport_channel = 0,
    .address = TEST_NODE_ADDRESS,
    .op_status = LINE_Diag_GetOperationStatus,
    .power_status = LINE_Diag_GetPowerStatus,
    .serial_number = LINE_Diag_GetSerialNumber,
    .software_version = LINE_Diag_GetSoftwareVersion
};

class TestUdsLineServices : public testing::Test {
public:
    static void SetUpTestSuite() {
        LINE_Transport_Init(0, false);
        LINE_Diag_Init(0, &diag_config);
        UDS_Init();
    }
protected:
    void SetUp() override {
        
    }
};

FAKE_VOID_FUNC2(UDS_FrontLight_VoidWithParams_OnServiceRequest, 
                UDS_Service_FrontLight_VoidWithParams_RequestContext_t*,
                UDS_Service_FrontLight_VoidWithParams_ResponseContext_t*);
FAKE_VOID_FUNC2(UDS_FrontLight_IntegerNoParams_OnServiceRequest, 
                UDS_Service_FrontLight_IntegerNoParams_RequestContext_t*,
                UDS_Service_FrontLight_IntegerNoParams_ResponseContext_t*);
FAKE_VOID_FUNC2(UDS_FrontLight_IntegerWithParams_OnServiceRequest, 
                UDS_Service_FrontLight_IntegerWithParams_RequestContext_t*,
                UDS_Service_FrontLight_IntegerWithParams_ResponseContext_t*);
FAKE_VOID_FUNC2(UDS_FrontLight_BooleanWithParams_OnServiceRequest, 
                UDS_Service_FrontLight_BooleanWithParams_RequestContext_t*,
                UDS_Service_FrontLight_BooleanWithParams_ResponseContext_t*);
FAKE_VOID_FUNC2(UDS_FrontLight_VoidNoParams_OnServiceRequest, 
                UDS_Service_FrontLight_VoidNoParams_RequestContext_t*,
                UDS_Service_FrontLight_VoidNoParams_ResponseContext_t*);

TEST_F(TestUdsLineServices, Call_UnknownService)
{
    BUILD_FRAME(request, UDS_SERVICE_CALL_REQUEST_ID | TEST_NODE_ADDRESS, 0x40, 0x00);
    for (int i = 0; i < sizeof(request); i++) {
        LINE_Transport_Receive(0, request[i]);
    }

    BUILD_REQUEST(response, UDS_SERVICE_RETURN_REQUEST_ID | TEST_NODE_ADDRESS);
    for (int i = 0; i < sizeof(response); i++) {
        LINE_Transport_Receive(0, response[i]);
    }

    EXPECT_EQ(LINE_Transport_WriteResponse_fake.call_count, 1);
    EXPECT_EQ(LINE_Transport_WriteResponse_fake.arg0_val, 0);
    EXPECT_EQ(LINE_Transport_WriteResponse_fake.arg1_val, 3);
    EXPECT_EQ(LINE_Transport_WriteResponse_fake.arg2_val[0], 0x40);
    EXPECT_EQ(LINE_Transport_WriteResponse_fake.arg2_val[1], 0x00);
    EXPECT_EQ(LINE_Transport_WriteResponse_fake.arg2_val[2], UDS_SERVICE_CALL_NO_SUCH_SERVICE);
}

TEST_F(TestUdsLineServices, Call_VoidNoParams_Invalid)
{
    BUILD_FRAME(request,
                UDS_SERVICE_CALL_REQUEST_ID | TEST_NODE_ADDRESS,
                UINT16_H(UDS_SERVICE_FrontLight_VoidNoParams_ID),
                UINT16_L(UDS_SERVICE_FrontLight_VoidNoParams_ID),
                0x00);
    for (int i = 0; i < sizeof(request); i++) {
        LINE_Transport_Receive(0, request[i]);
    }

    BUILD_REQUEST(response, UDS_SERVICE_RETURN_REQUEST_ID | TEST_NODE_ADDRESS);
    for (int i = 0; i < sizeof(response); i++) {
        LINE_Transport_Receive(0, response[i]);
    }

    EXPECT_EQ(LINE_Transport_WriteResponse_fake.call_count, 1);
    EXPECT_EQ(LINE_Transport_WriteResponse_fake.arg0_val, 0);
    EXPECT_EQ(LINE_Transport_WriteResponse_fake.arg1_val, 3);
    EXPECT_EQ(LINE_Transport_WriteResponse_fake.arg2_val[0], UINT16_H(UDS_SERVICE_FrontLight_VoidNoParams_ID));
    EXPECT_EQ(LINE_Transport_WriteResponse_fake.arg2_val[1], UINT16_L(UDS_SERVICE_FrontLight_VoidNoParams_ID));
    EXPECT_EQ(LINE_Transport_WriteResponse_fake.arg2_val[2], UDS_SERVICE_CALL_BAD_REQUEST);
}

TEST_F(TestUdsLineServices, Call_VoidNoParams_Success)
{
    /* Service call */
    BUILD_FRAME(request,
                UDS_SERVICE_CALL_REQUEST_ID | TEST_NODE_ADDRESS,
                UINT16_H(UDS_SERVICE_FrontLight_VoidNoParams_ID),
                UINT16_L(UDS_SERVICE_FrontLight_VoidNoParams_ID));
    for (int i = 0; i < sizeof(request); i++) {
        LINE_Transport_Receive(0, request[i]);
    }
    EXPECT_EQ(UDS_FrontLight_VoidNoParams_OnServiceRequest_fake.call_count, 1);

    /* Response */
    BUILD_REQUEST(response_1, UDS_SERVICE_RETURN_REQUEST_ID | TEST_NODE_ADDRESS);
    for (int i = 0; i < sizeof(response_1); i++) {
        LINE_Transport_Receive(0, response_1[i]);
    }

    EXPECT_EQ(LINE_Transport_WriteResponse_fake.call_count, 1);
    EXPECT_EQ(LINE_Transport_WriteResponse_fake.arg0_val, 0);
    EXPECT_EQ(LINE_Transport_WriteResponse_fake.arg1_val, 3);
    EXPECT_EQ(LINE_Transport_WriteResponse_fake.arg2_val[0], UINT16_H(UDS_SERVICE_FrontLight_VoidNoParams_ID));
    EXPECT_EQ(LINE_Transport_WriteResponse_fake.arg2_val[1], UINT16_L(UDS_SERVICE_FrontLight_VoidNoParams_ID));
    EXPECT_EQ(LINE_Transport_WriteResponse_fake.arg2_val[2], UDS_SERVICE_CALL_NOT_READY);

    /* Finish service */
    UDS_FrontLight_VoidNoParams_FinishServiceRequest(UDS_SERVICE_CALL_SUCCESS);

    /* Response */
    BUILD_REQUEST(response_2, UDS_SERVICE_RETURN_REQUEST_ID | TEST_NODE_ADDRESS);
    for (int i = 0; i < sizeof(response_2); i++) {
        LINE_Transport_Receive(0, response_2[i]);
    }

    EXPECT_EQ(LINE_Transport_WriteResponse_fake.call_count, 2);
    EXPECT_EQ(LINE_Transport_WriteResponse_fake.arg0_val, 0);
    EXPECT_EQ(LINE_Transport_WriteResponse_fake.arg1_val, 3);
    EXPECT_EQ(LINE_Transport_WriteResponse_fake.arg2_val[0], UINT16_H(UDS_SERVICE_FrontLight_VoidNoParams_ID));
    EXPECT_EQ(LINE_Transport_WriteResponse_fake.arg2_val[1], UINT16_L(UDS_SERVICE_FrontLight_VoidNoParams_ID));
    EXPECT_EQ(LINE_Transport_WriteResponse_fake.arg2_val[2], UDS_SERVICE_CALL_SUCCESS);
}

int main(int argc, char **argv) {
    ::testing::InitGoogleTest(&argc, argv);
    return RUN_ALL_TESTS();
}

#include "gtest/gtest.h"
#include "fff.h"

extern "C" {
    #include "uds_api.h"
    #include "uds_diag.h"

    #include "uds_line.h"

    #include "line_protocol.h"
}

DEFINE_FFF_GLOBALS;

FAKE_VALUE_FUNC0(uint32_t, LINE_Diag_GetSerialNumber);
FAKE_VALUE_FUNC0(LINE_Diag_SoftwareVersion_t*, LINE_Diag_GetSoftwareVersion);
FAKE_VALUE_FUNC0(LINE_Diag_PowerStatus_t*, LINE_Diag_GetPowerStatus);
FAKE_VALUE_FUNC0(uint8_t, LINE_Diag_GetOperationStatus);

FAKE_VOID_FUNC3(LINE_Transport_OnError, bool, uint16_t, line_transport_error);
FAKE_VOID_FUNC3(LINE_Transport_WriteResponse, uint8_t, uint8_t*, uint8_t);
FAKE_VOID_FUNC1(LINE_Transport_WriteRequest, uint16_t);

FAKE_VOID_FUNC1(UDS_OnGetProperty, uint16_t);
FAKE_VOID_FUNC3(UDS_OnSetProperty, uint16_t, uint8_t, uint8_t*);

#define TEST_NODE_ADDRESS 0x5

class TestUdsLineProperties : public testing::Test {
public:
    static void SetUpTestSuite() {
        LINE_Transport_Init(false);
        LINE_Diag_Init();
        LINE_Diag_SetAddress(0x5);
        UDS_LINE_Init();
    }
protected:
    void SetUp() override {
        RESET_FAKE(LINE_Diag_GetSerialNumber);
        RESET_FAKE(LINE_Diag_GetSoftwareVersion);
        RESET_FAKE(LINE_Diag_GetPowerStatus);
        RESET_FAKE(LINE_Diag_GetOperationStatus);

        RESET_FAKE(LINE_Transport_OnError);
        RESET_FAKE(LINE_Transport_WriteResponse);
        RESET_FAKE(LINE_Transport_WriteRequest);

        RESET_FAKE(UDS_OnGetProperty);
        RESET_FAKE(UDS_OnSetProperty);
    }
};

static uint16_t request_code(uint16_t data) {
    uint8_t parity1 = 0;
    uint16_t tempData = data;
    // TODO: potentially wrong result if data goes outside of the 14bit range
    while (tempData != 0) {
        parity1 ^= (tempData & 1);
        tempData >>= 1;
    }

    uint8_t parity2 = 0;
    tempData = data;
    for (int i = 0; i < 6; i++) {
        parity2 ^= (tempData & 1);
        tempData >>= 2;
    }

    return (((parity1 << 1) | parity2) << LINE_REQUEST_PARITY_POS) | data;
}

uint8_t calculate_checksum(uint8_t* data, size_t size) {
    uint8_t checksum = size;
    for (int i = 0; i < size; i++) {
        checksum += data[i];
    }
    checksum += 0xA3;
    return checksum;
}

#define BUILD_FRAME(array, id, ...) \
    uint8_t array##_frame[] = {__VA_ARGS__}; \
    uint8_t array##_size = sizeof(array##_frame); \
    uint16_t array##_req_code = request_code(id); \
    uint8_t array[] = { \
        0x55, \
        (uint8_t)((array##_req_code >> 8) & 0xFF), \
        (uint8_t)(array##_req_code & 0xFF), \
        array##_size, \
        __VA_ARGS__, \
        calculate_checksum(array##_frame, array##_size) \
    };

#define BUILD_REQUEST(array, id) \
    uint16_t array##_req_code = request_code(id); \
    uint8_t array[] = { \
        0x55, \
        (uint8_t)((array##_req_code >> 8) & 0xFF), \
        (uint8_t)(array##_req_code & 0xFF) \
    };

TEST_F(TestUdsLineProperties, SetPropertyRequest) {
    BUILD_FRAME(data, UDS_PROPERTY_SET_CALL_REQUEST_ID | TEST_NODE_ADDRESS, 0x40, 0x00, 0x00, 0x01, 0x02, 0x03);
    for (int i = 0; i < sizeof(data); i++) {
        LINE_Transport_Receive(data[i]);
    }

    EXPECT_EQ(UDS_OnSetProperty_fake.call_count, 1);
    EXPECT_EQ(UDS_OnSetProperty_fake.arg0_val, 0x4000);
    EXPECT_EQ(UDS_OnSetProperty_fake.arg1_val, 4);
    EXPECT_EQ(UDS_OnSetProperty_fake.arg2_val[0], 0x0);
    EXPECT_EQ(UDS_OnSetProperty_fake.arg2_val[1], 0x1);
    EXPECT_EQ(UDS_OnSetProperty_fake.arg2_val[2], 0x2);
    EXPECT_EQ(UDS_OnSetProperty_fake.arg2_val[3], 0x3);
}

TEST_F(TestUdsLineProperties, SetPropertyResponse_NoRequest) {
    BUILD_REQUEST(data, UDS_PROPERTY_SET_RETURN_REQUEST_ID | TEST_NODE_ADDRESS);
    for (int i = 0; i < sizeof(data); i++) {
        LINE_Transport_Receive(data[i]);
    }

    EXPECT_EQ(LINE_Transport_WriteResponse_fake.arg0_val, 3);
    EXPECT_EQ(LINE_Transport_WriteResponse_fake.arg1_val[2], UDS_PROPERTY_GET_RETURN_NO_REQUEST);
}

TEST_F(TestUdsLineProperties, SetPropertyResponse_NotReady) {
    UDS_OnSetProperty_fake.custom_fake = [](uint16_t property_id, uint8_t size, uint8_t* data) {
        UDS_EnqueueSetPropertyResponse(property_id, UDS_PROPERTY_SET_RETURN_NOT_READY);
    };

    BUILD_FRAME(request, UDS_PROPERTY_SET_CALL_REQUEST_ID | TEST_NODE_ADDRESS, 0x40, 0x00, 0x00, 0x01, 0x02, 0x03);
    for (int i = 0; i < sizeof(request); i++) {
        LINE_Transport_Receive(request[i]);
    }

    BUILD_REQUEST(response, UDS_PROPERTY_SET_RETURN_REQUEST_ID | TEST_NODE_ADDRESS);
    for (int i = 0; i < sizeof(response); i++) {
        LINE_Transport_Receive(response[i]);
    }

    EXPECT_EQ(UDS_OnSetProperty_fake.call_count, 1);
    EXPECT_EQ(UDS_OnSetProperty_fake.arg0_val, 0x4000);

    EXPECT_EQ(LINE_Transport_WriteResponse_fake.arg0_val, 3);
    EXPECT_EQ(LINE_Transport_WriteResponse_fake.arg1_val[0], 0x40 | 0x80);
    EXPECT_EQ(LINE_Transport_WriteResponse_fake.arg1_val[1], 0x00);
    EXPECT_EQ(LINE_Transport_WriteResponse_fake.arg1_val[2], UDS_PROPERTY_SET_RETURN_NOT_READY);
}

TEST_F(TestUdsLineProperties, SetPropertyResponse_ErrorResponse) {
    UDS_OnSetProperty_fake.custom_fake = [](uint16_t property_id, uint8_t size, uint8_t* data) {
        UDS_EnqueueSetPropertyResponse(property_id, UDS_PROPERTY_GET_RETURN_NO_SUCH_PROPERTY);
    };

    BUILD_FRAME(request, UDS_PROPERTY_SET_CALL_REQUEST_ID | TEST_NODE_ADDRESS, 0x40, 0x00, 0x00, 0x01, 0x02, 0x03);
    for (int i = 0; i < sizeof(request); i++) {
        LINE_Transport_Receive(request[i]);
    }

    BUILD_REQUEST(response, UDS_PROPERTY_SET_RETURN_REQUEST_ID | TEST_NODE_ADDRESS);
    for (int i = 0; i < sizeof(response); i++) {
        LINE_Transport_Receive(response[i]);
    }

    EXPECT_EQ(UDS_OnSetProperty_fake.call_count, 1);
    EXPECT_EQ(UDS_OnSetProperty_fake.arg0_val, 0x4000);

    EXPECT_EQ(LINE_Transport_WriteResponse_fake.arg0_val, 3);
    EXPECT_EQ(LINE_Transport_WriteResponse_fake.arg1_val[0], 0x40 | 0x80);
    EXPECT_EQ(LINE_Transport_WriteResponse_fake.arg1_val[1], 0x00);
    EXPECT_EQ(LINE_Transport_WriteResponse_fake.arg1_val[2], UDS_PROPERTY_GET_RETURN_NO_SUCH_PROPERTY);
}

TEST_F(TestUdsLineProperties, GetPropertyResponse_ValidResponse) {
    UDS_OnSetProperty_fake.custom_fake = [](uint16_t property_id, uint8_t size, uint8_t* data) {
        UDS_EnqueueSetPropertyResponse(property_id, UDS_PROPERTY_SET_RETURN_SUCCESS);
    };

    BUILD_FRAME(request, UDS_PROPERTY_SET_CALL_REQUEST_ID | TEST_NODE_ADDRESS, 0x40, 0x00, 0x00, 0x01, 0x02, 0x03);
    for (int i = 0; i < sizeof(request); i++) {
        LINE_Transport_Receive(request[i]);
    }

    BUILD_REQUEST(response, UDS_PROPERTY_SET_RETURN_REQUEST_ID | TEST_NODE_ADDRESS);
    for (int i = 0; i < sizeof(response); i++) {
        LINE_Transport_Receive(response[i]);
    }

    EXPECT_EQ(UDS_OnSetProperty_fake.call_count, 1);
    EXPECT_EQ(UDS_OnSetProperty_fake.arg0_val, 0x4000);

    EXPECT_EQ(LINE_Transport_WriteResponse_fake.arg0_val, 3);
    EXPECT_EQ(LINE_Transport_WriteResponse_fake.arg1_val[0], 0x40 | 0x80);
    EXPECT_EQ(LINE_Transport_WriteResponse_fake.arg1_val[1], 0x00);
    EXPECT_EQ(LINE_Transport_WriteResponse_fake.arg1_val[2], UDS_PROPERTY_SET_RETURN_SUCCESS);
}

int main(int argc, char **argv) {
    ::testing::InitGoogleTest(&argc, argv);
    return RUN_ALL_TESTS();
}

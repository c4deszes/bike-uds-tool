#include "gtest/gtest.h"
#include "fff.h"

extern "C" {
    #include "uds_diag.h"
    #include "uds_gen.h"

    #include "line_protocol.h"
    #include "line_tester.h"
}

DEFINE_FFF_GLOBALS;

FAKE_VALUE_FUNC0(uint32_t, LINE_Diag_GetSerialNumber);
FAKE_VALUE_FUNC0(LINE_Diag_SoftwareVersion_t*, LINE_Diag_GetSoftwareVersion);
FAKE_VALUE_FUNC0(LINE_Diag_PowerStatus_t*, LINE_Diag_GetPowerStatus);
FAKE_VALUE_FUNC0(uint8_t, LINE_Diag_GetOperationStatus);

FAKE_VOID_FUNC4(LINE_Transport_OnError, uint8_t, bool, uint16_t, line_transport_error);
FAKE_VOID_FUNC4(LINE_Transport_WriteResponse, uint8_t, uint8_t, uint8_t*, uint8_t);
FAKE_VOID_FUNC2(LINE_Transport_WriteRequest, uint8_t, uint16_t);

FAKE_VOID_FUNC0(UDS_FrontLight_BooleanProperty_OnChange);
FAKE_VOID_FUNC0(UDS_FrontLight_Integer8Property_OnChange);
FAKE_VOID_FUNC0(UDS_FrontLight_Integer16Property_OnChange);
FAKE_VOID_FUNC0(UDS_FrontLight_Integer32Property_OnChange);
FAKE_VOID_FUNC1(UDS_FrontLight_OnPropertyChange, const uds_property_t*);

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

#define TRANSPORT_CHANNEL 0
#define TEST_NODE_ADDRESS 0x5

LINE_Diag_Config_t diag_config = {
    .transport_channel = TRANSPORT_CHANNEL,
    .address = TEST_NODE_ADDRESS,
    .op_status = LINE_Diag_GetOperationStatus,
    .power_status = LINE_Diag_GetPowerStatus,
    .serial_number = LINE_Diag_GetSerialNumber,
    .software_version = LINE_Diag_GetSoftwareVersion
};

LINE_TRANSPORT_INST(transport_instance, 64, 64, TWOWIRE);

class TestUdsLineProperties : public testing::Test {
    public:
        static void SetUpTestSuite() {
            LINE_Transport_Init(TRANSPORT_CHANNEL, &transport_instance);
            LINE_Diag_Init(0, &diag_config);
            UDS_Init();
        }
    protected:
        void SetUp() override {
            RESET_FAKE(LINE_Diag_GetSerialNumber);
            RESET_FAKE(LINE_Diag_GetSoftwareVersion);
            RESET_FAKE(LINE_Diag_GetPowerStatus);
            RESET_FAKE(LINE_Diag_GetOperationStatus);
        }
};

TEST_F(TestUdsLineProperties, GetPropertyResponse_NoRequest) {
    BUILD_REQUEST(response, UDS_PROPERTY_GET_RETURN_REQUEST_ID | TEST_NODE_ADDRESS);
    for (int i = 0; i < sizeof(response); i++) {
        LINE_Transport_Receive(TRANSPORT_CHANNEL, response[i]);
    }

    ASSERT_EQ(LINE_Transport_WriteResponse_fake.call_count, 1);
    EXPECT_EQ(LINE_Transport_WriteResponse_fake.arg1_val, 3);
    EXPECT_EQ(LINE_Transport_WriteResponse_fake.arg2_val[0], UINT16_H(UDS_PROPERTY_STATUS_MASK));
    EXPECT_EQ(LINE_Transport_WriteResponse_fake.arg2_val[1], 0x00);
    EXPECT_EQ(LINE_Transport_WriteResponse_fake.arg2_val[2], UDS_PROPERTY_GET_RETURN_NO_REQUEST);
}

TEST_F(TestUdsLineProperties, GetPropertyResponse_BadRequest) {
    BUILD_FRAME(request,
                UDS_PROPERTY_GET_CALL_REQUEST_ID | TEST_NODE_ADDRESS,
                0xFF);
    for (int i = 0; i < sizeof(request); i++) {
        LINE_Transport_Receive(TRANSPORT_CHANNEL, request[i]);
    }

    BUILD_REQUEST(response, UDS_PROPERTY_GET_RETURN_REQUEST_ID | TEST_NODE_ADDRESS);
    for (int i = 0; i < sizeof(response); i++) {
        LINE_Transport_Receive(TRANSPORT_CHANNEL, response[i]);
    }

    ASSERT_EQ(LINE_Transport_WriteResponse_fake.call_count, 1);
    EXPECT_EQ(LINE_Transport_WriteResponse_fake.arg1_val, 3);
    EXPECT_EQ(LINE_Transport_WriteResponse_fake.arg2_val[0], UINT16_H(UDS_PROPERTY_STATUS_MASK));
    EXPECT_EQ(LINE_Transport_WriteResponse_fake.arg2_val[1], 0x00);
    EXPECT_EQ(LINE_Transport_WriteResponse_fake.arg2_val[2], UDS_PROPERTY_GET_RETURN_BAD_REQUEST);
}

TEST_F(TestUdsLineProperties, GetPropertyResponse_NoSuchProperty) {
    BUILD_FRAME(request,
                UDS_PROPERTY_GET_CALL_REQUEST_ID | TEST_NODE_ADDRESS,
                UINT16_H(0xFFFF),
                UINT16_L(0xFFFF));
    for (int i = 0; i < sizeof(request); i++) {
        LINE_Transport_Receive(TRANSPORT_CHANNEL, request[i]);
    }

    BUILD_REQUEST(response, UDS_PROPERTY_GET_RETURN_REQUEST_ID | TEST_NODE_ADDRESS);
    for (int i = 0; i < sizeof(response); i++) {
        LINE_Transport_Receive(TRANSPORT_CHANNEL, response[i]);
    }

    ASSERT_EQ(LINE_Transport_WriteResponse_fake.call_count, 1);
    EXPECT_EQ(LINE_Transport_WriteResponse_fake.arg1_val, 3);
    EXPECT_EQ(LINE_Transport_WriteResponse_fake.arg2_val[0], UINT16_H(0xFFFF));
    EXPECT_EQ(LINE_Transport_WriteResponse_fake.arg2_val[1], UINT16_L(0xFFFF));
    EXPECT_EQ(LINE_Transport_WriteResponse_fake.arg2_val[2], UDS_PROPERTY_GET_RETURN_NO_SUCH_PROPERTY);
}

TEST_F(TestUdsLineProperties, GetPropertyResponse_ValidResponse_Bool) {
    UDS_FrontLight_Properties.BooleanProperty = true;

    BUILD_FRAME(request,
                UDS_PROPERTY_GET_CALL_REQUEST_ID | TEST_NODE_ADDRESS,
                UINT16_H(UDS_PROP_FrontLight_BooleanProperty_ID),
                UINT16_L(UDS_PROP_FrontLight_BooleanProperty_ID));
    for (int i = 0; i < sizeof(request); i++) {
        LINE_Transport_Receive(TRANSPORT_CHANNEL, request[i]);
    }

    BUILD_REQUEST(response, UDS_PROPERTY_GET_RETURN_REQUEST_ID | TEST_NODE_ADDRESS);
    for (int i = 0; i < sizeof(response); i++) {
        LINE_Transport_Receive(TRANSPORT_CHANNEL, response[i]);
    }

    ASSERT_EQ(LINE_Transport_WriteResponse_fake.call_count, 1);
    EXPECT_EQ(LINE_Transport_WriteResponse_fake.arg1_val, 3);
    EXPECT_EQ(LINE_Transport_WriteResponse_fake.arg2_val[0], UINT16_H(UDS_PROP_FrontLight_BooleanProperty_ID));
    EXPECT_EQ(LINE_Transport_WriteResponse_fake.arg2_val[1], UINT16_L(UDS_PROP_FrontLight_BooleanProperty_ID));
    EXPECT_EQ(LINE_Transport_WriteResponse_fake.arg2_val[2], 0x01);
}

TEST_F(TestUdsLineProperties, GetPropertyResponse_ValidResponse_8bit) {
    UDS_FrontLight_Properties.Integer8Property = 0x34;

    BUILD_FRAME(request,
                UDS_PROPERTY_GET_CALL_REQUEST_ID | TEST_NODE_ADDRESS,
                UINT16_H(UDS_PROP_FrontLight_Integer8Property_ID),
                UINT16_L(UDS_PROP_FrontLight_Integer8Property_ID));
    for (int i = 0; i < sizeof(request); i++) {
        LINE_Transport_Receive(TRANSPORT_CHANNEL, request[i]);
    }

    BUILD_REQUEST(response, UDS_PROPERTY_GET_RETURN_REQUEST_ID | TEST_NODE_ADDRESS);
    for (int i = 0; i < sizeof(response); i++) {
        LINE_Transport_Receive(TRANSPORT_CHANNEL, response[i]);
    }

    ASSERT_EQ(LINE_Transport_WriteResponse_fake.call_count, 1);
    EXPECT_EQ(LINE_Transport_WriteResponse_fake.arg1_val, 3);
    EXPECT_EQ(LINE_Transport_WriteResponse_fake.arg2_val[0], UINT16_H(UDS_PROP_FrontLight_Integer8Property_ID));
    EXPECT_EQ(LINE_Transport_WriteResponse_fake.arg2_val[1], UINT16_L(UDS_PROP_FrontLight_Integer8Property_ID));
    EXPECT_EQ(LINE_Transport_WriteResponse_fake.arg2_val[2], 0x34);
}

TEST_F(TestUdsLineProperties, GetPropertyResponse_ValidResponse_16bit) {
    UDS_FrontLight_Properties.Integer16Property = 0xAB09;

    BUILD_FRAME(request,
                UDS_PROPERTY_GET_CALL_REQUEST_ID | TEST_NODE_ADDRESS,
                UINT16_H(UDS_PROP_FrontLight_Integer16Property_ID),
                UINT16_L(UDS_PROP_FrontLight_Integer16Property_ID));
    for (int i = 0; i < sizeof(request); i++) {
        LINE_Transport_Receive(TRANSPORT_CHANNEL, request[i]);
    }

    BUILD_REQUEST(response, UDS_PROPERTY_GET_RETURN_REQUEST_ID | TEST_NODE_ADDRESS);
    for (int i = 0; i < sizeof(response); i++) {
        LINE_Transport_Receive(TRANSPORT_CHANNEL, response[i]);
    }

    ASSERT_EQ(LINE_Transport_WriteResponse_fake.call_count, 1);
    EXPECT_EQ(LINE_Transport_WriteResponse_fake.arg1_val, 4);
    EXPECT_EQ(LINE_Transport_WriteResponse_fake.arg2_val[0], UINT16_H(UDS_PROP_FrontLight_Integer16Property_ID));
    EXPECT_EQ(LINE_Transport_WriteResponse_fake.arg2_val[1], UINT16_L(UDS_PROP_FrontLight_Integer16Property_ID));
    EXPECT_EQ(LINE_Transport_WriteResponse_fake.arg2_val[2], 0x09);
    EXPECT_EQ(LINE_Transport_WriteResponse_fake.arg2_val[3], 0xAB);
}

TEST_F(TestUdsLineProperties, GetPropertyResponse_ValidResponse_32bit) {
    UDS_FrontLight_Properties.Integer32Property = 0x01020304;

    BUILD_FRAME(request,
                UDS_PROPERTY_GET_CALL_REQUEST_ID | TEST_NODE_ADDRESS,
                UINT16_H(UDS_PROP_FrontLight_Integer32Property_ID),
                UINT16_L(UDS_PROP_FrontLight_Integer32Property_ID));
    for (int i = 0; i < sizeof(request); i++) {
        LINE_Transport_Receive(TRANSPORT_CHANNEL, request[i]);
    }

    BUILD_REQUEST(response, UDS_PROPERTY_GET_RETURN_REQUEST_ID | TEST_NODE_ADDRESS);
    for (int i = 0; i < sizeof(response); i++) {
        LINE_Transport_Receive(TRANSPORT_CHANNEL, response[i]);
    }

    ASSERT_EQ(LINE_Transport_WriteResponse_fake.call_count, 1);
    EXPECT_EQ(LINE_Transport_WriteResponse_fake.arg1_val, 6);
    EXPECT_EQ(LINE_Transport_WriteResponse_fake.arg2_val[0], UINT16_H(UDS_PROP_FrontLight_Integer32Property_ID));
    EXPECT_EQ(LINE_Transport_WriteResponse_fake.arg2_val[1], UINT16_L(UDS_PROP_FrontLight_Integer32Property_ID));
    EXPECT_EQ(LINE_Transport_WriteResponse_fake.arg2_val[2], 0x04);
    EXPECT_EQ(LINE_Transport_WriteResponse_fake.arg2_val[3], 0x03);
    EXPECT_EQ(LINE_Transport_WriteResponse_fake.arg2_val[4], 0x02);
    EXPECT_EQ(LINE_Transport_WriteResponse_fake.arg2_val[5], 0x01);
}

TEST_F(TestUdsLineProperties, SetPropertyResponse_ValidResponse_32bit) {
    BUILD_FRAME(request,
                UDS_PROPERTY_SET_CALL_REQUEST_ID | TEST_NODE_ADDRESS,
                UINT16_H(UDS_PROP_FrontLight_Integer32Property_ID),
                UINT16_L(UDS_PROP_FrontLight_Integer32Property_ID),
                0x00, 0x01, 0x02, 0x03);
    for (int i = 0; i < sizeof(request); i++) {
        LINE_Transport_Receive(TRANSPORT_CHANNEL, request[i]);
    }

    ASSERT_EQ(UDS_FrontLight_Integer32Property_OnChange_fake.call_count, 1);
    ASSERT_EQ(UDS_FrontLight_OnPropertyChange_fake.call_count, 1);
    EXPECT_EQ(UDS_FrontLight_OnPropertyChange_fake.arg0_val->property_id, UDS_PROP_FrontLight_Integer32Property_ID);
    EXPECT_EQ(UDS_FrontLight_OnPropertyChange_fake.arg0_val->storage_class, uds_storage_class_volatile);
    EXPECT_EQ(UDS_FrontLight_OnPropertyChange_fake.arg0_val->value_ptr, &UDS_FrontLight_Properties.Integer32Property);

    BUILD_REQUEST(response, UDS_PROPERTY_SET_RETURN_REQUEST_ID | TEST_NODE_ADDRESS);
    for (int i = 0; i < sizeof(response); i++) {
        LINE_Transport_Receive(TRANSPORT_CHANNEL, response[i]);
    }

    ASSERT_EQ(LINE_Transport_WriteResponse_fake.call_count, 1);
    EXPECT_EQ(LINE_Transport_WriteResponse_fake.arg1_val, 3);
    EXPECT_EQ(LINE_Transport_WriteResponse_fake.arg2_val[0], UINT16_H(UDS_PROP_FrontLight_Integer32Property_ID) | 0x80);
    EXPECT_EQ(LINE_Transport_WriteResponse_fake.arg2_val[1], UINT16_L(UDS_PROP_FrontLight_Integer32Property_ID));
    EXPECT_EQ(LINE_Transport_WriteResponse_fake.arg2_val[2], UDS_PROPERTY_SET_RETURN_SUCCESS);
    EXPECT_EQ(UDS_FrontLight_Properties.Integer32Property, 0x03020100);
}

int main(int argc, char **argv) {
    ::testing::InitGoogleTest(&argc, argv);
    return RUN_ALL_TESTS();
}

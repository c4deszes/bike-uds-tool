#if !defined(UDS_PROPERTY_H)
#define UDS_PROPERTY_H

#if defined(__cplusplus)
extern "C" {
#endif

typedef enum {
    uds_storage_class_persistent = 0x00,
    uds_storage_class_volatile = 0x01,
} uds_storage_class_t;

typedef struct {
    uint16_t property_id;
    uds_storage_class_t storage_class;
    void* value_ptr;
} uds_property_t;

void UDS_Init(void);

#if defined(__cplusplus)
}
#endif

#endif // UDS_PROPERTY_H

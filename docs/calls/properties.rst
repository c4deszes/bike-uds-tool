Property manipulation
=====================

Devices can have properties, these are values that change how the device behaves.

Both property writing and reading consist of two operations, firstly the master scheduling the read
or write followed by another request returning the variable or the write operation status.

Get property
------------

Master requests ``0x0B8X <PropertyId>``, where ``PropertyId`` is a 16bit identifier.

Master polls the device until it responds with ``0x0B9X <PropertyId> <Value>``, where ``Value`` is
a data array.

Intermediate response can be ``0x0B9X <0b1|PropertyId> 0x01`` if the device is still processing the
request, here's the list of possible intermediate responses:

- ``0x00``: No request has been received
- ``0x01``: Response is not ready yet
- ``0x02``: Property not found
- ``0x03``: Property not readable
- ``0x0F``: Bad request

Set property
------------

Master requests ``0x0BAX <PropertyId> <Value>``, where ``PropertyId`` is a 16bit identifier and
``Value`` is a data array.

Master polls the device until it responds with ``0x0BBX <0b01|PropertyId> 0x01`` if the write was
successful or ``0x0BBX <0b01|PropertyId> 0x02`` if the device is still processing the request, here's the
list of possible intermediate responses:

- ``0x00``: No request has been received
- ``0x01``: Write successful
- ``0x02``: Response is not ready yet
- ``0x03``: Property not found
- ``0x04``: Write failure
- ``0x05``: Write rejected
- ``0x0F``: Bad request

Examples
--------

Reading a property
~~~~~~~~~~~~~~~~~~

``M2S 0x0B82 0x4010`` to read the property with ID 0x4010

``S2M 0x0B92 0xC010 0x02`` not ready

``S2M 0x0B92 0xC010 0x02`` not ready

``S2M 0x0B92 0x4010 0x00 0x01`` returned value

Writing a property
~~~~~~~~~~~~~~~~~~

``M2S 0x0BA2 0x4012 0x00 0x01 0x02 0x04`` to write the property with ID 0x4012

``S2M 0x0BB2 0xC012 0x02`` not ready

``S2M 0x0BB2 0xC012 0x02`` not ready

``S2M 0x0B92 0xC012 0x01`` write successful

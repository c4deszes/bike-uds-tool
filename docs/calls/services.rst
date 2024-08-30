Service call
============

A service call initaties an operation run on a device, it could be be something that only needs
occasional checks like triggering output stage diagnostics, but could be something more frequent
like resetting an internal counter.

A single call takes form in three requests.

Call
----

Master requests ``0xB0X <ServiceId> <Arguments>``, where ``ServiceId`` is a 16bit identifier of the
service to call and ``Arguments`` is a free form byte array, the decoding is specific to the service.

This schedules the target device to run the service.

Return
------

Master requests ``0xB1X``, slave responds with a finished service's return value.

The response format is ``<ServiceId> <Return value>``, where the called service identifier
is included and it's followed by free form data, decoding is specific to the service.

If there were no pending service calls or the service calls have not yet finished the slave responds
with ``0x0000``.

Examples
--------

Single call
~~~~~~~~~~~

``M2S 0x0B01 0x4024 0x00 0x00 0x01 0x00``

``S2M 0x0B21 0x4024 0x00``

Integration
===========

CMake
-----

The CMake project registers it's headers and soruce files are interface libraries which should be
linked into the executable. The project can be included via CPM.cmake or as a submodule.

.. code-block:: cmake

    find_package(Python REQUIRED)

    include(tools/cmake/CPM.cmake)
    CPMAddPackage("gh:c4deszes/bike-uds-tool#master")

    uds_codegen(
        TARGET test-uds-lib
        PROFILE example_profile.json
    )

    add_executable(MyApp src/main.c)
    target_link_libraries(MyApp PUBLIC test-uds-lib)

C code
------

.. code-block:: c

    void COMM_Init() {
        LINE_Transport_Init(true);

        UDS_Init();             // Initializes properties and services
        UDS_LINE_Init();        // Registers diagnostic callouts
    }

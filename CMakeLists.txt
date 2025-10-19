cmake_minimum_required(VERSION 3.20)

project(
    line-uds
    VERSION "0.3.0"
    LANGUAGES C CXX)

################################################################################
# Options
################################################################################
option(UDS_LINE_BUILD_TESTS "Enables library test cases" OFF)
option(UDS_LINE_BUILD_DOCS "Enables library documentation" OFF)

################################################################################
# Dependencies
################################################################################
include(tools/cmake/CPM.cmake)
CPMAddPackage("gh:c4deszes/bike-line-protocol@0.3.0")

find_package(Python REQUIRED)

################################################################################
# Interface
################################################################################
add_library(line-uds-api INTERFACE)
target_include_directories(line-uds-api INTERFACE
    ${CMAKE_CURRENT_SOURCE_DIR}/src
)
target_link_libraries(line-uds-api INTERFACE line-protocol-api)

function(uds_codegen)

cmake_parse_arguments(
    ""
    ""
    "TARGET;CONFIG"
    ""
    ${ARGN}
)

    set(uds_codegen_dir ${CMAKE_CURRENT_BINARY_DIR}/${_TARGET}_gencode)
    add_custom_target(
        uds-codegen-${_TARGET}
        COMMAND ${Python_EXECUTABLE} -m line_uds.codegen ${_CONFIG} --output ${uds_codegen_dir}
        DEPENDS ${_CONFIG}
        WORKING_DIRECTORY ${CMAKE_CURRENT_SOURCE_DIR}
        BYPRODUCTS ${uds_codegen_dir}/uds_gen.c ${uds_codegen_dir}/uds_gen.h
    )
    add_library(${_TARGET} INTERFACE)
    target_sources(${_TARGET} INTERFACE ${uds_codegen_dir}/uds_gen.c)
    target_include_directories(${_TARGET} INTERFACE ${uds_codegen_dir})
    target_link_libraries(${_TARGET} INTERFACE line-uds-api)
    add_dependencies(${_TARGET} uds-codegen-${_TARGET})
endfunction()

################################################################################
# Testing
################################################################################
if(UDS_LINE_BUILD_TESTS)
    enable_testing()
    add_subdirectory(tests)
endif()

################################################################################
# Documentation
################################################################################
if(UDS_LINE_BUILD_DOCS)
    add_subdirectory(docs)
endif()

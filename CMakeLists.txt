cmake_minimum_required(VERSION 3.20)
project(
    line-uds
    VERSION "0.1.0"
    LANGUAGES C CXX)

option(UDS_LINE_BUILD_TESTS "Enables library test cases" OFF)

include(tools/cmake/CPM.cmake)
CPMAddPackage("gh:c4deszes/bike-line-protocol@0.1.0")

add_library(line-uds-api INTERFACE)
target_include_directories(line-uds-api INTERFACE
    ${CMAKE_CURRENT_SOURCE_DIR}/src
)
target_link_libraries(line-uds-api INTERFACE line-protocol-api)

add_library(line-uds-sources INTERFACE)
target_sources(line-uds-sources INTERFACE
    ${CMAKE_CURRENT_SOURCE_DIR}/src/uds_call.c
    ${CMAKE_CURRENT_SOURCE_DIR}/src/uds_line.c
    ${CMAKE_CURRENT_SOURCE_DIR}/src/uds_property.c
)

function(uds_codegen)

cmake_parse_arguments(
    ""
    ""
    "TARGET;PROFILE"
    ""
    ${ARGN}
)

    set(uds_codegen_dir ${CMAKE_CURRENT_BINARY_DIR}/${_TARGET}_gencode)
    add_custom_target(
        uds-codegen-${_TARGET}
        COMMAND ${Python_EXECUTABLE} -m line_uds.codegen ${_PROFILE} --output ${uds_codegen_dir}
        DEPENDS ${_PROFILE}
        WORKING_DIRECTORY ${CMAKE_CURRENT_SOURCE_DIR}
        BYPRODUCTS ${uds_codegen_dir}/uds_gencode.c ${uds_codegen_dir}/uds_gencode.h
    )
    add_library(${_TARGET} INTERFACE)
    target_sources(${_TARGET} INTERFACE ${uds_codegen_dir}/uds_gencode.c)
    target_include_directories(${_TARGET} INTERFACE ${uds_codegen_dir})
    target_link_libraries(${_TARGET} INTERFACE line-uds-sources line-uds-api)
    add_dependencies(${_TARGET} line-codegen-${_TARGET})
endfunction()

if(UDS_LINE_BUILD_TESTS)
    enable_testing()
    include(FetchContent)
    include(GoogleTest)

    FetchContent_Declare(
        googletest
        GIT_REPOSITORY https://github.com/google/googletest.git
        GIT_TAG        release-1.12.0
    )
    FetchContent_Declare(
        fff
        GIT_REPOSITORY https://github.com/meekrosoft/fff.git
        GIT_TAG        5111c61e1ef7848e3afd3550044a8cf4405f4199
    )

    FetchContent_MakeAvailable(googletest fff)
    add_subdirectory(tests)

    add_custom_target(
        coverage
        COMMAND ${Python_EXECUTABLE} -m gcovr --html-self-contained --html-details ${CMAKE_BINARY_DIR}/coverage.html
        WORKING_DIRECTORY ${CMAKE_CURRENT_SOURCE_DIR}
    )

    add_custom_target(
        docs
        COMMAND ${Python_EXECUTABLE} -m sphinx -b html -E ${CMAKE_CURRENT_SOURCE_DIR}/docs ${CMAKE_CURRENT_SOURCE_DIR}/docs/_build
        WORKING_DIRECTORY ${CMAKE_CURRENT_SOURCE_DIR}
    )
endif()

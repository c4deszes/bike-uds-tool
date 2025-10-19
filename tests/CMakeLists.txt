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

function(add_test TARGET)
    target_compile_options(${TARGET} PRIVATE $<$<COMPILE_LANGUAGE:C>:--coverage>)
    target_link_libraries(${TARGET} PRIVATE gtest fff gcov)
    gtest_discover_tests(${TARGET} DISCOVERY_MODE POST_BUILD)
endfunction()

add_custom_target(
    coverage
    COMMAND ${Python_EXECUTABLE} -m gcovr --html-self-contained --html-details ${CMAKE_BINARY_DIR}/coverage.html
    WORKING_DIRECTORY ${CMAKE_CURRENT_SOURCE_DIR}
)

## Generated code testing
uds_codegen(
    TARGET test-uds-lib-single
    CONFIG codegen_single.json
)

# 
add_executable(test_UdsLine_Properties EXCLUDE_FROM_ALL)
target_sources(test_UdsLine_Properties PRIVATE
    test_UdsLine_Properties.cpp
)
target_link_libraries(test_UdsLine_Properties PRIVATE
    line-uds-api
    line-protocol-api line-protocol-sources
    test-uds-lib-single
)
add_test(test_UdsLine_Properties)

# 
add_executable(test_UdsLine_ServiceCall EXCLUDE_FROM_ALL)
target_sources(test_UdsLine_ServiceCall PRIVATE
    test_UdsLine_ServiceCall.cpp
)
target_link_libraries(test_UdsLine_ServiceCall PRIVATE
    line-uds-api
    line-protocol-api line-protocol-sources
    test-uds-lib-single
)
add_test(test_UdsLine_ServiceCall)

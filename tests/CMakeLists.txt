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

################################################################################
# Coverage
################################################################################
add_custom_target(coverage_report
    COMMAND ${CMAKE_COMMAND} -E echo "Generating coverage report..."
    COMMAND ${CMAKE_COMMAND} -E make_directory coverage
    COMMAND gcovr -r ${CMAKE_SOURCE_DIR} --cobertura coverage/coverage.xml
                                         --html coverage/coverage.html
                                         --html-details coverage/coverage_details.html
)

################################################################################
# Test targets
################################################################################

## Property retrival
# add_executable(test_UdsLine_GetProperties EXCLUDE_FROM_ALL)
# target_sources(test_UdsLine_GetProperties PRIVATE
#     test_UdsLine_GetProperties.cpp
# )
# target_link_libraries(test_UdsLine_GetProperties PRIVATE
#     line-uds-api line-uds-sources 
#     line-protocol-api line-protocol-sources
#     line-protocol-adapter-sources
# )
# add_test(test_UdsLine_GetProperties)

# ## Property setting
# add_executable(test_UdsLine_SetProperties EXCLUDE_FROM_ALL)
# target_sources(test_UdsLine_SetProperties PRIVATE
#     test_UdsLine_SetProperties.cpp
# )
# target_link_libraries(test_UdsLine_SetProperties PRIVATE
#     line-uds-api line-uds-sources 
#     line-protocol-api line-protocol-sources
#     line-protocol-adapter-sources
# )
# add_test(test_UdsLine_SetProperties)

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

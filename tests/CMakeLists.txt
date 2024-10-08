function(add_test TARGET)
    target_compile_options(${TARGET} PRIVATE $<$<COMPILE_LANGUAGE:C>:--coverage>)
    target_link_libraries(${TARGET} PRIVATE gtest fff gcov)
    gtest_discover_tests(${TARGET} DISCOVERY_MODE POST_BUILD)
endfunction()

## Property retrival
add_executable(test_UdsLine_GetProperties EXCLUDE_FROM_ALL)
target_sources(test_UdsLine_GetProperties PRIVATE
    test_UdsLine_GetProperties.cpp
)
target_link_libraries(test_UdsLine_GetProperties PRIVATE
    line-uds-api line-uds-sources 
    line-protocol-api line-protocol-sources
    line-protocol-adapter-sources
)
add_test(test_UdsLine_GetProperties)

## Property setting
add_executable(test_UdsLine_SetProperties EXCLUDE_FROM_ALL)
target_sources(test_UdsLine_SetProperties PRIVATE
    test_UdsLine_SetProperties.cpp
)
target_link_libraries(test_UdsLine_SetProperties PRIVATE
    line-uds-api line-uds-sources 
    line-protocol-api line-protocol-sources
    line-protocol-adapter-sources
)
add_test(test_UdsLine_SetProperties)

## Generated code testing
uds_codegen(
    TARGET test-uds-lib
    PROFILE example_profile.json
)

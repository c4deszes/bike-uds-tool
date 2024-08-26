function(add_test TARGET)
    target_compile_options(${TARGET} PRIVATE $<$<COMPILE_LANGUAGE:C>:--coverage>)
    target_link_libraries(${TARGET} PRIVATE gtest fff gcov)
    gtest_discover_tests(${TARGET} DISCOVERY_MODE POST_BUILD)
endfunction()

## Application mode tests
add_executable(test_UdsLine_Properties EXCLUDE_FROM_ALL)
target_sources(test_UdsLine_Properties PRIVATE
    test_UdsLine_Properties.cpp
)
target_link_libraries(test_UdsLine_Properties PRIVATE
    line-uds-api line-uds-sources 
    line-protocol-api line-protocol-sources
    line-protocol-adapter-sources
)
add_test(test_UdsLine_Properties)

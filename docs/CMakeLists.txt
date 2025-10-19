
set(SPHINX_SOURCE ${CMAKE_CURRENT_SOURCE_DIR})
set(SPHINX_BUILD ${CMAKE_CURRENT_BINARY_DIR}/docs)

set(DOXYGEN_INPUT_DIRS
    "${CMAKE_SOURCE_DIR}/include ${CMAKE_SOURCE_DIR}/src"
)
set(DOXYGEN_OUTPUT_DIR ${CMAKE_CURRENT_BINARY_DIR}/doxygen)
set(DOXYGEN_INDEX_FILE ${DOXYGEN_OUTPUT_DIR}/html/index.html)
set(DOXYFILE_IN ${CMAKE_CURRENT_SOURCE_DIR}/Doxyfile)
set(DOXYFILE_OUT ${CMAKE_CURRENT_BINARY_DIR}/Doxyfile)

configure_file(${DOXYFILE_IN} ${DOXYFILE_OUT} @ONLY)

file(MAKE_DIRECTORY ${DOXYGEN_OUTPUT_DIR})
add_custom_target(Doxygen
                   COMMAND doxygen ${DOXYFILE_OUT}
                   #MAIN_DEPENDENCY ${DOXYFILE_OUT} ${DOXYFILE_IN}
                   #DEPENDS ${PROJECT_TARGETS}
                   COMMENT "Generating docs")

#add_custom_target(Doxygen ALL DEPENDS ${DOXYGEN_INDEX_FILE})

set(SPHINX_SOURCE ${CMAKE_CURRENT_SOURCE_DIR})
set(SPHINX_BUILD ${CMAKE_CURRENT_SOURCE_DIR}/_build)

add_custom_target(Sphinx ALL
                  COMMAND
                  sphinx-build -E -b html
                  -Dbreathe_projects.flash_line=${DOXYGEN_OUTPUT_DIR}/xml
                  ${SPHINX_SOURCE} ${SPHINX_BUILD}
                  DEPENDS Doxygen
                  WORKING_DIRECTORY ${CMAKE_CURRENT_BINARY_DIR}
                  COMMENT "Generating documentation with Sphinx")
message(" - rosidl_generator_cpp_generate_interfaces.cmake")
message("   - target: ${rosidl_generate_interfaces_TARGET}")
message("   - interface files: ${rosidl_generate_interfaces_IDL_FILES}")
message("   - dependency package names: ${rosidl_generate_interfaces_DEPENDENCY_PACKAGE_NAMES}")

set(_output_path "${CMAKE_CURRENT_BINARY_DIR}/rosidl_generator_cpp/${PROJECT_NAME}")
set(_generated_files "")
foreach(_idl_file ${rosidl_generate_interfaces_IDL_FILES})
  get_filename_component(_extension "${_idl_file}" EXT)
  if("${_extension}" STREQUAL ".msg")
    get_filename_component(name "${_idl_file}" NAME_WE)
    list(APPEND _generated_files
      "${_output_path}/${name}.h"
      "${_output_path}/${name}_Struct.h"
    )
  elseif("${_extension}" STREQUAL ".srv")
    get_filename_component(name "${_idl_file}" NAME_WE)
    list(APPEND _generated_files
      "${_output_path}/${name}.h"
      "${_output_path}/${name}_Service.h"
    )
  endif()
endforeach()

set(_dependency_files "")
set(_dependencies "")
foreach(_pkg_name ${rosidl_generate_interfaces_DEPENDENCY_PACKAGE_NAMES})
  foreach(_idl_file ${${_pkg_name}_INTERFACE_FILES})
    set(_abs_idl_file "${${_pkg_name}_DIR}/../${_idl_file}")
    normalize_path(_abs_idl_file "${_abs_idl_file}")
    list(APPEND _dependency_files "${_abs_idl_file}")
    list(APPEND _dependencies "${_pkg_name}:${_abs_idl_file}")
  endforeach()
endforeach()

message("   - generated files: ${_generated_files}")
message("   - dependencies: ${_dependencies}")

add_custom_command(
  OUTPUT ${_generated_files}
  COMMAND ${PYTHON_EXECUTABLE} ${rosidl_generator_cpp_BIN}
  --pkg-name ${PROJECT_NAME}
  --ros-interface-files ${rosidl_generate_interfaces_IDL_FILES}
  --deps ${_dependencies}
  --output-dir ${_output_path}
  --template-dir ${rosidl_generator_cpp_TEMPLATE_DIR}
  DEPENDS
  ${rosidl_generator_cpp_BIN}
  ${rosidl_generator_cpp_GENERATOR_FILES}
  ${rosidl_generator_cpp_TEMPLATE_DIR}/msg.h.template
  ${rosidl_generator_cpp_TEMPLATE_DIR}/msg_Struct.h.template
  ${rosidl_generator_cpp_TEMPLATE_DIR}/srv.h.template
  ${rosidl_generator_cpp_TEMPLATE_DIR}/srv_Service.h.template
  ${rosidl_generate_interfaces_IDL_FILES}
  ${_dependency_files}
  COMMENT "Generating C++ code for ROS interfaces"
  VERBATIM
)

add_custom_target(
  ${rosidl_generate_interfaces_TARGET}__cpp
  DEPENDS
  ${_generated_files}
)
add_dependencies(
  ${rosidl_generate_interfaces_TARGET}
  ${rosidl_generate_interfaces_TARGET}__cpp
)

install(
  FILES ${_generated_files}
  DESTINATION "include/${PROJECT_NAME}"
)

ament_export_include_directories(include)

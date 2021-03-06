
#ifndef __rosidl_generator_cpp__MessageTypeSupport__h__
#define __rosidl_generator_cpp__MessageTypeSupport__h__

namespace rosidl_generator_cpp
{

typedef struct MessageTypeSupportHandle {
  const char * _typesupport_identifier;
  const void * _data;
} MessageTypeSupportHandle;

template<typename T>
const MessageTypeSupportHandle& get_type_support_handle();

}  // namespace rosidl_generator_cpp

#endif  // __rosidl_generator_cpp__MessageTypeSupport__h__

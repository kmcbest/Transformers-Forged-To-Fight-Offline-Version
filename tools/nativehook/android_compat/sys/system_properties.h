#ifndef _SYS_SYSTEM_PROPERTIES_H
#define _SYS_SYSTEM_PROPERTIES_H

#ifdef __cplusplus
extern "C" {
#endif

#define PROP_VALUE_MAX 92
int __system_property_get(const char *name, char *value);

#ifdef __cplusplus
}
#endif

#endif /* _SYS_SYSTEM_PROPERTIES_H */

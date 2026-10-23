#pragma once
#include <stddef.h>

#ifdef __cplusplus
extern "C" {
#endif

char* strstr(const char* haystack, const char* needle);
size_t strlen(const char* s);
int strcmp(const char* s1, const char* s2);
int strncmp(const char* s1, const char* s2, size_t n);
char* strncpy(char* dest, const char* src, size_t n);
void* memset(void* s, int c, size_t n);
void* memcpy(void* dest, const void* src, size_t n);

#ifdef __cplusplus
}
#endif

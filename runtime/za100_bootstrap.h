// Development boot path only. It must never opt unknown builds into 2.0.2 hooks.
#ifndef ZA100_BOOTSTRAP_H
#define ZA100_BOOTSTRAP_H
#include <stdbool.h>
#include <stdint.h>
#include <stdlib.h>
#include <string.h>

static inline bool za100_build(const uint8_t id[8]) {
    static const uint8_t expected[8] = {0x72, 0x22, 0xe1, 0x3e, 0xcf, 0x6a, 0xdb, 0x32};
    return !memcmp(id, expected, sizeof expected);
}

static inline bool za100_bootstrap_enabled(void) {
    const char *value = getenv("LZA_EXPERIMENTAL_ZA100_BOOTSTRAP");
    return value && !strcmp(value, "1");
}
// Separate opt-in: never change the bootstrap's default 30 FPS diagnostic path.
static inline bool za100_timing120_enabled(void) {
    const char *value = getenv("LZA_EXPERIMENTAL_ZA100_TIMING");
    return za100_bootstrap_enabled() && value && !strcmp(value, "120");
}
#endif

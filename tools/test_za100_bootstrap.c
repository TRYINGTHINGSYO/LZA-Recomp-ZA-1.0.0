#include "../runtime/za100_bootstrap.h"
#include <assert.h>

int main(void) {
    uint8_t id[8] = {0x72, 0x22, 0xe1, 0x3e, 0xcf, 0x6a, 0xdb, 0x32};
    assert(za100_build(id));
    id[0] ^= 1;
    assert(!za100_build(id));
    const char *value = getenv("LZA_EXPERIMENTAL_ZA100_BOOTSTRAP");
    assert(za100_bootstrap_enabled() == (value && !strcmp(value, "1")));
    const char *timing = getenv("LZA_EXPERIMENTAL_ZA100_TIMING");
    assert(za100_timing120_enabled() == (za100_bootstrap_enabled() && timing && !strcmp(timing, "120")));
    return 0;
}

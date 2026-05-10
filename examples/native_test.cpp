#include <iostream>
#include <string>
#include <vector>
#include <cstdint>

extern "C" {
    int64_t fast_add(int64_t v_a, int64_t v_b) {
        int64_t v_0 = v_a + v_b;
        return v_0;
    }

}

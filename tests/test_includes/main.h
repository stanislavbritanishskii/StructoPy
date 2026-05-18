#ifndef MAIN_H
#define MAIN_H

#include <stdint.h>
#include <vector>
#include "utils/types.h"

typedef struct Boundary {
    PointF   center;
    Range    span;
    uint32_t flags;
};

#endif

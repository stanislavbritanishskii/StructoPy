// Multi-level nesting: RobotState contains Pose contains Vec3f/Quaternion.

typedef struct Vec3f {
    float x;
    float y;
    float z;
};

typedef struct Quaternion {
    float w;
    float x;
    float y;
    float z;
};

typedef struct Pose {
    Vec3f      position;
    Quaternion orientation;
};

typedef struct RobotState {
    Pose      base_pose;
    Pose      tool_pose;
    int64_t   timestamp_ns;
    uint32_t  sequence;
    uint8_t   mode;
    uint8_t   battery_percent;
};

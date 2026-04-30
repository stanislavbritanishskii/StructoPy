#ifndef SAMPLE_H
#define SAMPLE_H
#include "included_sample.h"
#define MAX_NAME_LEN	32
#define MAX_SENSORS		8
#define MAX_PAYLOAD		64

// ---------------------- Basic vector ----------------------

typedef struct Vec3 {
	float x;
	float y;
	float z;
};

// ---------------------- Timestamp ----------------------

typedef struct Timestamp {
	uint32_t	seconds;
	uint32_t	microseconds;
};

// ---------------------- Sensor data ----------------------

typedef struct Sensor {
	uint8_t		id;
	float		value;
	int16_t		status;
	Vec3		offset;
};

// ---------------------- Device metadata ----------------------

typedef struct DeviceInfo {
	char		name[MAX_NAME_LEN];
	char        val;
	uint8_t		type;
	uint16_t	version;
	uint32_t	serial;
};

// ---------------------- Payload block ----------------------

typedef struct Payload {
	uint8_t		data[MAX_PAYLOAD];
	uint16_t	length;
};

// ---------------------- Full telemetry packet ----------------------

typedef struct TelemetryPacket {
	Timestamp		time;
	DeviceInfo		device;

	Sensor			sensors[MAX_SENSORS];
	uint8_t			sensor_count;

	Vec3			position;
	Vec3			velocity;

	Payload			payload;

	int8_t			flags;
	uint32_t		counter;
};

#endif // EXAMPLE_HPP
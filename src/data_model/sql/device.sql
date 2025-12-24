CREATE TABLE device (
        ieee_address VARCHAR(24) NOT NULL,
        friendly_name VARCHAR(120) NOT NULL,
        network_address INTEGER,
        firmware_build_date DATE,
        firmware_version VARCHAR(60),
        device_type VARCHAR(60),
        zigbee_model VARCHAR(120),
        zigbee_manufacturer VARCHAR(120),
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL,
        retired_at DATETIME,
        PRIMARY KEY (ieee_address),
        CONSTRAINT ck_device_network_address_range CHECK ((network_address IS NULL) OR (network_address >= 0 AND network_address <= 65535)),
        UNIQUE (friendly_name)
)

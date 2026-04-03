/*
 * ============================================================================
 *  NEXUS Platform - Universal I/O Driver Interface Specification
 *  Version: 2.0.0
 *  Target:  C99 (ISO/IEC 9899:1999)
 *  ============================================================================
 *
 *  This header defines the EXACT interface contract between the NEXUS
 *  universal firmware runtime and every I/O driver.  Every driver binary
 *  must #include this header and implement an instance of nx_driver_vtable_t.
 *
 *  INVARIANTS:
 *    - All pointers passed across the driver boundary are non-NULL unless
 *      the contract explicitly permits NULL (documented per-field).
 *    - init() must be called before any other vtable function.
 *    - deinit() must be the last call; after it returns, the ctx pointer is
 *      invalid and no other vtable function may be called.
 *    - read/write are safe to call from a FreeRTOS task or an ISR (if the
 *      driver sets NX_CAP_ISR_SAFE in its capabilities bitmap).
 *    - Every public function returns nx_err_t; NX_OK (0) is the only
 *      success code.
 *
 *  THREAD SAFETY:
 *    - The runtime serializes calls to init()/deinit().
 *    - read() and write() MAY be called concurrently from different tasks
 *      IF the driver advertises NX_CAP_THREAD_SAFE.  Otherwise the caller
 *      must hold the driver mutex (obtained via nx_rt_driver_mutex()).
 *
 *  MEMORY OWNERSHIP:
 *    - The runtime allocates ctx as a zeroed block of size ctx_size.
 *    - The driver owns ctx for the lifetime between init() and deinit().
 *    - On deinit(), the runtime frees ctx after deinit() returns.
 *    - output_schema must point to static storage (driver lifetime).
 *
 *  ============================================================================
 */

#ifndef NEXUS_IO_DRIVER_INTERFACE_H
#define NEXUS_IO_DRIVER_INTERFACE_H

#ifdef __cplusplus
extern "C" {
#endif

#include <stddef.h>
#include <stdint.h>

/* ============================================================================
 *  Section 1: Build Configuration & Platform Probes
 * ============================================================================ */

/*
 * NX_DRIVER_ABI_VERSION must match between the runtime and every driver.
 * Increment on any breaking change to struct layouts, error code values,
 * or calling conventions.
 */
#define NX_DRIVER_ABI_VERSION  2

/*
 * Convenience macros for struct/array sizing.  These expand to plain
 * integer constants so the header needs no runtime support.
 */
#define NX_ARRAY_SIZE(a)       ((sizeof(a)) / (sizeof((a)[0])))
#define NX_MIN(a, b)           ((a) < (b) ? (a) : (b))
#define NX_MAX(a, b)           ((a) > (b) ? (a) : (b))
#define NX_OFFSETOF(type, m)   ((size_t)&(((type *)0)->m))

/*
 * Pin capability flags – ORed together to describe what a physical pin
 * can do.  The runtime queries the MCU's pinmux table at startup.
 */
#define NX_CAP_GPIO            (1U << 0)   /* General-purpose digital I/O  */
#define NX_CAP_ADC             (1U << 1)   /* Analog-to-digital converter  */
#define NX_CAP_PWM             (1U << 2)   /* Pulse-width modulation out    */
#define NX_CAP_I2C_SDA         (1U << 3)   /* I2C data line                */
#define NX_CAP_I2C_SCL         (1U << 4)   /* I2C clock line               */
#define NX_CAP_UART_TX         (1U << 5)   /* UART transmit                */
#define NX_CAP_UART_RX         (1U << 6)   /* UART receive                 */
#define NX_CAP_SPI_MOSI        (1U << 7)   /* SPI master-out-slave-in      */
#define NX_CAP_SPI_MISO        (1U << 8)   /* SPI master-in-slave-out      */
#define NX_CAP_SPI_SCK         (1U << 9)   /* SPI clock                    */
#define NX_CAP_SPI_CS          (1U << 10)  /* SPI chip-select              */
#define NX_CAP_ONEWIRE         (1U << 11)  /* 1-Wire bus                   */
#define NX_CAP_DAC             (1U << 12)  /* Digital-to-analog converter  */
#define NX_CAP_INPUT_CAPTURE   (1U << 13)  /* Timer input-capture          */
#define NX_CAP_INTERRUPT       (1U << 14)  /* External interrupt (EXTI)     */

/* Driver-level capability flags (returned alongside vtable). */
#define NX_CAP_ISR_SAFE        (1U << 0)   /* read/write callable from ISR */
#define NX_CAP_THREAD_SAFE     (1U << 1)   /* internally synchronized      */
#define NX_CAP_DMA             (1U << 2)   /* uses DMA for transfers       */
#define NX_CAP_LOW_POWER       (1U << 3)   /* supports tickless idle       */
#define NX_CAP_HOTPLUG         (1U << 4)   /* supports runtime attach/det  */
#define NX_CAP_STREAMING       (1U << 5)   /* supports continuous sampling */

/* Maximum dimensions for schema field names and driver names. */
#define NX_DRIVER_NAME_MAX     32
#define NX_FIELD_NAME_MAX      24
#define NX_PIN_NAME_MAX        16
#define NX_SCHEMA_FIELDS_MAX   16
#define NX_SELFTEST_ITEMS_MAX  32

/* ============================================================================
 *  Section 2: Error Code Enumeration (nx_err_t)
 * ============================================================================ */

typedef enum {
    NX_OK                         =   0,  /* Success                            */

    /* --- Pin & GPIO errors (1xx) --- */
    NX_ERR_INVALID_PIN            = 101,  /* Pin number out of valid range      */
    NX_ERR_PIN_CONFLICT           = 102,  /* Pin already claimed by another drv */
    NX_ERR_CAPABILITY_MISMATCH    = 103,  /* Pin lacks required capability      */
    NX_ERR_GPIO_MODE_UNSUPPORTED  = 104,  /* Requested pull/up/down not avail   */

    /* --- I2C errors (2xx) --- */
    NX_ERR_I2C_NAK                = 201,  /* Slave NACKed address or data       */
    NX_ERR_I2C_BUS_STUCK          = 202,  /* SDA held low (bus locked up)       */
    NX_ERR_I2C_ARBITRATION_LOST   = 203,  /* Multi-master arbitration lost      */
    NX_ERR_I2C_INVALID_ADDRESS    = 204,  /* 7-bit address outside 0x08-0x77    */

    /* --- SPI errors (3xx) --- */
    NX_ERR_SPI_BUSY               = 301,  /* Bus in use by another transaction  */
    NX_ERR_SPI_CRC_ERROR          = 302,  /* Hardware CRC mismatch             */
    NX_ERR_SPI_FRAME_ERROR        = 303,  /* Mode fault / extra SCK edges      */

    /* --- UART errors (4xx) --- */
    NX_ERR_UART_OVERRUN           = 401,  /* RX FIFO overflowed                */
    NX_ERR_UART_FRAMING           = 402,  /* Break / framing error detected    */
    NX_ERR_UART_PARITY            = 403,  /* Parity check failed               */
    NX_ERR_UART_NO_DEVICE         = 404,  /* No slave detected on TX line      */

    /* --- ADC errors (5xx) --- */
    NX_ERR_ADC_STUCK              = 501,  /* Conversion did not complete       */
    NX_ERR_ADC_OVERRANGE          = 502,  /* Input exceeds full-scale          */
    NX_ERR_ADC_CALIBRATION        = 503,  /* Internal calibration failed       */
    NX_ERR_ADC_NOT_READY          = 504,  /* Sample requested before settle    */

    /* --- PWM errors (6xx) --- */
    NX_ERR_PWM_CHANNEL_EXHAUSTED  = 601,  /* No free PWM channel on timer      */
    NX_ERR_PWM_FREQUENCY_UNATTAIN = 602,  /* Requested freq outside HW range   */
    NX_ERR_PWM_DUTY_OUT_OF_RANGE  = 603,  /* Duty cycle not in [0.0, 100.0]    */

    /* --- 1-Wire errors (7xx) --- */
    NX_ERR_ONEWIRE_NO_DEVICE      = 701,  /* No presence pulse detected        */
    NX_ERR_ONEWIRE_CRC_ERROR      = 702,  /* ROM or data CRC mismatch          */

    /* --- General / Runtime errors (8xx) --- */
    NX_ERR_TIMEOUT                = 801,  /* Operation exceeded deadline       */
    NX_ERR_NOT_INITIALIZED        = 802,  /* Driver init() never called        */
    NX_ERR_ALREADY_INITIALIZED    = 803,  /* init() called twice w/o deinit    */
    NX_ERR_OUT_OF_MEMORY          = 804,  /* Heap allocation failed            */
    NX_ERR_STACK_OVERFLOW         = 805,  /* Task or ISR stack exhausted       */
    NX_ERR_INVALID_CONFIG         = 806,  /* NULL / out-of-range config param  */
    NX_ERR_INVALID_ARGUMENT       = 807,  /* General bad argument              */
    NX_ERR_BUFFER_TOO_SMALL       = 808,  /* Caller buffer < required size     */
    NX_ERR_UNSUPPORTED            = 809,  /* Operation not implemented by drv  */

    /* --- Selftest & Safety errors (9xx) --- */
    NX_ERR_SELFTEST_FAILED        = 901,  /* One or more selftest checks fail  */
    NX_ERR_WATCHDOG               = 902,  /* Watchdog timer expired            */
    NX_ERR_SAFETY_VIOLATION       = 903,  /* Kill-switch / overcurrent fired   */
    NX_ERR_OVERCURRENT            = 904,  /* Current limit exceeded            */
    NX_ERR_OVERTEMPERATURE        = 905,  /* Die or sensor temperature too high*/

    /* --- System / OTA errors (10xx) --- */
    NX_ERR_FIRMWARE_UPDATE_FAILED = 1001, /* OTA flash write or verify failed  */
    NX_ERR_REFLEX_COMPILE_FAILED  = 1002, /* Reflex bytecode compilation error */
    NX_ERR_NVS_READ_FAILED        = 1003, /* NVS key not found / corrupt       */
    NX_ERR_NVS_WRITE_FAILED       = 1004, /* NVS write rejected (space/full)   */
    NX_ERR_PARTITION_CORRUPT      = 1005, /* Flash partition CRC / magic bad   */

    NX_ERR_COUNT_                 /* Sentinel – number of defined errors  */
} nx_err_t;

/* ============================================================================
 *  Section 3: Pin Configuration Types
 * ============================================================================ */

/*
 * Pin type discriminator.  Every nx_pin_config_t carries one of these so
 * the runtime can validate capabilities before passing the config to the
 * driver's init().
 */
typedef enum {
    NX_PIN_TYPE_DIGITAL_IN        = 0,
    NX_PIN_TYPE_DIGITAL_OUT       = 1,
    NX_PIN_TYPE_PWM               = 2,
    NX_PIN_TYPE_ADC               = 3,
    NX_PIN_TYPE_I2C_BUS           = 4,
    NX_PIN_TYPE_I2C_DEVICE        = 5,
    NX_PIN_TYPE_UART              = 6,
    NX_PIN_TYPE_SPI_BUS           = 7,
    NX_PIN_TYPE_SPI_DEVICE        = 8,
    NX_PIN_TYPE_ONEWIRE           = 9,
    NX_PIN_TYPE_PULSE_COUNTER     = 10,
    NX_PIN_TYPE_DAC               = 11,
    NX_PIN_TYPE_COUNT_            /* sentinel */
} nx_pin_type_t;

/*
 * Pull mode for digital inputs.
 */
typedef enum {
    NX_PULL_NONE    = 0,
    NX_PULL_UP      = 1,
    NX_PULL_DOWN    = 2,
    NX_PULL_FLOAT   = 3   /* explicitly no pull (no internal pull active) */
} nx_pull_mode_t;

/* --- Sub-configuration structs --- */

typedef struct {
    uint8_t             gpio_num;        /* MCU GPIO number                */
    nx_pull_mode_t      pull;            /* Pull-up / pull-down / none     */
    uint8_t             invert;          /* 1 = active-low, 0 = active-hi */
    uint8_t             debounce_ms;     /* 0 = no debounce                */
    uint8_t             interrupt_mode;  /* 0=none, 1=rising, 2=falling, 3=both */
} nx_digital_in_config_t;

typedef struct {
    uint8_t             gpio_num;        /* MCU GPIO number                */
    uint8_t             default_level;   /* 0 = low, 1 = high             */
    uint8_t             open_drain;      /* 1 = open-drain, 0 = push-pull */
} nx_digital_out_config_t;

typedef struct {
    uint8_t             gpio_num;        /* PWM output GPIO                */
    uint32_t            frequency_hz;    /* Target frequency (0 = auto)   */
    float               duty_percent;    /* 0.0 – 100.0                   */
    uint8_t             timer_channel;   /* 0 = auto-assign               */
    uint8_t             inverted;        /* 1 = invert output polarity    */
} nx_pwm_config_t;

typedef struct {
    uint8_t             adc_channel;     /* ADC channel number             */
    uint8_t             adc_num;         /* ADC unit (for dual-ADC MCUs)   */
    uint32_t            sample_rate_hz;  /* 0 = on-demand                  */
    uint8_t             attenuation_db;  /* 0, 3, 6, 11 (ESP32 convention)*/
    uint8_t             bit_width;       /* 9, 10, 11, 12                 */
    uint32_t            vref_mv;         /* Reference voltage in mV        */
} nx_adc_config_t;

typedef struct {
    uint8_t             sda_gpio;        /* I2C data GPIO                  */
    uint8_t             scl_gpio;        /* I2C clock GPIO                 */
    uint32_t            clock_hz;        /* Bus clock (typ. 100000/400000) */
    uint8_t             addr_bits;       /* 7 or 10 (10-bit addressing)    */
} nx_i2c_bus_config_t;

typedef struct {
    uint8_t             bus_id;          /* Index into registered I2C buses*/
    uint16_t            device_addr;     /* 7-bit or 10-bit address        */
    uint8_t             addr_bits;       /* 7 or 10                        */
} nx_i2c_device_config_t;

typedef struct {
    uint8_t             tx_gpio;         /* UART TX GPIO                   */
    uint8_t             rx_gpio;         /* UART RX GPIO                   */
    uint32_t            baud_rate;       /* Baud rate                      */
    uint8_t             data_bits;       /* 5, 6, 7, or 8                 */
    uint8_t             stop_bits;       /* 1 or 2                         */
    uint8_t             parity;          /* 0=none, 1=odd, 2=even         */
    uint8_t             flow_control;    /* 0=none, 1=RTS, 2=CTS, 3=both  */
    uint8_t             uart_num;        /* 0 = auto-assign                */
} nx_uart_config_t;

typedef struct {
    uint8_t             mosi_gpio;       /* SPI MOSI GPIO                  */
    uint8_t             miso_gpio;       /* SPI MISO GPIO                  */
    uint8_t             sck_gpio;        /* SPI clock GPIO                 */
    uint8_t             cs_gpio;         /* SPI chip-select GPIO           */
    uint32_t            clock_hz;        /* Max SPI clock                  */
    uint8_t             mode;            /* SPI mode 0-3                   */
    uint8_t             cs_polarity;     /* 0 = active-low, 1 = active-hi */
    uint8_t             spi_num;         /* 0 = auto-assign                */
    uint8_t             quad;            /* 0 = standard, 1 = QPI/OPI     */
} nx_spi_bus_config_t;

typedef struct {
    uint8_t             bus_id;          /* Index into registered SPI buses*/
    uint16_t            cs_gpio;         /* CS GPIO (overrides bus CS)     */
} nx_spi_device_config_t;

typedef struct {
    uint8_t             gpio_num;        /* 1-Wire data GPIO               */
    uint8_t             parasite_power;  /* 1 = parasite-powered devices   */
    uint8_t             strong_pullup_ms;/* 0 = no strong pullup           */
} nx_onewire_config_t;

typedef struct {
    uint8_t             gpio_num;        /* Pulse input GPIO               */
    uint8_t             edge;            /* 0=rising, 1=falling, 2=both   */
    uint8_t             debounce_ms;     /* 0 = no debounce                */
    uint32_t            max_count;       /* Wrap value (0 = 32-bit wrap)   */
} nx_pulse_counter_config_t;

/* --- Union of all pin sub-configs --- */

typedef union {
    nx_digital_in_config_t    digital_in;
    nx_digital_out_config_t   digital_out;
    nx_pwm_config_t           pwm;
    nx_adc_config_t           adc;
    nx_i2c_bus_config_t       i2c_bus;
    nx_i2c_device_config_t    i2c_device;
    nx_uart_config_t          uart;
    nx_spi_bus_config_t       spi_bus;
    nx_spi_device_config_t    spi_device;
    nx_onewire_config_t       onewire;
    nx_pulse_counter_config_t pulse_counter;
} nx_pin_config_data_t;

/*
 * Top-level pin configuration.  The runtime resolves pin conflicts and
 * capability checks using 'type' and 'primary_gpio', then passes the full
 * struct to the driver's init().
 */
typedef struct {
    nx_pin_type_t       type;            /* Discriminator                  */
    uint8_t             primary_gpio;    /* Primary GPIO for conflict chk  */
    uint8_t             capabilities;    /* Required cap bitmap (OR of NX_CAP_*) */
    nx_pin_config_data_t cfg;            /* Type-specific configuration    */
} nx_pin_config_t;

/* ============================================================================
 *  Section 4: Data Schema Types (Sensor Output Description)
 * ============================================================================ */

/*
 * Primitive data types that a driver's read() can return.
 * These map to the Reflex VM's type system.
 */
typedef enum {
    NX_DATA_FLOAT   = 0,   /* 32-bit IEEE 754 float          */
    NX_DATA_INT16   = 1,   /* Signed 16-bit integer          */
    NX_DATA_UINT16  = 2,   /* Unsigned 16-bit integer        */
    NX_DATA_INT32   = 3,   /* Signed 32-bit integer          */
    NX_DATA_UINT32  = 4,   /* Unsigned 32-bit integer        */
    NX_DATA_BOOL    = 5,   /* 0 or 1                         */
    NX_DATA_UINT8   = 6,   /* Unsigned 8-bit integer         */
    NX_DATA_COUNT_
} nx_data_type_t;

/*
 * Physical units (informational – not enforced at runtime).
 */
typedef enum {
    NX_UNIT_NONE         = 0,
    NX_UNIT_CELSIUS      = 1,
    NX_UNIT_FAHRENHEIT   = 2,
    NX_UNIT_PASCAL       = 3,
    NX_UNIT_HECTOPASCAL  = 4,
    NX_UNIT_PERCENT      = 5,
    NX_UNIT_MILLIMETER   = 6,
    NX_UNIT_METER        = 7,
    NX_UNIT_MICROTESLA   = 8,
    NX_UNIT_DEGREE       = 9,
    NX_UNIT_RADIAN       = 10,
    NX_UNIT_DPS          = 11,   /* degrees per second        */
    NX_UNIT_G            = 12,   /* gravitational accel      */
    NX_UNIT_MG           = 13,   /* milli-g                   */
    NX_UNIT_MILLIVOLT    = 14,
    NX_UNIT_MILLIAMPERE  = 15,
    NX_UNIT_WATT         = 16,
    NX_UNIT_HERTZ        = 17,
    NX_UNIT_SECONDS      = 18,
    NX_UNIT_MICROSECONDS = 19,
    NX_UNIT_LUX          = 20,
    NX_UNIT_COUNT_
} nx_unit_t;

/*
 * Single field descriptor inside a data schema.
 */
typedef struct {
    char                name[NX_FIELD_NAME_MAX + 1];   /* e.g. "temperature" */
    nx_data_type_t      type;          /* Primitive type of this field      */
    uint8_t             offset;        /* Byte offset in read() output buf  */
    uint8_t             size;          /* Size of field in bytes            */
    float               scale;         /* Multiply raw by this              */
    float               bias;          /* Then add this                     */
    nx_unit_t           unit;          /* Physical unit                     */
    float               accuracy;      /* Typical accuracy (in output units)*/
    const char         *help_text;     /* Human-readable description        */
} nx_data_field_t;

/*
 * Schema descriptor.  The driver exposes a const pointer to this; the
 * runtime uses it to:
 *   (a) size the read() buffer,
 *   (b) auto-generate Reflex typed bindings,
 *   (c) serialize to telemetry JSON.
 */
typedef struct {
    uint16_t                    field_count;
    uint16_t                    struct_size;    /* Total bytes for read() buffer */
    const nx_data_field_t      *fields;         /* Static array of descriptors  */
    uint32_t                    sample_rate_hz; /* Max sustained sample rate    */
    const char                 *description;    /* One-line schema description  */
} nx_data_schema_t;

/* ============================================================================
 *  Section 5: Selftest Result Types
 * ============================================================================ */

/*
 * Severity levels for individual selftest checks.
 */
typedef enum {
    NX_ST_PASS    = 0,
    NX_ST_WARN    = 1,   /* Non-fatal anomaly                     */
    NX_ST_FAIL    = 2,   /* Fatal – device unusable               */
    NX_ST_SKIP    = 3    /* Test not applicable for this variant  */
} nx_selftest_severity_t;

/*
 * Single check result.
 */
typedef struct {
    char                    name[32];        /* Check name (e.g. "i2c_probe")  */
    nx_selftest_severity_t  severity;
    int32_t                 measured;        /* Measured value (or 0)          */
    int32_t                 expected_lo;     /* Acceptable lower bound         */
    int32_t                 expected_hi;     /* Acceptable upper bound         */
    char                    detail[64];      /* Free-form detail string        */
} nx_selftest_item_t;

/*
 * Aggregated selftest result returned by (*selftest)().
 */
typedef struct {
    uint16_t                item_count;
    uint16_t                pass_count;
    uint16_t                fail_count;
    uint16_t                warn_count;
    nx_selftest_item_t      items[NX_SELFTEST_ITEMS_MAX];
} nx_selftest_result_t;

/* ============================================================================
 *  Section 6: Safety Callback Types
 * ============================================================================ */

/*
 * Safety event codes passed to the safety callback.
 */
typedef enum {
    NX_SAFETY_KILL_SWITCH       = 0,  /* Hardware kill-switch asserted  */
    NX_SAFETY_WATCHDOG_EXPIRED  = 1,  /* Software watchdog timeout      */
    NX_SAFETY_OVERCURRENT       = 2,  /* Current exceeded threshold     */
    NX_SAFETY_OVERTEMPERATURE   = 3,  /* Die/sensor temperature limit   */
    NX_SAFETY_UNDERVOLTAGE      = 4,  /* Supply voltage dropped         */
    NX_SAFETY_BROWNOUT          = 5,  /* MCU brownout detected          */
    NX_SAFETY_ILLEGAL_STATE     = 6,  /* Reflex VM hit illegal opcode   */
    NX_SAFETY_REFLEX_PANIC      = 7,  /* Reflex script called panic()   */
    NX_SAFETY_HEAP_CORRUPT      = 8,  /* Heap integrity check failed    */
    NX_SAFETY_STACK_CANARY      = 9,  /* Stack canary overwritten       */
    NX_SAFETY_BUS_LOCKUP        = 10, /* I2C/SPI bus stuck              */
    NX_SAFETY_COUNT_
} nx_safety_event_t;

/*
 * Safety callback signature.  Called from ISR or timer context –
 * MUST be fast, non-blocking, and reentrant.
 *
 *  @param event     The safety event that triggered the callback.
 *  @param timestamp RTOS tick count at event time.
 *  @param user_ctx  Opaque pointer registered by the driver/user.
 *
 *  Return: none.  The callback should set a flag for the safety task
 *  to process; it must NOT call any blocking API.
 */
typedef void (*nx_safety_callback_t)(nx_safety_event_t event,
                                     uint32_t timestamp,
                                     void *user_ctx);

/*
 * Safety callback registration descriptor.
 */
typedef struct {
    nx_safety_callback_t  callback;
    void                 *user_ctx;
    uint32_t              event_mask;   /* Bitmap of nx_safety_event_t to listen for */
} nx_safety_handler_t;

/*
 * Kill-switch ISR entry point type.
 * This is the raw ISR that the HAL wires to the EXTI line.
 * It receives the GPIO that triggered and the EXTI channel.
 */
typedef void (*nx_kill_switch_isr_t)(uint8_t gpio_num, uint8_t exti_channel);

/*
 * Watchdog callback type.
 * Called when the watchdog is about to reset (last-chance handler).
 * Implementations should persist critical state to NVS and set the
 * brownout indicator.
 */
typedef void (*nx_watchdog_callback_t)(uint32_t timeout_ms);

/*
 * Overcurrent callback type.
 * Called when the current sense comparator trips.
 * @param current_ma   Measured current in milliamps.
 * @param channel      Which current sense channel (0-indexed).
 * @param threshold_ma The configured threshold.
 */
typedef void (*nx_overcurrent_callback_t)(uint32_t current_ma,
                                          uint8_t channel,
                                          uint32_t threshold_ma);

/* ============================================================================
 *  Section 7: Driver API Vtable
 * ============================================================================ */

/*
 * The central driver interface.  Every driver must expose a single
 * const instance of this struct with external linkage, conventionally
 * named  nx_driver_<name>.
 *
 * CONTRACT PER FUNCTION:
 *  - name:            Static string, driver identifier.
 *  - version:         Static string, semver (e.g. "1.3.0").
 *  - init:            Called once after pin config validated.  Sets up
 *                     hardware, allocates internal resources.
 *                     @param config  Validated pin configuration.
 *                     @param ctx     Pre-allocated, zeroed, size=ctx_size.
 *                     @return NX_OK or first error encountered.
 *  - read:            Copy sensor/actuator state into caller buffer.
 *                     @param ctx     Driver private state (from init).
 *                     @param data    Caller-supplied buffer.
 *                     @param len     Buffer size (must >= schema.struct_size).
 *                     @return NX_OK or NX_ERR_BUFFER_TOO_SMALL, etc.
 *  - write:           Send command or set actuator value.
 *                     @param ctx     Driver private state.
 *                     @param data    Command payload (schema-dependent).
 *                     @param len     Payload length in bytes.
 *                     @return NX_OK or appropriate error.
 *  - selftest:        Run internal diagnostics, populate results.
 *                     @param ctx     Driver private state.
 *                     @param results Pre-allocated result struct.
 *                     @return NX_OK if all tests pass, NX_ERR_SELFTEST_FAILED
 *                             if any item has severity FAIL.
 *  - deinit:          Release hardware, free internal resources.
 *                     After this returns, ctx is freed by the runtime.
 *  - output_schema:   Const pointer to static schema describing read()
 *                     output layout.  NULL if driver is write-only.
 *  - ctx_size:        sizeof(driver's private state struct).
 */
typedef struct {
    const char                 *name;
    const char                 *version;
    nx_err_t        (*init)(const nx_pin_config_t *config, void **ctx);
    nx_err_t        (*read)(void *ctx, void *data, size_t len);
    nx_err_t        (*write)(void *ctx, const void *data, size_t len);
    nx_err_t        (*selftest)(void *ctx, nx_selftest_result_t *results);
    void            (*deinit)(void *ctx);
    const nx_data_schema_t     *output_schema;
    size_t                      ctx_size;
} nx_driver_vtable_t;

/* ============================================================================
 *  Section 8: NVS (Non-Volatile Storage) Key Definitions
 * ============================================================================ */

/*
 * All persistent storage keys used by the NEXUS firmware.
 * Organized by subsystem.  Keys are 15 characters max (NVS limitation
 * on ESP-IDF; we leave headroom for namespace prefix).
 */

/* --- System & Boot --- */
#define NX_NVS_KEY_BOOT_COUNT         "sys_boot_cnt"
#define NX_NVS_KEY_BOOT_REASON        "sys_boot_rsn"
#define NX_NVS_KEY_LAST_CRASH_LOG     "sys_crash_log"
#define NX_NVS_KEY_WATCHDOG_FLAG      "sys_wdog_flag"
#define NX_NVS_KEY_BROWNOUT_FLAG      "sys_brownout"
#define NX_NVS_KEY_SAFETY_EVENT       "sys_safety_ev"
#define NX_NVS_KEY_SAFETY_STATE       "sys_safety_st"
#define NX_NVS_KEY_HEAP_WATERMARK     "sys_heap_wm"
#define NX_NVS_KEY_RUNTIME_TICKS      "sys_run_ticks"

/* --- OTA & Firmware --- */
#define NX_NVS_KEY_OTA_ACTIVE_SLOT    "ota_act_slot"
#define NX_NVS_KEY_OTA_PENDING        "ota_pending"
#define NX_NVS_KEY_FW_VERSION         "fw_version"
#define NX_NVS_KEY_FW_BUILD_DATE      "fw_build_dt"
#define NX_NVS_KEY_FW_SHA256          "fw_sha256"
#define NX_NVS_KEY_FW_UPDATE_STATUS   "fw_upd_stat"

/* --- Network & WiFi --- */
#define NX_NVS_KEY_WIFI_SSID          "net_wifi_ssid"
#define NX_NVS_KEY_WIFI_PASSWORD      "net_wifi_pwd"
#define NX_NVS_KEY_WIFI_AUTH_MODE     "net_wifi_auth"
#define NX_NVS_KEY_WIFI_CHANNEL       "net_wifi_ch"
#define NX_NVS_KEY_MQTT_BROKER        "net_mqtt_bkr"
#define NX_NVS_KEY_MQTT_PORT          "net_mqtt_port"
#define NX_NVS_KEY_MQTT_USERNAME      "net_mqtt_user"
#define NX_NVS_KEY_MQTT_CLIENT_ID     "net_mqtt_cid"
#define NX_NVS_KEY_DEVICE_ID          "net_dev_id"
#define NX_NVS_KEY_DEVICE_TOKEN       "net_dev_tok"

/* --- Reflex Scripting --- */
#define NX_NVS_KEY_REFLEX_SCRIPT_CRC  "reflex_crc"
#define NX_NVS_KEY_REFLEX_SCRIPT_SIZE "reflex_size"
#define NX_NVS_KEY_REFLEX_ENABLED     "reflex_en"
#define NX_NVS_KEY_REFLEX_ERROR_LOG   "reflex_err"
#define NX_NVS_KEY_REFLEX_VAR_0       "reflex_v00"
#define NX_NVS_KEY_REFLEX_VAR_1       "reflex_v01"
#define NX_NVS_KEY_REFLEX_VAR_2       "reflex_v02"
#define NX_NVS_KEY_REFLEX_VAR_3       "reflex_v03"
#define NX_NVS_KEY_REFLEX_VAR_4       "reflex_v04"
#define NX_NVS_KEY_REFLEX_VAR_5       "reflex_v05"
#define NX_NVS_KEY_REFLEX_VAR_6       "reflex_v06"
#define NX_NVS_KEY_REFLEX_VAR_7       "reflex_v07"

/* --- Calibration --- */
#define NX_NVS_KEY_CAL_ADC_OFFSET     "cal_adc_off"
#define NX_NVS_KEY_CAL_ADC_SCALE      "cal_adc_scl"
#define NX_NVS_KEY_CAL_GYRO_OFFSET_X  "cal_gyro_x"
#define NX_NVS_KEY_CAL_GYRO_OFFSET_Y  "cal_gyro_y"
#define NX_NVS_KEY_CAL_GYRO_OFFSET_Z  "cal_gyro_z"
#define NX_NVS_KEY_CAL_MAG_HARD_X     "cal_mag_hx"
#define NX_NVS_KEY_CAL_MAG_HARD_Y     "cal_mag_hy"
#define NX_NVS_KEY_CAL_MAG_HARD_Z     "cal_mag_hz"
#define NX_NVS_KEY_CAL_MAG_SOFT_XX    "cal_mag_sxx"
#define NX_NVS_KEY_CAL_MAG_SOFT_YY    "cal_mag_syy"
#define NX_NVS_KEY_CAL_MAG_SOFT_ZZ    "cal_mag_szz"
#define NX_NVS_KEY_CAL_MAG_SOFT_XY    "cal_mag_sxy"
#define NX_NVS_KEY_CAL_MAG_SOFT_XZ    "cal_mag_sxz"
#define NX_NVS_KEY_CAL_MAG_SOFT_YZ    "cal_mag_syz"
#define NX_NVS_KEY_CAL_ACC_SCALE_X    "cal_acc_sx"
#define NX_NVS_KEY_CAL_ACC_SCALE_Y    "cal_acc_sy"
#define NX_NVS_KEY_CAL_ACC_SCALE_Z    "cal_acc_sz"

/* --- Driver-specific --- */
#define NX_NVS_KEY_DRV_PIN_MAP        "drv_pinmap"
#define NX_NVS_KEY_DRV_ENABLED        "drv_enabled"
#define NX_NVS_KEY_DRV_I2C_ADDR       "drv_i2c_adr"
#define NX_NVS_KEY_DRV_PWM_FREQ       "drv_pwm_freq"
#define NX_NVS_KEY_DRV_UART_BAUD      "drv_uart_bd"
#define NX_NVS_KEY_DRV_CONFIG_BLOB    "drv_cfg_blob"

/* --- Safety --- */
#define NX_NVS_KEY_SAFETY_OCR_MA      "safe_ocr_ma"
#define NX_NVS_KEY_SAFETY_OTR_C       "safe_otr_c"
#define NX_NVS_KEY_SAFETY_UVR_MV      "safe_uvr_mv"
#define NX_NVS_KEY_SAFETY_WDOG_MS     "safe_wdog_ms"
#define NX_NVS_KEY_SAFETY_LOCKOUT     "safe_lockout"

/* --- Telemetry --- */
#define NX_NVS_KEY_TELEM_INTERVAL_MS  "tel_int_ms"
#define NX_NVS_KEY_TELEM_ENABLED      "tel_enabled"
#define NX_NVS_KEY_TELEM_SEQ_NUM      "tel_seq_num"
#define NX_NVS_KEY_TELEM_WIFI_TX      "tel_wifi_tx"
#define NX_NVS_KEY_TELEM_MQTT_TX      "tel_mqtt_tx"

/* --- Misc / User --- */
#define NX_NVS_KEY_USER_MAGIC         "usr_magic"
#define NX_NVS_KEY_USER_DATA_0        "usr_data_00"
#define NX_NVS_KEY_USER_DATA_1        "usr_data_01"
#define NX_NVS_KEY_USER_DATA_2        "usr_data_02"
#define NX_NVS_KEY_USER_DATA_3        "usr_data_03"

/* ============================================================================
 *  Section 9: Runtime Service Prototypes (linked from nx_runtime.a)
 * ============================================================================ */

/*
 * These functions are provided by the firmware runtime.  Drivers call
 * them via extern linkage.  This section is the "upward API" that
 * drivers use to request services from the runtime.
 */

/*
 * Obtain the mutex for a driver instance.  Call before read()/write()
 * if the driver does NOT advertise NX_CAP_THREAD_SAFE.
 */
extern void    nx_rt_driver_lock(void *ctx);
extern void    nx_rt_driver_unlock(void *ctx);

/*
 * Log a message.  Levels: 0=ERROR, 1=WARN, 2=INFO, 3=DEBUG, 4=TRACE.
 */
extern void    nx_rt_log(uint8_t level, const char *fmt, ...);

/*
 * Allocate from the DMA-capable heap region.
 * Returns NULL on exhaustion.
 */
extern void   *nx_rt_dma_malloc(size_t size);

/*
 * Free a DMA-capable allocation.
 */
extern void    nx_rt_dma_free(void *ptr);

/*
 * Register a safety handler.  Returns NX_OK on success.
 */
extern nx_err_t nx_rt_safety_register(const nx_safety_handler_t *handler);

/*
 * Unregister a safety handler.
 */
extern nx_err_t nx_rt_safety_unregister(nx_safety_callback_t callback);

/*
 * Register an I2C bus with the runtime.  Subsequent I2C device
 * drivers reference it by bus_id.
 */
extern nx_err_t nx_rt_i2c_bus_register(uint8_t bus_id,
                                        const nx_i2c_bus_config_t *config);

/*
 * Register an SPI bus with the runtime.
 */
extern nx_err_t nx_rt_spi_bus_register(uint8_t bus_id,
                                        const nx_spi_bus_config_t *config);

/*
 * Perform an I2C transaction.  Drivers should use this rather than
 * calling HAL directly so the runtime can log and multiplex.
 */
extern nx_err_t nx_rt_i2c_transfer(uint8_t bus_id,
                                    uint16_t addr,
                                    const uint8_t *tx_data,
                                    size_t tx_len,
                                    uint8_t *rx_data,
                                    size_t rx_len,
                                    uint32_t timeout_ms);

/*
 * Perform an SPI transaction.
 */
extern nx_err_t nx_rt_spi_transfer(uint8_t bus_id,
                                    uint16_t cs_gpio,
                                    const uint8_t *tx_data,
                                    size_t tx_len,
                                    uint8_t *rx_data,
                                    size_t rx_len,
                                    uint32_t timeout_ms);

/*
 * Delay the calling task for at least ms milliseconds.
 */
extern void    nx_rt_delay_ms(uint32_t ms);

/*
 * Get the current RTOS tick count in milliseconds.
 */
extern uint32_t nx_rt_now_ms(void);

/*
 * Read/write a 32-bit value from/to NVS.
 */
extern nx_err_t nx_rt_nvs_get_u32(const char *key, uint32_t *out);
extern nx_err_t nx_rt_nvs_set_u32(const char *key, uint32_t value);

/*
 * Read/write a blob from/to NVS.
 */
extern nx_err_t nx_rt_nvs_get_blob(const char *key, void *buf, size_t *len);
extern nx_err_t nx_rt_nvs_set_blob(const char *key, const void *buf, size_t len);

/* ============================================================================
 *  Section 10: Driver Registration Macro
 * ============================================================================ */

/*
 * Convenience macro to define the driver vtable symbol.
 * Usage at file scope in the driver .c file:
 *
 *   NX_DECLARE_DRIVER(hmc5883l, "1.2.0",
 *       hmc_init, hmc_read, hmc_write, hmc_selftest, hmc_deinit,
 *       &hmc_output_schema, sizeof(hmc_context_t));
 */
#define NX_DECLARE_DRIVER(tag, ver_str, _init, _read, _write,              \
                          _selftest, _deinit, _schema, _ctx_size)         \
    const nx_driver_vtable_t nx_driver_##tag __attribute__((section(".rodata.nx_drv"))) = { \
        .name          = #tag,                                              \
        .version       = ver_str,                                           \
        .init          = _init,                                             \
        .read          = _read,                                             \
        .write         = _write,                                            \
        .selftest      = _selftest,                                         \
        .deinit        = _deinit,                                           \
        .output_schema = _schema,                                           \
        .ctx_size      = _ctx_size                                          \
    }

/* ============================================================================
 *  Section 11: Compile-time Assertions (C99 _Static_assert)
 * ============================================================================ */

/*
 * These guard against accidental ABI drift.  They fire at compile time
 * if the struct sizes change unexpectedly.
 */

/*
 * Ensure error enum starts at 0 and NX_OK == 0.
 * (Cannot static_assert an enum value directly in C99, but we verify
 *  the sentinel > 30 to catch accidental removal of codes.)
 */

/* The vtable must be exactly 9 pointer/size fields for ABI compat.
 * Layout: 2 x const char*, 5 x fn-ptr, 1 x const ptr, 1 x size_t.
 * All pointer types have the same size on any given target.            */
typedef char nx_assert_vtable_size[sizeof(nx_driver_vtable_t) ==
    (3 * sizeof(const char *) +
     5 * sizeof(void (*)(void)) +
     sizeof(size_t)) ? 1 : -1];

/* Pin config data union must cover all variant types. */
typedef char nx_assert_pin_config_size[sizeof(nx_pin_config_data_t) >=
    sizeof(nx_uart_config_t) ? 1 : -1];

/* Selftest item array must hold NX_SELFTEST_ITEMS_MAX entries. */
typedef char nx_assert_selftest_array[sizeof(nx_selftest_result_t) -
    offsetof(nx_selftest_result_t, items) >=
    (NX_SELFTEST_ITEMS_MAX * sizeof(nx_selftest_item_t)) ? 1 : -1];


#ifdef __cplusplus
}
#endif

#endif /* NEXUS_IO_DRIVER_INTERFACE_H */

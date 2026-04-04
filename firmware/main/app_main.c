/**
 * NEXUS Firmware — Application Entry Point
 *
 * Creates and manages the 6 FreeRTOS tasks per memory_map_and_partitions.md §5:
 *   1. vm_tick_task      — Bytecode VM execution at 1ms tick (priority 20)
 *   2. wire_rx_task      — Wire protocol frame reception (priority 18)
 *   3. wire_tx_task      — Wire protocol frame transmission (priority 17)
 *   4. io_poll_task      — Sensor polling and actuator output (priority 15)
 *   5. safety_task       — Safety supervisor, heartbeat, watchdog (priority 24)
 *   6. app_task          — Application logic, command processing (priority 10)
 */

#include <stdio.h>
#include <string.h>

#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "esp_log.h"
#include "esp_system.h"
#include "nvs_flash.h"

#include "vm.h"

static const char *TAG = "nexus";

/* Task stack sizes (4KB each per spec) */
#define TASK_STACK_SIZE 4096

/* Task priorities per memory_map_and_partitions.md §5 */
#define PRIORITY_SAFETY     24
#define PRIORITY_VM_TICK    20
#define PRIORITY_WIRE_RX    18
#define PRIORITY_WIRE_TX    17
#define PRIORITY_IO_POLL    15
#define PRIORITY_APP        10

/* Static VM state — zero heap allocation */
static vm_state_t g_vm_state;

/* Task handles for watchdog monitoring */
static TaskHandle_t h_safety_task;
static TaskHandle_t h_vm_tick_task;
static TaskHandle_t h_wire_rx_task;
static TaskHandle_t h_wire_tx_task;
static TaskHandle_t h_io_poll_task;
static TaskHandle_t h_app_task;

static void safety_task(void *arg)
{
    (void)arg;
    ESP_LOGI(TAG, "safety_task started (priority %d)", PRIORITY_SAFETY);

    while (1) {
        /* TODO Sprint 1.1: Four-tier safety monitoring
         * - Feed hardware watchdog (0x55/0xAA pattern)
         * - Check heartbeat from Jetson
         * - Monitor task watchdog check-ins
         * - Enforce safety state machine transitions
         */
        vTaskDelay(pdMS_TO_TICKS(10));
    }
}

static void vm_tick_task(void *arg)
{
    (void)arg;
    ESP_LOGI(TAG, "vm_tick_task started (priority %d)", PRIORITY_VM_TICK);

    while (1) {
        /* TODO Sprint 0.2: Execute VM tick
         * - Copy sensor registers into VM state
         * - Execute bytecode (vm_execute_tick)
         * - Copy actuator registers out
         * - Clamp all actuator outputs to safe ranges
         */
        vTaskDelay(pdMS_TO_TICKS(1));
    }
}

static void wire_rx_task(void *arg)
{
    (void)arg;
    ESP_LOGI(TAG, "wire_rx_task started (priority %d)", PRIORITY_WIRE_RX);

    while (1) {
        /* TODO Sprint 0.3: Wire protocol reception
         * - Read bytes from UART
         * - COBS decode frames
         * - Validate CRC-16
         * - Dispatch to message handlers
         */
        vTaskDelay(pdMS_TO_TICKS(1));
    }
}

static void wire_tx_task(void *arg)
{
    (void)arg;
    ESP_LOGI(TAG, "wire_tx_task started (priority %d)", PRIORITY_WIRE_TX);

    while (1) {
        /* TODO Sprint 0.3: Wire protocol transmission
         * - Dequeue messages from priority TX queues
         * - Build message header
         * - COBS encode frame
         * - Transmit via UART
         */
        vTaskDelay(pdMS_TO_TICKS(1));
    }
}

static void io_poll_task(void *arg)
{
    (void)arg;
    ESP_LOGI(TAG, "io_poll_task started (priority %d)", PRIORITY_IO_POLL);

    while (1) {
        /* TODO Sprint 0.2+: I/O polling
         * - Poll I2C/SPI sensors
         * - Write actuator outputs to hardware
         * - Update sensor registers for VM
         */
        vTaskDelay(pdMS_TO_TICKS(1));
    }
}

static void app_task(void *arg)
{
    (void)arg;
    ESP_LOGI(TAG, "app_task started (priority %d)", PRIORITY_APP);

    while (1) {
        /* TODO Sprint 0.4: Application logic
         * - Process incoming commands
         * - Manage reflex deployment
         * - Handle trust-gated operations
         */
        vTaskDelay(pdMS_TO_TICKS(100));
    }
}

void app_main(void)
{
    ESP_LOGI(TAG, "NEXUS Firmware v0.1.0 starting...");
    ESP_LOGI(TAG, "Target: ESP32-S3, CPU: 240MHz, PSRAM: 8MB");

    /* Initialize NVS */
    esp_err_t ret = nvs_flash_init();
    if (ret == ESP_ERR_NVS_NO_FREE_PAGES || ret == ESP_ERR_NVS_NEW_VERSION_FOUND) {
        ESP_ERROR_CHECK(nvs_flash_erase());
        ret = nvs_flash_init();
    }
    ESP_ERROR_CHECK(ret);

    /* Initialize VM state */
    vm_init(&g_vm_state);
    ESP_LOGI(TAG, "VM initialized: stack=%d, vars=%d, sensors=%d, actuators=%d",
             VM_STACK_SIZE, VM_VAR_COUNT, VM_SENSOR_COUNT, VM_ACTUATOR_COUNT);

    /* Create tasks — highest priority first */
    xTaskCreate(safety_task,  "safety",  TASK_STACK_SIZE, NULL, PRIORITY_SAFETY,  &h_safety_task);
    xTaskCreate(vm_tick_task, "vm_tick", TASK_STACK_SIZE, NULL, PRIORITY_VM_TICK, &h_vm_tick_task);
    xTaskCreate(wire_rx_task, "wire_rx", TASK_STACK_SIZE, NULL, PRIORITY_WIRE_RX, &h_wire_rx_task);
    xTaskCreate(wire_tx_task, "wire_tx", TASK_STACK_SIZE, NULL, PRIORITY_WIRE_TX, &h_wire_tx_task);
    xTaskCreate(io_poll_task, "io_poll", TASK_STACK_SIZE, NULL, PRIORITY_IO_POLL, &h_io_poll_task);
    xTaskCreate(app_task,     "app",     TASK_STACK_SIZE, NULL, PRIORITY_APP,     &h_app_task);

    ESP_LOGI(TAG, "All 6 RTOS tasks created. System running.");
}

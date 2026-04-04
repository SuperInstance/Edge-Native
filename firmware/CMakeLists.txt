# NEXUS ESP32-S3 Firmware — ESP-IDF Top-Level Project CMakeLists.txt
# Build with: idf.py set-target esp32s3 && idf.py build

cmake_minimum_required(VERSION 3.16)

# ESP-IDF component directories
set(EXTRA_COMPONENT_DIRS
    "${CMAKE_CURRENT_SOURCE_DIR}/nexus_vm"
    "${CMAKE_CURRENT_SOURCE_DIR}/wire_protocol"
    "${CMAKE_CURRENT_SOURCE_DIR}/safety"
    "${CMAKE_CURRENT_SOURCE_DIR}/drivers"
)

include($ENV{IDF_PATH}/tools/cmake/project.cmake)
project(nexus_firmware)

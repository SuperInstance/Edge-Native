# NEXUS Distributed Intelligence Platform — Top-Level CMakeLists.txt
# This file orchestrates builds for both ESP32-S3 firmware and host-based tests.
#
# Usage:
#   ESP32 firmware build: cd firmware && idf.py build
#   Host unit tests:      mkdir build && cd build && cmake -DNEXUS_HOST_TEST=ON .. && make && ctest

cmake_minimum_required(VERSION 3.16)
project(nexus VERSION 0.1.0 LANGUAGES C CXX)

option(NEXUS_HOST_TEST "Build host-side unit tests (Unity framework)" OFF)

if(NEXUS_HOST_TEST)
    enable_testing()

    set(CMAKE_C_STANDARD 11)
    set(CMAKE_C_STANDARD_REQUIRED ON)
    set(CMAKE_C_FLAGS "${CMAKE_C_FLAGS} -Wall -Wextra -Werror -Wno-unused-parameter")

    # Unity test framework (vendored in third_party/)
    add_library(unity STATIC third_party/unity/src/unity.c)
    target_include_directories(unity PUBLIC third_party/unity/src)

    # VM library (compiled for host)
    add_library(nexus_vm STATIC
        firmware/nexus_vm/vm_core.c
        firmware/nexus_vm/vm_opcodes.c
        firmware/nexus_vm/vm_validate.c
        firmware/nexus_vm/vm_syscalls.c
    )
    target_include_directories(nexus_vm PUBLIC
        firmware/nexus_vm/include
        shared/bytecode
    )

    # Wire protocol library (compiled for host)
    add_library(nexus_wire STATIC
        firmware/wire_protocol/cobs.c
        firmware/wire_protocol/crc16.c
    )
    target_include_directories(nexus_wire PUBLIC
        firmware/wire_protocol
    )

    # Unit tests
    file(GLOB VM_TEST_SOURCES tests/unit/firmware/test_vm_*.c)
    foreach(test_src ${VM_TEST_SOURCES})
        get_filename_component(test_name ${test_src} NAME_WE)
        add_executable(${test_name} ${test_src})
        target_link_libraries(${test_name} nexus_vm unity m)
        add_test(NAME ${test_name} COMMAND ${test_name})
    endforeach()

    file(GLOB WIRE_TEST_SOURCES tests/unit/firmware/test_cobs*.c tests/unit/firmware/test_crc*.c)
    foreach(test_src ${WIRE_TEST_SOURCES})
        get_filename_component(test_name ${test_src} NAME_WE)
        add_executable(${test_name} ${test_src})
        target_link_libraries(${test_name} nexus_wire unity m)
        add_test(NAME ${test_name} COMMAND ${test_name})
    endforeach()
endif()

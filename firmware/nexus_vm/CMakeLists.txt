idf_component_register(
    SRCS "vm_core.c" "vm_opcodes.c" "vm_validate.c" "vm_syscalls.c"
    INCLUDE_DIRS "include" "../../shared/bytecode"
)

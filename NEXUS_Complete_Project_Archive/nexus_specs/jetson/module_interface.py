"""
NEXUS Jetson Module Interface
==============================

Defines the abstract base contract for all modules running on the Jetson
cognitive layer.  Every module (safety monitor, reflex runner, learning
pipeline, chat interface, etc.) **must** subclass :class:`NexusModule` and
implement the lifecycle and callback methods declared here.

Design goals
------------
* **Deterministic startup ordering** – modules declare their dependencies
  and the runtime resolves them into a valid topological sort.
* **Hot-reload** – module code can be replaced at runtime without restarting
  the host process or its sibling modules.
* **Resource budgets** – each module declares its GPU memory, CPU, and RAM
  requirements up-front so the scheduler can reject overcommitted loads.
* **Type-safe telemetry & safety callbacks** – structured :class:`dataclass`
  types prevent ad-hoc dictionary proliferation.

Usage
-----
::

    class MyModule(NexusModule):
        name = "my-module"
        dependencies: ClassVar[list[str]] = ["core-telemetry"]

        async def init(self, config: ModuleConfig) -> None:
            ...

        async def start(self) -> None:
            ...

        # ... implement remaining abstract methods
"""

from __future__ import annotations

import abc
import asyncio
import enum
import hashlib
import importlib
import importlib.util
import logging
import sys
import time
import traceback
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import (
    Any,
    Callable,
    ClassVar,
    Coroutine,
    Dict,
    List,
    Optional,
    Sequence,
    Set,
)

# ---------------------------------------------------------------------------
# Logger
# ---------------------------------------------------------------------------
logger = logging.getLogger("nexus.module")


# ===========================================================================
# Enums & Constants
# ===========================================================================

class ModuleState(str, Enum):
    """Runtime lifecycle state of a module."""
    UNINITIALIZED = "uninitialized"
    INITIALIZING = "initializing"
    READY = "ready"
    STARTING = "starting"
    RUNNING = "running"
    STOPPING = "stopping"
    STOPPED = "stopped"
    ERROR = "error"
    RELOADING = "reloading"


class HealthStatus(str, Enum):
    """Health result from a module health check."""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


class SafetySeverity(str, Enum):
    """Severity levels for safety events."""
    INFO = "info"
    WARNING = "warning"
    CAUTION = "caution"
    CRITICAL = "critical"
    EMERGENCY = "emergency"


class HotReloadStrategy(str, Enum):
    """Strategy for applying a hot-reload."""
    GRACEFUL = "graceful"       # Call stop() on old, then start() on new
    IMMEDIATE = "immediate"     # Swap in-place, no stop/start cycle
    ROLLING = "rolling"         # Drain in-flight work, then swap


# ===========================================================================
# Data Classes
# ===========================================================================

@dataclass(frozen=True)
class ResourceBudget:
    """Declarative resource requirements for a module.

    The runtime uses these values to admit or reject a module from running on
    a given Jetson node.
    """
    gpu_memory_mb: float = 0.0
    cpu_percent: float = 0.0      # 0.0 – 100.0
    ram_mb: float = 0.0
    max_concurrent_tasks: int = 8
    shared_memory_mb: float = 0.0

    def validate(self) -> List[str]:
        """Return a list of constraint violation messages."""
        errors: List[str] = []
        if self.gpu_memory_mb < 0:
            errors.append("gpu_memory_mb must be >= 0")
        if not (0.0 <= self.cpu_percent <= 100.0):
            errors.append("cpu_percent must be in [0, 100]")
        if self.ram_mb < 0:
            errors.append("ram_mb must be >= 0")
        if self.max_concurrent_tasks < 1:
            errors.append("max_concurrent_tasks must be >= 1")
        if self.shared_memory_mb < 0:
            errors.append("shared_memory_mb must be >= 0")
        return errors


@dataclass(frozen=True)
class ResourceUsage:
    """Actual resource consumption reported at runtime."""
    gpu_memory_used_mb: float = 0.0
    gpu_percent: float = 0.0
    cpu_percent: float = 0.0
    ram_used_mb: float = 0.0
    active_tasks: int = 0
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class ModuleConfig:
    """Configuration object passed to :meth:`NexusModule.init`.

    Values come from the site-wide YAML/JSON config, merged with
    module-specific overrides.
    """
    module_name: str
    site_id: str
    node_id: str
    settings: Dict[str, Any] = field(default_factory=dict)
    secrets: Dict[str, str] = field(default_factory=dict)
    environment: str = "production"

    def get(self, key: str, default: Any = None) -> Any:
        return self.settings.get(key, default)

    def require(self, key: str) -> Any:
        """Return setting *key* or raise :class:`KeyError`."""
        if key not in self.settings:
            raise KeyError(f"Required config key '{key}' not found for module '{self.module_name}'")
        return self.settings[key]


@dataclass
class TelemetryEvent:
    """Structured telemetry datum received from an ESP32 node via MQTT.

    Instances are delivered to modules via :meth:`NexusModule.on_telemetry`.
    """
    node_id: str
    timestamp: datetime
    readings: Dict[str, Any] = field(default_factory=dict)
    sequence: int = 0
    metadata: Dict[str, str] = field(default_factory=dict)
    raw_payload: bytes = b""

    # Convenience accessors
    def get_reading(self, key: str, default: float = 0.0) -> float:
        """Get a numeric sensor reading."""
        val = self.readings.get(key, default)
        try:
            return float(val)
        except (TypeError, ValueError):
            return default

    def get_flag(self, key: str, default: bool = False) -> bool:
        """Get a boolean sensor flag."""
        val = self.readings.get(key, default)
        if isinstance(val, bool):
            return val
        if isinstance(val, str):
            return val.lower() in ("true", "1", "yes")
        return default


@dataclass
class SafetyEvent:
    """Safety-critical event routed to all modules via :meth:`NexusModule.on_safety_event`.

    These events MUST be handled within the configured timeout or the module
    will be marked unhealthy.
    """
    event_id: str = field(default_factory=lambda: uuid.uuid4().hex)
    node_id: str = ""
    source: str = "unknown"
    severity: SafetySeverity = SafetySeverity.WARNING
    category: str = "other"
    description: str = ""
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    resolved: bool = False
    resolution: str = ""
    affected_subsystems: List[str] = field(default_factory=list)
    reflex_id: str = ""
    sensor_id: str = ""
    actions_taken: List[str] = field(default_factory=list)
    metadata: Dict[str, str] = field(default_factory=dict)


@dataclass
class HealthReport:
    """Result of a module health check."""
    status: HealthStatus = HealthStatus.UNKNOWN
    message: str = ""
    resource_usage: Optional[ResourceUsage] = None
    details: Dict[str, Any] = field(default_factory=dict)
    checked_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class ModuleStatus:
    """Snapshot of a module's current runtime state."""
    module_name: str
    state: ModuleState = ModuleState.UNINITIALIZED
    health: HealthStatus = HealthStatus.UNKNOWN
    uptime_seconds: float = 0.0
    config_hash: str = ""
    resource_budget: Optional[ResourceBudget] = None
    resource_usage: Optional[ResourceUsage] = None
    dependency_names: List[str] = field(default_factory=list)
    loaded_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    error_message: str = ""


# ===========================================================================
# Hot-reload context
# ===========================================================================

@dataclass
class HotReloadRequest:
    """Request object describing what to reload."""
    module_name: str
    strategy: HotReloadStrategy = HotReloadStrategy.GRACEFUL
    new_code_path: Optional[str] = None   # Path to new .py file
    new_config: Optional[ModuleConfig] = None


@dataclass
class HotReloadResult:
    """Result of a hot-reload operation."""
    success: bool
    module_name: str
    previous_config_hash: str
    new_config_hash: str
    reload_time_ms: float
    strategy_used: HotReloadStrategy
    message: str = ""
    error_detail: str = ""


# ===========================================================================
# Abstract Base Class
# ===========================================================================

class NexusModule(abc.ABC):
    """Abstract base class for all Jetson cognitive-layer modules.

    Subclasses **must**:

    * Set :attr:`name` (a ``ClassVar`` or instance attribute).
    * Set :attr:`dependencies` (a ``ClassVar[list[str]]`` of module names
      this module depends on).
    * Set :attr:`resource_budget` (a ``ClassVar[ResourceBudget]`` or
      override the :meth:`resource_budget` property).
    * Implement all ``@abstractmethod`` methods.

    The module runtime (``ModuleHost`` below) manages the lifecycle:

    1. Resolve dependency order via topological sort.
    2. Call :meth:`init` with the module's :class:`ModuleConfig`.
    3. Call :meth:`start` to begin async operation.
    4. Route telemetry & safety events to the appropriate callbacks.
    5. On shutdown or hot-reload, call :meth:`stop`.
    """

    # Subclass overrides -------------------------------------------------------
    name: ClassVar[str] = ""                     # MUST be set by subclass
    dependencies: ClassVar[list[str]] = []       # Names of required modules
    _resource_budget: ClassVar[Optional[ResourceBudget]] = None

    # -----------------------------------------------------------------------
    # Resource budget – can be overridden as a property for dynamic values
    # -----------------------------------------------------------------------
    @classmethod
    def resource_budget(cls) -> ResourceBudget:
        """Return the resource budget for this module.

        Override as a classmethod or set the ``_resource_budget`` class var.
        """
        if cls._resource_budget is not None:
            return cls._resource_budget
        return ResourceBudget()

    # -----------------------------------------------------------------------
    # Lifecycle
    # -----------------------------------------------------------------------
    @abc.abstractmethod
    async def init(self, config: ModuleConfig) -> None:
        """Initialize the module with its configuration.

        Called once during startup **before** any dependent module is started.
        Use this to allocate GPU memory, load models, open connections, etc.

        Raises:
            RuntimeError: If initialization cannot succeed.
        """

    @abc.abstractmethod
    async def start(self) -> None:
        """Begin the module's main async operation.

        Called after all dependencies are in :attr:`ModuleState.RUNNING`.
        The method should return quickly; any long-running work must be
        scheduled as asyncio tasks.
        """

    @abc.abstractmethod
    async def stop(self) -> None:
        """Gracefully shut down the module.

        Called during shutdown or before a hot-reload.  The module must:
        * Cancel all background tasks.
        * Release GPU memory.
        * Close connections.
        * Flush any buffers.
        """

    # -----------------------------------------------------------------------
    # Event callbacks
    # -----------------------------------------------------------------------
    async def on_telemetry(self, event: TelemetryEvent) -> None:
        """Handle an incoming telemetry event from an ESP32 node.

        Override this to process sensor data.  The default implementation
        is a no-op so modules that don't care about telemetry don't need
        to override it.

        .. note::
            This callback MUST return within the configured event-loop
            timeout (default 5 s) or the module will be flagged degraded.
        """

    async def on_safety_event(self, event: SafetyEvent) -> None:
        """Handle a safety-critical event.

        **All modules MUST respond to safety events.** The default
        implementation logs the event and marks the module as acknowledging
        it. Override for module-specific safety logic.

        .. note::
            This callback MUST return within the safety timeout (default 1 s).
        """
        logger.warning(
            "[SAFETY] %s – %s: %s (severity=%s)",
            self.name, event.event_id, event.description, event.severity.value,
        )

    # -----------------------------------------------------------------------
    # Status & health
    # -----------------------------------------------------------------------
    @abc.abstractmethod
    async def get_status(self) -> ModuleStatus:
        """Return a snapshot of the module's current status."""

    @abc.abstractmethod
    async def health_check(self) -> HealthReport:
        """Run a health check and return a detailed report.

        This is called periodically by the :class:`ModuleHost`.
        """

    # -----------------------------------------------------------------------
    # Hot-reload support (optional)
    # -----------------------------------------------------------------------
    async def on_before_reload(self) -> None:
        """Called just before the module instance is replaced.

        Override to flush state, persist buffers, or notify dependents.
        The default implementation calls :meth:`stop`.
        """
        await self.stop()

    async def on_after_reload(self, previous_state: Dict[str, Any]) -> None:
        """Called on the **new** instance after a hot-reload completes.

        *previous_state* is the serializable state snapshot returned by
        :meth:`capture_state` on the old instance.

        Override to restore state from the previous instance.
        """

    def capture_state(self) -> Dict[str, Any]:
        """Return a JSON-serializable snapshot of the module's state.

        Used to transfer state across hot-reloads.  The default returns
        an empty dict.
        """
        return {}

    # -----------------------------------------------------------------------
    # Resource reporting
    # -----------------------------------------------------------------------
    async def get_resource_usage(self) -> ResourceUsage:
        """Report actual resource consumption.

        Override with GPU/CPU/RAM measurements. The default returns zeros.
        """
        return ResourceUsage()

    # -----------------------------------------------------------------------
    # Internal state (managed by ModuleHost, not subclasses)
    # -----------------------------------------------------------------------
    _state: ModuleState = ModuleState.UNINITIALIZED
    _start_time: Optional[float] = None
    _config: Optional[ModuleConfig] = None
    _config_hash: str = ""
    _tasks: Set[asyncio.Task] = None  # type: ignore[assignment]

    def __init_subclass__(cls, **kwargs: Any) -> None:
        super().__init_subclass__(**kwargs)
        # Ensure subclasses set a name
        if not getattr(cls, "name", ""):
            raise TypeError(
                f"Module subclass {cls.__qualname__} must set a class-level "
                f"'name' attribute (e.g. name = 'my-module')"
            )

    def __init__(self) -> None:
        self._state = ModuleState.UNINITIALIZED
        self._start_time: Optional[float] = None
        self._config: Optional[ModuleConfig] = None
        self._config_hash: str = ""
        self._tasks: Set[asyncio.Task] = set()

    # -- helpers for subclasses -------------------------------------------
    def _create_task(self, coro: Coroutine[Any, Any, Any], name: str = "") -> asyncio.Task:
        """Schedule a background asyncio task that is tracked and auto-cancelled on stop."""
        task = asyncio.create_task(coro, name=name or f"{self.name}-task")
        self._tasks.add(task)
        task.add_done_callback(self._tasks.discard)
        return task

    def _cancel_all_tasks(self) -> None:
        """Cancel every task created via :meth:`_create_task`."""
        for task in self._tasks:
            task.cancel()
        self._tasks.clear()

    def _compute_config_hash(self, config: ModuleConfig) -> str:
        """Compute a SHA-256 hash of the config settings for change detection."""
        raw = str(sorted(config.settings.items())).encode()
        return hashlib.sha256(raw).hexdigest()[:16]

    def _uptime_seconds(self) -> float:
        if self._start_time is None:
            return 0.0
        return time.monotonic() - self._start_time


# ===========================================================================
# Dependency Resolution
# ===========================================================================

class DependencyError(Exception):
    """Raised when module dependencies cannot be resolved."""


def resolve_module_order(modules: Sequence[NexusModule]) -> List[NexusModule]:
    """Topological sort of modules based on their declared dependencies.

    Args:
        modules: All registered module instances.

    Returns:
        Ordered list where each module appears after all its dependencies.

    Raises:
        DependencyError: If a circular dependency is detected or a dependency
            refers to a module that is not registered.
    """
    index: Dict[str, NexusModule] = {m.name: m for m in modules}
    visited: Set[str] = set()
    order: List[NexusModule] = []
    visiting: Set[str] = set()  # For cycle detection

    def _visit(name: str) -> None:
        if name in visited:
            return
        if name in visiting:
            cycle = " -> ".join(visiting) + f" -> {name}"
            raise DependencyError(f"Circular dependency detected: {cycle}")
        if name not in index:
            raise DependencyError(
                f"Module '{name}' required as dependency but not registered. "
                f"Available: {sorted(index.keys())}"
            )
        visiting.add(name)
        module = index[name]
        for dep in module.dependencies:
            _visit(dep)
        visiting.discard(name)
        visited.add(name)
        order.append(module)

    for m in modules:
        _visit(m.name)

    return order


# ===========================================================================
# Module Host – manages lifecycle of all modules on a single Jetson node
# ===========================================================================

class ModuleHost:
    """Host process that manages the lifecycle of all :class:`NexusModule`
    instances on a single Jetson node.

    Responsibilities:

    * Topologically sort modules and start them in order.
    * Route telemetry and safety events.
    * Run periodic health checks.
    * Execute hot-reloads.
    * Enforce resource budgets.
    """

    def __init__(
        self,
        site_id: str,
        node_id: str,
        health_check_interval_s: float = 30.0,
        safety_event_timeout_s: float = 1.0,
        telemetry_event_timeout_s: float = 5.0,
    ) -> None:
        self.site_id = site_id
        self.node_id = node_id
        self.health_check_interval_s = health_check_interval_s
        self.safety_event_timeout_s = safety_event_timeout_s
        self.telemetry_event_timeout_s = telemetry_event_timeout_s

        self._modules: Dict[str, NexusModule] = {}
        self._ordered: List[NexusModule] = []
        self._running = False
        self._health_task: Optional[asyncio.Task] = None
        self._telemetry_handlers: List[Callable[[TelemetryEvent], Coroutine[Any, Any, None]]] = []
        self._safety_handlers: List[Callable[[SafetyEvent], Coroutine[Any, Any, None]]] = []

    # -- Registration -----------------------------------------------------
    def register(self, module: NexusModule, config: ModuleConfig) -> None:
        """Register a module instance with its configuration.

        Modules must be registered **before** :meth:`start_all` is called.
        """
        if module.name in self._modules:
            raise ValueError(f"Module '{module.name}' is already registered")
        module._config = config
        module._config_hash = module._compute_config_hash(config)
        self._modules[module.name] = module
        logger.info("Registered module '%s' with %d dependencies",
                     module.name, len(module.dependencies))

    # -- Startup / Shutdown -----------------------------------------------
    async def start_all(self) -> None:
        """Initialize and start all registered modules in dependency order."""
        modules = list(self._modules.values())

        # 1. Validate resource budgets
        for m in modules:
            budget = m.resource_budget()
            errors = budget.validate()
            if errors:
                raise ValueError(f"Module '{m.name}' has invalid resource budget: {errors}")

        # 2. Resolve dependency order
        self._ordered = resolve_module_order(modules)
        logger.info("Module start order: %s", [m.name for m in self._ordered])

        # 3. Initialize each module
        for m in self._ordered:
            assert m._config is not None
            m._state = ModuleState.INITIALIZING
            try:
                await m.init(m._config)
            except Exception:
                m._state = ModuleState.ERROR
                logger.exception("Module '%s' failed to initialize", m.name)
                raise
            m._state = ModuleState.READY
            logger.info("Module '%s' initialized", m.name)

        # 4. Start each module
        for m in self._ordered:
            m._state = ModuleState.STARTING
            try:
                await m.start()
            except Exception:
                m._state = ModuleState.ERROR
                logger.exception("Module '%s' failed to start", m.name)
                raise
            m._state = ModuleState.RUNNING
            m._start_time = time.monotonic()
            logger.info("Module '%s' is running", m.name)

        # 5. Start background health checker
        self._running = True
        self._health_task = asyncio.create_task(self._health_loop())

    async def stop_all(self) -> None:
        """Stop all modules in reverse dependency order."""
        self._running = False
        if self._health_task:
            self._health_task.cancel()
            try:
                await self._health_task
            except asyncio.CancelledError:
                pass

        for m in reversed(self._ordered):
            m._state = ModuleState.STOPPING
            try:
                await m.stop()
            except Exception:
                logger.exception("Error stopping module '%s'", m.name)
            m._cancel_all_tasks()
            m._state = ModuleState.STOPPED
            logger.info("Module '%s' stopped", m.name)

    # -- Event routing ----------------------------------------------------
    async def dispatch_telemetry(self, event: TelemetryEvent) -> None:
        """Deliver a telemetry event to all running modules."""
        for m in self._ordered:
            if m._state == ModuleState.RUNNING:
                try:
                    await asyncio.wait_for(
                        m.on_telemetry(event),
                        timeout=self.telemetry_event_timeout_s,
                    )
                except asyncio.TimeoutError:
                    logger.warning(
                        "Module '%s' telemetry callback timed out after %.1fs",
                        m.name, self.telemetry_event_timeout_s,
                    )
                except Exception:
                    logger.exception("Module '%s' telemetry callback error", m.name)

    async def dispatch_safety_event(self, event: SafetyEvent) -> None:
        """Deliver a safety event to all running modules (high priority)."""
        for m in self._ordered:
            if m._state == ModuleState.RUNNING:
                try:
                    await asyncio.wait_for(
                        m.on_safety_event(event),
                        timeout=self.safety_event_timeout_s,
                    )
                except asyncio.TimeoutError:
                    logger.error(
                        "[SAFETY] Module '%s' failed to handle safety event "
                        "'%s' within %.1fs – marking unhealthy",
                        m.name, event.event_id, self.safety_event_timeout_s,
                    )
                    m._state = ModuleState.DEGRADED
                except Exception:
                    logger.exception(
                        "[SAFETY] Module '%s' error handling safety event '%s'",
                        m.name, event.event_id,
                    )

    # -- Health loop ------------------------------------------------------
    async def _health_loop(self) -> None:
        """Periodic health check loop."""
        while self._running:
            await asyncio.sleep(self.health_check_interval_s)
            for m in self._ordered:
                if m._state == ModuleState.RUNNING:
                    try:
                        report = await asyncio.wait_for(
                            m.health_check(),
                            timeout=10.0,
                        )
                        if report.status == HealthStatus.UNHEALTHY:
                            logger.warning(
                                "Module '%s' reported unhealthy: %s",
                                m.name, report.message,
                            )
                    except Exception:
                        logger.exception("Health check failed for module '%s'", m.name)

    # -- Hot-reload -------------------------------------------------------
    async def hot_reload(self, request: HotReloadRequest) -> HotReloadResult:
        """Replace a running module with a new version.

        Steps:
        1. Capture state from the old instance.
        2. Call ``on_before_reload()`` on the old instance.
        3. Load the new module class from ``new_code_path``.
        4. Instantiate the new class, call ``init()`` and ``start()``.
        5. Call ``on_after_reload()`` on the new instance with the old state.
        6. Replace the module in the host's registry.
        """
        old_module = self._modules.get(request.module_name)
        if old_module is None:
            return HotReloadResult(
                success=False,
                module_name=request.module_name,
                previous_config_hash="",
                new_config_hash="",
                reload_time_ms=0.0,
                strategy_used=request.strategy,
                message=f"Module '{request.module_name}' not found",
            )

        old_hash = old_module._config_hash
        t0 = time.monotonic()

        try:
            # Step 1 – capture state
            state = old_module.capture_state()

            # Step 2 – teardown old module
            old_module._state = ModuleState.RELOADING
            if request.strategy == HotReloadStrategy.GRACEFUL:
                await old_module.on_before_reload()
            else:
                await old_module.stop()
                old_module._cancel_all_tasks()

            # Step 3 – load new module class
            if request.new_code_path:
                spec = importlib.util.spec_from_file_location(
                    f"_reload_{request.module_name}",
                    request.new_code_path,
                )
                if spec is None or spec.loader is None:
                    raise ImportError(f"Cannot load module from {request.new_code_path}")
                mod = importlib.util.module_from_spec(spec)
                sys.modules[spec.name] = mod
                spec.loader.exec_module(mod)

                # Find the NexusModule subclass in the loaded module
                new_cls: Optional[type] = None
                for attr_name in dir(mod):
                    attr = getattr(mod, attr_name)
                    if (isinstance(attr, type)
                            and issubclass(attr, NexusModule)
                            and attr is not NexusModule
                            and not attr.__name__.startswith("_")):
                        new_cls = attr
                        break
                if new_cls is None:
                    raise ImportError(
                        f"No NexusModule subclass found in {request.new_code_path}"
                    )
            else:
                # Re-instantiate the same class (e.g. config-only reload)
                new_cls = type(old_module)

            # Step 4 – instantiate, init, start
            new_instance: NexusModule = new_cls()
            config = request.new_config or old_module._config
            assert config is not None
            new_instance._config = config
            new_instance._config_hash = new_instance._compute_config_hash(config)
            await new_instance.init(config)
            await new_instance.start()
            new_instance._state = ModuleState.RUNNING
            new_instance._start_time = time.monotonic()

            # Step 5 – restore state
            await new_instance.on_after_reload(state)

            # Step 6 – swap in registry
            self._modules[request.module_name] = new_instance
            idx = next(
                (i for i, m in enumerate(self._ordered) if m.name == request.module_name),
                None,
            )
            if idx is not None:
                self._ordered[idx] = new_instance

            elapsed_ms = (time.monotonic() - t0) * 1000.0
            return HotReloadResult(
                success=True,
                module_name=request.module_name,
                previous_config_hash=old_hash,
                new_config_hash=new_instance._config_hash,
                reload_time_ms=elapsed_ms,
                strategy_used=request.strategy,
                message=f"Module reloaded in {elapsed_ms:.1f}ms",
            )

        except Exception:
            elapsed_ms = (time.monotonic() - t0) * 1000.0
            tb = traceback.format_exc()
            logger.exception("Hot-reload failed for module '%s'", request.module_name)
            return HotReloadResult(
                success=False,
                module_name=request.module_name,
                previous_config_hash=old_hash,
                new_config_hash="",
                reload_time_ms=elapsed_ms,
                strategy_used=request.strategy,
                message="Hot-reload failed",
                error_detail=tb,
            )

    # -- Queries ----------------------------------------------------------
    def get_module(self, name: str) -> Optional[NexusModule]:
        return self._modules.get(name)

    def get_all_statuses(self) -> Dict[str, ModuleStatus]:
        return {m.name: m._state for m in self._ordered}  # type: ignore[return-value]

    async def get_full_status(self) -> Dict[str, ModuleStatus]:
        result: Dict[str, ModuleStatus] = {}
        for m in self._ordered:
            try:
                result[m.name] = await m.get_status()
            except Exception:
                result[m.name] = ModuleStatus(
                    module_name=m.name,
                    state=m._state,
                    health=HealthStatus.UNKNOWN,
                )
        return result


# ===========================================================================
# EXAMPLE: Concrete module implementation – ThrottleMonitor
# ===========================================================================

class ThrottleMonitor(NexusModule):
    """Example module that monitors ESP32 node throttle telemetry.

    * Subscribes to telemetry events and watches for thermal throttling.
    * Emits safety events when a node exceeds temperature thresholds.
    * Maintains a rolling window of per-node temperature readings.
    * Publishes aggregated health scores via the module status.
    """

    name: ClassVar[str] = "throttle-monitor"
    dependencies: ClassVar[list[str]] = []   # No dependencies – standalone
    _resource_budget: ClassVar[ResourceBudget] = ResourceBudget(
        gpu_memory_mb=0.0,
        cpu_percent=2.0,
        ram_mb=64.0,
        max_concurrent_tasks=4,
    )

    # -- Config keys expected in ModuleConfig.settings --------------------
    CONFIG_WARN_TEMP = "warn_temperature_c"
    CONFIG_CRIT_TEMP = "crit_temperature_c"
    CONFIG_WINDOW_SEC = "window_seconds"
    CONFIG_MIN_SAMPLES = "min_samples_for_alert"

    # -- Internal state ---------------------------------------------------
    def __init__(self) -> None:
        super().__init__()
        self._warn_temp: float = 70.0
        self._crit_temp: float = 85.0
        self._window_sec: float = 300.0
        self._min_samples: int = 5
        self._safety_callback: Optional[Callable] = None
        # node_id -> list of (timestamp, temperature)
        self._temperature_history: Dict[str, List[tuple]] = {}
        self._total_events: int = 0
        self._total_alerts: int = 0

    async def init(self, config: ModuleConfig) -> None:
        """Load configuration thresholds."""
        self._warn_temp = config.get(self.CONFIG_WARN_TEMP, 70.0)
        self._crit_temp = config.get(self.CONFIG_CRIT_TEMP, 85.0)
        self._window_sec = config.get(self.CONFIG_WINDOW_SEC, 300.0)
        self._min_samples = config.get(self.CONFIG_MIN_SAMPLES, 5)
        logger.info(
            "ThrottleMonitor initialized: warn=%.1f°C, crit=%.1f°C, window=%.0fs",
            self._warn_temp, self._crit_temp, self._window_sec,
        )

    async def start(self) -> None:
        """Start the background cleanup task."""
        self._create_task(self._cleanup_loop(), name="throttle-monitor-cleanup")
        logger.info("ThrottleMonitor started")

    async def stop(self) -> None:
        """Stop and clear history."""
        self._cancel_all_tasks()
        self._temperature_history.clear()
        logger.info("ThrottleMonitor stopped")

    async def on_telemetry(self, event: TelemetryEvent) -> None:
        """Process incoming telemetry for temperature readings."""
        temp = event.get_reading("temperature_c")
        if temp <= 0.0:
            return  # No temperature reading in this event

        self._total_events += 1
        now = datetime.now(timezone.utc)

        # Store reading
        if event.node_id not in self._temperature_history:
            self._temperature_history[event.node_id] = []
        self._temperature_history[event.node_id].append((now, temp))

        # Check thresholds
        if temp >= self._crit_temp:
            await self._emit_safety(
                node_id=event.node_id,
                severity=SafetySeverity.CRITICAL,
                category="thermal",
                description=f"Node {event.node_id} at {temp:.1f}°C (critical: {self._crit_temp:.1f}°C)",
            )
        elif temp >= self._warn_temp:
            # Only warn if the rolling average also exceeds threshold
            avg = self._rolling_average(event.node_id)
            if avg >= self._warn_temp:
                await self._emit_safety(
                    node_id=event.node_id,
                    severity=SafetySeverity.WARNING,
                    category="thermal",
                    description=(
                        f"Node {event.node_id} at {temp:.1f}°C, "
                        f"rolling avg {avg:.1f}°C (warn: {self._warn_temp:.1f}°C)"
                    ),
                )

    async def on_safety_event(self, event: SafetyEvent) -> None:
        """Acknowledge safety events (extend parent logging)."""
        await super().on_safety_event(event)
        # If another module already resolved a thermal event for our node, clear history
        if event.category == "thermal" and event.resolved and event.node_id:
            self._temperature_history.pop(event.node_id, None)

    async def get_status(self) -> ModuleStatus:
        return ModuleStatus(
            module_name=self.name,
            state=self._state,
            health=HealthStatus.HEALTHY if self._state == ModuleState.RUNNING else HealthStatus.UNKNOWN,
            uptime_seconds=self._uptime_seconds(),
            config_hash=self._config_hash,
            resource_budget=self.resource_budget(),
            resource_usage=await self.get_resource_usage(),
            dependency_names=list(self.dependencies),
            details={
                "nodes_monitored": len(self._temperature_history),
                "total_events": self._total_events,
                "total_alerts": self._total_alerts,
            },
        )

    async def health_check(self) -> HealthReport:
        total_readings = sum(len(v) for v in self._temperature_history.values())
        return HealthReport(
            status=HealthStatus.HEALTHY,
            message="ThrottleMonitor is operational",
            resource_usage=await self.get_resource_usage(),
            details={
                "nodes_monitored": len(self._temperature_history),
                "total_readings_in_window": total_readings,
                "total_events_processed": self._total_events,
                "total_alerts_issued": self._total_alerts,
            },
        )

    async def get_resource_usage(self) -> ResourceUsage:
        return ResourceUsage(
            cpu_percent=0.5,
            ram_used_mb=8.0,
            active_tasks=len(self._tasks),
        )

    # -- Safety callback injection (set by ModuleHost or wiring layer) ---
    def set_safety_callback(
        self, cb: Callable[[SafetyEvent], Coroutine[Any, Any, None]]
    ) -> None:
        """Inject a callback for emitting safety events (e.g. MQTT publish)."""
        self._safety_callback = cb

    # -- Private helpers --------------------------------------------------
    def _rolling_average(self, node_id: str) -> float:
        """Compute rolling average temperature for a node within the window."""
        now = datetime.now(timezone.utc)
        cutoff = now.timestamp() - self._window_sec
        history = self._temperature_history.get(node_id, [])
        recent = [t for ts, t in history if ts.timestamp() >= cutoff]
        if len(recent) < self._min_samples:
            return 0.0
        return sum(recent) / len(recent)

    async def _emit_safety(
        self,
        node_id: str,
        severity: SafetySeverity,
        category: str,
        description: str,
    ) -> None:
        """Create and dispatch a safety event."""
        self._total_alerts += 1
        event = SafetyEvent(
            node_id=node_id,
            source=self.name,
            severity=severity,
            category=category,
            description=description,
            affected_subsystems=[],
        )
        if self._safety_callback is not None:
            await self._safety_callback(event)
        else:
            logger.warning(
                "[SAFETY-UNROUTED] %s – %s (no safety callback configured)",
                event.event_id, description,
            )

    async def _cleanup_loop(self) -> None:
        """Periodically prune old temperature readings."""
        while True:
            await asyncio.sleep(60.0)
            now = datetime.now(timezone.utc)
            cutoff = now.timestamp() - self._window_sec
            for node_id in list(self._temperature_history.keys()):
                self._temperature_history[node_id] = [
                    (ts, t) for ts, t in self._temperature_history[node_id]
                    if ts.timestamp() >= cutoff
                ]
                if not self._temperature_history[node_id]:
                    del self._temperature_history[node_id]

    def capture_state(self) -> Dict[str, Any]:
        """Capture state for hot-reload transfer."""
        return {
            "warn_temp": self._warn_temp,
            "crit_temp": self._crit_temp,
            "total_events": self._total_events,
            "total_alerts": self._total_alerts,
            "temperature_history": {
                nid: [(ts.isoformat(), t) for ts, t in readings]
                for nid, readings in self._temperature_history.items()
            },
        }

    async def on_after_reload(self, previous_state: Dict[str, Any]) -> None:
        """Restore state from previous instance after hot-reload."""
        self._warn_temp = previous_state.get("warn_temp", self._warn_temp)
        self._crit_temp = previous_state.get("crit_temp", self._crit_temp)
        self._total_events = previous_state.get("total_events", 0)
        self._total_alerts = previous_state.get("total_alerts", 0)
        raw_history = previous_state.get("temperature_history", {})
        self._temperature_history = {
            nid: [
                (datetime.fromisoformat(ts_str), t) for ts_str, t in readings
            ]
            for nid, readings in raw_history.items()
        }
        logger.info(
            "ThrottleMonitor restored state: %d events, %d alerts, %d nodes",
            self._total_events, self._total_alerts,
            len(self._temperature_history),
        )


# ===========================================================================
# Example: Wiring everything together
# ===========================================================================

async def _demo_main() -> None:
    """Demonstration of module registration, startup, event routing, and hot-reload."""
    host = ModuleHost(site_id="site-hq-01", node_id="jetson-orin-01")

    # Create and register modules
    throttle = ThrottleMonitor()
    throttle_config = ModuleConfig(
        module_name="throttle-monitor",
        site_id="site-hq-01",
        node_id="jetson-orin-01",
        settings={
            "warn_temperature_c": 70.0,
            "crit_temperature_c": 85.0,
            "window_seconds": 300.0,
            "min_samples_for_alert": 3,
        },
    )
    host.register(throttle, throttle_config)

    # Start all modules
    await host.start_all()

    # Simulate telemetry events
    fake_event = TelemetryEvent(
        node_id="esp32-cam-03",
        timestamp=datetime.now(timezone.utc),
        readings={"temperature_c": 88.0, "humidity_pct": 45.2},
        sequence=1,
    )
    await host.dispatch_telemetry(fake_event)

    # Check status
    statuses = await host.get_full_status()
    for name, status in statuses.items():
        print(f"  {name}: {status.state} | {status.health}")

    # Hot-reload demonstration
    reload_req = HotReloadRequest(
        module_name="throttle-monitor",
        strategy=HotReloadStrategy.GRACEFUL,
    )
    result = await host.hot_reload(reload_req)
    print(f"  Hot-reload: success={result.success}, time={result.reload_time_ms:.1f}ms")

    # Shutdown
    await host.stop_all()
    print("  All modules stopped.")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
    asyncio.run(_demo_main())

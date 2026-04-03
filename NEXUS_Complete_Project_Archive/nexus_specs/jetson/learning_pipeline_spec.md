# NEXUS Learning Pipeline Specification

**Version:** 2.0.0
**Target Platform:** NVIDIA Jetson Orin NX (16 GB)
**Runtime:** Python 3.11, PyTorch 2.2, CUDA 12.2
**Last Updated:** 2025-01-15
**Status:** Implementation-Ready

---

## Table of Contents

1. [Observation Data Model](#1-observation-data-model)
2. [Pattern Discovery Engine](#2-pattern-discovery-engine)
3. [Narration Processing Pipeline](#3-narration-processing-pipeline)
4. [A/B Testing Framework](#4-ab-testing-framework)
5. [Reflex Synthesis Pipeline](#5-reflex-synthesis-pipeline)

---

## 1. Observation Data Model

### 1.1 UnifiedObservation Record Schema

Every observation is a single timestamped row in a Parquet file. The schema is fixed and versioned. All timeseries data is stored at the highest common sample rate; lower-rate sensors use forward-fill on read.

```python
@dataclass(frozen=True)
class UnifiedObservation:
    """
    Canonical observation record. One row per highest-frequency sample tick.
    All fields are required; missing sensor data is represented by NaN.
    """
    # ── Identity ──────────────────────────────────────────────
    timestamp_ns:       int       # Unix epoch nanoseconds (int64)
    session_id:         str       # UUIDv4 string
    sequence_number:    int32     # Monotonic counter within session

    # ── Navigation ────────────────────────────────────────────
    gps_latitude:       float64   # Decimal degrees, WGS-84  [-90, 90]
    gps_longitude:      float64   # Decimal degrees, WGS-84  [-180, 180]
    gps_altitude_m:     float64   # Metres above WGS-84 ellipsoid
    gps_speed_m_s:      float64   # Ground speed, m/s
    gps_heading_deg:    float64   # Course over ground, 0-360 deg true
    gps_hdop:           float64   # Horizontal dilution of precision
    gps_sat_count:      int16     # Number of satellites in fix
    gps_fix_quality:    int8      # 0=none, 1=GPS, 2=DGPS, 3=RTK

    # ── Attitude (IMU) ────────────────────────────────────────
    imu_roll_deg:       float32   # Roll, -180 to 180
    imu_pitch_deg:      float32   # Pitch, -90 to 90
    imu_yaw_deg:        float32   # Yaw, 0 to 360
    imu_accel_x_m_s2:   float32   # Body-frame linear accel X (m/s^2)
    imu_accel_y_m_s2:   float32   # Body-frame linear accel Y (m/s^2)
    imu_accel_z_m_s2:   float32   # Body-frame linear accel Z (m/s^2)
    imu_gyro_x_deg_s:   float32   # Angular rate X (deg/s)
    imu_gyro_y_deg_s:   float32   # Angular rate Y (deg/s)
    imu_gyro_z_deg_s:   float32   # Angular rate Z (deg/s)
    imu_mag_x_uT:       float32   # Magnetometer X (micro-Tesla)
    imu_mag_y_uT:       float32   # Magnetometer Y (micro-Tesla)
    imu_mag_z_uT:       float32   # Magnetometer Z (micro-Tesla)

    # ── Environment ───────────────────────────────────────────
    wind_speed_m_s:     float32   # True wind speed (m/s)
    wind_direction_deg: float32   # True wind from-direction (0=N, CW, deg)
    wind_gust_m_s:      float32   # Max 3-sec gust speed (m/s)
    air_temp_c:         float32   # Ambient air temperature (deg C)
    water_temp_c:       float32   # Sea surface temperature (deg C)
    barometric_hpa:     float32   # Barometric pressure (hPa)
    humidity_pct:       float32   # Relative humidity (%)
    visibility_m:       float32   # Meteorological visibility (m)
    wave_height_m:      float32   # Significant wave height (m)
    current_speed_m_s:  float32   # Water current speed (m/s)
    current_dir_deg:    float32   # Water current from-direction (deg)

    # ── Propulsion ────────────────────────────────────────────
    throttle_pct:       float32   # Throttle command 0-100 %
    rudder_angle_deg:   float32   # Rudder angle, -45 to +45 (starboard +)
    engine_rpm:         float32   # Engine RPM
    fuel_flow_L_h:      float32   # Instantaneous fuel flow (L/h)
    fuel_total_L:       float32   # Cumulative fuel consumed (L)
    engine_temp_c:      float32   # Engine coolant temperature (deg C)
    engine_hours:       float32   # Total engine running hours

    # ── Auxiliary Actuators ───────────────────────────────────
    bow_thruster_pct:   float32   # Bow thruster command -100 to +100 %
    stern_thruster_pct: float32   # Stern thruster command -100 to +100 %
    trim_tab_angle_deg: float32   # Trim tab angle (deg)
    anchor_winch_m:     float32   # Anchor rode paid out (m)
    bilge_pump_active:  bool      # Bilge pump running

    # ── Perception ────────────────────────────────────────────
    lidar_obstacle_dist_m: float32   # Nearest lidar obstacle (m), inf if none
    lidar_obstacle_bearing_deg: float32  # Bearing to nearest obstacle
    radar_contacts_count: int16    # Number of radar contacts
    radar_nearest_m:    float32   # Nearest radar contact distance (m)
    camera_depth_forward_m: float32  # Forward depth estimate (m)
    ais_contact_count:  int16     # AIS contacts in range
    ais_nearest_m:      float32   # Nearest AIS contact CPA distance (m)

    # ── System Health ─────────────────────────────────────────
    cpu_usage_pct:      float32   # Jetson CPU utilisation (%)
    gpu_usage_pct:      float32   # Jetson GPU utilisation (%)
    memory_usage_pct:   float32   # RAM utilisation (%)
    disk_usage_pct:     float32   # NVMe utilisation (%)
    core_temp_c:        float32   # SoC temperature (deg C)
    power_draw_w:       float32   # Total system power (W)
    network_latency_ms: float32   # RTT to cloud gateway (ms)
    vault12_status:     int8      # 0=offline, 1=standby, 2=active, 3=fault

    # ── Autonomy State ────────────────────────────────────────
    autonomy_level:     int8      # 0-5 current autonomy level
    trust_score:        float32   # Current trust score [0, 1]
    active_mode:        str       # Current autonomy mode name
    active_reflex_id:   str       # Currently executing reflex ID (or "")
    pilot_present:      bool      # Human pilot at controls
    override_active:    bool      # Human override in progress
```

### 1.2 Sensor Registration Format

Every sensor must be registered before its data is accepted into the observation stream.

```python
@dataclass(frozen=True)
class SensorRegistration:
    """
    Declares a sensor source to the observation bus.
    """
    name:               str       # Unique identifier, e.g. "gps_primary"
    display_name:       str       # Human-readable name
    sensor_type:        str       # One of: GPS, IMU, ANEMOMETER, THERMOMETER,
                                  #   BAROMETER, HYGROMETER, LIDAR, RADAR,
                                  #   CAMERA_DEPTH, AIS, FUEL_FLOW, RPM,
                                  #   ACTUATOR_POSITION, SYSTEM_HEALTH
    unit:               str       # SI unit string, e.g. "m/s", "deg", "hPa"
    value_range:        tuple     # (min, max) valid measurement range
    accuracy:           float     # 1-sigma accuracy in stated units
    sample_rate_hz:     float     # Expected sample rate (Hz)
    data_type:          str       # Parquet physical type: "float32", "float64",
                                  #   "int8", "int16", "int32", "int64", "bool"
    source_bus:         str       # CAN, SPI, I2C, UART, USB, NETWORK
    priority:           int       # 0=highest, 99=lowest; used for conflict resolution
    timeout_ms:         int       # Max acceptable interval between readings
    forward_fill:       bool      # If True, last value is carried forward on timeout
    observation_field:  str       # Exact field name in UnifiedObservation
```

**Built-in registrations** (shipped with firmware, loaded at boot):

| name | sensor_type | unit | range | accuracy | rate |
|------|-------------|------|-------|----------|------|
| gps_primary | GPS | deg | (-90,90)/(−180,180) | 2.5 m CEP | 10 Hz |
| imu_bno085 | IMU | various | per-axis | 0.1 deg orientation | 100 Hz |
| anemometer | ANEMOMETER | m/s | (0, 60) | 0.3 m/s | 10 Hz |
| wind_vane | ANEMOMETER | deg | (0, 360) | 3.0 deg | 10 Hz |
| barometer | BAROMETER | hPa | (870, 1084) | 0.12 hPa | 1 Hz |
| thermometer_air | THERMOMETER | C | (-40, 85) | 0.3 C | 1 Hz |
| thermometer_water | THERMOMETER | C | (-5, 45) | 0.2 C | 1 Hz |
| hygrometer | HYGROMETER | % | (0, 100) | 2.0 % | 1 Hz |
| lidar_solidstate | LIDAR | m | (0.3, 200) | 0.03 m | 20 Hz |
| radar_halogen | RADAR | m | (0, 72) nmi | 1 % of range | 24 RPM |
| fuel_flow_meter | FUEL_FLOW | L/h | (0, 200) | 0.5 % | 10 Hz |
| rpm_sensor | RPM | 1/min | (0, 6000) | 1 RPM | 10 Hz |
| rudder_feedback | ACTUATOR_POSITION | deg | (-45, 45) | 0.5 deg | 50 Hz |
| throttle_feedback | ACTUATOR_POSITION | % | (0, 100) | 1.0 % | 50 Hz |
| ais_receiver | AIS | m | (0, 50000) | 10 m | 1 Hz |
| camera_stereo_depth | CAMERA_DEPTH | m | (0.5, 30) | 5 % | 15 Hz |

### 1.3 ObservationSession Lifecycle

```python
class ObservationSession:
    """
    Manages the lifecycle of a data collection session.
    Thread-safe. Writes to a rolling Parquet file on NVMe SSD.
    """

    def __init__(self, vessel_id: str, tags: list[str] = None):
        self.session_id: str = str(uuid4())
        self.vessel_id: str = vessel_id
        self.created_at: datetime = utcnow()
        self.tags: list[str] = tags or []
        self.status: Literal["recording", "paused", "closed"] = "recording"
        self.row_count: int = 0
        self.size_bytes: int = 0
        self.metadata: dict = {}  # Free-form, searchable

    def record(self, observation: UnifiedObservation) -> None:
        """
        Append a single observation to the session buffer.
        Buffer flushes to disk every 1 second or 10,000 rows,
        whichever comes first.
        """
        assert self.status == "recording"
        # Validate timestamp is monotonic within session
        # Validate against registered sensor ranges
        # Append to in-memory Apache Arrow table
        # Increment counters

    def tag(self, key: str, value: str) -> None:
        """Attach arbitrary metadata (e.g., 'weather:foggy')."""
        self.tags.append(f"{key}={value}")

    def pause(self) -> None:
        """Pause recording without closing the session."""
        self.status = "paused"

    def resume(self) -> None:
        """Resume recording."""
        assert self.status == "paused"
        self.status = "recording"

    def close(self) -> None:
        """
        Finalize the session:
        1. Flush remaining buffer to Parquet
        2. Write _metadata sidecar JSON
        3. Compute and store column statistics (min, max, mean, null_count)
        4. Register session in session index (SQLite)
        5. Move to hot storage tier
        """
        self.status = "closed"

    def export(self, format: str = "parquet",
               start_time: datetime = None,
               end_time: datetime = None,
               columns: list[str] = None) -> str:
        """
        Export session data (or subset) to file.
        Returns path to exported file.
        Formats: parquet, csv, jsonl
        """
        assert self.status == "closed"
```

### 1.4 Storage Format: Parquet Column Schema

The primary storage format is Apache Parquet (version 2.x) with Snappy compression for hot storage and ZSTD for warm/cold.

```
Parquet File Schema (per session, partitioned by hour)
=======================================================

Row Group Size:    100,000 rows (~2-5 MB at 100 Hz per hour)
Compression:       HOT=Snappy, WARM/COLD=ZSTD(level=3)
Encoding:          DICTIONARY for low-cardinality strings,
                   BYTE_STREAM_SPLIT for float arrays
Partitioning:      /data/{vessel_id}/hot/{session_id}/hour={YYYYMMDDHH}.parquet

Column Listing (physical storage order for locality):
┌────────────────────────────┬──────────┬──────────────────────┐
│ Column                     │ Physical  │ Logical Type          │
│                            │ Type     │ (annotation)          │
├────────────────────────────┼──────────┼──────────────────────┤
│ timestamp_ns               │ INT64    │ TIMESTAMP(isAdjusted) │
│ session_id                 │ BYTE[36] │ STRING                │
│ sequence_number            │ INT32    │ —                     │
│ gps_latitude               │ DOUBLE   │ —                     │
│ gps_longitude              │ DOUBLE   │ —                     │
│ gps_altitude_m             │ DOUBLE   │ —                     │
│ gps_speed_m_s              │ DOUBLE   │ —                     │
│ gps_heading_deg            │ DOUBLE   │ —                     │
│ gps_hdop                   │ DOUBLE   │ —                     │
│ gps_sat_count              │ INT16    │ —                     │
│ gps_fix_quality            │ INT8     │ —                     │
│ imu_roll_deg               │ FLOAT    │ —                     │
│ imu_pitch_deg              │ FLOAT    │ —                     │
│ imu_yaw_deg                │ FLOAT    │ —                     │
│ imu_accel_x_m_s2           │ FLOAT    │ —                     │
│ imu_accel_y_m_s2           │ FLOAT    │ —                     │
│ imu_accel_z_m_s2           │ FLOAT    │ —                     │
│ imu_gyro_x_deg_s           │ FLOAT    │ —                     │
│ imu_gyro_y_deg_s           │ FLOAT    │ —                     │
│ imu_gyro_z_deg_s           │ FLOAT    │ —                     │
│ imu_mag_x_uT               │ FLOAT    │ —                     │
│ imu_mag_y_uT               │ FLOAT    │ —                     │
│ imu_mag_z_uT               │ FLOAT    │ —                     │
│ wind_speed_m_s             │ FLOAT    │ —                     │
│ wind_direction_deg         │ FLOAT    │ —                     │
│ wind_gust_m_s              │ FLOAT    │ —                     │
│ air_temp_c                 │ FLOAT    │ —                     │
│ water_temp_c               │ FLOAT    │ —                     │
│ barometric_hpa             │ FLOAT    │ —                     │
│ humidity_pct               │ FLOAT    │ —                     │
│ visibility_m               │ FLOAT    │ —                     │
│ wave_height_m              │ FLOAT    │ —                     │
│ current_speed_m_s          │ FLOAT    │ —                     │
│ current_dir_deg            │ FLOAT    │ —                     │
│ throttle_pct               │ FLOAT    │ —                     │
│ rudder_angle_deg           │ FLOAT    │ —                     │
│ engine_rpm                 │ FLOAT    │ —                     │
│ fuel_flow_L_h              │ FLOAT    │ —                     │
│ fuel_total_L               │ FLOAT    │ —                     │
│ engine_temp_c              │ FLOAT    │ —                     │
│ engine_hours               │ FLOAT    │ —                     │
│ bow_thruster_pct           │ FLOAT    │ —                     │
│ stern_thruster_pct         │ FLOAT    │ —                     │
│ trim_tab_angle_deg         │ FLOAT    │ —                     │
│ anchor_winch_m             │ FLOAT    │ —                     │
│ bilge_pump_active          │ BOOLEAN  │ —                     │
│ lidar_obstacle_dist_m      │ FLOAT    │ —                     │
│ lidar_obstacle_bearing_deg │ FLOAT    │ —                     │
│ radar_contacts_count       │ INT16    │ —                     │
│ radar_nearest_m            │ FLOAT    │ —                     │
│ camera_depth_forward_m     │ FLOAT    │ —                     │
│ ais_contact_count          │ INT16    │ —                     │
│ ais_nearest_m              │ FLOAT    │ —                     │
│ cpu_usage_pct              │ FLOAT    │ —                     │
│ gpu_usage_pct              │ FLOAT    │ —                     │
│ memory_usage_pct           │ FLOAT    │ —                     │
│ disk_usage_pct             │ FLOAT    │ —                     │
│ core_temp_c                │ FLOAT    │ —                     │
│ power_draw_w               │ FLOAT    │ —                     │
│ network_latency_ms         │ FLOAT    │ —                     │
│ vault12_status             │ INT8     │ —                     │
│ autonomy_level             │ INT8     │ —                     │
│ trust_score                │ FLOAT    │ —                     │
│ active_mode                │ BYTE[64] │ STRING                │
│ active_reflex_id           │ BYTE[64] │ STRING                │
│ pilot_present              │ BOOLEAN  │ —                     │
│ override_active            │ BOOLEAN  │ —                     │
└────────────────────────────┴──────────┴──────────────────────┘

Estimated row size:  72 fields x avg 5 bytes = ~360 bytes/row
At 100 Hz:          ~32 MB/minute, ~1.9 GB/hour, ~46 GB/day
```

### 1.5 Retention Policy

```
┌──────────┬──────────┬────────────────────┬──────────────────────┬──────────┐
│  Tier    │ Duration │    Storage          │  Compression         │  I/O     │
├──────────┼──────────┼────────────────────┼──────────────────────┼──────────┤
│  HOT     │ 7 days   │ NVMe SSD (local)   │  Snappy (fast R/W)   │  ~3 GB/s │
│  WARM    │ 90 days  │ NVMe SSD (local)   │  ZSTD level 3        │  ~1 GB/s │
│  COLD    │ 2 years  │ Cloud (S3/GCS)     │  ZSTD level 3        │  Network │
│  ARCHIVE │ delete   │ N/A                │  N/A                 │  N/A     │
└──────────┴──────────┴────────────────────┴──────────────────────┴──────────┘

Expected compression ratios:
  Snappy (HOT):    2:1   (46 GB/day -> 23 GB/day)
  ZSTD-3 (WARM):  5:1   (46 GB/day -> 9.2 GB/day)
  ZSTD-3 (COLD):  5:1   (same, stored on cheap cloud storage)

Tier transition triggers:
  HOT  -> WARM:  cron daily at 02:00 UTC, age > 7 days
  WARM -> COLD:  cron daily at 03:00 UTC, age > 90 days
  COLD -> DELETE: cron daily at 04:00 UTC, age > 730 days

Transition process:
  1. Verify integrity: checksum (xxh3_128) of source matches metadata
  2. Compress/convert if needed
  3. Write to destination tier
  4. Verify destination checksum
  5. Update session index
  6. Delete source (only after successful verification)

Disk budget (1 TB NVMe):
  HOT:  7 x 9.2 = ~65 GB  (after warm transition, but retains 7 days)
  WARM: ~850 GB available (holds ~92 days of 100 Hz data)
  Safety margin: ~85 GB for OS, models, logs
```

---

## 2. Pattern Discovery Engine

The pattern discovery engine runs as a background service on the Jetson, triggered after each session closes. It processes observations to extract correlations, change points, behavioral clusters, temporal rules, and reward weights.

### 2.1 Cross-Correlation Scanner

Identifies time-lagged relationships between all sensor variables and all actuator commands.

```python
@dataclass(frozen=True)
class CorrelationRecord:
    variable_a:          str       # Source variable name
    variable_b:          str       # Target variable name
    lag_s:               float     # Time lag in seconds (negative = A leads)
    correlation:         float     # Pearson correlation coefficient at best lag
    p_value:             float     # Bonferroni-corrected p-value
    sample_size:         int       # Number of overlapping samples used
    effect_direction:    str       # "A_leads_B", "B_leads_A", or "simultaneous"


def cross_correlation_scan(
    session_data: pd.DataFrame,
    sensor_columns: list[str],       # All sensor reading column names
    actuator_columns: list[str],     # All actuator command column names
    all_columns: list[str] = None,   # Defaults to sensor_columns + actuator_columns
) -> list[CorrelationRecord]:
    """
    Parameters
    ----------
    session_data : pd.DataFrame
        Full session observations with timestamp_ns as index (sorted).
    sensor_columns, actuator_columns : list[str]
        Column names to include in pairwise analysis.
    all_columns : list[str], optional
        Override to scan custom variable sets.

    Configuration
    -------------
    max_lag_s     : float = 60.0      # Maximum lag to test in either direction
    lag_resolution_ms : float = 100.0 # Lag step size in milliseconds
    threshold_r   : float = 0.6       # Minimum absolute Pearson r to report
    min_overlap   : float = 0.5       # Minimum fractional overlap for valid lag
    correction    : str = "bonferroni" # Multiple testing correction method

    Algorithm
    ---------
    1. For each unique pair (A, B) where A != B:
       a. Resample both columns to uniform 100 ms grid (linear interpolation)
       b. Compute cross-correlation at lags from -600 to +600 (60 s at 100 ms)
          using scipy.signal.correlate with mode='same'
       c. Convert to Pearson r at each lag: r(lag) = CCF(lag) / (std_A * std_B)
       d. Find argmax |r(lag)|
       e. Compute two-tailed p-value for that r using scipy.stats.t:
          t = r * sqrt(n_eff - 2) / sqrt(1 - r^2)
          p = 2 * (1 - t_cdf(|t|, df=n_eff-2))
          where n_eff = total_samples - abs(lag_samples)
       f. Apply Bonferroni correction:
          p_corrected = p * num_comparisons
          num_comparisons = C(N, 2) where N = len(all_columns)

    2. Filter: report only if |r| >= threshold_r AND p_corrected < 0.05

    3. Determine direction:
       if lag_s < -1.0:  "B_leads_A"  (B's change precedes A)
       if lag_s >  1.0:  "A_leads_B"  (A's change precedes B)
       else:             "simultaneous"

    Returns
    -------
    list[CorrelationRecord], sorted by |correlation| descending
    """
```

**Performance notes:**
- N = 72 columns -> C(72,2) = 2556 pairs
- Each pair: 1201 lag positions, vectorised via NumPy
- Typical session (1 hour at 100 Hz = 360,000 rows): ~8 seconds on Jetson Orin NX
- Result set typically < 50 significant correlations per session

### 2.2 Change-Point Detection

Detects abrupt shifts in the statistical properties of sensor time series using Bayesian Online Change Point Detection (BOCPD).

```python
@dataclass(frozen=True)
class ChangePoint:
    timestamp:       int64     # Unix nanoseconds at detected change
    sensor:          str       # Sensor variable that changed
    before_mean:     float     # Running mean before change point
    after_mean:      float     # Running mean after change point
    before_std:      float     # Running std before change point
    after_std:       float     # Running std after change point
    confidence:      float     # Posterior probability of change at this point [0, 1]
    run_length:      int       # Number of observations since last change point


def bocpd_detect(
    series: np.ndarray,
    timestamps: np.ndarray,
    sensor_name: str,
    hazard_lambda: float = 0.01,
    run_length_threshold: int = 100,
    prior_mu: float = 0.0,
    prior_kappa: float = 1.0,
    prior_alpha: float = 1.0,
    prior_beta: float = 1.0,
) -> list[ChangePoint]:
    """
    Bayesian Online Change Point Detection (Adams & MacKay, 2007).

    Parameters
    ----------
    series : np.ndarray, shape (T,)
        The observed time series values.
    timestamps : np.ndarray, shape (T,)
        Corresponding timestamps in nanoseconds.
    sensor_name : str
        Name of the sensor being analysed.
    hazard_lambda : float = 0.01
        Constant hazard function rate.
        Represents prior belief that a change point occurs with probability
        lambda at each time step. Smaller = expects fewer changes.
        Range: [0.001, 0.1]. Default 0.01 implies expected ~100 observations
        between change points.
    run_length_threshold : int = 100
        Minimum observations between reported change points.
        Prevents reporting spurious changes in rapid succession.
    prior_mu, prior_kappa, prior_alpha, prior_beta : float
        Normal-Inverse-Gamma conjugate prior parameters for the
        Gaussian observation model.
        NIG(mu0, kappa0, alpha0, beta0) ->
          mean ~ Student-t(2*alpha, mu, beta/(alpha*kappa))
    """
    T = len(series)

    # Growth probabilities: P(run_length increases by 1)
    # Computed incrementally via message passing
    growth_probs = np.zeros(T)
    # Evidence: marginal likelihood of data up to t
    log_evidence = np.zeros(T)

    # Sufficient statistics (online update)
    mu_t = np.zeros(T)   # Predictive mean at time t
    var_t = np.zeros(T)  # Predictive variance at time t

    # ── Initialise ──
    R = np.zeros((T + 1, T + 1))  # Run length probability matrix
    R[0, 0] = 1.0

    change_points: list[ChangePoint] = []
    last_cp_index = 0

    for t in range(1, T):
        # Prior for each possible run length
        pi = np.exp(-hazard_lambda * np.arange(t + 1))

        # Predictive distribution (Student-t)
        pred_probs = np.zeros(t + 1)
        for r in range(t + 1):
            if R[t-1, r] < 1e-300:
                continue
            # Posterior parameters after r observations
            kappa_r = prior_kappa + r
            mu_r = (prior_kappa * prior_mu + r * mu_t[t-1]) / kappa_r
            alpha_r = prior_alpha + r / 2
            beta_r = prior_beta + 0.5 * (
                np.sum(series[t-r:t]**2)
                + prior_kappa * prior_mu**2
                - kappa_r * mu_r**2
            )

            # Student-t predictive: 2*alpha_r DoF, location mu_r, scale beta_r*(kappa_r+1)/(kappa_r*alpha_r)
            scale = beta_r * (kappa_r + 1) / (kappa_r * alpha_r)
            pred_probs[r] = R[t-1, r] * student_t_pdf(
                series[t], df=2*alpha_r, loc=mu_r, scale=scale
            )

        # Normalise
        total = np.sum(pred_probs)
        if total < 1e-300:
            pred_probs = np.ones(t + 1) / (t + 1)
        else:
            pred_probs /= total

        # Update run length probabilities
        R[t, 1:] = pred_probs[:-1] * (1 - pi[:-1])  # Growth
        R[t, 0]  = np.sum(pred_probs * pi)            # Changepoint (reset)

        # Store max probability run length
        growth_probs[t] = np.max(R[t, 1:])

        # Check for change point
        cp_prob = R[t, 0]
        if (cp_prob > 0.5 and
            (t - last_cp_index) >= run_length_threshold):
            change_points.append(ChangePoint(
                timestamp=timestamps[t],
                sensor=sensor_name,
                before_mean=float(np.mean(series[last_cp_index:t])),
                after_mean=float(np.mean(series[t:])),
                before_std=float(np.std(series[last_cp_index:t])),
                after_std=float(np.std(series[t:])),
                confidence=float(cp_prob),
                run_length=t - last_cp_index,
            ))
            last_cp_index = t

    return change_points
```

**Applied to:** All continuous sensor columns (exclude booleans, enums).
**Run schedule:** After each session close, per-column in parallel (thread pool, 4 workers).

### 2.3 Behavioral Clustering

Groups similar segments of vessel behavior into distinct clusters (e.g., "cruising," "docking," "rough-weather maneuvering").

```python
@dataclass(frozen=True)
class BehaviorCluster:
    cluster_id:         int       # HDBSCAN cluster label (-1 = noise)
    centroid_features:  np.ndarray  # 5-dimensional PCA centroid
    member_count:       int       # Number of 10-second windows in cluster
    typical_context:    dict      # {sensor_name: (mean, std)} at cluster center
    temporal_pattern:   str       # "stationary", "transient", "periodic"
    duration_range_s:   tuple     # (min, max) duration of contiguous segments


def behavioral_clustering(
    session_data: pd.DataFrame,
    window_seconds: float = 10.0,
    sample_rate_hz: float = 100.0,
    pca_components: int = 5,
    hdbscan_min_cluster_size: int = 10,
    hdbscan_min_samples: int = 3,
) -> list[BehaviorCluster]:
    """
    Parameters
    ----------
    session_data : pd.DataFrame
        Full session with timestamp_ns index, sorted.
    window_seconds : float = 10.0
        Size of sliding window for feature extraction.
    sample_rate_hz : float = 100.0
        Target resampling rate for feature computation.
    pca_components : int = 5
        Number of PCA components to retain.
    hdbscan_min_cluster_size : int = 10
        HDBSCAN minimum cluster size. Larger = fewer, bigger clusters.
    hdbscan_min_samples : int = 3
        HDBSCAN minimum samples in neighbourhood. Larger = more conservative.

    Algorithm Steps
    ---------------
    STEP 1: Feature Extraction (per window)
    ──────────────────────────────────────
    For each non-overlapping 10-second window, extract from these columns:
      gps_speed_m_s, imu_roll_deg, imu_pitch_deg, rudder_angle_deg,
      throttle_pct, engine_rpm, wind_speed_m_s, imu_accel_x/y/z_m_s2

    Statistical features (per column):
      f1 = mean(x)                          — central tendency
      f2 = std(x)                           — variability
      f3 = min(x)                           — minimum
      f4 = max(x)                           — maximum
      f5 = spectral_centroid(x)             — frequency-domain centre of mass
          = sum(k * |FFT(x)[k]|) / sum(|FFT(x)[k]|)

    Total raw features per window: 8 columns x 5 features = 40 dimensions

    STEP 2: Normalisation
    ─────────────────────
    RobustScaler (median, IQR) per feature across all windows.

    STEP 3: Dimensionality Reduction
    ────────────────────────────────
    PCA with n_components=5.
    Retain components explaining >= 85% of variance (fail-open: use 5 regardless).
    Store explained_variance_ratio_ for downstream interpretation.

    STEP 4: Clustering
    ───────────────────
    HDBSCAN(metric='euclidean', min_cluster_size=10, min_samples=3,
            cluster_selection_method='eom').
    cluster_selection_epsilon not set (automatic).
    Noise points (label=-1) are discarded from results.

    STEP 5: Cluster Characterisation
    ────────────────────────────────
    For each cluster:
      - Centroid = mean of PCA-transformed features for cluster members
      - Typical context = mean and std of raw sensor values for cluster windows
      - Temporal pattern = classify via autocorrelation of the segment:
          * Compute autocorrelation at lag 1 of window speeds
          * If autocorrelation < 0.3: "transient"
          * If autocorrelation > 0.7: "stationary"
          * Otherwise: "periodic"
      - Duration range = min/max of contiguous same-cluster segment lengths

    Returns
    -------
    list[BehaviorCluster], sorted by member_count descending
    """
```

### 2.4 Temporal Pattern Mining

Discovers recurrent event-response patterns: "When X happens, the pilot (or autopilot) typically does Y."

```python
@dataclass(frozen=True)
class TemporalRule:
    event_definition:    str       # Human-readable condition string
    event_definition_ast: dict     # Structured AST of the condition
    typical_response:    list[str] # Ordered sequence of actuator changes
    response_sequence:   list[dict]# [{actuator, delta, delay_s}, ...]
    consistency:         float     # Fraction of event occurrences with similar response [0, 1]
    exceptions:          list[str] # Contexts where response deviated
    sample_count:        int       # Number of observed occurrences
    avg_response_latency_s: float  # Mean time from event to first response action


# ── Event Definition Language ──────────────────────────────────

EVENT_LANGUAGE_GRAMMAR = """
event       := condition ('AND' condition)*
condition   := variable comparator threshold
variable    := <any UnifiedObservation field name>
comparator  := '>' | '>=' | '<' | '<=' | '==' | '!=' | 'CHANGES_BY' | 'CROSSES'
threshold   := number
CHANGES_BY  := abs(delta) > threshold within 5 seconds
CROSSES     := value crosses threshold (upward or downward)
"""

# Examples:
#   "wind_speed_m_s > 12 AND wave_height_m > 1.5"
#   "gps_speed_m_s CROSSES 0.5"
#   "lidar_obstacle_dist_m < 10 AND lidar_obstacle_bearing_deg > 340 AND lidar_obstacle_bearing_deg < 20"


def mine_temporal_patterns(
    session_data: pd.DataFrame,
    event_definitions: list[str] = None,
    pre_window_s: float = 10.0,
    post_window_s: float = 30.0,
    dtw_threshold: float = 2.0,
    consistency_threshold: float = 0.6,
    min_occurrences: int = 5,
) -> list[TemporalRule]:
    """
    Parameters
    ----------
    session_data : pd.DataFrame
        Full session with timestamp_ns index, sorted.
    event_definitions : list[str], optional
        Pre-defined events to search for. If None, auto-discover events
        from the top-20 cross-correlation results (section 2.1).
    pre_window_s : float = 10.0
        Seconds before event trigger to include in context.
    post_window_s : float = 30.0
        Seconds after event trigger to search for response actions.
    dtw_threshold : float = 2.0
        DTW distance threshold for considering two response sequences
        as belonging to the same pattern cluster.
    consistency_threshold : float = 0.6
        Minimum fraction of consistent responses to report a rule.
    min_occurrences : int = 5
        Minimum number of event occurrences to report a rule.

    Algorithm Steps
    ---------------
    STEP 1: Event Detection
    ───────────────────────
    Parse each event definition into an AST.
    Evaluate the AST against session_data at each timestep.
    Record (timestamp, context_snapshot) for each event occurrence.
    Context snapshot = all sensor/actuator values at trigger time.

    STEP 2: Response Extraction
    ───────────────────────────
    For each event occurrence:
      a. Extract actuator columns for [trigger - pre_window, trigger + post_window]
      b. Detect significant actuator changes:
         For each actuator, find timesteps where |delta| > threshold:
           rudder_angle_deg:    |delta| > 2.0 deg
           throttle_pct:        |delta| > 5.0 %
           bow_thruster_pct:    |delta| > 10.0 %
           stern_thruster_pct:  |delta| > 10.0 %
           trim_tab_angle_deg:  |delta| > 1.0 deg
      c. Build response sequence:
         [{actuator: "rudder_angle_deg", delta: -12.3, delay_s: 1.2}, ...]
      d. Normalise delta values to z-scores relative to that actuator's
         historical distribution.

    STEP 3: Response Clustering (DTW)
    ─────────────────────────────────
    For each event definition with >= min_occurrences occurrences:
      a. Compute pairwise DTW distance matrix between all response sequences.
         DTW metric: Euclidean on the multi-dimensional actuator vector.
         Sakoe-Chiba band: 20% of max sequence length.
      b. Hierarchical agglomerative clustering (Ward linkage) on DTW matrix.
         Cut dendrogram at height = dtw_threshold.
      c. Select largest cluster as "typical response."
      d. Consistency = size_of_largest_cluster / total_occurrences.
      e. Exceptions = contexts from non-dominant clusters.

    STEP 4: Rule Assembly
    ──────────────────────
    For each event with consistency >= consistency_threshold:
      a. typical_response = median actuator sequence of dominant cluster
      b. Compute avg_response_latency_s = mean delay to first significant actuator change
      c. Build TemporalRule dataclass

    Returns
    -------
    list[TemporalRule], sorted by (sample_count * consistency) descending
    """
```

### 2.5 Bayesian Reward Inference

Infers a scalar reward function from observed behavior, weighted across multiple objectives.

```python
REWARD_FEATURES = [
    "speed_comfort",        # Penalise deviation from comfortable speed range
    "heading_accuracy",     # Penalise heading error from target/course
    "fuel_efficiency",      # Reward lower fuel flow per unit distance
    "smoothness",           # Penalise high jerk (derivative of acceleration)
    "safety_margin",        # Reward maintaining distance from obstacles
    "wind_compensation",    # Reward appropriate heading correction for wind
]


@dataclass(frozen=True)
class RewardWeights:
    w_speed_comfort:       float
    w_heading_accuracy:    float
    w_fuel_efficiency:     float
    w_smoothness:          float
    w_safety_margin:       float
    w_wind_compensation:   float
    log_likelihood:        float     # Log-likelihood on held-out trajectories
    interpretation:        dict      # Human-readable interpretation of weights


def compute_reward_features(
    session_data: pd.DataFrame,
    target_speed: float = None,
    target_heading: float = None,
    comfortable_speed_min: float = 3.0,
    comfortable_speed_max: float = 7.0,
) -> np.ndarray:
    """
    Compute normalised feature matrix (T x 6) for reward inference.

    f1: speed_comfort = 1.0 - sigmoid((speed - max)^2 / (0.5 * max))
         Ranges [0, 1]. 1.0 when speed is within comfortable range.
    f2: heading_accuracy = cos(target_heading - actual_heading)
         Ranges [-1, 1]. 1.0 when heading matches target exactly.
    f3: fuel_efficiency = -fuel_flow_L_h / max(gps_speed_m_s, 0.1)
         Normalised to [0, 1] via min-max across session.
    f4: smoothness = -RMS(jerk_heave) where jerk_heave = d(accel_z)/dt
         Normalised to [0, 1]. 1.0 = perfectly smooth.
    f5: safety_margin = min(lidar_obstacle_dist_m, 100) / 100
         1.0 when no obstacles within 100m, 0.0 when obstacle at 0m.
    f6: wind_compensation = -|actual_drift_angle - wind_drift_angle|
         Measures how well the pilot compensates for wind-induced drift.
         Normalised to [0, 1].
    """
    T = len(session_data)
    features = np.zeros((T, 6))

    # f1: speed comfort
    speed = session_data['gps_speed_m_s'].values
    mid = (comfortable_speed_min + comfortable_speed_max) / 2
    half_range = (comfortable_speed_max - comfortable_speed_min) / 2
    features[:, 0] = np.clip(1.0 - ((speed - mid) / half_range) ** 2, 0, 1)

    # f2: heading accuracy (when target_heading is known)
    if target_heading is not None:
        heading_err = np.radians(session_data['gps_heading_deg'].values - target_heading)
        features[:, 1] = np.cos(heading_err)
    else:
        features[:, 1] = 1.0  # Default: no heading penalty when no target

    # f3: fuel efficiency
    speed_safe = np.maximum(session_data['gps_speed_m_s'].values, 0.1)
    fuel_per_dist = session_data['fuel_flow_L_h'].values / (speed_safe * 3.6)  # L/km
    f3_raw = -fuel_per_dist
    features[:, 2] = (f3_raw - f3_raw.min()) / (f3_raw.max() - f3_raw.min() + 1e-10)

    # f4: smoothness (negated jerk magnitude)
    accel_z = session_data['imu_accel_z_m_s2'].values
    dt = np.gradient(session_data['timestamp_ns'].values) / 1e9
    jerk = np.gradient(accel_z, dt)
    jerk_rms = np.sqrt(np.convolve(jerk**2, np.ones(100)/100, mode='same'))
    f4_raw = -jerk_rms
    features[:, 3] = (f4_raw - f4_raw.min()) / (f4_raw.max() - f4_raw.min() + 1e-10)

    # f5: safety margin
    dist = session_data['lidar_obstacle_dist_m'].values
    # Replace inf with 200m
    dist = np.where(np.isinf(dist), 200.0, dist)
    features[:, 4] = np.clip(dist / 100.0, 0, 1)

    # f6: wind compensation
    # Simplified: correlation between rudder input and cross-wind component
    wind_cross = session_data['wind_speed_m_s'].values * np.sin(
        np.radians(session_data['wind_direction_deg'].values - session_data['gps_heading_deg'].values)
    )
    rudder = session_data['rudder_angle_deg'].values
    # High correlation = good compensation
    corr_window = 100  # 1 second at 100 Hz
    f6_raw = np.array([
        np.corrcoef(rudder[max(0,i-corr_window):i+1],
                    wind_cross[max(0,i-corr_window):i+1])[0,1]
        if i >= 10 else 0.0
        for i in range(T)
    ])
    f6_raw = np.nan_to_num(f6_raw, nan=0.0)
    features[:, 5] = np.clip(f6_raw, 0, 1)

    return features


def infer_reward_weights(
    features: np.ndarray,
    actions: np.ndarray,
    narration_seeds: dict[str, float] = None,
    prior_alpha: float = 1.0,
    prior_beta: float = 1.0,
    test_split: float = 0.2,
    optimizer: str = "L-BFGS-B",
    max_iter: int = 1000,
    tol: float = 1e-6,
) -> RewardWeights:
    """
    Bayesian reward inference via Maximum A Posteriori (MAP) estimation.

    Parameters
    ----------
    features : np.ndarray, shape (T, 6)
        Reward feature matrix from compute_reward_features().
    actions : np.ndarray, shape (T, N_actuators)
        Actuator commands at each timestep.
    narration_seeds : dict[str, float], optional
        Prior belief about feature weights from narration processing.
        e.g., {"safety_margin": 0.8, "fuel_efficiency": 0.3}
        If None, uniform prior.
    prior_alpha, prior_beta : float = 1.0
        Beta distribution parameters for uniform [0, 1] prior on weights.
    test_split : float = 0.2
        Fraction of trajectory reserved for held-out evaluation.
    optimizer : str = "L-BFGS-B"
        scipy.optimize optimizer.
    max_iter, tol : optimization hyperparameters.

    Model
    -----
    We assume the pilot's policy approximately maximises:
        r(t) = w . features(t)

    Given features and observed actions, we find weights w that make the
    observed actions look "reward-maximising" under a Boltzmann rationality
    model:
        P(action_t | state_t) ∝ exp(Q(state_t, action_t) / temperature)

    This reduces to a convex optimisation problem (softmax over actions).

    Optimisation Objective (MAP):
    ────────────────────────────
    maximize  L(w) = sum_t [w . features(t)] - prior_penalty(w)
    where:
        prior_penalty(w) = sum_i [ (alpha_i - 1) * log(w_i) + (beta_i - 1) * log(1 - w_i) ]
        subject to: sum(w) = 1, w_i >= 0

    The narration_seeds modify the prior:
        If narration says "safety is critical":
            prior_alpha["safety_margin"] = 3.0, prior_beta["safety_margin"] = 1.0
            This shifts the prior toward higher weight for safety_margin.

    Returns
    -------
    RewardWeights with normalised weights, log-likelihood, and interpretation.
    """
    # Split data
    n_train = int(len(features) * (1 - test_split))
    X_train, X_test = features[:n_train], features[n_train:]
    a_train, a_test = actions[:n_train], actions[n_train:]

    # Set priors from narration seeds
    if narration_seeds is None:
        narration_seeds = {}
    alphas = np.full(6, prior_alpha)
    betas = np.full(6, prior_beta)
    for i, feat_name in enumerate(REWARD_FEATURES):
        if feat_name in narration_seeds:
            seed = narration_seeds[feat_name]
            alphas[i] = prior_alpha + seed * 2  # Shift toward seed
            betas[i] = prior_beta + (1 - seed) * 2

    # Define objective: negative log posterior
    def objective(w):
        # Log-likelihood: sum of reward under observed actions
        rewards = X_train @ w
        ll = np.sum(rewards)
        # Log-prior: Beta distribution
        log_prior = np.sum(
            (alphas - 1) * np.log(w + 1e-10) + (betas - 1) * np.log(1 - w + 1e-10)
        )
        return -(ll + log_prior)

    # Constraints: weights sum to 1, each in [0, 1]
    from scipy.optimize import minimize
    result = minimize(
        objective,
        x0=np.ones(6) / 6,
        method=optimizer,
        bounds=[(0.001, 1.0)] * 6,
        constraints={'type': 'eq', 'fun': lambda w: np.sum(w) - 1.0},
        options={'maxiter': max_iter, 'ftol': tol},
    )

    w_map = result.x

    # Evaluate on held-out
    test_rewards = X_test @ w_map
    test_ll = float(np.sum(test_rewards))

    # Interpretation
    interpretation = {}
    sorted_idx = np.argsort(w_map)[::-1]
    for rank, idx in enumerate(sorted_idx):
        interpretation[REWARD_FEATURES[idx]] = {
            "weight": float(w_map[idx]),
            "rank": rank + 1,
            "interpretation": _interpret_weight(REWARD_FEATURES[idx], w_map[idx]),
        }

    return RewardWeights(
        w_speed_comfort=w_map[0],
        w_heading_accuracy=w_map[1],
        w_fuel_efficiency=w_map[2],
        w_smoothness=w_map[3],
        w_safety_margin=w_map[4],
        w_wind_compensation=w_map[5],
        log_likelihood=test_ll,
        interpretation=interpretation,
    )


def _interpret_weight(feature: str, weight: float) -> str:
    if weight > 0.25:
        return "very high priority"
    elif weight > 0.18:
        return "high priority"
    elif weight > 0.12:
        return "moderate priority"
    elif weight > 0.08:
        return "low priority"
    else:
        return "minimal consideration"
```

---

## 3. Narration Processing Pipeline

### 3.1 Whisper Transcription Configuration

```python
WHISPER_CONFIG = {
    "model": "whisper-large-v3",       # Best accuracy for maritime vocabulary
    "language": "en",                    # Fixed English (maritime standard)
    "beam_size": 5,                     # Beam search width
    "temperature": 0.0,                 # Greedy-ish for consistency
    "temperature_fallback": [0.2, 0.4, 0.6, 0.8, 1.0],
    "condition_on_previous_text": True,
    "no_speech_threshold": 0.6,
    "compression_ratio_threshold": 2.4,
    "logprob_threshold": -1.0,
    "initial_prompt": (
        "Maritime vessel operations. Terms: rudder, throttle, heading, bearing, "
        "bow, stern, port, starboard, windward, leeward, waypoint, waypoint, "
        "mooring, dock, slip, channel, fairway, anchor, rode, scope, "
        "knots, nautical miles, fathoms, draft, trim, list, heel. "
        "Abbreviations: GPS, AIS, RPM, SOG, COG."
    ),
    "device": "cuda",                   # Jetson GPU
    "compute_type": "float16",
    "vad_filter": True,
    "vad_parameters": {
        "min_speech_duration_ms": 250,
        "min_silence_duration_ms": 500,
        "speech_pad_ms": 200,
    },
}
```

### 3.2 Intent Classification

```python
INTENT_CATEGORIES = {
    "navigational_command": {
        "description": "Direct instruction to change course, speed, or position",
        "examples": [
            "Head to waypoint three",
            "Reduce speed to five knots",
            "Come to heading two-seven-zero",
            "Steer for the channel entrance",
            "Hold position here",
            "Proceed at idle speed",
        ],
        "required_entities": ["action", "target"],  # target can be heading/speed/waypoint
        "confidence_threshold": 0.85,
    },
    "safety_alert": {
        "description": "Warning about immediate danger or concern",
        "examples": [
            "Watch out for that vessel",
            "There's a log in the water",
            "Shallow water ahead",
            "Ferry crossing our path",
            "Breakwater is too close",
            "Swimmers on our starboard side",
        ],
        "required_entities": ["hazard_type", "location"],
        "confidence_threshold": 0.90,
    },
    "operational_instruction": {
        "description": "Instruction about vessel systems or operations",
        "examples": [
            "Deploy the bow thruster",
            "Lower the trim tabs",
            "Start the backup generator",
            "Switch to manual steering",
            "Check the engine temperature",
            "Pump the bilge",
        ],
        "required_entities": ["system", "action"],
        "confidence_threshold": 0.85,
    },
    "environmental_observation": {
        "description": "Description of current conditions (informative, not directive)",
        "examples": [
            "Wind is picking up from the northeast",
            "Current is running about two knots against us",
            "Fog is rolling in",
            "Sea state is building",
            "Visibility is dropping to half a mile",
        ],
        "required_entities": ["condition", "value"],
        "confidence_threshold": 0.80,
    },
    "preference_expression": {
        "description": "Statement of pilot preference or style",
        "examples": [
            "I prefer a smoother ride over speed",
            "Stay well clear of other vessels",
            "Always give way to sailboats",
            "I like to approach docks slowly",
            "Keep fuel efficiency in mind",
            "Safety margin is more important than schedule",
        ],
        "required_entities": ["preference_topic", "sentiment"],
        "confidence_threshold": 0.75,
    },
    "contextual_commentary": {
        "description": "General commentary not directly actionable",
        "examples": [
            "Nice weather today",
            "This is a good spot for fishing",
            "The new radar is working well",
            "Remember we need fuel before returning",
        ],
        "required_entities": [],
        "confidence_threshold": 0.70,
    },
}

# Training requirements for intent classifier:
# - Fine-tune DistilBERT-base on domain-specific dataset
# - Minimum 500 labeled examples per category
# - Augment with back-translation and synonym replacement
# - Train with class weights to handle imbalance
# - Evaluation metric: macro F1 >= 0.88 on held-out set
# - Deploy as ONNX model on Jetson ( inference < 50ms per utterance)
```

### 3.3 Policy Extraction Prompt Template

```
You are a maritime autonomy policy engineer. Convert the following narrated
instruction into a formal JSON reflex policy for the NEXUS autopilot system.

INPUT:
  Intent: {intent_category}
  Raw narration: "{raw_narration}"
  Extracted entities: {entity_dict}
  Current context: {context_snapshot}
  Reward weights: {reward_weights}

OUTPUT FORMAT (strict JSON, no markdown):
{{
  "reflex_id": "R-{intent_category}-{unique_id}",
  "name": "{human_readable_name}",
  "description": "{one_sentence_description}",
  "trigger": {{
    "conditions": [
      {{"sensor": "<field>", "operator": "<op>", "value": <num>}},
      ...
    ],
    "logic": "AND",
    "cooldown_seconds": {cooldown},
    "max_activations_per_hour": {max_activations}
  }},
  "action_sequence": [
    {{
      "actuator": "<field>",
      "command": {{
        "type": "absolute" | "relative" | "rate",
        "value": <num>,
        "unit": "<unit>"
      }},
      "delay_ms": <num>,
      "duration_ms": <num>,
      "condition": "<optional_guard>"
    }},
    ...
  ],
  "safety_constraints": [
    {{
      "description": "<human_readable>",
      "sensor": "<field>",
      "operator": "<op>",
      "value": <num>,
      "on_violation": "abort" | "override_to_safe" | "warn"
    }},
    ...
  ],
  "priority": <int_0_to_100>,
  "autonomy_level_required": <int_0_to_5>,
  "evaluation_metrics": [
    {{
      "name": "<metric_name>",
      "formula": "<metric_formula>",
      "expected_range": [<min>, <max>],
      "weight": <float>
    }},
    ...
  ],
  "expiry": "{ISO8601_datetime_or_never}",
  "tags": ["{tag1}", "{tag2}"]
}}

RULES:
1. Every reflex MUST include at least one safety constraint.
2. Actuator commands must respect physical limits (see actuator ranges above).
3. Prioritize safety over precision in ambiguous situations.
4. If the narration is ambiguous, set "needs_clarification": true and include
   a "clarification_prompt" field.
5. Cooldown should prevent rapid re-triggering (minimum 5 seconds).
6. For navigational commands, always include a safety constraint on obstacle proximity.
```

### 3.4 Entity Resolution Rules

```python
ENTITY_RESOLUTION_TABLE = {
    # ── Direction Terms ────────────────────────────────────────
    "port":                {"type": "direction", "value": "270", "unit": "deg"},
    "starboard":           {"type": "direction", "value": "90",  "unit": "deg"},
    "left":                {"type": "direction", "value": "270", "unit": "deg"},
    "right":               {"type": "direction", "value": "90",  "unit": "deg"},
    "ahead":               {"type": "direction", "value": "0",   "unit": "deg"},
    "astern":              {"type": "direction", "value": "180", "unit": "deg"},
    "bow":                 {"type": "position",  "value": "0",   "unit": "deg"},
    "stern":               {"type": "position",  "value": "180", "unit": "deg"},

    # ── Speed Terms ────────────────────────────────────────────
    "idle":                {"type": "speed",     "value": "0.0",  "unit": "m/s"},
    "slow":                {"type": "speed",     "value": "1.5",  "unit": "m/s"},
    "cruising speed":      {"type": "speed",     "value": "5.1",  "unit": "m/s"},
    "full speed":          {"type": "speed",     "value": "7.7",  "unit": "m/s"},
    "dead slow":           {"type": "speed",     "value": "0.8",  "unit": "m/s"},
    "half speed":          {"type": "speed",     "value": "3.8",  "unit": "m/s"},
    "three-quarter speed": {"type": "speed",     "value": "5.8",  "unit": "m/s"},

    # ── Numeric Conversion ─────────────────────────────────────
    "knots":               {"type": "unit_conv", "factor": "0.5144", "to": "m/s"},
    "nautical miles":      {"type": "unit_conv", "factor": "1852.0", "to": "m"},
    "fathoms":             {"type": "unit_conv", "factor": "1.8288", "to": "m"},
    "feet":                {"type": "unit_conv", "factor": "0.3048", "to": "m"},
    "yards":               {"type": "unit_conv", "factor": "0.9144", "to": "m"},

    # ── Heading (spoken as individual digits) ──────────────────
    # Pattern: r"heading\s+(zero|one|two|three|four|five|six|seven|eight|nine)\s*-*\s*..."
    "zero":   {"type": "heading_digit", "value": "0"},
    "one":    {"type": "heading_digit", "value": "1"},
    "two":    {"type": "heading_digit", "value": "2"},
    "three":  {"type": "heading_digit", "value": "3"},
    "four":   {"type": "heading_digit", "value": "4"},
    "five":   {"type": "heading_digit", "value": "5"},
    "six":    {"type": "heading_digit", "value": "6"},
    "seven":  {"type": "heading_digit", "value": "7"},
    "eight":  {"type": "heading_digit", "value": "8"},
    "nine":   {"type": "heading_digit", "value": "9"},
    "north":  {"type": "compass", "value": "0"},
    "south":  {"type": "compass", "value": "180"},
    "east":   {"type": "compass", "value": "90"},
    "west":   {"type": "compass", "value": "270"},
    "northeast":  {"type": "compass", "value": "45"},
    "southeast":  {"type": "compass", "value": "135"},
    "southwest":  {"type": "compass", "value": "225"},
    "northwest":  {"type": "compass", "value": "315"},

    # ── Distance Qualifiers ────────────────────────────────────
    "close":          {"type": "distance_qualifier", "value": "10",   "unit": "m"},
    "very close":     {"type": "distance_qualifier", "value": "5",    "unit": "m"},
    "far":            {"type": "distance_qualifier", "value": "100",  "unit": "m"},
    "very far":       {"type": "distance_qualifier", "value": "500",  "unit": "m"},
    "wide berth":     {"type": "distance_qualifier", "value": "50",   "unit": "m"},
    "safe distance":  {"type": "distance_qualifier", "value": "30",   "unit": "m"},

    # ── Vessel Parts ───────────────────────────────────────────
    "rudder":         {"type": "actuator", "field": "rudder_angle_deg"},
    "throttle":       {"type": "actuator", "field": "throttle_pct"},
    "bow thruster":   {"type": "actuator", "field": "bow_thruster_pct"},
    "stern thruster": {"type": "actuator", "field": "stern_thruster_pct"},
    "trim tabs":      {"type": "actuator", "field": "trim_tab_angle_deg"},
    "anchor":         {"type": "actuator", "field": "anchor_winch_m"},
}
```

### 3.5 Ambiguity Scoring Algorithm

```python
def compute_ambiguity_score(
    intent: str,
    entities: dict,
    confidence: float,
    narration: str,
) -> tuple[float, list[str]]:
    """
    Returns (ambiguity_score, list_of_ambiguity_factors).

    Ambiguity score ranges from 0.0 (fully clear) to 1.0 (maximally ambiguous).

    Score Components (weighted sum):
    ────────────────────────────────
    1. Intent confidence deficit:    weight = 0.25
       deficit = max(0, 1.0 - confidence)

    2. Missing required entities:    weight = 0.30
       missing_ratio = count(missing_required) / count(total_required)

    3. Entity value precision:       weight = 0.20
       imprecision = 0 if all entities have exact numeric values,
                     0.5 if using qualitative terms ("close", "slow"),
                     1.0 if entities are completely absent

    4. Context conflict:             weight = 0.15
       conflict = 1.0 if entity values contradict current state
                 (e.g., "speed up to 20 knots" when max speed is 10 knots)
       Otherwise 0.0

    5. Multiple valid interpretations: weight = 0.10
       Interpretability score from intent classifier's softmax output.
       entropy = -sum(p * log(p)) / log(num_classes)
       High entropy = ambiguous intent.

    Total: 0.25 * deficit + 0.30 * missing + 0.20 * precision +
           0.15 * conflict + 0.10 * entropy

    Thresholds:
      score < 0.2:  CLEAR - proceed directly to policy extraction
      0.2 <= score < 0.5: MINOR - proceed but flag for review
      0.5 <= score < 0.8: MODERATE - enter clarification dialogue
      score >= 0.8: SEVERE - reject and request re-narration
    """
```

### 3.6 Clarification Dialogue State Machine

```
States:
  IDLE            -> listening for narration
  PROCESSING      -> transcribing, classifying, extracting entities
  CLARIFYING      -> asking follow-up questions
  CONFIRMING      -> presenting extracted policy for approval
  REJECTED        -> narration could not be parsed (return to IDLE)

Transitions:

  IDLE
    │ (narration detected by VAD)
    ▼
  PROCESSING
    │
    ├── (ambiguity < 0.2)  ──► CONFIRMING
    ├── (ambiguity < 0.5)  ──► CONFIRMING (with review flag)
    ├── (ambiguity < 0.8)  ──► CLARIFYING
    └── (ambiguity >= 0.8) ──► REJECTED

  CLARIFYING
    │  Generate clarification question based on ambiguity factors:
    │    - Missing entity:       "What heading should I steer?"
    │    - Imprecise value:      "By 'slow', do you mean ~3 knots or ~1.5 knots?"
    │    - Context conflict:     "Current speed is already below your target. Clarify?"
    │    - Multiple intents:     "Did you mean to change speed or change heading?"
    │
    ├── (pilot responds with clarification)
    │   │ Re-run entity extraction with combined context
    │   │ Recompute ambiguity score
    │   ├── (new ambiguity < 0.3) ──► CONFIRMING
    │   └── (new ambiguity >= 0.3) ──► CLARIFYING (max 3 rounds)
    │
    ├── (max 3 clarification rounds reached)
    │   └──► CONFIRMING (with best-guess flag)
    │
    └── (pilot cancels) ──► IDLE

  CONFIRMING
    │  Present extracted reflex JSON to pilot:
    │  "I understood: [trigger] -> [action]. Is this correct?"
    │
    ├── (pilot confirms) ──► IDLE (reflex submitted to validation pipeline)
    └── (pilot corrects) ──► CLARIFYING

  REJECTED
    │  Audio prompt: "I didn't understand that. Please try again."
    │  Wait 2 seconds for pilot to re-narrate.
    │
    └──► IDLE
```

---

## 4. A/B Testing Framework

### 4.1 Test Configuration

```python
@dataclass(frozen=True)
class ABTestConfig:
    """
    Configuration for an A/B test comparing two reflex policies or
    autonomy configurations.
    """
    test_id:             str       # UUIDv4
    name:                str       # Human-readable test name
    description:         str       # What is being tested and why
    created_at:          datetime  # ISO 8601

    # ── What is being tested ───────────────────────────────────
    reflex_id_control:   str       # ID of the control (current) reflex
    reflex_id_treatment: str       # ID of the treatment (new) reflex
    trigger_condition:   str       # Common trigger that activates either reflex

    # ── Randomization ──────────────────────────────────────────
    randomization_method: str = "alternating"
    # Options:
    #   "alternating"    - strictly ABABAB... (deterministic, simple)
    #   "random"         - 50/50 coin flip per trigger event
    #   "stratified"     - balance by context (e.g., weather, traffic density)
    #   "bandit"         - Thompson sampling, adaptively favouring better arm

    random_seed:         int = 42

    # ── Stopping conditions ────────────────────────────────────
    min_duration_hours:  float = 4.0     # Minimum 2 hours per condition
    min_triggers_per_condition: int = 30 # Minimum 30 trigger events per condition
    max_duration_hours:  float = 48.0    # Safety limit
    alpha:               float = 0.05    # Statistical significance level

    # ── Safety limits ──────────────────────────────────────────
    max_override_rate:   float = 0.05    # 5% override rate triggers rollback
    max_response_latency_s: float = None  # If set, >2x baseline triggers rollback
    zero_tolerance_events: list[str] = [
        "safety_rule_violation",
        "sensor_failure",
        "heartbeat_timeout",
    ]  # Any of these during treatment -> immediate rollback
```

### 4.2 Standardized Metrics

```python
STANDARD_METRICS = {
    "fuel_efficiency": {
        "name": "Fuel Efficiency",
        "unit": "km/L",
        "formula": "distance_m / fuel_consumed_L / 1000",
        "higher_is_better": True,
        "compute": lambda df: (
            (df['gps_speed_m_s'] * df['timestamp_ns'].diff().abs() / 1e9).sum()
            / df['fuel_flow_L_h'].sum() * 3600 / 1000
        ),
        "typical_range": (1.0, 15.0),
    },
    "speed_consistency": {
        "name": "Speed Consistency",
        "unit": "ratio",
        "formula": "1 - std(target_speed - actual_speed) / mean(target_speed)",
        "higher_is_better": True,
        "compute": lambda df, target: (
            1.0 - np.std(target - df['gps_speed_m_s'].values)
                 / (np.mean(target) + 1e-10)
        ),
        "typical_range": (0.0, 1.0),
    },
    "heading_accuracy": {
        "name": "Heading Accuracy",
        "unit": "degrees",
        "formula": "mean(|target_heading - actual_heading|)",
        "higher_is_better": False,  # Lower is better
        "compute": lambda df, target: float(np.mean(np.abs(
            np.radians(target - df['gps_heading_deg'].values)
        )) * 180 / np.pi),
        "typical_range": (0.0, 30.0),
    },
    "ride_comfort": {
        "name": "Ride Comfort",
        "unit": "m/s^2",
        "formula": "RMS(sqrt(accel_heave^2 + accel_roll^2))",
        "higher_is_better": False,  # Lower is better
        "compute": lambda df: float(np.sqrt(np.mean(
            df['imu_accel_z_m_s2'].values ** 2
            + df['imu_roll_deg'].values ** 2 * (np.pi / 180) ** 2
        ))),
        "typical_range": (0.0, 5.0),
    },
    "override_frequency": {
        "name": "Override Frequency",
        "unit": "overrides/hour",
        "formula": "count_overrides / duration_hours",
        "higher_is_better": False,
        "compute": lambda df: (
            df['override_active'].sum()
            / (df['timestamp_ns'].iloc[-1] - df['timestamp_ns'].iloc[0]) / 1e9 / 3600
        ),
        "typical_range": (0.0, 10.0),
    },
    "response_latency_ms": {
        "name": "Response Latency",
        "unit": "milliseconds",
        "formula": "mean(time_trigger_to_actuator_response)",
        "higher_is_better": False,
        "compute": lambda trigger_times, action_times: float(
            np.mean([
                (action - trigger) / 1e6
                for trigger, action in zip(trigger_times, action_times)
            ])
        ),
        "typical_range": (50.0, 2000.0),
    },
    "actuator_wear": {
        "name": "Actuator Wear Index",
        "unit": "deg/hour or %/hour (per actuator)",
        "formula": "sum(|delta_actuator|) / duration_hours",
        "higher_is_better": False,
        "compute": lambda df, actuator_col: float(
            np.abs(np.diff(df[actuator_col].values)).sum()
            / (df['timestamp_ns'].iloc[-1] - df['timestamp_ns'].iloc[0]) / 1e9 * 3600
        ),
        "typical_range": (0.0, 10000.0),
    },
}
```

### 4.3 Statistical Testing

```python
def evaluate_ab_test(
    control_metrics: dict[str, list[float]],
    treatment_metrics: dict[str, list[float]],
    alpha: float = 0.05,
) -> dict:
    """
    Evaluate A/B test results using paired statistical tests.

    Parameters
    ----------
    control_metrics : dict[str, list[float]]
        Metric values from control condition.
        Key = metric name, Value = list of per-trigger-event metric values.
    treatment_metrics : dict[str, list[float]]
        Same structure for treatment condition.

    Returns
    -------
    dict with keys:
      - metric_name: {
          "control_mean": float,
          "treatment_mean": float,
          "absolute_change": float,
          "relative_change_pct": float,
          "t_statistic": float,
          "p_value": float,
          "significant": bool,
          "cohens_d": float,
          "effect_label": str,   # "negligible" | "small" | "medium" | "large"
          "confidence_interval_95": (float, float),
        }

    Statistical Test: Paired two-tailed t-test (scipy.stats.ttest_rel)
    ──────────────────────────────────────────────────────────────
    Assumptions:
      1. Paired observations (same trigger events evaluated under both conditions)
      2. Differences are approximately normally distributed
      3. Independence between pairs

    H0: mean(control - treatment) = 0
    H1: mean(control - treatment) != 0

    If p_value < alpha AND |cohens_d| >= 0.2:
        Result is "statistically significant with at least small effect"

    Effect Size: Cohen's d (paired)
    ────────────────────────────────────
    d = mean(control - treatment) / std(control - treatment)

    Interpretation:
      |d| < 0.2:  "negligible"
      |d| < 0.5:  "small"
      |d| < 0.8:  "medium"
      |d| >= 0.8: "large"

    Confidence Interval: 95% CI for mean difference
    ────────────────────────────────────────────────
    CI = mean_diff +/- t_critical * (std_diff / sqrt(n))
    where t_critical = t.ppf(0.975, df=n-1)
    """
    from scipy import stats

    results = {}
    for metric_name in control_metrics:
        control = np.array(control_metrics[metric_name])
        treatment = np.array(treatment_metrics[metric_name])

        # Ensure equal length (pair)
        n = min(len(control), len(treatment))
        control = control[:n]
        treatment = treatment[:n]

        # Paired t-test
        t_stat, p_value = stats.ttest_rel(control, treatment)

        # Cohen's d (paired)
        differences = control - treatment
        cohens_d = np.mean(differences) / (np.std(differences) + 1e-10)

        # 95% CI
        t_crit = stats.t.ppf(0.975, df=n - 1)
        se = np.std(differences) / np.sqrt(n)
        ci = (np.mean(differences) - t_crit * se,
              np.mean(differences) + t_crit * se)

        # Effect label
        abs_d = abs(cohens_d)
        if abs_d < 0.2:
            effect_label = "negligible"
        elif abs_d < 0.5:
            effect_label = "small"
        elif abs_d < 0.8:
            effect_label = "medium"
        else:
            effect_label = "large"

        results[metric_name] = {
            "control_mean": float(np.mean(control)),
            "treatment_mean": float(np.mean(treatment)),
            "absolute_change": float(np.mean(treatment) - np.mean(control)),
            "relative_change_pct": float(
                (np.mean(treatment) - np.mean(control))
                / (np.mean(control) + 1e-10) * 100
            ),
            "t_statistic": float(t_stat),
            "p_value": float(p_value),
            "significant": bool(p_value < alpha),
            "cohens_d": float(cohens_d),
            "effect_label": effect_label,
            "confidence_interval_95": (float(ci[0]), float(ci[1])),
        }

    return results
```

### 4.4 Automatic Rollback Triggers

```python
def check_rollback_conditions(
    treatment_session_data: pd.DataFrame,
    baseline_metrics: dict[str, float],
    config: ABTestConfig,
) -> tuple[bool, str]:
    """
    Check if treatment should be immediately rolled back.

    Rollback Conditions (ANY triggers rollback):
    ──────────────────────────────────────────────
    1. Override rate > 5%:
       count(override_active=True) / total_rows > 0.05
       Rationale: Pilot is rejecting the treatment's decisions.

    2. Any zero-tolerance safety event:
       safety_rule_violation == True at any point
       sensor_failure == True at any point
       heartbeat_timeout == True at any point
       Rationale: Treatment caused or failed to prevent a safety incident.

    3. Response latency > 2x baseline:
       mean_response_latency_treatment > 2 * mean_response_latency_baseline
       Rationale: Treatment is dangerously slow.

    4. Heading accuracy > 3x baseline:
       mean_heading_error_treatment > 3 * mean_heading_error_baseline
       Rationale: Treatment is losing control of heading.

    Returns (should_rollback: bool, reason: str)
    """
```

### 4.5 Test Execution Flow

```
1. CONFIGURE
   - Define test with ABTestConfig
   - Verify baseline metrics exist (from last N hours of control operation)
   - Assign test_id, write config to /data/ab_tests/{test_id}/config.json

2. ARM
   - Load both reflex policies (control + treatment) into reflex executor
   - Register trigger condition with randomization selector
   - Log: test started, expected duration, stopping criteria

3. EXECUTE
   - On each trigger event:
     a. Select condition (control or treatment) per randomization_method
     b. Execute the selected reflex
     c. Record metrics for this event (all 7 standard metrics)
     d. Check rollback conditions on treatment events
     e. If rollback triggered: halt test, log reason, revert to control-only
   - Periodically (every 30 min): check if stopping criteria met

4. EVALUATE (stopping criteria met)
   - Run evaluate_ab_test() on collected metric pairs
   - Generate report:
     * Per-metric: mean, change, p-value, effect size, CI
     * Overall: recommendation (adopt / iterate / reject)
   - Store report at /data/ab_tests/{test_id}/report.json

5. FINALIZE
   - If treatment wins significantly on primary metric AND
     no safety regression: promote treatment to new default
   - If inconclusive: extend test or iterate on treatment
   - If treatment loses: revert to control, log learnings
```

---

## 5. Reflex Synthesis Pipeline

### 5.1 Cloud LLM System Prompt

The following prompt is sent to the cloud LLM (GPT-4 class) to generate a reflex JSON from extracted narration data:

```
SYSTEM PROMPT (Cloud LLM Reflex Synthesis)
==========================================

You are the NEXUS Reflex Synthesis Engine. Your role is to convert structured
narration data into safe, executable JSON reflex policies for an autonomous
maritime vessel autopilot.

CRITICAL SAFETY RULES (these override all other instructions):
──────────────────────────────────────────────────────────────
1. EVERY reflex MUST include a hard safety constraint that limits maximum
   actuator output. No reflex may command full deflection without a guard.
2. Every reflex MUST include an obstacle proximity guard: if lidar_obstacle_dist_m
   < 5.0, the reflex must yield to collision avoidance.
3. Rudder commands are clamped to [-45, +45] degrees. Throttle to [0, 100] percent.
   Never generate commands outside these ranges.
4. A reflex MUST have a cooldown of at least 3 seconds between activations.
5. If the narration mentions speed values > vessel_max_speed (default 7.7 m/s),
   clamp to vessel_max_speed and note the clamping.
6. Every action sequence MUST include a termination condition or maximum duration.
7. Reflexes that modify navigation (heading/speed) MUST include a maximum
   duration of 300 seconds (5 minutes) after which they auto-expire.
8. NEVER generate a reflex that disables or overrides safety systems.

INPUT SCHEMA:
─────────────
{
  "intent": "<one of: navigational_command, safety_alert, operational_instruction, preference_expression>",
  "entities": {
    "action": "<string>",
    "target": "<string or number with unit>",
    "hazard_type": "<string>",
    "location": "<string>",
    "system": "<string>",
    "condition": "<string>",
    "value": "<number>",
    "preference_topic": "<string>",
    "sentiment": "<positive|negative|neutral>"
  },
  "context": {
    "current_speed_m_s": <float>,
    "current_heading_deg": <float>,
    "current_position": {"lat": <float>, "lon": <float>},
    "wind_speed_m_s": <float>,
    "wind_direction_deg": <float>,
    "nearest_obstacle_m": <float>,
    "autonomy_level": <int 0-5>,
    "vessel_max_speed_m_s": <float>,
    "vessel_length_m": <float>,
    "vessel_type": "<string>"
  },
  "reward_weights": {
    "speed_comfort": <float>,
    "heading_accuracy": <float>,
    "fuel_efficiency": <float>,
    "smoothness": <float>,
    "safety_margin": <float>,
    "wind_compensation": <float>
  },
  "ambiguity_score": <float 0-1>
}

OUTPUT SCHEMA (strict JSON, no markdown fences):
─────────────────────────────────────────────────
{
  "reflex_id": "R-{intent}-{8_char_random_hex}",
  "name": "<short_descriptive_name>",
  "description": "<one_sentence_what_this_reflex_does>",
  "source": {
    "narration": "<original_raw_text>",
    "intent": "<classified_intent>",
    "confidence": <float>,
    "created_at": "<ISO8601>"
  },
  "trigger": {
    "conditions": [
      {"sensor": "<UnifiedObservation_field>", "operator": "<|>|<=|>=|==|!=|changes_by|crosses>", "value": <number>}
    ],
    "logic": "AND",
    "cooldown_seconds": <int, minimum 3>,
    "max_activations_per_hour": <int, recommended 60>
  },
  "action_sequence": [
    {
      "step": <int, 0-indexed>,
      "actuator": "<UnifiedObservation_actuator_field>",
      "command": {
        "type": "<absolute|relative|rate>",
        "value": <number>,
        "unit": "<deg|pct|m>"
      },
      "delay_ms": <int, 0 = immediate>,
      "duration_ms": <int, max 300000>,
      "condition": "<optional_guard_condition_string>"
    }
  ],
  "termination": {
    "type": "<timeout|condition|manual>",
    "timeout_ms": <int>,
    "condition": "<optional_success_condition>"
  },
  "safety_constraints": [
    {
      "id": "sc_obsacle_guard",
      "description": "Yield for collision avoidance",
      "sensor": "lidar_obstacle_dist_m",
      "operator": "<",
      "value": 5.0,
      "on_violation": "abort"
    },
    {
      "id": "sc_actuator_limit",
      "description": "Actuator range limit",
      "sensor": "<actuator_field>",
      "operator": "!=",
      "value": "clamped",
      "on_violation": "clamp_to_range"
    }
  ],
  "priority": <int 0-100, default 50>,
  "autonomy_level_required": <int 0-5>,
  "evaluation_metrics": [
    {
      "name": "<metric_name_from_standard_set>",
      "expected_direction": "<higher_is_better|lower_is_better>",
      "expected_magnitude": "<approximate_value>"
    }
  ],
  "tags": ["synthesized", "<intent_category>"],
  "needs_clarification": <bool>,
  "clarification_prompt": "<string or null>"
}

QUALITY REQUIREMENTS:
─────────────────────
- The trigger conditions must be specific enough to avoid false activations
  but general enough to fire in the intended scenarios.
- The action sequence must be physically realistic for the vessel type.
- Safety constraints must cover both the specific action and general hazards.
- The reflex should be self-contained and not depend on other reflexes.
- If ambiguity_score >= 0.5, set needs_clarification=true and provide a
  concise clarification_prompt.
```

### 5.2 Validation Tiers

```python
@dataclass(frozen=True)
class ValidationResult:
    tier:           str       # "syntax" | "semantic" | "safety" | "simulation"
    passed:         bool
    score:          float     # 0.0 to 1.0
    findings:       list[dict]# [{severity, message, field, suggestion}]
    duration_ms:    float


VALIDATION_TIERS = {
    # ── Tier 1: Syntax Validation ──────────────────────────────
    "syntax": {
        "executor": "jetson_local",
        "timeout_ms": 100,
        "checks": [
            "Valid JSON with all required fields present",
            "reflex_id matches pattern R-{intent}-{hex8}",
            "trigger.conditions is non-empty array",
            "action_sequence is non-empty array",
            "safety_constraints has >= 1 entry",
            "actuator names exist in UnifiedObservation schema",
            "sensor names exist in UnifiedObservation schema",
            "operator values are in allowed set: >, <, >=, <=, ==, !=, changes_by, crosses",
            "numeric values are within physical limits for their fields",
            "cooldown_seconds >= 3",
            "autonomy_level_required is int in [0, 5]",
            "priority is int in [0, 100]",
        ],
        "pass_criteria": "ALL checks pass. No warnings.",
        "fail_action": "Reject reflex. Return error messages to cloud pipeline.",
    },

    # ── Tier 2: Semantic Validation ────────────────────────────
    "semantic": {
        "executor": "jetson_local",
        "timeout_ms": 500,
        "checks": [
            "Trigger conditions are logically consistent (no contradictions)",
            "Action sequence steps are in correct dependency order",
            "No circular references in condition fields",
            "Termination condition is reachable from action sequence",
            "Duration_ms values are positive and bounded (max 300,000 ms)",
            "Sensor/actuator field types match expected data types",
            "No duplicate safety_constraint IDs",
            "Priority does not conflict with existing critical reflexes",
            "Tags contain 'synthesized' and the intent category",
        ],
        "pass_criteria": "ALL checks pass. Warnings allowed but logged.",
        "fail_action": "Flag for human review. Do not deploy.",
    },

    # ── Tier 3: Safety Validation ──────────────────────────────
    "safety": {
        "executor": "jetson_local",
        "timeout_ms": 1000,
        "checks": [
            "Obstacle proximity guard present (< 5m abort)",
            "Actuator commands respect physical limits (clamped check)",
            "Maximum duration constraint present for navigation changes",
            "No reflex can disable safety systems",
            "Priority does not exceed critical safety reflexes (priority > 90 reserved)",
            "Action sequence cannot create a sustained dangerous state",
            "Rate of change commands (type='rate') have reasonable limits",
            "If autonomy_level_required >= 3, safety_constraints has >= 3 entries",
            "No reflex modifies vault12_status or heartbeat-related systems",
        ],
        "pass_criteria": "ALL checks pass. ANY failure blocks deployment.",
        "fail_action": "BLOCK. Return to cloud pipeline with detailed safety findings.",
    },

    # ── Tier 4: Simulation Validation ──────────────────────────
    "simulation": {
        "executor": "cloud_gpu",
        "timeout_ms": 60000,
        "methodology": "See section 5.3 below",
        "checks": [
            "Reflex executes without errors in 100 simulated trigger events",
            "No safety constraint violations in simulation",
            "Metric values are within typical range (see STANDARD_METRICS)",
            "No oscillation or instability in actuator outputs",
            "Response latency < 200ms in simulation",
        ],
        "pass_criteria": "ALL checks pass across 100 scenarios.",
        "fail_action": "Flag for human review with simulation logs.",
    },
}
```

### 5.3 Simulation Replay Methodology

```python
def simulate_reflex(
    reflex_json: dict,
    session_data: pd.DataFrame,
    n_scenarios: int = 100,
    perturbation_std: float = 0.1,
) -> dict:
    """
    Replay the reflex against historical session data with perturbations
    to test robustness.

    Parameters
    ----------
    reflex_json : dict
        Validated reflex JSON (passed tiers 1-3).
    session_data : pd.DataFrame
        Historical observation session used as simulation environment.
    n_scenarios : int = 100
        Number of perturbed replay scenarios.
    perturbation_std : float = 0.1
        Standard deviation of Gaussian noise added to sensor readings.

    Algorithm
    ---------
    For each scenario i in range(n_scenarios):
      1. Create perturbed session: session_data + N(0, perturbation_std * sensor_range)
      2. Find trigger timestamps in perturbed data
      3. For each trigger:
         a. Execute reflex action sequence deterministically
         b. Record actuator commands and resulting state changes
         c. Check all safety constraints at each timestep
         d. Compute metrics (fuel_efficiency, heading_accuracy, etc.)
      4. Aggregate: record pass/fail, constraint violations, metric values

    Evaluation
    ----------
    A scenario "passes" if:
      - Zero safety constraint violations
      - All metrics within 3 standard deviations of historical baseline
      - No actuator oscillation (defined as > 5 zero-crossings in 2 seconds)

    Overall simulation passes if:
      - >= 95 of 100 scenarios pass
      - Mean metric values are within 10% of historical baseline
      - Zero critical safety constraint violations across all scenarios

    Returns
    -------
    {
      "scenarios_passed": int,
      "scenarios_total": int,
      "pass_rate": float,
      "mean_metrics": dict,
      "std_metrics": dict,
      "safety_violations": list[dict],
      "oscillation_events": list[dict],
      "recommendation": "APPROVE" | "REVIEW" | "REJECT"
    }
    """
```

### 5.4 Human Review Checklist

```python
HUMAN_REVIEW_CHECKLIST = {
    "reflex_id": "R-XXXXXXXX",
    "reviewer": "",
    "review_date": "",
    "sections": [
        {
            "category": "Intent Accuracy",
            "items": [
                "Does the reflex accurately capture the pilot's narrated intent?",
                "Are the entity values correct (heading, speed, distance)?",
                "Is the trigger specific enough to fire in the right situations?",
            ],
        },
        {
            "category": "Safety",
            "items": [
                "Are all required safety constraints present?",
                "Is the obstacle proximity guard (< 5m) included?",
                "Are actuator limits properly clamped?",
                "Is the maximum duration reasonable?",
                "Could this reflex interfere with any existing safety reflex?",
                "Is the priority level appropriate (not conflicting with safety systems)?",
            ],
        },
        {
            "category": "Performance",
            "items": [
                "Is the action sequence efficient and minimal?",
                "Are the delays between steps reasonable?",
                "Is the cooldown appropriate?",
                "Does the expected impact align with reward weights?",
            ],
        },
        {
            "category": "Robustness",
            "items": [
                "Does the reflex handle edge cases (sensor NaN, timeout)?",
                "Is the trigger resilient to noise in sensor data?",
                "Would this reflex behave safely in adverse weather?",
                "Would this reflex behave safely in high traffic?",
            ],
        },
        {
            "category": "Scope",
            "items": [
                "Is the autonomy_level_required appropriate?",
                "Should this reflex be vessel-specific or fleet-wide?",
                "Should it have a time-limited expiry?",
                "Are the tags accurate and useful for search?",
            ],
        },
    ],
    "verdict": "APPROVED | REJECTED | NEEDS_REVISION",
    "revision_notes": "",
}
```

---

## Appendix: Data Flow Diagram

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         NEXUS LEARNING PIPELINE                         │
│                                                                         │
│  ┌──────────┐   ┌──────────────┐   ┌────────────────────────────────┐  │
│  │  Sensors  │──▶│ Observation   │──▶│     Storage Tiers             │  │
│  │  (CAN/   │   │ Bus (100Hz)   │   │  HOT ──▶ WARM ──▶ COLD ──▶ X  │  │
│  │  SPI/I2C)│   │              │   │  7d     90d     2yr            │  │
│  └──────────┘   └──────────────┘   └────────────────────────────────┘  │
│                                         │                               │
│                                         ▼                               │
│  ┌──────────┐   ┌──────────────┐   ┌────────────────────────────────┐  │
│  │  Micro-  │   │  Narration   │──▶│    Pattern Discovery Engine    │  │
│  │  phone   │──▶│  Processor   │   │  ┌──────────────────────────┐  │  │
│  │  (Whisper)│  │  (Intent +   │   │  │ Cross-correlation scanner │  │  │
│  └──────────┘   │   Entity)    │   │  │ Change-point detection    │  │  │
│                 └──────────────┘   │  │ Behavioral clustering      │  │  │
│                        │           │  │ Temporal pattern mining    │  │  │
│                        ▼           │  │ Bayesian reward inference  │  │  │
│                 ┌──────────────┐   │  └──────────────────────────┘  │  │
│                 │  Cloud LLM   │   └────────────────────────────────┘  │
│                 │  Reflex      │                  │                     │
│                 │  Synthesis   │                  ▼                     │
│                 └──────────────┘   ┌────────────────────────────────┐  │
│                        │           │       A/B Testing              │  │
│                        ▼           │  ┌──────────────────────────┐  │  │
│                 ┌──────────────┐   │  │ Control vs Treatment     │  │  │
│                 │  Validation  │   │  │ 7 standard metrics       │  │  │
│                 │  Pipeline    │   │  │ Paired t-test            │  │  │
│                 │  (4 tiers)   │   │  │ Automatic rollback       │  │  │
│                 └──────────────┘   │  └──────────────────────────┘  │  │
│                        │           └────────────────────────────────┘  │
│                        ▼                                              │
│                 ┌──────────────┐                                       │
│                 │  Reflex      │                                       │
│                 │  Executor    │                                       │
│                 │  (Production)│                                       │
│                 └──────────────┘                                       │
└─────────────────────────────────────────────────────────────────────────┘
```

---

*End of NEXUS Learning Pipeline Specification*

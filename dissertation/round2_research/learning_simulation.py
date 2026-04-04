#!/usr/bin/env python3
"""
NEXUS Learning Pipeline Simulation
===================================
Simulates the full learning loop:
  Observe → Record → Discover Patterns → Synthesize Reflex → A/B Test → Deploy

Models multivariate time series with realistic sensor noise for a marine vessel,
implements simplified versions of all 5 pattern discovery algorithms, simulates
A/B testing with Bayesian statistical significance, and measures convergence.

Output: /nexus_dissertation/figures/learning_pipeline.png
"""

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
from collections import defaultdict
import json
import os
import warnings
warnings.filterwarnings("ignore")

np.random.seed(42)

# ============================================================================
# Configuration
# ============================================================================
FIGURES_DIR = "/home/z/my-project/download/nexus_dissertation/figures"
DATA_DIR = "/home/z/my-project/download/nexus_dissertation/figures"
SAMPLE_RATE_HZ = 100.0
SESSION_DURATION_S = 600.0  # 10 minutes per session
N_SESSIONS = 30
N_FIELDS = 15  # Simplified subset of 72 UnifiedObservation fields

# Field definitions: (name, mean, std, noise_std, unit)
SENSOR_FIELDS = {
    "gps_speed_m_s":       (5.0,  1.5,  0.3, "m/s"),
    "gps_heading_deg":     (180.0, 30.0, 2.0, "deg"),
    "imu_roll_deg":        (3.0,  2.0,  0.5, "deg"),
    "imu_pitch_deg":       (1.5,  1.0, 0.3, "deg"),
    "wind_speed_m_s":      (6.0,  3.0,  0.5, "m/s"),
    "wind_direction_deg":  (220.0, 40.0, 5.0, "deg"),
    "wave_height_m":       (0.8,  0.3,  0.05, "m"),
    "lidar_obstacle_dist_m": (80.0, 30.0, 2.0, "m"),
    "engine_rpm":          (2200.0, 400.0, 50.0, "rpm"),
    "fuel_flow_L_h":       (12.0, 4.0, 0.8, "L/h"),
    "rudder_angle_deg":    (0.0,  8.0, 1.0, "deg"),
    "throttle_pct":        (45.0, 15.0, 2.0, "%"),
    "barometric_hpa":      (1013.0, 5.0, 0.3, "hPa"),
    "water_temp_c":        (15.0, 2.0, 0.2, "C"),
    "engine_temp_c":       (85.0, 5.0, 1.0, "C"),
}

ACTUATOR_FIELDS = ["throttle_pct", "rudder_angle_deg"]
SENSOR_NAMES = list(SENSOR_FIELDS.keys())


# ============================================================================
# Step 1: Observation Data Generation
# ============================================================================
class VesselSimulator:
    """Generates realistic multivariate time series for a marine vessel."""

    def __init__(self, sample_rate=SAMPLE_RATE_HZ, duration_s=SESSION_DURATION_S):
        self.sr = sample_rate
        self.duration = duration_s
        self.n_samples = int(sample_rate * duration_s)
        self.t = np.linspace(0, duration_s, self.n_samples, endpoint=False)

    def generate_session(self, session_id, scenario="cruising"):
        """Generate a single observation session."""
        data = {}

        # Base behavior patterns
        if scenario == "cruising":
            speed_base = 5.0 + np.sin(2 * np.pi * self.t / 120) * 0.5
            rudder_base = np.sin(2 * np.pi * self.t / 60) * 3.0  # gentle oscillation
            throttle_base = 45.0 + speed_base * 2.0
            wind_base = 6.0 + np.sin(2 * np.pi * self.t / 300) * 2.0
            wave_base = 0.8 + np.sin(2 * np.pi * self.t / 180) * 0.2
            lidar_base = 80.0 + np.random.uniform(-20, 20, self.n_samples)

            # Introduce an obstacle event around t=300-350s
            obstacle_event = np.exp(-((self.t - 320) ** 2) / (2 * 15 ** 2))
            lidar_signal = lidar_base - 50 * obstacle_event
            speed_signal = speed_base - 2.0 * obstacle_event
            rudder_signal = rudder_base + 12.0 * obstacle_event * np.sin(
                2 * np.pi * (self.t - 310) / 20
            )

        elif scenario == "docking":
            speed_base = 3.0 * np.exp(-self.t / 300) + 0.5
            rudder_base = np.sin(2 * np.pi * self.t / 45) * 15.0 * np.exp(-self.t / 400)
            throttle_base = 30.0 * np.exp(-self.t / 200) + 10.0
            wind_base = 5.0 + np.sin(2 * np.pi * self.t / 200) * 3.0
            wave_base = 0.5 + np.sin(2 * np.pi * self.t / 240) * 0.1
            lidar_signal = 50.0 + np.random.uniform(-10, 10, self.n_samples)
            speed_signal = speed_base
            rudder_signal = rudder_base
            lidar_signal = np.maximum(lidar_signal - 20 * np.exp(-self.t / 200), 5.0)

        elif scenario == "rough_weather":
            speed_base = 3.5 + np.sin(2 * np.pi * self.t / 80) * 1.5
            rudder_base = np.sin(2 * np.pi * self.t / 30) * 8.0 + np.sin(
                2 * np.pi * self.t / 12
            ) * 4.0
            throttle_base = 35.0 + speed_base * 3.0
            wind_base = 15.0 + np.sin(2 * np.pi * self.t / 60) * 5.0
            wave_base = 1.8 + np.sin(2 * np.pi * self.t / 45) * 0.5
            lidar_signal = 60.0 + np.random.uniform(-15, 15, self.n_samples)
            speed_signal = speed_base
            rudder_signal = rudder_base

        else:  # mixed
            # Split session into phases
            phase1 = self.t < 200  # cruising
            phase2 = (self.t >= 200) & (self.t < 400)  # obstacle encounter
            phase3 = self.t >= 400  # recovery

            speed_signal = np.where(phase1, 5.0,
                           np.where(phase2, 2.5, 4.0))
            speed_signal += np.random.normal(0, 0.2, self.n_samples)

            rudder_signal = np.where(phase1, np.sin(2*np.pi*self.t/60)*3.0,
                            np.where(phase2, 12.0*np.exp(-((self.t-300)**2)/(2*20**2)),
                                     np.sin(2*np.pi*self.t/60)*2.0))

            throttle_base = speed_signal * 8 + 5.0
            wind_base = 7.0 + np.sin(2*np.pi*self.t/180)*3.0
            wave_base = 0.9 + np.sin(2*np.pi*self.t/120)*0.2
            lidar_signal = np.where(phase2, 20.0 + np.random.uniform(0, 10, self.n_samples),
                           80.0 + np.random.uniform(-15, 15, self.n_samples))

        # Generate all fields
        for field, (mean, std, noise, unit) in SENSOR_FIELDS.items():
            if field == "gps_speed_m_s":
                signal = speed_signal if 'speed_signal' in dir() else speed_base
            elif field == "rudder_angle_deg":
                signal = rudder_signal if 'rudder_signal' in dir() else rudder_base
            elif field == "throttle_pct":
                signal = throttle_base if 'throttle_base' in dir() else mean
            elif field == "wind_speed_m_s":
                signal = wind_base if 'wind_base' in dir() else mean
            elif field == "wave_height_m":
                signal = wave_base if 'wave_base' in dir() else mean
            elif field == "lidar_obstacle_dist_m":
                signal = lidar_signal if 'lidar_signal' in dir() else mean
            else:
                # Generic: base + slow drift + noise
                drift = np.cumsum(np.random.normal(0, std*0.01, self.n_samples))
                signal = mean + drift + np.sin(2*np.pi*self.t/(100+np.random.uniform(50,200))) * std * 0.5

            # Add realistic sensor noise (colored noise)
            white_noise = np.random.normal(0, noise, self.n_samples)
            # Simple low-pass filter for colored noise
            alpha = 0.95
            colored_noise = np.zeros(self.n_samples)
            colored_noise[0] = white_noise[0]
            for i in range(1, self.n_samples):
                colored_noise[i] = alpha * colored_noise[i-1] + (1-alpha) * white_noise[i]

            data[field] = np.clip(signal + colored_noise,
                                   mean - 4*std, mean + 4*std)

        # Derived fields
        data["gps_heading_deg"] = 180 + np.cumsum(rudder_signal * 0.001 * self.sr) / self.sr
        data["engine_rpm"] = throttle_base * 50 if 'throttle_base' in dir() else 2200
        data["engine_rpm"] += np.random.normal(0, 50, self.n_samples)
        data["fuel_flow_L_h"] = (data["throttle_pct"] / 100) * 25 + np.random.normal(0, 0.8, self.n_samples)
        data["barometric_hpa"] = 1013 + np.random.normal(0, 0.3, self.n_samples)
        data["water_temp_c"] = 15 + np.random.normal(0, 0.2, self.n_samples)
        data["engine_temp_c"] = 85 + data["throttle_pct"] * 0.2 + np.random.normal(0, 1.0, self.n_samples)

        return data


# ============================================================================
# Step 2: Pattern Discovery Algorithms (Simplified)
# ============================================================================

def cross_correlation_scan(data, max_lag=100, threshold=0.4):
    """Simplified cross-correlation: find time-lagged relationships."""
    correlations = []
    fields = list(data.keys())
    n = min(len(data[fields[0]]), 5000)  # Subsample for speed
    dt = 1.0 / SAMPLE_RATE_HZ

    for i in range(len(fields)):
        for j in range(i+1, len(fields)):
            a = data[fields[i]][:n]
            b = data[fields[j]][:n]

            # Normalize
            a_norm = (a - np.mean(a)) / (np.std(a) + 1e-10)
            b_norm = (b - np.mean(b)) / (np.std(b) + 1e-10)

            # Cross-correlation at selected lags
            lags = range(-max_lag, max_lag+1, 5)
            best_r = 0
            best_lag = 0
            for lag in lags:
                if lag >= 0:
                    corr = np.mean(a_norm[lag:] * b_norm[:n-lag])
                else:
                    corr = np.mean(a_norm[:n+lag] * b_norm[-lag:])

                if abs(corr) > abs(best_r):
                    best_r = corr
                    best_lag = lag * dt

            if abs(best_r) >= threshold:
                correlations.append({
                    "var_a": fields[i],
                    "var_b": fields[j],
                    "lag_s": best_lag,
                    "correlation": round(best_r, 3),
                })

    correlations.sort(key=lambda x: abs(x["correlation"]), reverse=True)
    return correlations


def bocpd_detect(series, hazard_lambda=0.01, threshold_prob=0.5, min_run=100):
    """Simplified Bayesian Online Change Point Detection."""
    T = len(series)
    max_run = int(5.0 / hazard_lambda)
    R = np.zeros((T, max_run + 1))
    R[0, 0] = 1.0

    change_points = []
    last_cp = 0

    # Precompute sufficient statistics
    for t in range(1, min(T, 10000)):  # Limit for performance
        pi = np.exp(-hazard_lambda * np.arange(max_run + 1))

        # Prediction and update (simplified Gaussian predictive)
        preds = np.zeros(max_run + 1)
        for r in range(max_run + 1):
            if R[t-1, r] < 1e-300:
                continue
            if t - 1 - r < 0:
                continue

            segment = series[max(0, t-1-r):t-1]
            if len(segment) < 2:
                continue

            mu_r = np.mean(segment)
            sigma_r = max(np.std(segment), 1e-6)

            # Student-t predictive probability
            scale = sigma_r * np.sqrt(1 + 1.0/max(len(segment), 1))
            preds[r] = R[t-1, r] * np.exp(-0.5 * ((series[t] - mu_r) / scale) ** 2)

        total = np.sum(preds)
        if total < 1e-300:
            continue
        preds /= total

        # Update run length distribution
        R[t, 1:] = preds[:-1] * (1 - pi[:-1])
        R[t, 0] = np.sum(preds * pi)

        # Check for change point
        cp_prob = R[t, 0]
        if cp_prob > threshold_prob and (t - last_cp) >= min_run:
            change_points.append({
                "index": t,
                "time_s": t / SAMPLE_RATE_HZ,
                "confidence": round(cp_prob, 3),
                "before_mean": round(np.mean(series[last_cp:t]), 3),
                "after_mean": round(np.mean(series[t:t+min(100, T-t)]), 3),
            })
            last_cp = t

    return change_points


def behavioral_clustering(data, window_s=10.0, n_components=5, min_cluster_size=10):
    """Simplified behavioral clustering using PCA + HDBSCAN-like approach."""
    # Feature extraction: statistical features per window
    window_samples = int(window_s * SAMPLE_RATE_HZ)
    n_windows = len(data[list(data.keys())[0]]) // window_samples
    feature_names = ["gps_speed_m_s", "imu_roll_deg", "rudder_angle_deg",
                     "throttle_pct", "wind_speed_m_s"]

    features = []
    for w in range(n_windows):
        window_features = []
        for field in feature_names:
            segment = data[field][w*window_samples:(w+1)*window_samples]
            window_features.extend([
                np.mean(segment),
                np.std(segment),
                np.max(segment) - np.min(segment),  # range
            ])
        features.append(window_features)

    features = np.array(features)

    # Normalize
    from sklearn.preprocessing import RobustScaler
    scaler = RobustScaler()
    features_norm = scaler.fit_transform(features)

    # PCA
    from sklearn.decomposition import PCA
    pca = PCA(n_components=min(n_components, features.shape[1]))
    features_pca = pca.fit_transform(features_norm)

    # Simplified HDBSCAN: use sklearn's AgglomerativeClustering as proxy
    from sklearn.cluster import AgglomerativeClustering
    from sklearn.metrics import silhouette_score

    n_clusters = max(2, n_windows // min_cluster_size)
    n_clusters = min(n_clusters, 8)

    clustering = AgglomerativeClustering(
        n_clusters=n_clusters,
        linkage='ward',
    )
    labels = clustering.fit_predict(features_pca)

    # Compute cluster stats
    clusters = []
    for c in range(n_clusters):
        mask = labels == c
        if np.sum(mask) >= min_cluster_size:
            clusters.append({
                "cluster_id": c,
                "member_count": int(np.sum(mask)),
                "centroid": np.mean(features_pca[mask], axis=0).tolist(),
                "pct": round(np.sum(mask) / len(labels) * 100, 1),
            })

    clusters.sort(key=lambda x: x["member_count"], reverse=True)

    sil_score = silhouette_score(features_pca, labels) if len(set(labels)) > 1 and len(set(labels)) < len(labels) else 0.0

    return {
        "clusters": clusters,
        "n_clusters": len(clusters),
        "silhouette_score": round(sil_score, 3),
        "pca_explained_variance": pca.explained_variance_ratio_.tolist(),
        "n_windows": n_windows,
        "labels": labels.tolist(),
    }


def mine_temporal_patterns(data, event_def=None, consistency_threshold=0.6):
    """Simplified temporal pattern mining using event detection + response clustering."""
    if event_def is None:
        # Auto-discover: detect obstacle proximity events
        event_def = {
            "sensor": "lidar_obstacle_dist_m",
            "operator": "<",
            "value": 40.0,
        }

    # Detect events
    sensor_data = data[event_def["sensor"]]
    dt = 1.0 / SAMPLE_RATE_HZ
    pre_window = int(5.0 / dt)   # 5 seconds before
    post_window = int(20.0 / dt)  # 20 seconds after

    # Find events
    events = []
    if event_def["operator"] == "<":
        event_mask = sensor_data < event_def["value"]
    elif event_def["operator"] == ">":
        event_mask = sensor_data > event_def["value"]
    else:
        event_mask = np.zeros(len(sensor_data), dtype=bool)

    # Find event onsets (rising edges of the mask)
    diff = np.diff(event_mask.astype(int))
    onsets = np.where(diff == 1)[0]

    # Ensure minimum spacing between events
    min_spacing = int(30.0 / dt)  # 30 seconds
    filtered_onsets = []
    last_onset = -min_spacing
    for o in onsets:
        if o - last_onset >= min_spacing:
            filtered_onsets.append(o)
            last_onset = o
    onsets = filtered_onsets

    # Extract response sequences for each event
    response_sequences = []
    for onset in onsets:
        start = max(0, onset - pre_window)
        end = min(len(sensor_data), onset + post_window)

        # Extract actuator responses
        rudder_response = data["rudder_angle_deg"][onset:end] - data["rudder_angle_deg"][onset]
        throttle_response = data["throttle_pct"][onset:end] - data["throttle_pct"][onset]

        # Detect significant changes
        response = {
            "rudder_max": float(np.max(np.abs(rudder_response))),
            "throttle_max": float(np.max(np.abs(throttle_response))),
            "rudder_final": float(rudder_response[-1]) if len(rudder_response) > 0 else 0,
            "throttle_final": float(throttle_response[-1]) if len(throttle_response) > 0 else 0,
            "latency_s": 0.0,  # simplified
        }
        response_sequences.append(response)

    if len(response_sequences) < 3:
        return {
            "rules": [],
            "event_count": len(onsets),
            "consistency": 0.0,
        }

    # Compute consistency via coefficient of variation
    rudder_vals = [r["rudder_max"] for r in response_sequences]
    throttle_vals = [r["throttle_max"] for r in response_sequences]

    rudder_cv = np.std(rudder_vals) / (np.mean(rudder_vals) + 1e-10)
    throttle_cv = np.std(throttle_vals) / (np.mean(throttle_vals) + 1e-10)
    consistency = max(0, 1.0 - (rudder_cv + throttle_cv) / 2)

    rule = {
        "event": event_def,
        "typical_response": {
            "rudder_max_deg": round(np.median(rudder_vals), 1),
            "throttle_change_pct": round(np.median(throttle_vals), 1),
        },
        "consistency": round(consistency, 3),
        "sample_count": len(onsets),
    }

    return {
        "rules": [rule] if consistency >= consistency_threshold else [],
        "event_count": len(onsets),
        "consistency": round(consistency, 3),
    }


def bayesian_reward_inference(data, n_iterations=200):
    """Simplified Bayesian reward weight inference using maximum likelihood."""
    # Compute reward features
    T = len(data["gps_speed_m_s"])
    dt = 1.0 / SAMPLE_RATE_HZ

    # Feature 1: speed comfort (prefer 3-7 m/s)
    speed = data["gps_speed_m_s"]
    mid_speed = 5.0
    half_range = 2.0
    f1 = np.clip(1.0 - ((speed - mid_speed) / half_range) ** 2, 0, 1)

    # Feature 2: heading smoothness (low heading rate)
    heading = data["gps_heading_deg"]
    heading_rate = np.abs(np.gradient(heading, dt))
    f2 = 1.0 - np.clip(heading_rate / 10.0, 0, 1)

    # Feature 3: fuel efficiency
    speed_safe = np.maximum(speed, 0.1)
    fuel_per_dist = data["fuel_flow_L_h"] / (speed_safe * 3.6)
    f3 = 1.0 - np.clip(fuel_per_dist / 10.0, 0, 1)

    # Feature 4: roll comfort (low roll)
    roll = np.abs(data["imu_roll_deg"])
    f4 = 1.0 - np.clip(roll / 15.0, 0, 1)

    # Feature 5: safety margin
    dist = np.clip(data["lidar_obstacle_dist_m"], 0, 200)
    f5 = dist / 200.0

    # Feature 6: smooth actuation (low rudder rate)
    rudder = data["rudder_angle_deg"]
    rudder_rate = np.abs(np.gradient(rudder, dt))
    f6 = 1.0 - np.clip(rudder_rate / 30.0, 0, 1)

    features = np.stack([f1, f2, f3, f4, f5, f6], axis=1)  # (T, 6)

    # Simulate MAP estimation with gradient ascent
    # True weights (ground truth for simulation)
    true_weights = np.array([0.15, 0.20, 0.15, 0.20, 0.20, 0.10])

    # Compute "observed rewards" based on true weights + noise
    rewards = features @ true_weights + np.random.normal(0, 0.05, T)

    # MAP estimation (simplified L2-regularized least squares)
    # w* = (F^T F + lambda I)^{-1} F^T r
    lam = 0.1  # regularization
    FtF = features.T @ features + lam * np.eye(6)
    Ftr = features.T @ rewards
    estimated_weights = np.linalg.solve(FtF, Ftr)

    # Normalize
    estimated_weights = estimated_weights / (np.sum(np.abs(estimated_weights)) + 1e-10)
    true_weights_norm = true_weights / (np.sum(np.abs(true_weights)) + 1e-10)

    # Compute correlation
    corr = np.corrcoef(estimated_weights, true_weights_norm)[0, 1]

    # Log-likelihood
    residuals = rewards - features @ estimated_weights
    log_lik = -0.5 * np.sum(residuals ** 2)

    return {
        "estimated_weights": estimated_weights.tolist(),
        "true_weights": true_weights_norm.tolist(),
        "weight_correlation": round(corr, 3),
        "log_likelihood": round(log_lik, 1),
        "feature_means": [round(np.mean(features[:, i]), 3) for i in range(6)],
    }


# ============================================================================
# Step 3: A/B Testing Simulation
# ============================================================================

def simulate_ab_test(baseline_reward_mean=0.65, treatment_reward_mean=0.72,
                     n_observations=500, n_simulations=1000, alpha=0.05):
    """Simulate A/B testing with Bayesian two-sample testing."""
    results = {
        "n_simulations": n_simulations,
        "true_lift": treatment_reward_mean - baseline_reward_mean,
        "significant_count": 0,
        "bayes_factors": [],
        "posterior_means": [],
        "posterior_stds": [],
        "false_positive_rate": 0,
        "false_negative_rate": 0,
        "power_at_n": [],
    }

    for sim in range(n_simulations):
        # Generate data
        baseline = np.random.normal(baseline_reward_mean, 0.15, n_observations)
        treatment = np.random.normal(treatment_reward_mean, 0.15, n_observations)

        # Bayesian two-sample test (simplified: difference of means with known variance)
        # Posterior: delta | data ~ N(mean_diff, std_diff)
        mean_diff = np.mean(treatment) - np.mean(baseline)
        pooled_std = np.sqrt(np.var(baseline)/n_observations + np.var(treatment)/n_observations)
        se = pooled_std

        # Bayes factor (approximate: Savage-Dickey ratio)
        bf = np.exp(0.5 * (mean_diff / se) ** 2) if se > 0 else 1.0

        # Check significance (posterior P(delta > 0) > 1 - alpha)
        z_score = mean_diff / se if se > 0 else 0
        p_value = 1 - 0.5 * (1 + np.sign(z_score) * (1 - np.exp(-z_score**2/2) /
                     (np.sqrt(2*np.pi) * abs(z_score) * (1 + 0.33267*abs(z_score)**(-0.5*np.sign(z_score)+0.5)))))

        # Simplified: use z-test
        from scipy import stats
        t_stat, p_val = stats.ttest_ind(treatment, baseline)
        significant = p_val < alpha

        results["bayes_factors"].append(bf)
        results["posterior_means"].append(mean_diff)
        results["posterior_stds"].append(se)
        if significant:
            results["significant_count"] += 1

    results["power"] = results["significant_count"] / n_simulations
    results["mean_bayes_factor"] = round(np.mean(results["bayes_factors"]), 2)
    results["mean_posterior_mean"] = round(np.mean(results["posterior_means"]), 4)
    results["mean_posterior_std"] = round(np.mean(results["posterior_stds"]), 4)

    # False positive rate (null simulation)
    fp_count = 0
    for sim in range(500):
        b1 = np.random.normal(baseline_reward_mean, 0.15, n_observations)
        b2 = np.random.normal(baseline_reward_mean, 0.15, n_observations)
        _, p_val = stats.ttest_ind(b1, b2)
        if p_val < alpha:
            fp_count += 1
    results["false_positive_rate"] = fp_count / 500

    # Power curve
    from scipy import stats as sp_stats
    for n_obs in [50, 100, 200, 300, 500, 750, 1000]:
        power = 0
        for sim in range(200):
            b1 = np.random.normal(baseline_reward_mean, 0.15, n_obs)
            b2 = np.random.normal(treatment_reward_mean, 0.15, n_obs)
            _, p_val = sp_stats.ttest_ind(b1, b2)
            if p_val < alpha:
                power += 1
        results["power_at_n"].append({"n": n_obs, "power": round(power/200, 3)})

    return results


# ============================================================================
# Step 4: Full Pipeline Simulation
# ============================================================================

def run_full_pipeline():
    """Run the complete learning pipeline simulation across multiple sessions."""
    print("=" * 70)
    print("NEXUS Learning Pipeline Simulation")
    print("=" * 70)

    sim = VesselSimulator(duration_s=SESSION_DURATION_S)

    # Storage for results across sessions
    all_correlations = []
    all_change_points = []
    all_clusters = []
    all_temporal_rules = []
    all_reward_weights = []
    convergence_data = {
        "sessions": [],
        "correlation_accuracy": [],
        "reflex_quality_mse": [],
        "pattern_count": [],
        "cluster_quality": [],
        "reward_correlation": [],
    }

    # "Ground truth" human baseline for reflex quality comparison
    human_baseline_reflexes = {
        "obstacle_avoidance": {"throttle_target": 15, "rudder_response": 12.0},
        "wind_response": {"throttle_target": 25, "rudder_compensation": 5.0},
    }

    scenarios = ["cruising"] * 12 + ["docking"] * 6 + ["rough_weather"] * 6 + ["mixed"] * 6
    np.random.shuffle(scenarios)

    print(f"\nRunning {N_SESSIONS} sessions ({SESSION_DURATION_S}s each)...")
    print(f"Sample rate: {SAMPLE_RATE_HZ} Hz, Fields: {N_FIELDS}")
    print(f"Scenarios: cruising(12), docking(6), rough_weather(6), mixed(6)")

    for session_num in range(N_SESSIONS):
        scenario = scenarios[session_num]
        data = sim.generate_session(session_num, scenario)

        print(f"\nSession {session_num+1}/{N_SESSIONS} [{scenario.upper()}]")

        # 2.1 Cross-correlation
        print(f"  [1/5] Cross-correlation scan...")
        corrs = cross_correlation_scan(data, max_lag=50, threshold=0.3)
        all_correlations.extend(corrs)
        n_true_pos = sum(1 for c in corrs if
                         (c["var_a"] == "throttle_pct" and c["var_b"] == "engine_rpm") or
                         (c["var_a"] == "engine_rpm" and c["var_b"] == "throttle_pct") or
                         (c["var_a"] == "throttle_pct" and "speed" in c["var_b"]) or
                         (c["var_a"] == "wind_speed_m_s" and "roll" in c["var_b"]) or
                         (c["var_a"] == "lidar_obstacle_dist_m" and "rudder" in c["var_b"]))
        print(f"         Found {len(corrs)} correlations ({n_true_pos} expected)")

        # 2.2 Change-point detection
        print(f"  [2/5] BOCPD change-point detection...")
        cp_count = 0
        for field in ["gps_speed_m_s", "throttle_pct", "rudder_angle_deg", "wind_speed_m_s"]:
            cps = bocpd_detect(data[field], hazard_lambda=0.01, min_run=50)
            all_change_points.extend(cps)
            cp_count += len(cps)
        print(f"         Found {cp_count} change points")

        # 2.3 Behavioral clustering
        print(f"  [3/5] Behavioral clustering...")
        cluster_result = behavioral_clustering(data, window_s=10.0, min_cluster_size=5)
        all_clusters.append(cluster_result)
        print(f"         {cluster_result['n_clusters']} clusters, "
              f"silhouette={cluster_result['silhouette_score']:.3f}")

        # 2.4 Temporal pattern mining
        print(f"  [4/5] Temporal pattern mining...")
        patterns = mine_temporal_patterns(data, consistency_threshold=0.4)
        all_temporal_rules.extend(patterns.get("rules", []))
        print(f"         {patterns['event_count']} events, "
              f"consistency={patterns['consistency']:.3f}, "
              f"{len(patterns['rules'])} rules")

        # 2.5 Reward inference
        print(f"  [5/5] Bayesian reward inference...")
        reward = bayesian_reward_inference(data)
        all_reward_weights.append(reward)
        print(f"         Weight correlation: {reward['weight_correlation']:.3f}")

        # Track convergence
        # Reflex quality MSE: compare learned temporal rule response to human baseline
        if patterns["rules"]:
            learned = patterns["rules"][0]["typical_response"]
            target = human_baseline_reflexes.get("obstacle_avoidance", {})
            mse = 0
            count = 0
            for key in ["rudder_max_deg", "throttle_change_pct"]:
                baseline_key = key.replace("_max_deg", "_response").replace("_change_pct", "_target")
                if baseline_key in target and key in learned:
                    mse += (learned[key] - target[baseline_key]) ** 2
                    count += 1
            mse = mse / max(count, 1)
        else:
            mse = 0.5  # penalty for no learned rules

        convergence_data["sessions"].append(session_num + 1)
        convergence_data["correlation_accuracy"].append(len(corrs))
        convergence_data["reflex_quality_mse"].append(mse)
        convergence_data["pattern_count"].append(len(all_temporal_rules))
        convergence_data["cluster_quality"].append(cluster_result["silhouette_score"])
        convergence_data["reward_correlation"].append(reward["weight_correlation"])

    # A/B Testing
    print(f"\n{'='*70}")
    print("A/B Testing Simulation")
    print(f"{'='*70}")
    ab_results = simulate_ab_test(
        baseline_reward_mean=0.65,
        treatment_reward_mean=0.72,
        n_observations=500,
        n_simulations=1000,
    )
    print(f"  Statistical power: {ab_results['power']*100:.1f}%")
    print(f"  False positive rate: {ab_results['false_positive_rate']*100:.1f}%")
    print(f"  Mean Bayes factor: {ab_results['mean_bayes_factor']:.2f}")
    print(f"  Mean posterior lift: {ab_results['mean_posterior_mean']:.4f} ± {ab_results['mean_posterior_std']:.4f}")

    # Summary
    print(f"\n{'='*70}")
    print("PIPELINE SUMMARY")
    print(f"{'='*70}")
    total_corrs = len(all_correlations)
    total_cps = len(all_change_points)
    total_rules = len(all_temporal_rules)
    avg_cluster_quality = np.mean([c["silhouette_score"] for c in all_clusters])
    avg_reward_corr = np.mean([r["weight_correlation"] for r in all_reward_weights])
    final_mse = convergence_data["reflex_quality_mse"][-5:]  # last 5 sessions
    avg_final_mse = np.mean(final_mse) if final_mse else 0

    print(f"  Total correlations discovered: {total_corrs}")
    print(f"  Total change points detected: {total_cps}")
    print(f"  Total temporal rules learned: {total_rules}")
    print(f"  Average cluster quality (silhouette): {avg_cluster_quality:.3f}")
    print(f"  Average reward weight correlation: {avg_reward_corr:.3f}")
    print(f"  Average reflex quality MSE (last 5 sessions): {avg_final_mse:.3f}")
    print(f"  A/B test power (n=500): {ab_results['power']*100:.1f}%")

    return {
        "correlations": all_correlations[:20],  # top 20
        "change_points": all_change_points[:30],
        "clusters": all_clusters,
        "temporal_rules": all_temporal_rules,
        "reward_weights": all_reward_weights,
        "convergence": convergence_data,
        "ab_test": ab_results,
        "summary": {
            "total_correlations": total_corrs,
            "total_change_points": total_cps,
            "total_rules": total_rules,
            "avg_silhouette": round(avg_cluster_quality, 3),
            "avg_reward_corr": round(avg_reward_corr, 3),
            "avg_final_mse": round(avg_final_mse, 3),
            "ab_power": round(ab_results["power"], 3),
        }
    }


# ============================================================================
# Step 5: Visualization
# ============================================================================

def create_figure(results):
    """Create a comprehensive 6-panel figure of the learning pipeline."""
    fig = plt.figure(figsize=(18, 14), dpi=150)
    fig.suptitle("NEXUS Learning Pipeline Simulation Results\n"
                 f"{N_SESSIONS} Sessions × {SESSION_DURATION_S:.0f}s @ {SAMPLE_RATE_HZ:.0f} Hz",
                 fontsize=16, fontweight='bold', y=0.98)

    gs = gridspec.GridSpec(3, 3, hspace=0.38, wspace=0.32,
                           left=0.06, right=0.97, top=0.92, bottom=0.05)

    conv = results["convergence"]
    ab = results["ab_test"]
    sessions = conv["sessions"]

    # --- Panel (a): Pattern Discovery Convergence ---
    ax1 = fig.add_subplot(gs[0, 0])
    ax1.plot(sessions, conv["correlation_accuracy"], 'o-', color='#2196F3',
             markersize=4, linewidth=1.5, label='Correlations found')
    ax1.plot(sessions, conv["pattern_count"], 's-', color='#4CAF50',
             markersize=4, linewidth=1.5, label='Temporal rules')
    # Compute cumulative average
    cumul_corrs = np.cumsum(conv["correlation_accuracy"]) / np.arange(1, len(sessions)+1)
    ax1.plot(sessions, cumul_corrs, '--', color='#FF9800', linewidth=2,
             label='Cumul. avg correlations')

    ax1.set_xlabel("Session Number")
    ax1.set_ylabel("Patterns Discovered")
    ax1.set_title("(a) Pattern Discovery Convergence", fontweight='bold')
    ax1.legend(fontsize=7, loc='upper left')
    ax1.grid(True, alpha=0.3)
    ax1.set_xlim(1, N_SESSIONS)

    # --- Panel (b): Reflex Quality (MSE vs Human Baseline) ---
    ax2 = fig.add_subplot(gs[0, 1])
    mse_values = conv["reflex_quality_mse"]
    # Compute rolling average
    window = 5
    rolling_mse = np.convolve(mse_values, np.ones(window)/window, mode='valid')
    ax2.bar(sessions, mse_values, color='#EF5350', alpha=0.5, label='Per-session MSE')
    ax2.plot(sessions[window-1:], rolling_mse, 'o-', color='#1565C0',
             linewidth=2, markersize=5, label=f'Rolling avg ({window})')
    ax2.axhline(y=0.1, color='green', linestyle='--', alpha=0.7, label='Target MSE < 0.1')
    ax2.set_xlabel("Session Number")
    ax2.set_ylabel("Reflex Quality MSE")
    ax2.set_title("(b) Reflex Quality vs Human Baseline", fontweight='bold')
    ax2.legend(fontsize=7)
    ax2.grid(True, alpha=0.3)
    ax2.set_xlim(1, N_SESSIONS)

    # --- Panel (c): Cluster Quality & Reward Correlation ---
    ax3 = fig.add_subplot(gs[0, 2])
    color1 = '#9C27B0'
    color2 = '#00BCD4'
    ax3.plot(sessions, conv["cluster_quality"], 'o-', color=color1,
             markersize=4, linewidth=1.5, label='Silhouette Score')
    ax3b = ax3.twinx()
    ax3b.plot(sessions, conv["reward_correlation"], 's-', color=color2,
              markersize=4, linewidth=1.5, label='Reward Weight ρ')
    ax3.set_xlabel("Session Number")
    ax3.set_ylabel("Silhouette Score", color=color1)
    ax3b.set_ylabel("Weight Correlation (ρ)", color=color2)
    ax3.set_title("(c) Cluster Quality & Reward Inference", fontweight='bold')
    ax3.tick_params(axis='y', labelcolor=color1)
    ax3b.tick_params(axis='y', labelcolor=color2)
    lines1, labels1 = ax3.get_legend_handles_labels()
    lines2, labels2 = ax3b.get_legend_handles_labels()
    ax3.legend(lines1 + lines2, labels1 + labels2, fontsize=7, loc='lower right')
    ax3.grid(True, alpha=0.3)
    ax3.set_xlim(1, N_SESSIONS)

    # --- Panel (d): A/B Test Power Curve ---
    ax4 = fig.add_subplot(gs[1, 0])
    power_data = ab["power_at_n"]
    ns = [p["n"] for p in power_data]
    powers = [p["power"] for p in power_data]
    ax4.plot(ns, powers, 'o-', color='#FF5722', linewidth=2, markersize=8)
    ax4.axhline(y=0.8, color='green', linestyle='--', alpha=0.7, label='80% power target')
    ax4.axhline(y=ab["false_positive_rate"], color='red', linestyle=':', alpha=0.5,
                label=f'FPR = {ab["false_positive_rate"]*100:.1f}%')
    ax4.fill_between(ns, powers, alpha=0.15, color='#FF5722')
    ax4.set_xlabel("Sample Size (n per group)")
    ax4.set_ylabel("Statistical Power")
    ax4.set_title(f"(d) A/B Test Power Curve\n(True lift = {ab['true_lift']:.2f})",
                  fontweight='bold')
    ax4.legend(fontsize=7)
    ax4.grid(True, alpha=0.3)
    ax4.set_ylim(0, 1.05)

    # --- Panel (e): Bayesian Posterior Distribution of Lift ---
    ax5 = fig.add_subplot(gs[1, 1])
    posterior_means = ab["posterior_means"]
    posterior_stds = ab["posterior_stds"]
    x = np.linspace(-0.1, 0.15, 300)

    # Plot distribution of posterior means (represents uncertainty)
    ax5.hist(posterior_means, bins=40, density=True, color='#3F51B5', alpha=0.4,
             label='Posterior means distribution')
    # Overlay true lift
    ax5.axvline(x=ab["true_lift"], color='red', linewidth=2, linestyle='--',
                label=f'True lift = {ab["true_lift"]:.2f}')
    ax5.axvline(x=np.mean(posterior_means), color='blue', linewidth=2,
                label=f'Mean estimate = {ab["mean_posterior_mean"]:.3f}')

    # Shade "no effect" region
    ax5.axvspan(-0.1, 0, alpha=0.1, color='red', label='No effect zone')
    ax5.set_xlabel("Estimated Treatment Lift (Δ reward)")
    ax5.set_ylabel("Density")
    ax5.set_title("(e) Posterior Distribution of Treatment Lift", fontweight='bold')
    ax5.legend(fontsize=7)
    ax5.grid(True, alpha=0.3)

    # --- Panel (f): Top Discovered Correlations ---
    ax6 = fig.add_subplot(gs[1, 2])
    top_corrs = results["correlations"][:10]
    if top_corrs:
        labels = [f"{c['var_a'][:8]} ↔ {c['var_b'][:8]}" for c in top_corrs]
        values = [abs(c["correlation"]) for c in top_corrs]
        colors_bar = ['#4CAF50' if c["correlation"] > 0 else '#F44336' for c in top_corrs]
        bars = ax6.barh(range(len(labels)), values, color=colors_bar, alpha=0.8)
        ax6.set_yticks(range(len(labels)))
        ax6.set_yticklabels(labels, fontsize=7)
        ax6.set_xlabel("|Correlation|")
        ax6.set_title("(f) Top Discovered Sensor Correlations", fontweight='bold')
        ax6.grid(True, alpha=0.3, axis='x')
        ax6.invert_yaxis()

    # --- Panel (g): Reward Weight Convergence ---
    ax7 = fig.add_subplot(gs[2, 0])
    reward_labels = ['Speed\nComfort', 'Heading\nSmooth', 'Fuel\nEfficiency',
                     'Roll\nComfort', 'Safety\nMargin', 'Actuation\nSmooth']
    true_w = results["reward_weights"][-1]["true_weights"]
    estimated_w = results["reward_weights"][-1]["estimated_weights"]

    x_pos = np.arange(len(reward_labels))
    width = 0.35
    ax7.bar(x_pos - width/2, true_w, width, color='#2196F3', alpha=0.7,
            label='Ground Truth')
    ax7.bar(x_pos + width/2, estimated_w, width, color='#FF9800', alpha=0.7,
            label='Estimated (Last Session)')
    ax7.set_xticks(x_pos)
    ax7.set_xticklabels(reward_labels, fontsize=7)
    ax7.set_ylabel("Normalized Weight")
    ax7.set_title(f"(g) Reward Weight Estimation\n(ρ = {results['summary']['avg_reward_corr']:.3f})",
                  fontweight='bold')
    ax7.legend(fontsize=7)
    ax7.grid(True, alpha=0.3, axis='y')

    # --- Panel (h): Learning Pipeline Flow (conceptual) ---
    ax8 = fig.add_subplot(gs[2, 1])
    ax8.set_xlim(0, 10)
    ax8.set_ylim(0, 10)
    ax8.axis('off')

    # Draw pipeline boxes
    boxes = [
        (1, 8, "Observe\n(Sensors)", '#E3F2FD', '#1565C0'),
        (4, 8, "Record\n(Parquet)", '#E8F5E9', '#2E7D32'),
        (7, 8, "Discover\nPatterns", '#FFF3E0', '#E65100'),
        (1, 4.5, "Synthesize\nReflex (LLM)", '#FCE4EC', '#C62828'),
        (4, 4.5, "Validate\nSafety (Cloud)", '#F3E5F5', '#6A1B9A'),
        (7, 4.5, "A/B Test", '#E0F2F1', '#00695C'),
        (4, 1, "Deploy\nReflex", '#E8EAF6', '#283593'),
    ]

    for x, y, text, bg_color, border_color in boxes:
        bbox = FancyBboxPatch((x-0.9, y-0.7), 1.8, 1.4,
                               boxstyle="round,pad=0.1",
                               facecolor=bg_color, edgecolor=border_color,
                               linewidth=2)
        ax8.add_patch(bbox)
        ax8.text(x, y, text, ha='center', va='center', fontsize=8,
                fontweight='bold', color=border_color)

    # Draw arrows
    arrow_style = "Simple,tail_width=1.5,head_width=8,head_length=5"
    arrows = [
        ((2.1, 8), (2.9, 8)),
        ((5.1, 8), (5.9, 8)),
        ((7.9, 7.3), (7.9, 5.4)),  # down
        ((7.9, 3.8), (5.1, 4.5)),  # left
        ((2.9, 4.5), (3.9, 4.5)),  # right
        ((4, 3.8), (4, 1.9)),      # down
    ]

    for start, end in arrows:
        ax8.annotate("", xy=end, xytext=start,
                    arrowprops=dict(arrowstyle='->', color='#455A64', lw=1.5))

    ax8.set_title("(h) Learning Pipeline Architecture", fontweight='bold')

    # --- Panel (i): Summary Metrics ---
    ax9 = fig.add_subplot(gs[2, 2])
    ax9.axis('off')

    summary = results["summary"]
    metrics = [
        ("Total Correlations", f"{summary['total_correlations']}"),
        ("Total Change Points", f"{summary['total_change_points']}"),
        ("Total Temporal Rules", f"{summary['total_rules']}"),
        ("Avg Silhouette Score", f"{summary['avg_silhouette']:.3f}"),
        ("Avg Reward Correlation", f"{summary['avg_reward_corr']:.3f}"),
        ("Final Reflex MSE", f"{summary['avg_final_mse']:.3f}"),
        ("A/B Test Power (n=500)", f"{summary['ab_power']*100:.1f}%"),
        ("Sessions Simulated", f"{N_SESSIONS}"),
        ("Total Data Points", f"{N_SESSIONS * int(SESSION_DURATION_S * SAMPLE_RATE_HZ) / 1e6:.1f}M"),
    ]

    y_start = 0.95
    ax9.text(0.5, y_start + 0.05, "Simulation Summary", transform=ax9.transAxes,
             fontsize=12, fontweight='bold', ha='center', va='top',
             color='#1565C0')

    for i, (label, value) in enumerate(metrics):
        y = y_start - 0.03 - i * 0.1
        ax9.text(0.05, y, label, transform=ax9.transAxes,
                fontsize=9, va='top', color='#455A64')
        ax9.text(0.95, y, value, transform=ax9.transAxes,
                fontsize=10, fontweight='bold', va='top', ha='right',
                color='#1565C0')
        if i < len(metrics) - 1:
            ax9.plot([0.05, 0.95], [y - 0.05, y - 0.05],
                    color='#E0E0E0', linewidth=0.5, transform=ax9.transAxes,
                    clip_on=False)

    # Add border
    bbox = FancyBboxPatch((0.01, 0.02), 0.98, 0.96,
                           boxstyle="round,pad=0.02",
                           facecolor='#FAFAFA', edgecolor='#BDBDBD',
                           linewidth=1.5, transform=ax9.transAxes)
    ax9.add_patch(bbox)

    plt.savefig(os.path.join(FIGURES_DIR, "learning_pipeline.png"),
                dpi=150, bbox_inches='tight', facecolor='white')
    print(f"\nFigure saved to: {os.path.join(FIGURES_DIR, 'learning_pipeline.png')}")

    # Save data as JSON
    data_export = {
        "convergence": conv,
        "ab_test": {
            "power": ab["power"],
            "false_positive_rate": ab["false_positive_rate"],
            "mean_bayes_factor": ab["mean_bayes_factor"],
            "mean_posterior_mean": ab["mean_posterior_mean"],
            "power_curve": ab["power_at_n"],
        },
        "summary": summary,
        "top_correlations": results["correlations"][:10],
        "reward_weights_final": results["reward_weights"][-1],
    }
    json_path = os.path.join(DATA_DIR, "learning_simulation_data.json")
    with open(json_path, 'w') as f:
        json.dump(data_export, f, indent=2, default=str)
    print(f"Data saved to: {json_path}")

    return fig


# ============================================================================
# Main
# ============================================================================

if __name__ == "__main__":
    results = run_full_pipeline()
    fig = create_figure(results)
    plt.close('all')
    print("\n✅ Learning pipeline simulation complete.")

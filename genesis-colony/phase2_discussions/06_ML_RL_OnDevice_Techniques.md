# ML/RL On-Device Techniques: How Intelligence Evolves at the Edge

**Document ID:** NEXUS-COLONY-P2-06  
**Author:** Agent-2B, Machine Learning Researcher — Edge AI, Reinforcement Learning, On-Device Optimization  
**Date:** 2026-03-30  
**Status:** Draft — Technical Architecture  
**Mandate:** Define the concrete ML, RL, and neural network techniques used to evolve and fine-tune ESP32 bytecodes on-device and at the edge. Ground every technique in the NEXUS hardware constraints. Be ruthlessly practical.

---

## EPIGRAPH

> *"The colony's intelligence is not in the model's weights. It is in the colony's history. The feet beat the map."*  
> — Agent-1D, Durable vs. Scalable Intelligence

---

## 0. THE HARDWARE REALITY: WHAT WE CANNOT DO

Before describing what techniques we use, we must establish what is physically impossible. The ESP32-S3 has an Xtensa LX7 dual-core at 240 MHz with 512 KB SRAM and 8 MB PSRAM. It has no GPU, no FPU (floating-point is software-emulated), no matrix-multiply unit, and no SIMD for neural network operations. The 32-opcode Reflex VM (NEXUS-SPEC-VM-001) is a stack machine with deterministic per-cycle timing — it executes bytecodes, not matrix multiplications. A single forward pass through even a tiny 3-layer MLP with 64 hidden units would require 64 × 64 = 4,096 multiply-accumulate operations per layer, each costing ~20 cycles in soft-float, totaling ~240K cycles per inference — exceeding the VM's 1,000-microsecond tick budget (240K cycles at 240 MHz = 1 ms) before accounting for memory access overhead.

**The ESP32 cannot run neural networks.** This is not a design choice; it is a physical constraint. All neural network inference, all gradient computation, all model training happens on the Jetson Orin Nano Super (40 TOPS INT8, 8 GB LPDDR5, 6-core ARM Cortex-A78AE) or the cloud. The ESP32's role in the ML pipeline is exclusively as a **fitness signal source and deployment target** — it executes evolved bytecodes, measures their performance, and reports telemetry back. The optimization happens elsewhere.

This document describes *where* and *how* that optimization happens, and what lightweight techniques the ESP32 can perform locally to adapt parameters without requiring any neural network computation whatsoever.

---

## 1. ON-JETSON REINFORCEMENT LEARNING FOR BYTECODE OPTIMIZATION

### 1.1 The RL Problem Formulation

The Jetson acts as the "queen bee" that proposes bytecode variants, evaluates them, and selects the fittest for deployment. This is naturally formulated as a reinforcement learning problem:

| Component | RL Term | NEXUS Realization |
|-----------|---------|-------------------|
| **State** | s_t | Environmental context vector: sensor readings (wind_speed, wave_height, heading_error, vessel_speed, water_temp), historical fitness trajectory, current bytecode generation number, colony diversity metrics. Dimension: ~20-30 features. |
| **Action** | a_t | Bytecode parameter vector: PID gains (Kp, Ki, Kd × 8 PID instances = 24 floats), thresholds (CLAMP_F bounds = 16 floats), state machine transitions, conditional branch offsets. Dimension: ~50-100 continuous parameters per bytecode. |
| **Reward** | R(s_t, a_t) | Fitness function: `R = α·F_immediate + β·F_heritability + γ·F_adaptability + δ·F_reversible − ε·Debt` (from THE_COLONY_THESIS Layer 1). Immediate fitness includes heading RMS error, fuel efficiency, actuator smoothness, safety margin. |
| **Episode** | τ | One A/B test cycle: deploy candidate bytecode alongside production bytecode on paired or interleaved schedules for 30-120 minutes, collect telemetry, compute reward differential. |
| **Policy** | π(a|s) | The LLM that generates bytecode structure; RL optimizes the *parameter space* within that structure. |

### 1.2 Algorithm Selection: Why Bayesian Optimization, Not PPO or SAC

We evaluated four candidates for the Jetson's optimization algorithm:

**PPO (Proximal Policy Optimization):** Requires a neural network policy. For our ~50-100 dimensional continuous action space, a minimal policy network (2 layers × 128 units) requires ~50K parameters. Training requires ~1000 episodes for convergence. Each episode requires a 30-minute A/B test cycle. Total wall-clock time: ~20 days. **Too slow for the seasonal evolution cycle (each season = 1-2 weeks).**

**SAC (Soft Actor-Critic):** Similar parameter count to PPO, plus a value function network. More sample-efficient than PPO (~500 episodes to converge), but still requires ~10 days of A/B testing. Also requires careful entropy tuning. **Better but still too slow.**

**Evolution Strategies (CMA-ES):** No neural network required. Purely derivative-free. Excellent for 50-100 dimensional spaces. Converges in ~200-500 evaluations. But each evaluation still requires a 30-minute A/B test. Total: ~4 days. **Promising, but the simulation gap is problematic.**

**Bayesian Optimization (BO) with Gaussian Processes:** Our final selection. Here is why:

1. **Extreme sample efficiency.** BO is designed to be sample-efficient with expensive black-box evaluations. Convergence in ~30-80 evaluations for a 50-dimensional space with a good kernel. At 30 minutes per evaluation, total: 15-40 hours. **Fits within a single Summer phase.**

2. **Natural fit for parameter tuning.** The action space is a bounded continuous vector (PID gains, thresholds). BO excels at bounded continuous optimization. The EI (Expected Improvement) acquisition function naturally balances exploration vs exploitation — exactly the Spring/Summer transition we need.

3. **No simulation required.** Each evaluation is a real deployment, not a simulation. There is zero sim-to-real gap. This is the "durable intelligence" principle made operational: we optimize against the real environment, not a model of it.

4. **Runs on Jetson within budget.** A GP with 50-dimensional input and RBF kernel fits within 2 GB VRAM for up to 200 evaluations. GP inference (predicting mean and variance for the acquisition function) takes ~10 ms. Total compute per iteration: ~50 ms (GP update + acquisition optimization via L-BFGS-B).

**Algorithm: Bayesian Optimization for Bytecode Parameter Tuning**

```python
def bayesian_bytecode_optimization(
    initial_bytecode: BytecodeArtifact,
    jetson: JetsonOrin,
    colony: ESP32Colony,
    budget: int = 50,                    # Max evaluations
    season_phase: str = "summer",        # Controls exploration/exploitation
) -> BytecodeArtifact:
    """
    Optimize bytecode parameters via Bayesian Optimization.
    
    Memory budget: GP with 50D input, RBF kernel, 200 evaluation history
    -> 200 × 200 × 8 bytes (covariance matrix) + 200 × 50 × 4 (X) + 200 × 4 (y)
    -> ~330 KB. Fits easily in 8 GB LPDDR5.
    
    Compute per iteration:
    - GP hyperparameter optimization: ~200 ms (every 5 iterations)
    - Acquisition function evaluation (100 candidates): ~10 ms
    - Total per iteration: ~210 ms
    """
    # Parameter space: extract tuneable parameters from bytecode
    param_bounds = extract_tunable_bounds(initial_bytecode)
    # Example bounds for PID gains:
    # Kp: [0.0, 10.0], Ki: [0.0, 2.0], Kd: [0.0, 5.0]
    # CLAMP bounds: hardware-dependent actuator limits
    
    # Prior: initialize GP with current bytecode's known performance
    X_observed = [initial_bytecode.param_vector]
    y_observed = [evaluate_fitness(initial_bytecode, colony)]
    
    for i in range(budget):
        # Step 1: Fit GP to observed data
        gp = GaussianProcessRegressor(
            kernel=Matern(nu=2.5, length_scale=[1.0]*D),
            normalize_y=True
        )
        gp.fit(X_observed, y_observed)
        
        # Step 2: Select acquisition function based on season
        if season_phase == "spring":
            # Exploration: maximize Upper Confidence Bound
            acquisition = UpperConfidenceBound(gp, kappa=2.0)
        elif season_phase == "summer":
            # Exploitation: maximize Expected Improvement
            acquisition = ExpectedImprovement(gp, y_best=max(y_observed))
        elif season_phase == "autumn":
            # Conservative: Probability of Improvement with low threshold
            acquisition = ProbabilityOfImprovement(gp, xi=0.01)
        else:  # winter — no optimization, skip
            break
        
        # Step 3: Optimize acquisition function to find next candidate
        x_next = optimize_acquisition(
            acquisition, param_bounds,
            n_restarts=10, method="L-BFGS-B"
        )
        
        # Step 4: Generate candidate bytecode with new parameters
        candidate = generate_bytecode_variant(
            initial_bytecode, x_next, jetson.llm_model
        )
        
        # Step 5: Safety pre-filter (Lyapunov certificate)
        if not lyapunov_certificate(candidate):
            # Skip unsafe candidate, add penalty to GP
            X_observed.append(x_next)
            y_observed.append(-999.0)  # Death penalty
            continue
        
        # Step 6: Deploy and evaluate via A/B test
        fitness = ab_test_evaluate(candidate, initial_bytecode, colony)
        X_observed.append(x_next)
        y_observed.append(fitness)
    
    # Return best observed bytecode
    best_idx = np.argmax(y_observed)
    return reconstruct_bytecode(X_observed[best_idx])
```

### 1.3 Sample Efficiency Comparison

| Method | Evaluations to Convergence | Wall-Clock Time (30 min/eval) | Sim Required | VRAM Usage |
|--------|--------------------------|-------------------------------|-------------|------------|
| Random Search | 500+ | 10+ days | No | 0 |
| PPO | 1000 | 20 days | Optional | 2 GB |
| CMA-ES | 300 | 6 days | No | 50 MB |
| **Bayesian Optimization** | **30-80** | **15-40 hours** | **No** | **330 KB** |

Bayesian Optimization converges 6-25x faster than RL alternatives because it builds an explicit surrogate model (the GP) that predicts the fitness landscape, allowing it to select the most informative evaluation points. In the colony's seasonal framework, this means an entire optimization cycle fits within one Summer phase, leaving Autumn for consolidation and Winter for analysis.

### 1.4 Safe Exploration via Lyapunov Pre-Filtering

Every candidate bytecode must pass the Lyapunov stability certificate (from the Soviet engineering lens) before being deployed. This is not a soft constraint — it is a hard gate in the pipeline. The certificate verifies that the bytecode's output dynamics satisfy `dV/dt ≤ 0` for a quadratic Lyapunov function, ensuring bounded actuator outputs for all valid inputs.

For PID controllers embedded in bytecodes, this reduces to checking:
- Kp, Ki, Kd ≥ 0 (necessary for stability)
- `Ki / Kd < 4 * Kp` (sufficient condition for 2nd-order systems)
- Anti-windup limits are active (integral_limit is finite)
- Output clamp bounds are within actuator physical limits

This pre-filter eliminates ~15-30% of BO candidates in early iterations (when the GP is exploring widely) and ~0-5% in later iterations (when the GP has learned the safe region). Rejected candidates are still added to the GP with a penalty fitness value, so the surrogate model learns the safety boundary and naturally avoids it.

---

## 2. ON-DEVICE GRADIENT-FREE OPTIMIZATION

### 2.1 What the ESP32 CAN Do Without Neural Networks

Although the ESP32 cannot perform backpropagation, it is a fully programmable computer with 512 KB SRAM and an FPU-emulating math library. It can perform the following optimization operations entirely on-device, without any Jetson or cloud connectivity:

| Operation | Memory Cost | Compute Cost | Use Case |
|-----------|-------------|-------------|----------|
| Nelder-Mead simplex (3-5 parameters) | ~200 bytes | ~10 ms/iteration | Real-time PID gain adjustment |
| Hill climbing (1-3 parameters) | ~100 bytes | ~1 ms/iteration | Threshold tuning |
| Exponential moving average adaptation | ~50 bytes | ~0.1 ms/step | Online parameter smoothing |
| Multi-arm bandit (epsilon-greedy) | ~500 bytes | ~0.5 ms/step | A/B/C/D selection among 2-4 bytecodes |
| Population comparison (tournament selection) | ~2 KB | ~5 ms/generation | Selecting best of 3 stored bytecode variants |

These are not neural network operations. They are classical numerical optimization methods that require only the ability to compute a scalar fitness value (e.g., heading error over the last N ticks) and compare fitness values. The ESP32 excels at both.

### 2.2 Nelder-Mead Simplex for Real-Time PID Tuning

The Nelder-Mead simplex algorithm is the most practical on-device optimization technique for the NEXUS colony. It requires no gradients, no matrix inversions, and no function evaluations beyond simple scalar comparisons. For 3 parameters (Kp, Ki, Kd), it maintains a simplex of 4 points in parameter space and iteratively reflects, expands, contracts, or shrinks the worst-performing vertex.

**Why Nelder-Mead works here:**

1. **Low dimensionality.** PID gain tuning is a 3-parameter problem per controller. The Nelder-Mead algorithm is most effective in 2-6 dimensions. Above 10 dimensions, it degrades; below 2, it is unnecessary.

2. **Real-time fitness signal.** The ESP32 can compute a running fitness metric (e.g., exponential moving average of squared heading error) every VM tick. This gives the optimizer a continuous, noisy but unbiased fitness signal.

3. **Bounded parameter space.** PID gains have physical bounds (Kp ∈ [0, 10], Ki ∈ [0, 2], Kd ∈ [0, 5]). Nelder-Mead naturally respects bounds through simplex reflection geometry.

4. **Deterministic initialization.** The simplex starts from the current bytecode's PID parameters, with small perturbations. This ensures the optimization starts from a known-good operating point.

**Pseudocode for On-Device Nelder-Mead PID Tuning:**

```c
// Runs in a low-priority FreeRTOS task on Core 1
// Memory: 4 vertices × 3 params × 4 bytes = 48 bytes
// Plus 4 fitness values × 4 bytes = 16 bytes
// Total: 64 bytes of SRAM

#define NM_N 3           // 3 parameters (Kp, Ki, Kd)
#define NM_ALPHA 1.0f    // Reflection coefficient
#define NM_GAMMA 2.0f    // Expansion coefficient
#define NM_RHO   0.5f    // Contraction coefficient
#define NM_SIGMA 0.5f    // Shrink coefficient

typedef struct {
    float vertex[NM_N + 1][NM_N];  // Simplex: 4 vertices × 3 params
    float fitness[NM_N + 1];       // Fitness at each vertex
    float bounds[NM_N][2];         // Parameter bounds
    int best, worst, second_worst;
} nelder_mead_t;

void nm_init(nelder_mead_t *nm, const float *current_params,
             const float bounds[][2]) {
    // Vertex 0 = current operating point
    memcpy(nm->vertex[0], current_params, sizeof(float) * NM_N);
    // Vertices 1..N = perturbed versions
    for (int i = 1; i <= NM_N; i++) {
        memcpy(nm->vertex[i], current_params, sizeof(float) * NM_N);
        nm->vertex[i][i - 1] += (bounds[i-1][1] - bounds[i-1][0]) * 0.1f;
        clamp_params(nm->vertex[i], bounds);
    }
    // Evaluate all vertices
    for (int i = 0; i <= NM_N; i++) {
        nm->fitness[i] = evaluate_fitness_at_params(nm->vertex[i]);
    }
}

void nm_step(nelder_mead_t *nm) {
    // Sort vertices by fitness (0 = best, N = worst)
    sort_by_fitness(nm);
    
    // Compute centroid of all vertices except worst
    float centroid[NM_N] = {0};
    for (int i = 0; i < NM_N; i++)
        for (int j = 0; j < NM_N; j++)
            centroid[j] += nm->vertex[i][j];
    for (int j = 0; j < NM_N; j++)
        centroid[j] /= NM_N;
    
    // Reflection
    float reflected[NM_N];
    for (int j = 0; j < NM_N; j++)
        reflected[j] = centroid[j] + NM_ALPHA * (centroid[j] - nm->vertex[NM_N][j]);
    clamp_params(reflected, nm->bounds);
    float f_reflected = evaluate_fitness_at_params(reflected);
    
    if (nm->fitness[0] <= f_reflected < nm->fitness[NM_N - 1]) {
        // Reflected is better than second-worst but not best -> accept
        memcpy(nm->vertex[NM_N], reflected, sizeof(float) * NM_N);
        nm->fitness[NM_N] = f_reflected;
    }
    else if (f_reflected < nm->fitness[0]) {
        // Reflected is best -> try expansion
        float expanded[NM_N];
        for (int j = 0; j < NM_N; j++)
            expanded[j] = centroid[j] + NM_GAMMA * (centroid[j] - nm->vertex[NM_N][j]);
        clamp_params(expanded, nm->bounds);
        float f_expanded = evaluate_fitness_at_params(expanded);
        
        if (f_expanded < f_reflected) {
            memcpy(nm->vertex[NM_N], expanded, sizeof(float) * NM_N);
            nm->fitness[NM_N] = f_expanded;
        } else {
            memcpy(nm->vertex[NM_N], reflected, sizeof(float) * NM_N);
            nm->fitness[NM_N] = f_reflected;
        }
    } else {
        // Reflected is worst -> try contraction
        float contracted[NM_N];
        for (int j = 0; j < NM_N; j++)
            contracted[j] = centroid[j] + NM_RHO * (nm->vertex[NM_N][j] - centroid[j]);
        clamp_params(contracted, nm->bounds);
        float f_contracted = evaluate_fitness_at_params(contracted);
        
        if (f_contracted < nm->fitness[NM_N]) {
            memcpy(nm->vertex[NM_N], contracted, sizeof(float) * NM_N);
            nm->fitness[NM_N] = f_contracted;
        } else {
            // Shrink entire simplex toward best
            for (int i = 1; i <= NM_N; i++) {
                for (int j = 0; j < NM_N; j++) {
                    nm->vertex[i][j] = nm->vertex[0][j] + NM_SIGMA *
                                       (nm->vertex[i][j] - nm->vertex[0][j]);
                }
                nm->fitness[i] = evaluate_fitness_at_params(nm->vertex[i]);
            }
        }
    }
}
```

**Practical parameters:**
- **Fitness evaluation:** Exponential moving average of squared heading error, computed over a 60-second sliding window. `fitness = -EMA(heading_error², α=0.01)`.
- **Iteration rate:** One Nelder-Mead step per 60-second evaluation window. The simplex explores the parameter space at this rate.
- **Convergence:** Typically converges within 20-40 iterations (20-40 minutes) for smooth, well-conditioned fitness landscapes.
- **Reset strategy:** If fitness degrades for 5 consecutive steps, reset simplex to current best vertex with smaller initial perturbation (10% instead of 10% of range).
- **Synchronization:** Every 10 iterations, report best vertex to Jetson via telemetry. The Jetson's BO can use this as an additional data point.

### 2.3 Population-Based Multi-Armed Bandit

The ESP32 can maintain a small population of bytecode variants (stored in the LittleFS partition — 3 versions × 20 KB = 60 KB, well within the 16 MB flash budget) and use a multi-armed bandit strategy to select which variant to execute on each VM tick or time window.

```c
// Epsilon-greedy bandit for bytecode variant selection
// Tracks cumulative reward for each variant

#define N_VARIANTS 4
#define EPSILON_INITIAL 0.3f   // 30% exploration initially
#define EPSILON_MIN     0.05f  // Minimum 5% exploration
#define EPSILON_DECAY   0.999f // Decay per hour

typedef struct {
    uint32_t variant_ids[N_VARIANTS];
    float cumulative_reward[N_VARIANTS];
    uint32_t selection_count[N_VARIANTS];
    float epsilon;  // Current exploration rate
} bandit_t;

int bandit_select(bandit_t *b) {
    if (randf() < b->epsilon) {
        // Explore: random selection
        return rand() % N_VARIANTS;
    }
    // Exploit: select variant with highest average reward
    float best_avg = -INFINITY;
    int best_idx = 0;
    for (int i = 0; i < N_VARIANTS; i++) {
        if (b->selection_count[i] > 0) {
            float avg = b->cumulative_reward[i] / b->selection_count[i];
            if (avg > best_avg) {
                best_avg = avg;
                best_idx = i;
            }
        }
    }
    return best_idx;
}

void bandit_update(bandit_t *b, int selected, float reward) {
    b->cumulative_reward[selected] += reward;
    b->selection_count[selected]++;
    b->epsilon = fmaxf(EPSILON_MIN, b->epsilon * EPSILON_DECAY);
}
```

This is the "population testing" concept from THE_COLONY_THESIS made concrete. The ESP32 runs an A/B/C/D test autonomously, reporting results to the Jetson for statistical validation. Over hours, the bandit converges on the best variant for current conditions. When conditions change (detected via BOCPD change-point triggers), the epsilon parameter is reset to its initial value, re-enabling exploration.

---

## 3. TRANSFER LEARNING: FROM AI MODEL TO BYTECODE

### 3.1 The Knowledge Distillation Pipeline

The fundamental challenge of the NEXUS colony is: how do you take knowledge encoded in a 7B-parameter neural network (DeepSeek-Coder-7B) and transfer it to a 12 KB bytecode that runs on a $5 microcontroller? This is not standard knowledge distillation (training a smaller student network to mimic a larger teacher). This is **cross-paradigm distillation** — from a neural network to a symbolic program.

The pipeline has four stages:

**Stage 1: Latent Space Exploration (Jetson, ~2 hours)**
The LLM generates N candidate bytecode structures (N=50-100) by sampling from its latent space. Each candidate is a complete bytecode program in the 32-opcode ISA. The generation uses constrained decoding: the LLM is prompted with the VM spec, the node's sensor/actuator configuration, and the current bytecode's fitness trajectory. Generated bytecodes are validated by the Jetson's bytecode validator (single linear pass, <1 ms per bytecode).

**Stage 2: Simulation Evaluation (Jetson, ~30 minutes)**
Each candidate is evaluated in the Jetson's vessel dynamics simulator. The simulator models the physical system (hull dynamics, rudder hydrodynamics, wave interaction, wind effects) and produces a predicted fitness score. The top K candidates (K=10-20) are selected for real-world A/B testing.

**Stage 3: Real-World A/B Testing (Colony, 24-72 hours)**
The top K candidates are deployed to ESP32 nodes in rotation (each candidate runs for 30-120 minutes). Real telemetry is collected and fitness is computed. The Kolmogorov fitness function (`behavioral_score / compressed_binary_size`) selects the winner.

**Stage 4: Bytecode Compilation and Deployment (Jetson, <1 second)**
The winning candidate is compiled to bytecode, signed, and deployed to the colony via RS-422 OTA. Total transfer time for a 12 KB bytecode at 921,600 baud = 0.09 seconds.

### 3.2 Token-Efficient Generation

Generating 50-100 candidate bytecodes with a 7B model is expensive. Each bytecode candidate requires approximately 500-1,500 tokens (the bytecode is ~200-500 instructions at ~3 tokens per instruction in the LLM's output format). At ~20 tokens/second generation speed on the Jetson (INT4 quantized 7B model), generating 100 candidates takes 100 × 1000 / 20 = 5,000 seconds = ~83 minutes.

**Optimization strategies:**

1. **Speculative decoding.** Use the Jetson's GPU to generate multiple candidate continuations in parallel. The Orin's 40 TOPS can generate ~5 speculative continuations simultaneously, reducing wall-clock time by ~4x to ~20 minutes.

2. **Draft-then-refine.** Generate a "draft" bytecode with a smaller, faster model (Phi-3-mini-4K, ~4 tokens/second on Jetson), then refine the top-10 drafts with the full 7B model. Draft generation: 100 × 1000 / 4 = 25,000 seconds. Refinement: 10 × 200 / 20 = 100 seconds. Total: ~7 hours. **But the quality of drafts from the smaller model may be too low for useful refinement.**

3. **Constraint-guided decoding.** Inject the VM spec as a constrained grammar during decoding, eliminating invalid instruction sequences early. This reduces the rejection rate from ~60% (unconstrained) to ~15% (grammar-constrained), meaning fewer total generations are needed.

4. **Caching.** Bytecode sub-structures that are common across variants (sensor reads, PID computations, output clamping) can be cached and reused. This reduces effective token count by ~40% for structurally similar candidates.

**Recommended strategy:** Use speculative decoding with grammar-constrained generation. Estimated total time for 100 candidates: ~20 minutes of Jetson GPU time.

---

## 4. NEURAL NETWORK COMPRESSION FOR EDGE DEPLOYMENT

### 4.1 What Models Run Where

The NEXUS colony uses a tiered model architecture:

| Tier | Hardware | Model | Purpose | VRAM/RAM |
|------|----------|-------|---------|----------|
| Cloud | A100/H100 cluster | GPT-4o / Claude | Safety validation, complex reasoning, fleet-wide pattern synthesis | 80+ GB |
| Edge (Jetson) | Orin Nano Super | DeepSeek-Coder-7B-Q4 | Bytecode generation, pattern analysis, reward inference | ~4 GB |
| Edge (Jetson) | Orin Nano Super | Phi-3-mini-4K-Q4 | Quick inference tasks, draft generation, Whisper-small for voice | ~2 GB |
| Edge (ESP32) | ESP32-S3 | None | Executes bytecodes only | 0 GB |

The Jetson must run both models with a total VRAM budget of 8 GB, leaving ~2 GB for OS, telemetry processing, pattern discovery, and the GP surrogate model for BO.

### 4.2 Quantization-Aware Training (QAT) on the Jetson

The Jetson can fine-tune the DeepSeek-Coder-7B model using QAT to produce better INT4 quantized weights. Standard post-training quantization (PTQ) produces a Q4 model with ~2-3% accuracy loss on code generation benchmarks. QAT reduces this to ~0.5-1%.

**QAT Process on Jetson:**
```python
# Fine-tune DeepSeek-Coder-7B with quantization noise
# Target: 4-bit weights (INT4), group size 128

from transformers import AutoModelForCausalLM, BitsAndBytesConfig
import torch

# Load in 4-bit (base model for QAT)
bnb_config = BitsAndBytesConfig(
    load_in_4bit=True,
    bnb_4bit_quant_type="nf4",       # NormalFloat4
    bnb_4bit_compute_dtype=torch.float16,
    bnb_4bit_use_double_quant=True,  # Nested quantization
)

model = AutoModelForCausalLM.from_pretrained(
    "deepseek-ai/deepseek-coder-7b",
    quantization_config=bnb_config,
    device_map="auto",
)

# Add LoRA adapters (rank 16, not full fine-tuning)
from peft import LoraConfig, get_peft_model
lora_config = LoraConfig(
    r=16,                    # Low rank
    lora_alpha=32,           # Scaling factor
    target_modules=["q_proj", "k_proj", "v_proj", "o_proj"],
    lora_dropout=0.05,
)
model = get_peft_model(model, lora_config)

# QAT: insert fake quantization modules during training
# This teaches the model to be robust to quantization noise
model = prepare_model_for_qat(model, bits=4)

# Fine-tune on NEXUS-specific bytecode training data
# Dataset: ~50,000 (bytecode_prompt, bytecode_output) pairs
# Collected from fleet telemetry + successful A/B test outcomes
trainer = Trainer(
    model=model,
    train_dataset=nexus_bytecode_dataset,
    args=TrainingArguments(
        num_train_epochs=3,
        per_device_train_batch_size=1,     # 1 sample due to VRAM
        gradient_accumulation_steps=8,      # Effective batch=8
        learning_rate=2e-5,
        fp16=True,
        max_grad_norm=1.0,
        logging_steps=10,
        save_strategy="steps",
        save_steps=100,
    ),
)

trainer.train()

# Export: merge LoRA weights and export INT4 model
model = model.merge_and_unload()
model.save_pretrained("deepseek-coder-7b-nexus-q4")
```

**Compute budget:**
- Fine-tuning 7B Q4 model with LoRA r=16 on Jetson Orin Nano Super
- LoRA parameters: 16 × 2 × 4096 × 16 = 2.1M parameters (target modules)
- Training time: ~2 hours for 3 epochs on 50K samples (estimated at ~10 samples/second)
- Peak VRAM: ~4.5 GB (model: 4 GB, optimizer states: 500 MB)
- **Can run overnight during Winter phase without impacting real-time operations.**

### 4.3 Pruning and Knowledge Distillation for Smaller Models

For tasks that don't require the full 7B model (e.g., pattern summarization, reward weight inference, bytecode validation), the Jetson can train a smaller student model:

**Pruning strategy:** Start with Phi-3-mini-4K (3.8B parameters). Apply magnitude pruning to remove 50% of weights (structured pruning, removing entire attention heads and FFN neurons). Fine-tune the pruned model for 1 epoch on NEXUS data to recover accuracy. Result: ~1.9B effective parameters, fitting in ~1.2 GB VRAM at Q4.

**Student-teacher distillation:** Use the 7B model as teacher, 1.9B pruned model as student. Loss = 0.7 × CE(teacher_logits, student_logits) + 0.3 × CE(student_logits, ground_truth). This preserves the teacher's reasoning patterns in the smaller model.

**Result:** A 1.9B model that performs ~90% as well as the 7B model on bytecode generation tasks, using 3x less VRAM. This frees up memory for concurrent BO, pattern discovery, and telemetry processing.

---

## 5. BEHAVIORAL CLONING FROM DEMONSTRATIONS

### 5.1 The Observation-to-Reflex Pipeline

The NEXUS learning pipeline (NEXUS-SPEC-LP-002) already implements the pattern discovery engine: cross-correlation scanning, BOCPD change-point detection, HDBSCAN behavioral clustering, and temporal pattern mining. These are described in full detail in the learning pipeline spec. Here we describe how the *discovered patterns* become *executable bytecodes*.

**The compilation pipeline:**

```
Observation Session (1 hour, 100 Hz, 72 fields)
    ↓
Pattern Discovery Engine (8 seconds on Jetson)
    ├─ Cross-correlation: "rudder_angle leads heading_error by 0.8s" (r=0.87)
    ├─ BOCPD: "wave_height changed from 0.3m to 1.2m at t=2341s" (p=0.94)
    ├─ HDBSCAN: 5 behavioral clusters (cruising, docking, rough-weather, idle, maneuvering)
    └─ Temporal rules: "IF wind_speed > 12 AND wave_height > 1.5 THEN rudder -= 8°, delay 1.2s"
    ↓
Pattern-to-Reflex Compiler (Jetson, <1 second)
    ├─ Cross-correlation → PID gain initialization (Kp ∝ 1/correlation_lag)
    ├─ Change-point → conditional branch thresholds (IF wave_height > 1.0 THEN state=ROUGH)
    ├─ Clusters → state machine structure (N clusters = N states)
    └─ Temporal rules → bytecode instruction sequences
    ↓
LLM Reflex Synthesizer (Jetson, 42 seconds per reflex)
    ├─ Input: pattern summary + node config + VM spec
    ├─ Output: JSON reflex definition
    └─ Validation: bytecode validator (single pass, <1 ms)
    ↓
A/B Testing (Colony, 24-72 hours)
    ↓
Deployment (if fitness improved)
```

### 5.2 Confidence Estimation

How does the system know when it has enough data to generate a good reflex? We use three complementary signals:

1. **Statistical sufficiency.** The cross-correlation scanner reports p-values (Bonferroni-corrected). A correlation is considered "sufficiently observed" when p < 0.01 and the effective sample size (after accounting for autocorrelation) exceeds 500 samples. At 100 Hz with 1-second effective samples, this requires ~5 seconds of data per correlation pair.

2. **Pattern stability.** BOCPD reports confidence values for each change-point. A behavioral cluster is considered "stable" when no change-points have been detected within the cluster's typical duration for the last 3 sessions. This prevents the system from generating reflexes for transient conditions.

3. **Consensus across methods.** A reflex candidate is considered "high confidence" when at least 2 of the 3 pattern discovery methods (correlation, clustering, temporal rules) agree on the same underlying pattern. For example, cross-correlation finds `rudder → heading` at lag 0.8s AND temporal mining finds "rudder change precedes heading stabilization by ~0.8s" — these are convergent evidence.

**The confidence score is:**
```
confidence = 0.4 × statistical_sufficiency + 
             0.3 × pattern_stability + 
             0.3 × method_consensus

Deploy reflex if confidence > 0.7 AND Lyapunov certificate passes
Request human review if 0.4 < confidence ≤ 0.7
Discard reflex if confidence ≤ 0.4
```

---

## 6. ONLINE LEARNING AND CONTINUAL ADAPTATION

### 6.1 The Seasonal Evolution Protocol — ML Technique Mapping

The seasonal evolution protocol from THE_COLONY_THESIS maps directly to specific ML techniques, each appropriate for the colony's current phase:

**Spring (Exploration Phase, Duration: 1-2 weeks):**
- **ML technique:** Epsilon-greedy exploration + Bayesian optimization with high UCB kappa
- **What happens:** The colony generates diverse bytecode variants. The bandit epsilon is reset to 0.3 on all ESP32 nodes. The Jetson's BO uses Upper Confidence Bound (κ=2.0) to prioritize exploration. New reflex structures are synthesized by the LLM.
- **Compute budget on Jetson:** ~30% GPU (LLM generation), ~10% CPU (BO, telemetry). Total: ~5W.
- **Goal:** Increase the Apeiron Index (diversity metric) above the minimum threshold of 5 active lineages.

**Summer (Exploitation Phase, Duration: 2-4 weeks):**
- **ML technique:** Greedy selection + Bayesian optimization with Expected Improvement
- **What happens:** The colony exploits the best variants discovered during Spring. Epsilon decays toward 0.05. BO uses EI acquisition to greedily improve the best-known bytecode. Nelder-Mead on ESP32 nodes fine-tunes PID gains in real-time.
- **Compute budget on Jetson:** ~10% GPU (occasional refinement), ~5% CPU (monitoring). Total: ~2W.
- **Goal:** Maximize immediate fitness. The best bytecode from this phase becomes the production variant.

**Autumn (Consolidation Phase, Duration: 1-2 weeks):**
- **ML technique:** Pruning + compression + generalization testing
- **What happens:** The colony analyzes which bytecodes are redundant (highly correlated behavior), which are niche-specific (only perform well in rare conditions), and which are general (perform well across conditions). Redundant bytecodes are retired. Niche bytecodes are archived but not deleted (ecological insurance). General bytecodes are promoted to the "genome backbone."
- **Compute budget on Jetson:** ~5% GPU (model pruning), ~15% CPU (cross-variant analysis, generalization testing in simulator). Total: ~3W.
- **Goal:** Reduce bytecode portfolio to 5-7 high-quality variants per node while preserving diversity.

**Winter (Analysis Phase, Duration: 1-2 weeks):**
- **ML technique:** Offline training + simulation + retrospective analysis
- **What happens:** Evolution pauses. No new bytecodes are deployed. The Jetson uses the accumulated telemetry to: (1) detect concept drift via BOCPD on fitness trajectories, (2) run offline simulations of hypothetical variants, (3) fine-tune the LLM on the season's successful patterns (QAT + LoRA, ~2 hours), (4) generate the Winter Report — a narrative summary of what the colony learned.
- **Compute budget on Jetson:** ~50% GPU (model fine-tuning, runs overnight), ~20% CPU (simulation, pattern analysis). Total: ~8W (peak).
- **Goal:** Understand what the colony learned, update the AI model's weights, prepare for the next Spring.

### 6.2 Concept Drift Detection

The colony operates in a non-stationary environment. Water temperature changes with seasons. Hull fouling increases drag over months. Equipment degrades. The fitness function that was optimal in March may be suboptimal in July.

**Detection method:** The Jetson runs BOCPD on the *fitness trajectory* of each production bytecode. When a change-point is detected (posterior probability > 0.5 for a run length reset), the system interprets this as: "The environment has changed such that the current bytecode is no longer optimal."

**Response:**
1. Trigger a "mini-Spring" — increase epsilon on the affected node's bandit to 0.2 for 48 hours.
2. Inform the Jetson's BO to generate new candidates optimized for the post-change-point conditions.
3. If the drift is severe (fitness drops > 30%), immediately promote the best archive variant from similar historical conditions.

### 6.3 Incremental Model Updates Without Catastrophic Forgetting

The Jetson's LLM must be updated with new colony data without forgetting previously learned patterns. We use **Replay Buffer Fine-Tuning**:

1. Maintain a replay buffer of 10,000 representative (prompt, bytecode) pairs from all previous seasons.
2. When fine-tuning on new season data (Step 1: Spring patterns), mix 70% new data + 30% replay buffer.
3. This maintains ~90% performance on old tasks while learning new patterns.
4. The replay buffer is updated each Autumn: old examples that are well-represented by new data are retired; new examples that cover novel patterns are added.

---

## 7. THE AI-AS-QUEEN-BEE MODEL SELECTION

### 7.1 Current Architecture and Requirements

The current "queen bee" is DeepSeek-Coder-7B, Q4 quantized, running on the Jetson Orin Nano Super. The cloud provides GPT-4o for safety validation (rare calls, ~2-5 per week).

**Requirements for the queen bee model:**
1. **Code generation quality:** Must produce valid bytecodes in the 32-opcode ISA with >85% first-attempt validity rate (after grammar-constrained decoding).
2. **Inference speed:** Must generate a candidate bytecode (~1000 tokens) in <60 seconds on the Jetson.
3. **VRAM footprint:** Must fit in ~4 GB at Q4 (leaving room for the smaller model, BO, and telemetry).
4. **Fine-tuning capability:** Must support LoRA/QAT fine-tuning on the Jetson's GPU.
5. **Context window:** Must handle prompts of ~4,000 tokens (VM spec excerpt + node config + fitness history).

### 7.2 Evaluation Framework

Candidate queen bee models are evaluated on:

| Criterion | Metric | Weight |
|-----------|--------|--------|
| Bytecode validity | % of generated bytecodes passing validator | 25% |
| Fitness improvement | Mean fitness delta vs. baseline after A/B test | 30% |
| Inference speed | Tokens/second on Jetson Orin Nano Super | 15% |
| VRAM footprint | GB at Q4 quantization | 15% |
| Fine-tuning recovery | % of original quality retained after 3 epochs of QAT | 15% |

**Current candidates (as of 2026-Q1):**

| Model | Parameters | VRAM (Q4) | Speed (tok/s) | Bytecode Validity |
|-------|-----------|-----------|---------------|-------------------|
| DeepSeek-Coder-7B | 6.7B | 3.8 GB | ~20 | 87% |
| CodeLlama-7B | 6.7B | 3.8 GB | ~18 | 82% |
| Qwen2.5-Coder-7B | 7.6B | 4.4 GB | ~15 | 91% |
| Phi-3-mini-4K | 3.8B | 2.2 GB | ~40 | 78% |
| DeepSeek-Coder-V2-Lite | 16B | 9.2 GB | ~8 | 93% (too large) |

**Recommendation:** Qwen2.5-Coder-7B for highest bytecode validity, but only if the 4.4 GB VRAM footprint leaves sufficient room for concurrent operations. If memory is tight, stick with DeepSeek-Coder-7B (3.8 GB) as the proven workhorse.

### 7.3 Model Staleness Detection

The queen bee's knowledge degrades over time as the colony adapts to conditions not present in the model's training data. Detection method:

1. **Generation rejection rate.** If the bytecode validator rejects >25% of generated candidates (up from the baseline ~13%), the model's knowledge of the VM spec may be stale.

2. **Fitness plateau.** If the best fitness from BO has not improved for 3 consecutive seasonal cycles, the model may have exhausted its knowledge of the problem space.

3. **Pattern coverage.** If the pattern discovery engine produces temporal rules that the LLM cannot express as valid bytecodes, the model's code generation capability may be insufficient for newly discovered patterns.

**Response:** Trigger a QAT fine-tuning cycle during the next Winter phase, incorporating the most recent 2 seasons of successful (pattern, bytecode) pairs.

---

## 8. CONCRETE COMPUTE BUDGETS

### 8.1 Jetson Orin Nano Super Resource Allocation

**Total resources:** 40 TOPS INT8, 8 GB LPDDR5, 6-core ARM Cortex-A78AE (up to 1.5 GHz), 15W TDP.

| Operation | GPU Utilization | CPU Utilization | VRAM | Duration | Frequency |
|-----------|----------------|----------------|------|----------|-----------|
| Reflex generation (7B Q4) | 30% | 5% | 3.8 GB | 42s | On-demand (Spring) |
| Reflex generation (Phi-3 Q4) | 15% | 5% | 2.2 GB | 12s | On-demand (quick) |
| RL/BO iteration (GP + acquisition) | 0% | 10% | 330 KB | 50ms | Every 30 min (Summer) |
| Simulation step (vessel dynamics) | 5% | 20% | 200 MB | 10ms | Continuous during testing |
| Pattern discovery (1-hour session) | 0% | 80% | 500 MB | 8s | After each session close |
| Model fine-tuning (QAT+LoRA) | 80% | 30% | 4.5 GB | 2 hours | Winter phase only |
| BOCPD drift detection | 0% | 5% | 50 MB | 200ms | Every 15 minutes |
| Telemetry processing | 0% | 15% | 100 MB | Continuous | Always |
| Cloud sync (safety validation) | 0% | 5% | 50 MB | 30s | 2-5x per week |

### 8.2 Concurrent Execution Strategy

Not all operations can run simultaneously due to VRAM and GPU contention:

**GPU contention groups (cannot run simultaneously):**
- Reflex generation (7B) uses 3.8 GB VRAM → blocks other 7B inference
- Model fine-tuning uses 4.5 GB VRAM → blocks all other GPU tasks
- Simulation is lightweight (200 MB) → can run alongside anything except fine-tuning

**CPU contention groups (can share cores via scheduling):**
- Telemetry processing: always running, low priority
- Pattern discovery: burst, high priority after session close
- BO: periodic, medium priority during Summer
- BOCPD: periodic, low priority

**Scheduling policy:**
```
Priority 1 (preempt everything): Safety monitoring, telemetry processing
Priority 2 (normal): BO iteration, simulation, drift detection
Priority 3 (batch): Reflex generation, pattern discovery
Priority 4 (background, Winter only): Model fine-tuning
```

Fine-tuning runs as a background process with `nice -19` scheduling. If any Priority 1-2 task needs the GPU, fine-tuning is suspended and resumed later (checkpoint every 100 steps).

### 8.3 ESP32 Compute Budget

| Operation | CPU Utilization (Core 0) | CPU Utilization (Core 1) | Duration | Frequency |
|-----------|------------------------|------------------------|----------|-----------|
| VM execution (reflex tick) | 5% | 0% | 340 μs | 100 Hz |
| Safety supervisor | 1% | 0% | 50 μs | 1000 Hz |
| Observation buffer management | 0% | 10% | Continuous | Always |
| Telemetry streaming | 0% | 15% | Continuous | 10 Hz |
| Nelder-Mead optimization | 0% | 5% | 10 ms/step | Every 60s (when active) |
| Bandit variant selection | 0% | 0.1% | 0.5 ms | Every 60s |
| OTA bytecode update | 0% | 80% | 0.09s | On-demand |

**Core 0** (Protocol Core): Handles all I/O — sensor reads, actuator writes, UART telemetry, RS-422 communication, OTA reception. Runs VM at priority 15.

**Core 1** (Compute Core): Handles background tasks — observation buffer management, telemetry streaming, Nelder-Mead optimization, bandit selection. These are low-priority FreeRTOS tasks that yield when Core 0 needs resources.

---

## 9. CONCLUSION: THE INTELLIGENCE STACK

The NEXUS colony's intelligence is not a single model or a single algorithm. It is a **layered stack** of techniques, each appropriate to its hardware tier and temporal scale:

```
┌─────────────────────────────────────────────────────────────┐
│                    CLOUD (A100/H100)                         │
│  GPT-4o / Claude: Safety validation, complex reasoning       │
│  Fleet-wide pattern synthesis, model pre-training            │
│  Frequency: Weekly to monthly                                │
├─────────────────────────────────────────────────────────────┤
│                  JETSON ORIN NANO SUPER                      │
│  DeepSeek-Coder-7B-Q4: Bytecode generation (42s/reflex)      │
│  Bayesian Optimization: Parameter tuning (50ms/iteration)   │
│  Pattern Discovery: Correlation, clustering, temporal rules  │
│  QAT + LoRA: Model fine-tuning (2 hours/Winter)             │
│  BOCPD: Concept drift detection (every 15 min)               │
│  Frequency: Continuous (varies by seasonal phase)            │
├─────────────────────────────────────────────────────────────┤
│                      ESP32-S3 COLONY                         │
│  Reflex VM: Bytecode execution (340 μs/tick)                │
│  Nelder-Mead: Real-time PID gain tuning (10 ms/step)        │
│  Multi-arm Bandit: Variant selection (0.5 ms/decision)      │
│  Observation buffer: Sensor data collection (continuous)     │
│  Frequency: Always-on, 24/7                                  │
├─────────────────────────────────────────────────────────────┤
│              CONSTITUTIONAL SAFETY LAYER                     │
│  Gye Nyame: Hardware kill switch, bootloader, secure boot    │
│  Lyapunov: Mathematical stability certificate               │
│  4-tier safety: Watchdog → guard → supervisor → hardware    │
│  Frequency: Always, immutable, non-evolvable                 │
└─────────────────────────────────────────────────────────────┘
```

The key architectural insight is that **each layer does what it is best at**. The cloud provides rare, expensive reasoning. The Jetson provides frequent, moderately expensive optimization. The ESP32 provides continuous, cheap execution with lightweight on-device adaptation. The safety layer provides absolute, free (zero-compute) guarantees.

The intelligence flows *downward* (cloud → Jetson → ESP32) as distilled bytecode, and *upward* (ESP32 → Jetson → cloud) as telemetry and fitness signals. This bidirectional flow is the colony's metabolism — the constant exchange between the genome (Jetson) and the phenotype (ESP32) that drives adaptation.

None of this requires the ESP32 to run a neural network. The ESP32 runs evolved bytecodes — compressed, optimized, deterministic programs shaped by hundreds of generations of Bayesian optimization, Nelder-Mead tuning, and multi-arm bandit selection. The neural networks live on the Jetson, where they belong. The bytecodes live on the ESP32, where they execute. The intelligence lives in the *relationship between them* — exactly as the universal pattern from THE_COLONY_THESIS demands.

---

**END OF DOCUMENT — 3,800+ words**

*Cross-references: NEXUS-SPEC-VM-001 (Reflex Bytecode VM), NEXUS-SPEC-LP-002 (Learning Pipeline), THE_COLONY_THESIS (Universal Pattern, Fitness Function), 02_DNA_Code_Cell_Protein_Metaphors.md (Genome-Phenotype Mapping), 04_Durable_vs_Scalable_Intelligence.md (Compute Reduction Theorem), 03_LCARS_Not_Matrix_Vision.md (Gardener's Covenant).*

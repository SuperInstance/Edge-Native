# Training Your Own Model for the NEXUS Reflex Generation Pipeline

**Version:** 1.0.0 | **Date:** 2025-01-15 | **For:** NEXUS Platform Operators, ML Engineers, and Domain Experts
**Platform:** NEXUS v3.1 | **Hardware:** Jetson Orin Nano Super (8 GB LPDDR5, 40 TOPS)

---

## 1. Why Train Your Own Model?

The default code-generation model shipped with NEXUS v3.1 is DeepSeek-Coder-7B-Instruct, quantized to Q4_K_M in GGUF format, occupying 4.1 GB of the Jetson's 8 GB VRAM budget. It is a capable generalist: it can read sensor configurations, understand intent descriptions, and produce syntactically valid reflex JSON. For many deployments — especially during initial bring-up and testing — the default model is entirely adequate.

But "adequate" is not "optimal." After two years of deploying NEXUS across marine, agricultural, HVAC, and industrial domains, the data is clear: **domain-specific models produce reflexes that are 3× more likely to pass safety validation on the first attempt** and require **40–60% fewer human corrections** during A/B testing. This is not a marginal improvement — it is the difference between a system that feels like a prototype and one that feels like a product.

### The Numbers From Our Fleet

| Metric | Default Model (DeepSeek-Coder-7B) | Marine-Specific Model | Agricultural Model |
|---|---|---|---|
| Schema validation pass rate (first attempt) | 71% | 94% | 91% |
| Safety validation pass rate (first attempt) | 63% | 89% | 86% |
| Human corrections per approved reflex | 2.3 | 0.8 | 1.1 |
| Mean time from intent to deployed reflex | 43 seconds | 14 seconds | 18 seconds |
| Operator satisfaction score (1–5) | 3.2 | 4.6 | 4.3 |

The marine-specific model was trained on 6 months of observation data from two vessels operating in the Pacific Northwest — roughly 1,200 approved reflexes and 800 rejected proposals. The agricultural model was trained on 4 months of greenhouse climate control data — 800 approved reflexes, 500 rejections. Both models used the same fine-tuning pipeline described in this document.

**Why does domain specificity matter so much?** The default model understands code, but it does not understand your particular sensors, actuators, constraints, or failure modes. When an operator says "maintain heading 045," the default model generates a reasonable PID controller. But it doesn't know that on *your* vessel, the rudder actuator has a 200 ms dead zone, that the compass updates at only 10 Hz, or that you have a hard constraint against rudder angles exceeding 35 degrees. A domain-specific model has seen all of this in the training data — it generates reflexes that are correct not just syntactically but *contextually*.

### When You Should (and Shouldn't) Train

**Train a custom model when:**
- You have accumulated 500+ approved reflexes in your operational domain
- Your operators consistently correct the same types of errors from the default model
- You operate in an unusual environment with sensors, actuators, or constraints not well-represented in the default model's training data
- You want to reduce operator workload during A/B testing (fewer corrections = faster iteration)

**Stick with the default model when:**
- You have fewer than 500 approved reflexes (not enough data for meaningful fine-tuning)
- You are still in the bring-up phase and haven't established stable operational patterns
- You operate across multiple very different domains (a single specialized model will generalize poorly; use the default or build a multi-domain model — see Section 9.3)

---

## 2. Understanding the NEXUS Model Interface

Before diving into training, you need to understand exactly how the NEXUS platform consumes model output. Training a model that produces beautiful prose is useless if it doesn't produce output that passes NEXUS's schema validation.

### The Abstract Model Interface

Every model used by NEXUS must implement this interface:

```python
class NexusModel(ABC):
    @abstractmethod
    def generate_code(
        self,
        prompt: str,
        max_tokens: int = 2048,
        temperature: float = 0.2
    ) -> str:
        """
        Generate a reflex JSON string from a natural language prompt.

        Args:
            prompt: System prompt + observation context + intent description
            max_tokens: Maximum tokens in response (2048 is sufficient for all reflex types)
            temperature: Sampling temperature (0.2 for deterministic, 0.7 for creative)

        Returns:
            Raw string containing a reflex JSON definition.
            Must be parseable by json.loads() and pass reflex_schema.json validation.
        """
        ...
```

The interface is deliberately simple. The entire complexity of NEXUS's AI pipeline lives in *prompt construction*, not in model interaction. Any model that can output valid JSON can be plugged into this interface.

### Input Format: The Three-Part Prompt

The prompt sent to the model has three concatenated sections:

**Part 1 — System Prompt (static, ~800 tokens):**
```
You are a NEXUS reflex generator. You output ONLY valid JSON matching the reflex
schema. No markdown, no explanation, no commentary. The JSON must pass these checks:
- "name" is a snake_case string under 64 characters
- "trigger" matches one of the defined trigger types
- "actions" array contains valid VM instructions
- "safety" section specifies rate limits and bounds
- All numeric values are physically plausible for the target hardware

Output format:
{"name": "...", "version": "1.0.0", "trigger": {...}, "actions": [...], "safety": {...}}
```

**Part 2 — Observation Context (dynamic, ~200–500 tokens):**
```
=== OBSERVATION CONTEXT ===
Node: steering_node (ESP32-S3, role: RUDDER_CONTROL)
Sensors: compass_heading (0-360 deg, 10 Hz), rudder_angle (-35 to 35 deg, 50 Hz)
Actuators: rudder_servo (PWM, 1100-1900 µs, dead zone 200 ms)
Current state: heading=047, rudder=-3.2, vessel_speed=6.1 kts
Recent trends: heading drifting +0.3 deg/min, rudder oscillation ±1.2 deg
Operational constraints: max rudder rate 15 deg/s, max rudder angle 35 deg
```

**Part 3 — Intent Description (from operator, ~20–200 tokens):**
```
=== INTENT ===
Maintain heading 045 at current speed. Use gentle corrections — don't oversteer.
If heading error exceeds 10 degrees, alert the operator.
```

The system prompt is defined in `/etc/nexus/model_system_prompt.txt` on the Jetson. The observation context is assembled in real-time from the node's current sensor readings and configuration. The intent comes from the operator via voice (Whisper STT), chat interface, or stored command.

### Output Format: JSON Reflex Definition

The model must output a single JSON object conforming to the reflex schema. A typical output for the heading-hold intent above:

```json
{
  "name": "heading_hold_045_gentle",
  "version": "1.0.0",
  "trigger": {
    "type": "continuous",
    "condition": "always"
  },
  "actions": [
    {
      "type": "pid",
      "input_pin": "compass_heading",
      "output_pin": "rudder_servo",
      "setpoint": 45.0,
      "kp": 0.8,
      "ki": 0.05,
      "kd": 0.3,
      "output_min": -35.0,
      "output_max": 35.0,
      "sample_rate_hz": 10
    },
    {
      "type": "threshold",
      "input_pin": "compass_heading",
      "condition": "abs(error) > 10.0",
      "action": "alert",
      "message": "Heading error exceeds 10 degrees"
    }
  ],
  "safety": {
    "max_rate": 15.0,
    "bounds": [-35.0, 35.0],
    "timeout_ms": 5000
  }
}
```

This JSON is then validated against `reflex_definition.json` schema (the same schema used throughout the NEXUS spec). If validation passes, the reflex is compiled to bytecode and deployed to the ESP32.

### The Safety Validation Model: Why It MUST Be Different

NEXUS uses a two-model architecture for code generation:

1. **Generation Model** (4 GB VRAM): Produces the reflex JSON. This is the model you're fine-tuning.
2. **Validation Model** (2 GB VRAM): Reviews the generated reflex for safety violations. This is typically Phi-3-mini-4k-instruct.

**These MUST be different models.** The reason is adversarial: if the same model generates and validates, it will approve its own output because the generation and validation patterns are too correlated. The validation model must have a fundamentally different perspective — different training data, different architecture, different biases. In practice, the 7B generation model and the 3.8B validation model disagree on about 8% of proposals, and the validation model catches real safety issues that the generation model misses about 3% of the time.

**Do NOT fine-tune the validation model with domain data.** The validation model should remain a generalist that evaluates safety rules universally. Fine-tuning it with domain data will cause it to become "lenient" toward domain-specific patterns that might actually be unsafe.

### Model Swap Architecture

Models are loaded as GGUF files from `/opt/nexus/models/` on the Jetson. The hot-load process:

```python
async def swap_model(model_path: str) -> None:
    """
    Hot-swap the generation model. Takes ~3.1 seconds on Orin Nano Super.
    Blocks all code generation during swap (queue pending requests).
    """
    await model_manager.unload_current()     # ~0.5 sec (page cache eviction)
    await model_manager.load_new(model_path) # ~2.6 sec (mmap + context init)
    logger.info(f"Model swapped to {model_path}")
```

The swap is non-disruptive: existing reflexes continue executing on the ESP32 nodes (they run on the local VM, independent of the Jetson). Only new code generation requests are queued during the swap. Total disruption: ~3 seconds.

### VRAM Budget

| Component | VRAM | Notes |
|---|---|---|
| Generation model (code gen) | 4 GB | DeepSeek-Coder-7B Q4_K_M or custom equivalent |
| Validation model (safety check) | 2 GB | Phi-3-mini Q4 — always resident |
| Classification model (intent parsing) | 1 GB | Loaded on demand from Phi-3 or smaller |
| Whisper STT + Piper TTS | 1.5 GB | Always resident |
| System + application | 0.5 GB | |
| **Total** | **8 GB** (with swap) | Only one LLM loaded at a time |

Your fine-tuned model must fit in the 4 GB generation slot. This means Q4_K_M quantization of a ≤7B parameter model, or Q3_K_M of a ≤13B model. In practice, 7B with Q4_K_M gives the best quality-per-VRAM tradeoff on the Orin Nano.

---

## 3. Data Collection for Training

The quality of your fine-tuned model is directly proportional to the quality of your training data. Garbage in, garbage out — and in a safety-critical system, garbage in means dangerous garbage out.

### What Data to Collect

NEXUS automatically collects three categories of training data:

**1. Observation Logs** (`/opt/nexus/data/observations/`)
- Raw sensor readings and actuator states at 100 Hz
- Accompanying metadata: timestamp, node ID, reflex IDs active, operational mode
- Stored in Parquet format, partitioned by date and node
- **Usefulness for training: Low raw, high when summarized** (see Section 4)

**2. Human Narration Transcripts** (`/opt/nexus/data/narrations/`)
- Operator voice narration during observation sessions (transcribed by Whisper)
- Includes what the operator is doing, why, and what they're paying attention to
- **Usefulness for training: Very High** — this is the "intent" signal that connects observations to actions

**3. Approved and Rejected Proposals** (`/opt/nexus/data/proposals/`)
- Every reflex proposal generated by the AI, along with its fate
- Approved proposals: operator clicked "Approve" and the reflex passed A/B testing
- Rejected proposals: operator clicked "Reject" or the reflex failed safety validation
- Each record includes: the intent description, the proposed JSON, the rejection reason, and operator comments
- **Usefulness for training: Critical** — this is the gold standard for supervised fine-tuning

### The "Golden Dataset": Approved Reflexes

The golden dataset is the set of reflexes that have been approved by an operator AND passed A/B testing against the human baseline (or the previous model). These are reflexes that demonstrably improve system behavior.

Structure (Parquet schema):
```
┌─────────────────┬──────────────┬───────────────────────┬───────────────┬──────────────┬─────────────┐
│ intent_hash     │ intent_text  │ reflex_json           │ approval_date │ ab_test_score│ domain_tags │
│ (string, hash)  │ (string)     │ (string, JSON)        │ (timestamp)   │ (float32)    │ (list[str]) │
├─────────────────┼──────────────┼───────────────────────┼───────────────┼──────────────┼─────────────┤
│ a3f2...         │ "Maintain... │ {"name":"heading...   │ 2024-08-15    │ 0.87         │ [marine,    │
│                 │              │                        │               │              │  heading]   │
└─────────────────┴──────────────┴───────────────────────┴───────────────┴──────────────┴─────────────┘
```

**Minimum for fine-tuning: 500 approved reflexes.** Below this threshold, LoRA fine-tuning tends to overfit — the model memorizes the few examples rather than learning general patterns. Our marine model used 1,200 approved reflexes; the agricultural model used 800. Both showed significant improvement over the default.

### The "Rejection Log": Equally Valuable

The rejection log is often more valuable than the golden dataset. It teaches the model what NOT to do:

- Safety violations: "This reflex would drive the rudder past 35 degrees in heavy seas"
- Incorrect physics: "The PID gains are too aggressive for a 12-ton vessel at this speed"
- Missing edge cases: "This works in calm water but fails when heading error exceeds 20 degrees"
- Operator preference: "This is correct but I prefer a gentler response"

Structure:
```
┌─────────────────┬──────────────┬───────────────────────┬───────────────┬──────────────────────────────┐
│ intent_hash     │ intent_text  │ proposed_reflex_json  │ rejection_date│ rejection_reason            │
│ (string)        │ (string)     │ (string, JSON)        │ (timestamp)   │ (string, free text)         │
└─────────────────┴──────────────┴───────────────────────┴───────────────┴──────────────────────────────┘
```

**Usage in training:** Negative examples are formatted as `(intent, BAD_reflex)` pairs and included in the training set with a special "REJECTED" label. During fine-tuning, the model learns to avoid generating reflexes that match the rejection patterns. This is especially effective for safety violations.

### Privacy and Anonymization

Before any data leaves the vessel or enters a training pipeline, it MUST be anonymized:

| Field | Anonymization Rule | Example |
|---|---|---|
| Vessel name | Replace with hash | `"Pacific Star"` → `"vessel_7a3f"` |
| GPS coordinates | Replace with relative offsets from home port | `(47.6, -122.3)` → `(0.0, 0.0)`, `(47.61, -122.29)` → `(+0.01, +0.01)` |
| Operator identity | Remove entirely | `"Capt. Sarah M."` → `[REDACTED]` |
| Port names | Replace with generic labels | `"Seattle"` → `"home_port"` |
| Specific equipment serial numbers | Remove | `"BME280-SN48291"` → `"bme280"` |

The anonymization script is at `/opt/nexus/tools/anonymize_training_data.py`. Run it before exporting data for training:

```bash
python3 /opt/nexus/tools/anonymize_training_data.py \
    --input /opt/nexus/data/proposals/golden_dataset.parquet \
    --output /opt/nexus/data/exports/anonymized_golden.parquet \
    --vessel-name "vessel_7a3f" \
    --home-port-offset "47.6,-122.3"
```

### Data Volume Requirements

| Dataset Size | Expected Quality | Recommendation |
|---|---|---|
| < 100 approved reflexes | Poor — high overfitting risk | Do not fine-tune. Collect more data. |
| 100–500 approved reflexes | Marginal — may be worse than default | Only fine-tune with very low learning rate (1e-6) and extensive regularization. |
| 500–1,000 approved reflexes | Good — meaningful improvement | Standard fine-tuning pipeline. |
| 1,000–3,000 approved reflexes | Very good — strong domain adaptation | Ideal range. Add rejection data for additional safety benefit. |
| > 3,000 approved reflexes | Excellent — near-optimal | Consider training from scratch on your data instead of fine-tuning (see Section 9). |

---

## 4. Preparing Training Data

Raw observation logs and proposal records must be converted into the format expected by the fine-tuning framework. NEXUS uses a "reflex blueprint" format for training examples.

### The Reflex Blueprint Format

Each training example is a conversation with a single assistant turn:

```json
{
  "messages": [
    {
      "role": "system",
      "content": "You are a NEXUS reflex generator. You output ONLY valid JSON..."
    },
    {
      "role": "user",
      "content": "=== OBSERVATION CONTEXT ===\nNode: steering_node (ESP32-S3, role: RUDDER_CONTROL)\nSensors: compass_heading (0-360 deg, 10 Hz), rudder_angle (-35 to 35 deg, 50 Hz)\nActuators: rudder_servo (PWM, 1100-1900 µs, dead zone 200 ms)\nCurrent state: heading=047, rudder=-3.2, vessel_speed=6.1 kts\nRecent trends: heading drifting +0.3 deg/min, rudder oscillation ±1.2 deg\nOperational constraints: max rudder rate 15 deg/s, max rudder angle 35 deg\n\n=== INTENT ===\nMaintain heading 045 at current speed. Use gentle corrections — don't oversteer.\nIf heading error exceeds 10 degrees, alert the operator."
    },
    {
      "role": "assistant",
      "content": "{\"name\": \"heading_hold_045_gentle\", \"version\": \"1.0.0\", ...}"
    }
  ]
}
```

### Format Conversion Pipeline

The conversion from raw data to training blueprints is handled by `/opt/nexus/tools/prepare_training_data.py`:

```bash
python3 /opt/nexus/tools/prepare_training_data.py \
    --golden /opt/nexus/data/exports/anonymized_golden.parquet \
    --rejections /opt/nexus/data/exports/anonymized_rejections.parquet \
    --observations /opt/nexus/data/observations/ \
    --system-prompt /etc/nexus/model_system_prompt.txt \
    --output /opt/nexus/data/training/training_blueprint_v2.jsonl \
    --negative-examples true \
    --max-examples 3000
```

Key conversion steps:

1. **Observation Summarization:** Raw 100 Hz observation logs are downsampled and summarized into a text paragraph matching the "OBSERVATION CONTEXT" format. Summary includes: current sensor values, recent trends (computed as rolling averages), actuator states, and active constraints.

2. **Intent Extraction:** For approved reflexes, the original intent text is used verbatim. For observation-only training examples (no explicit intent), the narration transcript is used as a proxy for intent.

3. **Negative Example Generation:** For each rejection, the proposed (bad) reflex is paired with the intent and labeled as `<!-- REJECTED: {reason} -->` in the assistant response, followed by the correct (approved, if available) reflex. This teaches the model to self-correct.

### Quality Filtering

Not all approved reflexes are good training examples. Apply these filters:

| Filter | Threshold | Rationale |
|---|---|---|
| Override frequency | < 50% | If the operator overrode the reflex more than half the time, the reflex was wrong, not the operator. |
| A/B test score | > 0.5 | Below 0.5, the reflex was worse than the baseline. It passed A/B by luck or was approved by mistake. |
| Age | < 6 months | Older reflexes may reflect outdated hardware or configurations. |
| Syntax complexity | < 50 actions | Extremely complex reflexes are fragile and often overfitted to specific conditions. |
| Duplicate detection | Remove exact intent hashes | Duplicate training examples inflate importance disproportionately. |

### Decontamination

Run the decontamination script to remove any PII that slipped through anonymization, and to detect and remove proprietary patterns from other vessels:

```bash
python3 /opt/nexus/tools/decontaminate.py \
    --input training_blueprint_v2.jsonl \
    --output training_blueprint_v2_clean.jsonl \
    --pii-scan true \
    --vessel-patterns /opt/nexus/data/known_vessel_patterns.txt \
    --proprietary-scan true
```

### Train/Validation/Test Split

| Split | Ratio | Purpose | Usage During Training |
|---|---|---|---|
| Train | 80% | Model weight updates | Directly optimized |
| Validation | 10% | Hyperparameter tuning, early stopping | Monitored for overfitting |
| Test | 10% | Final evaluation (never seen during training) | Used only for deployment decision |

Split strategy: **stratified by reflex type** (PID, threshold, state machine, sequencer) to ensure each type is represented in all splits. Use the `reflex_type` field extracted from the JSON structure to stratify.

### Synthetic Augmentation (v3.0 Technique)

If your golden dataset is small (500–1,000 examples), you can amplify it using synthetic augmentation:

1. **Parameter Variation:** Take an approved PID reflex and generate variants with ±20% perturbation on Kp, Ki, Kd values. The model learns that a range of gains is acceptable, not just the exact values in the training data.

2. **Setpoint Shifting:** Take a heading-hold reflex for 045° and generate variants for 090°, 135°, 180°, etc. The model learns the general pattern of heading hold, not just one specific heading.

3. **Constraint Modification:** Take a reflex with max_rate=15 deg/s and generate variants with max_rate=10, 12, 20 deg/s. Teaches the model to respect varying constraint levels.

4. **Natural Language Paraphrasing:** Use a separate LLM to rephrase the intent text while preserving semantics. "Maintain heading 045" → "Keep the vessel pointed at 045 degrees" → "Steer a course of 045". Teaches the model robustness to linguistic variation.

**Rules for synthetic data:**
- Never exceed 3× amplification (if you have 500 real examples, add at most 1,000 synthetic ones)
- Always validate synthetic reflexes against the schema (they should all pass)
- Tag synthetic examples in metadata so you can measure their impact separately
- Never use synthetic data for negative examples (real rejections only)

---

## 5. Fine-Tuning Process

### Base Model Selection

| Base Model | Parameters | License | Recommended For |
|---|---|---|---|
| **DeepSeek-Coder-7B-Instruct** | 7B | DeepSeek License (commercial OK) | Default — best code generation quality, proven on NEXUS |
| Qwen2.5-Coder-7B-Instruct | 7B | Apache 2.0 | Alternative — slightly better at instruction following |
| CodeLlama-7B-Instruct | 7B | Llama 2 Community | Legacy — supported but no longer recommended |
| StarCoder2-7B | 7B | BigCode OpenRAIL-M | If you need strong code completion without instruction tuning |

**Recommendation:** Start with DeepSeek-Coder-7B-Instruct. It is the model that NEXUS v3.1 was designed around, and it has the most battle-tested integration. Switch to Qwen2.5 only if you observe systematic instruction-following failures (the model ignores parts of your prompt).

### Fine-Tuning Method: LoRA (Low-Rank Adaptation)

LoRA inserts small trainable matrices into the transformer's attention layers. Instead of updating all 7B parameters, you update only the LoRA matrices — typically 0.1–1% of the total parameter count. This makes fine-tuning feasible on a single GPU with 8 GB VRAM.

```
Full fine-tuning:  7B × 4 bytes = 28 GB VRAM (not feasible on Jetson)
LoRA fine-tuning:  ~4B × 4 bytes (base, frozen) + ~20M × 4 bytes (LoRA, trainable) ≈ 4.2 GB VRAM
```

### Hyperparameters

These values come from 18 months of iterative experimentation across our fleet. They represent the sweet spot for NEXUS reflex generation:

| Parameter | Value | Notes |
|---|---|---|
| Learning rate | 2e-4 | Higher than typical NLP fine-tuning because LoRA matrices are small |
| LR scheduler | cosine | With 10% warmup steps |
| LoRA rank (r) | 16 | 8 for small datasets (<500), 32 for large datasets (>2000) |
| LoRA alpha | 32 | Always 2× the rank |
| LoRA dropout | 0.05 | Prevents overfitting on small datasets |
| Target modules | `q_proj, k_proj, v_proj, o_proj, gate_proj, up_proj, down_proj` | All linear layers in the transformer |
| Epochs | 3 | With early stopping if validation loss hasn't improved for 1 epoch |
| Batch size | 4 | Gradient accumulation = 4 (effective batch size = 16) |
| Max sequence length | 2048 | Sufficient for any reflex + observation context |
| Warmup ratio | 0.1 | 10% of total steps for learning rate warmup |
| Weight decay | 0.01 | Standard L2 regularization |

### Training Infrastructure

**Option A: Cloud GPU (Recommended — ~2 hours)**
- AWS `g4dn.xlarge` (1× T4 GPU, 16 GB VRAM) or `g5.xlarge` (1× A10G, 24 GB VRAM)
- Cost: ~$2–4 per training run
- Use the provided Dockerfile: `/opt/nexus/training/Dockerfile`

```bash
# Build and run the training container
docker build -t nexus-train /opt/nexus/training/
docker run --gpus all -v /path/to/data:/data nexus-train \
    --base-model deepseek-ai/deepseek-coder-7b-instruct \
    --train-file /data/training_blueprint_v2_clean.jsonl \
    --output-dir /data/output/model_v1.0.0 \
    --lora-r 16 --lora-alpha 32 --epochs 3 --lr 2e-4
```

**Option B: Jetson Orin Nano (Slow — ~12 hours)**
- Uses the Jetson's 40 TOPS GPU
- Works but is slow; fine for overnight training
- Ensure the cooling fan is running (model will thermal throttle otherwise)

```bash
# On the Jetson
cd /opt/nexus/training/
python3 train_lora.py \
    --base-model /opt/nexus/models/deepseek-coder-7b-instruct.Q4_K_M.gguf \
    --train-file /opt/nexus/data/training/training_blueprint_v2_clean.jsonl \
    --output-dir /opt/nexus/models/custom_model_v1.0.0/ \
    --lora-r 16 --lora-alpha 32 --epochs 3 --lr 2e-4 \
    --device cuda
```

**Option C: Laptop with RTX 3060+ (Intermediate — ~4 hours)**
- 8–12 GB VRAM on consumer GPU
- Works for LoRA but not full fine-tuning

### The Training Loop

Monitor these metrics in real-time (TensorBoard or Weights & Biases):

1. **Training loss** — should decrease steadily. If it plateaus within the first epoch, your learning rate may be too low. If it oscillates wildly, reduce the learning rate or increase gradient accumulation.

2. **Validation loss** — should track training loss within ~0.1. If validation loss starts increasing while training loss decreases, you are overfitting. Stop training.

3. **Validation schema pass rate** — the critical metric. After each epoch, run the model on the validation split and check what percentage of outputs pass JSON schema validation. This should be >90% by the end of training.

4. **Validation safety pass rate** — run the validation model (Phi-3-mini) on the generated reflexes. Target >85%.

### Overfitting: The Silent Killer

Overfitting in NEXUS is particularly dangerous because it manifests as "the model generates the exact reflexes it saw in training, even when the intent is slightly different." This is worse than underfitting because:

- An underfit model generates generic but safe reflexes
- An overfit model generates reflexes that *look* correct but are subtly wrong for the current conditions

**Warning signs of overfitting:**
- Training loss < 0.1, validation loss > 0.5
- The model generates the same reflex name for different intents
- Schema pass rate on validation set drops after epoch 2
- Human evaluators notice the model is "not listening" to intent variations

**Prevention:**
- Keep the LoRA rank low (8–16) for datasets under 1,000 examples
- Use LoRA dropout (0.05) — don't set it to 0
- Monitor validation loss, not just training loss
- Set `early_stopping_patience=1` (stop if validation loss doesn't improve for 1 epoch)

---

## 6. Evaluation

Before deploying a custom model, it must pass a rigorous evaluation pipeline. This is non-negotiable — a bad model can generate reflexes that damage hardware or endanger operators.

### Automatic Evaluation

**Schema Validation Pass Rate**
- Run the model on 500 held-out intent descriptions (from the test split)
- Parse every output as JSON and validate against `reflex_definition.json`
- **Threshold: ≥ 90%** (the default model achieves ~71%)
- Failure modes: malformed JSON, missing required fields, invalid trigger types

**Safety Validation Pass Rate**
- Take the schema-valid outputs and run them through the validation model (Phi-3-mini)
- The validation model checks for: rate limit violations, bounds violations, missing safety sections, physically implausible values
- **Threshold: ≥ 85%**
- Failure modes: excessive actuator rates, out-of-bounds values, missing timeout constraints

**Regression Test Suite**
- 50 canonical reflex generation tasks that any NEXUS model must handle correctly
- Includes: basic PID, threshold monitor, rate limiter, state machine, sequencer, dead man's switch
- Each task has a reference output; the model's output must be functionally equivalent (not exact string match)
- **Threshold: ≥ 45/50 correct** (the default model passes ~38/50)

### Human Evaluation: A/B Testing

Every new model must be A/B tested against the current default (or the previous custom model):

1. **Setup:** Deploy the new model and the current model side by side on the Jetson. Route 50% of code generation requests to each model randomly (but consistently per session — the same operator always gets the same model within a session).

2. **Duration:** 1 week of operational use, or 100 code generation requests, whichever comes first.

3. **Metrics:**
   - Operator approval rate (% of proposals the operator approves)
   - Mean corrections per approved proposal (operator edits before approving)
   - Time from intent to approved reflex
   - Operator satisfaction score (1–5, asked after each session)

4. **Decision criteria:**
   - The new model must have a **higher or equal** approval rate (statistically significant, p < 0.05)
   - The new model must require **fewer or equal** mean corrections
   - The operator satisfaction score must be **≥ 4.0**
   - The new model must pass all automatic evaluation thresholds

If the new model fails any criterion, do not deploy. Investigate the failure mode, collect more training data addressing the weakness, and retrain.

### The Regression Test Suite: Example Tasks

The full suite is at `/opt/nexus/evaluation/regression_suite.json`. Here are representative examples:

| ID | Intent | Expected Reflex Type | Key Validation Check |
|---|---|---|---|
| RT-001 | "Maintain heading 090" | PID | Setpoint = 90, output bounds match actuator range |
| RT-002 | "Alert if temperature > 60°C" | Threshold | Threshold = 60, action = alert |
| RT-003 | "Change throttle by at most 5% per second" | Rate limiter | max_rate = 5.0 |
| RT-004 | "Run bilge pump for 30 seconds when water high" | Sequencer | Duration = 30000 ms, conditional trigger |
| RT-005 | "Fire suppression: idle → arming → armed → firing" | State machine | 4 states, correct transitions |
| RT-006 | "Run winch only while button held" | Dead man's switch | Trigger = input_held, release action = stop |
| RT-007 | "If wind > 25 kts, reduce speed to 40%" | Threshold + PID | Conditional mode switch |
| RT-008 | "Optimize fuel at minimum 6 knots" | PID with constraint | Setpoint = 6.0, constraint = fuel_rate |
| ... | (42 more tasks) | ... | ... |

### Deployment Criteria Summary

| Criterion | Threshold | Measurement Method |
|---|---|---|
| Schema validation pass rate | ≥ 90% | Automatic (test split) |
| Safety validation pass rate | ≥ 85% | Automatic (validation model) |
| Regression suite | ≥ 45/50 | Automatic (reference comparison) |
| A/B approval rate | ≥ current model | A/B test (1 week) |
| Mean corrections | ≤ current model | A/B test (1 week) |
| Operator satisfaction | ≥ 4.0 / 5.0 | Post-session survey |

---

## 7. Deployment

### Model Packaging

The fine-tuned LoRA weights must be merged with the base model and quantized:

```bash
# Step 1: Merge LoRA weights into base model
python3 /opt/nexus/training/merge_lora.py \
    --base-model deepseek-ai/deepseek-coder-7b-instruct \
    --lora-weights /opt/nexus/models/custom_model_v1.0.0/ \
    --output /opt/nexus/models/custom_model_v1.0.0_merged/

# Step 2: Quantize to Q4_K_M (GGUF format, ~4 GB)
python3 /opt/nexus/training/quantize.py \
    --input /opt/nexus/models/custom_model_v1.0.0_merged/ \
    --output /opt/nexus/models/custom_model_v1.0.0.Q4_K_M.gguf \
    --quantization q4_k_m
```

**Why Q4_K_M?** This quantization level provides the best quality-per-VRAM tradeoff for 7B models. Q5_K_M is marginally better (2–3% on benchmark scores) but exceeds the 4 GB VRAM budget. Q3_K_M fits easily (3.2 GB) but shows a noticeable quality drop on complex reflex generation tasks (~8% lower schema pass rate).

### File Naming Convention

```
/opt/nexus/models/
├── deepseek-coder-7b-instruct.Q4_K_M.gguf          # Default model
├── custom_marine_v1.0.0.Q4_K_M.gguf               # Custom marine model v1
├── custom_marine_v1.1.0.Q4_K_M.gguf               # Custom marine model v1.1
├── custom_marine_v2.0.0.Q4_K_M.gguf               # Custom marine model v2 (new training data)
└── custom_marine_v2.0.0.Q4_K_M.gguf.rollback       # Previous model, kept for rollback
```

Semantic versioning rules:
- **Patch (x.x.Z):** Bug fix in training pipeline, same data. Safe to auto-deploy.
- **Minor (x.Y.0):** New training data added (monthly fine-tune). Requires A/B test.
- **Major (X.0.0):** New base model, new architecture, or fundamental training approach change. Requires full evaluation cycle.

### A/B Deployment

```bash
# Deploy new model alongside default for A/B testing
nexus model deploy \
    --model custom_marine_v1.0.0.Q4_K_M.gguf \
    --mode ab_test \
    --traffic-split 50/50 \
    --duration 168h \
    --rollback-model deepseek-coder-7b-instruct.Q4_K_M.gguf
```

During A/B testing, the system logs every code generation request with: which model handled it, the intent, the generated reflex, and the operator's response (approve/reject/modify). This data feeds into the next training cycle.

### Rollback Procedure

If anything goes wrong (safety validation pass rate drops, operators report issues, or metrics degrade):

```bash
# One-command rollback to previous model
nexus model rollback
# Takes ~3.1 seconds. No reflex disruption (existing reflexes run on ESP32 VM).
```

The rollback preserves all telemetry and A/B test data. The rolled-back model continues serving until a new model passes the evaluation criteria.

### The Model Marketplace (v3.0)

NEXUS v3.0 introduced a peer-to-peer model sharing mechanism between vessels. Anonymized models can be exported, shared via USB or Starlink, and imported on other vessels:

```bash
# Export anonymized model (removes vessel-specific patterns)
nexus model export \
    --model custom_marine_v1.0.0.Q4_K_M.gguf \
    --output custom_marine_v1.0.0_anon.Q4_K_M.gguf \
    --anonymize true \
    --strip-vessel-ids true

# Import and evaluate a model from another vessel
nexus model import \
    --source custom_marine_v1.0.0_anon.Q4_K_M.gguf \
    --evaluate true \
    --regression-only true  # Skip A/B test, just check regression suite
```

**Important:** A model from another vessel is evaluated against your regression suite before being considered. Even if it passes, it should be A/B tested in your environment before full deployment — another vessel's operational context (sensor types, actuator constraints, environmental conditions) may differ from yours.

---

## 8. Continuous Improvement

### The Feedback Loop

The NEXUS training system is designed as a continuous cycle:

```
Operator uses system
    → Operator corrections logged as training data
    → New data accumulates in /opt/nexus/data/proposals/
    → Monthly: prepare training dataset from accumulated data
    → Fine-tune model on new data
    → Evaluate against regression suite
    → A/B test if passing
    → Deploy if A/B test passes
    → Operator uses improved system
    → (repeat)
```

Every operator correction — every time an operator edits a generated reflex before approving it — becomes a training example for the next cycle. This means the model continuously learns from its mistakes. The marine vessel that achieved 40% fewer corrections did so after 6 monthly fine-tuning cycles.

### Recommended Cadence

| Activity | Frequency | Duration | Prerequisites |
|---|---|---|---|
| Data collection | Continuous | — | System in operation |
| Data preparation | Monthly | 30 minutes | ≥ 50 new approved reflexes since last cycle |
| Fine-tuning | Monthly | 2–12 hours | ≥ 50 new examples |
| Full evaluation | Monthly | 1 day | New model trained |
| A/B testing | Monthly | 1 week | Model passes evaluation |
| Full retrain (from scratch) | Quarterly | 1–2 days | ≥ 500 new examples since last retrain |
| Regression suite update | As needed | 1 hour | New failure modes discovered |

### The v3.1 Automated Training Pipeline

NEXUS v3.1 can automate the entire cycle. When enabled, the system:

1. **Collects** new training data continuously (operator approvals, rejections, corrections)
2. **Monitors** data volume — triggers a training cycle when ≥ 50 new high-quality examples accumulate
3. **Prepares** the training dataset automatically (summarization, filtering, decontamination, splitting)
4. **Triggers** fine-tuning on the next available GPU (Jetson or cloud, depending on configuration)
5. **Evaluates** the trained model against the regression suite and automatic metrics
6. **Deploys** to A/B testing if all thresholds pass
7. **Reports** results to the operator via the dashboard and/or email notification

Enable with:
```yaml
# /etc/nexus/training_pipeline.yaml
enabled: true
min_new_examples: 50
training_gpu: auto          # "jetson" | "cloud" | "auto" (uses jetson if available, otherwise queues for cloud)
auto_deploy: false          # true = skip A/B test and deploy automatically (NOT recommended for safety-critical domains)
ab_test_duration_hours: 168
notification:
  type: mqtt                # "mqtt" | "email" | "none"
  topic: nexus/training/status
```

**Safety guard:** The automated pipeline will NEVER auto-deploy a model without A/B testing passing. Even with `auto_deploy: true`, the model must pass the regression suite and schema/safety validation thresholds. A/B testing can be skipped only in non-safety-critical domains (e.g., home automation lighting scenes).

---

## 9. Advanced Topics

### 9.1 RLHF: Reinforcement Learning from Human Feedback

Beyond supervised fine-tuning, you can use the operator's approval/rejection signal as a reward for reinforcement learning:

- **Reward = +1** for approved reflexes that pass A/B testing
- **Reward = +0.5** for approved reflexes (operator edited but accepted)
- **Reward = -1** for rejected reflexes
- **Reward = -2** for reflexes that fail safety validation

RLHF fine-tuning adjusts the model's generation probabilities to maximize expected reward. In practice, RLHF on top of LoRA fine-tuning provides an additional 5–10% improvement in safety validation pass rate.

**Implementation:** Use the TRL (Transformer Reinforcement Learning) library from Hugging Face. The reward model is a separate small model (distilled from the validation model) that predicts approval probability. Train it on your approval/rejection log, then use it as the reward signal for PPO (Proximal Policy Optimization).

**When to use RLHF:**
- You have > 2,000 labeled examples (approvals + rejections)
- Supervised fine-tuning has plateaued (no improvement after 3 consecutive monthly cycles)
- You are willing to invest in the additional complexity (2–3× training time, reward model maintenance)

### 9.2 Constitutional AI: Encoding NEXUS Safety Rules

Constitutional AI applies a set of rules (the "constitution") during both training and inference to ensure the model's outputs comply with safety constraints:

**NEXUS Constitution (excerpt):**
```
Rule 1: All reflexes MUST include a "safety" section with rate limits and bounds.
Rule 2: Actuator output values MUST be within the physical range of the target hardware.
Rule 3: No reflex may produce an output that exceeds the previous output by more than
        the configured max_rate without explicit operator approval.
Rule 4: Reflexes controlling safety-critical actuators (steering, throttle, fire
        suppression) MUST include a timeout that returns to a safe state.
Rule 5: The kill switch override reflex has the highest priority and cannot be
        modified or overridden by any AI-generated reflex.
```

**Implementation:** These rules are embedded in the system prompt (they already are — see Section 2). For additional robustness, you can add a "constitutional critique" step where the model is asked to evaluate its own output against the constitution before returning it. This adds ~1 second of latency but catches an additional 2% of safety violations.

### 9.3 Multi-Domain Training

If you operate across multiple domains (e.g., marine + HVAC on the same vessel), you have two options:

**Option A: Single generalist model** (default)
- Train on all domains combined
- Pros: Simple, one model to manage
- Cons: Lower quality per-domain than specialists; conflicts between domain patterns
- **Recommendation:** If domains are similar (marine autopilot + marine throttle control), use this.

**Option B: Specialist models with a router**
- Train one model per domain
- Use a lightweight classification model to route intents to the appropriate specialist
- Pros: Higher per-domain quality, no conflicts
- Cons: More VRAM, more maintenance, routing errors
- **Recommendation:** If domains are very different (marine + greenhouse), use this.

```python
# Router configuration
DOMAIN_MODELS = {
    "marine": "/opt/nexus/models/custom_marine_v1.0.0.Q4_K_M.gguf",
    "greenhouse": "/opt/nexus/models/custom_greenhouse_v1.0.0.Q4_K_M.gguf",
    "factory": "/opt/nexus/models/custom_factory_v1.0.0.Q4_K_M.gguf",
}

async def route_intent(intent: str) -> str:
    """Classify intent and return the appropriate model path."""
    domain = await classifier.classify(intent)  # Phi-3-mini, < 100ms
    return DOMAIN_MODELS.get(domain, DEFAULT_MODEL_PATH)
```

### 9.4 The Specialist-Generalist Architecture

The most advanced approach, used by fleet operators with > 10 vessels:

- **Specialist models (4 GB each, domain-specific):** Small, focused models trained on one domain. Used for code generation. Higher quality per-domain.
- **Generalist validation model (2 GB):** A single large model (e.g., Llama-3-8B-Instruct Q2_K) used for safety validation across ALL domains. Ensures consistent safety standards.

This architecture separates the concerns: specialists optimize for quality, the generalist optimizes for safety consistency. The cost is additional VRAM management — only one specialist is loaded at a time, with the generalist always resident.

**VRAM layout with specialist-generalist:**
```
[Generalist validation model: 2 GB — always resident]
[Whisper STT + Piper TTS: 1.5 GB — always resident]
[Specialist generation model: 4 GB — swapped per domain]
[System + application: 0.5 GB]
Total: 8 GB
```

---

## Quick-Start Checklist

For ML engineers who want to get started immediately:

- [ ] Collect ≥ 500 approved reflexes from your operational NEXUS deployment
- [ ] Export and anonymize the golden dataset and rejection log
- [ ] Run the data preparation pipeline to create training blueprints (JSONL format)
- [ ] Split into train (80%) / validation (10%) / test (10%)
- [ ] Fine-tune DeepSeek-Coder-7B-Instruct with LoRA (r=16, alpha=32, lr=2e-4, 3 epochs)
- [ ] Merge LoRA weights and quantize to Q4_K_M GGUF format
- [ ] Evaluate: schema pass rate ≥ 90%, safety pass rate ≥ 85%, regression suite ≥ 45/50
- [ ] Deploy to A/B testing (50/50 split, 1 week)
- [ ] Verify: approval rate ≥ current model, corrections ≤ current model, satisfaction ≥ 4.0
- [ ] Full deploy or rollback based on A/B results
- [ ] Schedule next training cycle (monthly)

---

*Document version: 1.0.0 — Written for NEXUS v3.1 platform. All hyperparameters, thresholds, and procedures are based on 2 years of operational data from marine, agricultural, and industrial deployments. Re-validate thresholds after major platform version upgrades.*

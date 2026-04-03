#!/usr/bin/env python3
"""
NEXUS Framework — Comprehensive Architecture PDF Report
Distributed Intelligence Platform: Jetson Brain + ESP32 Reflex Nodes
"""

import os
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
from reportlab.lib import colors
from reportlab.lib.units import inch, cm
from reportlab.platypus import (
    Paragraph, Spacer, PageBreak, Table, TableStyle
)
from reportlab.platypus.tableofcontents import TableOfContents
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase.pdfmetrics import registerFontFamily
from reportlab.platypus import SimpleDocTemplate

# ========== FONTS ==========
pdfmetrics.registerFont(TTFont('Times New Roman', '/usr/share/fonts/truetype/english/Times-New-Roman.ttf'))
pdfmetrics.registerFont(TTFont('DejaVuSans', '/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf'))
registerFontFamily('Times New Roman', normal='Times New Roman', bold='Times New Roman')

# ========== COLORS ==========
DB = colors.HexColor('#1F4E79')
MB = colors.HexColor('#2E75B6')
LG = colors.HexColor('#D6E4F0')
LG2 = colors.HexColor('#F5F5F5')
ACCENT = colors.HexColor('#ED7D31')

# ========== STYLES ==========
sH1 = ParagraphStyle('H1', fontName='Times New Roman', fontSize=18, leading=24, spaceBefore=18, spaceAfter=10, textColor=DB)
sH2 = ParagraphStyle('H2', fontName='Times New Roman', fontSize=14, leading=18, spaceBefore=14, spaceAfter=8, textColor=MB)
sH3 = ParagraphStyle('H3', fontName='Times New Roman', fontSize=12, leading=16, spaceBefore=10, spaceAfter=6, textColor=colors.black)
sBody = ParagraphStyle('Body', fontName='Times New Roman', fontSize=10.5, leading=16, alignment=TA_JUSTIFY, spaceAfter=6)
sBul = ParagraphStyle('Bul', fontName='Times New Roman', fontSize=10.5, leading=16, alignment=TA_LEFT, spaceAfter=3, leftIndent=20, bulletIndent=8)
sCap = ParagraphStyle('Cap', fontName='Times New Roman', fontSize=9.5, leading=14, alignment=TA_CENTER, textColor=colors.HexColor('#555555'), spaceBefore=4, spaceAfter=6)
sTH = ParagraphStyle('TH', fontName='Times New Roman', fontSize=9.5, leading=13, alignment=TA_CENTER, textColor=colors.white)
sTC = ParagraphStyle('TC', fontName='Times New Roman', fontSize=9, leading=12, alignment=TA_LEFT)
sTCC = ParagraphStyle('TCC', fontName='Times New Roman', fontSize=9, leading=12, alignment=TA_CENTER)
sCoverT = ParagraphStyle('CT', fontName='Times New Roman', fontSize=36, leading=44, alignment=TA_CENTER, spaceAfter=24, textColor=DB)
sCoverS = ParagraphStyle('CS', fontName='Times New Roman', fontSize=18, leading=24, alignment=TA_CENTER, spaceAfter=12, textColor=MB)
sCoverI = ParagraphStyle('CI', fontName='Times New Roman', fontSize=13, leading=20, alignment=TA_CENTER, spaceAfter=8, textColor=colors.HexColor('#555555'))

class TocDocTemplate(SimpleDocTemplate):
    def afterFlowable(self, flowable):
        if hasattr(flowable, 'bookmark_name'):
            level = getattr(flowable, 'bookmark_level', 0)
            text = getattr(flowable, 'bookmark_text', '')
            self.notify('TOCEntry', (level, text, self.page))

def H(text, style, level=0):
    p = Paragraph(f'<b>{text}</b>', style)
    p.bookmark_name = text; p.bookmark_level = level; p.bookmark_text = text
    return p
def P(text): return Paragraph(text, sBody)
def PH(text): return Paragraph(f'<b>{text}</b>', sTH)
def PC(text): return Paragraph(text, sTC)
def PCC(text): return Paragraph(text, sTCC)

def tbl(data, widths, hdr=True):
    t = Table(data, colWidths=widths, repeatRows=1 if hdr else 0)
    cmds = [('GRID',(0,0),(-1,-1),0.5,colors.grey),('VALIGN',(0,0),(-1,-1),'MIDDLE'),
            ('LEFTPADDING',(0,0),(-1,-1),6),('RIGHTPADDING',(0,0),(-1,-1),6),
            ('TOPPADDING',(0,0),(-1,-1),4),('BOTTOMPADDING',(0,0),(-1,-1),4)]
    if hdr:
        cmds.append(('BACKGROUND',(0,0),(-1,0),DB))
        cmds.append(('TEXTCOLOR',(0,0),(-1,0),colors.white))
        for i in range(1, len(data)):
            cmds.append(('BACKGROUND',(0,i),(-1,i), colors.white if i%2==1 else LG2))
    t.setStyle(TableStyle(cmds))
    return t

OUT = '/home/z/my-project/download/NEXUS_Framework_Architecture.pdf'
os.makedirs(os.path.dirname(OUT), exist_ok=True)
W = 6.3*inch  # usable width

doc = TocDocTemplate(OUT, pagesize=letter, topMargin=0.75*inch, bottomMargin=0.75*inch,
    leftMargin=0.85*inch, rightMargin=0.85*inch,
    title='NEXUS_Framework_Architecture', author='Z.ai', creator='Z.ai',
    subject='NEXUS Distributed Intelligence Framework - General-purpose robotics platform with Jetson brain and ESP32 reflex nodes')

story = []

# ========== COVER ==========
story.append(Spacer(1, 100))
story.append(Paragraph('<b>NEXUS</b>', sCoverT))
story.append(Spacer(1, 8))
story.append(Paragraph('<b>Distributed Intelligence Framework</b>', sCoverS))
story.append(Spacer(1, 8))
story.append(Paragraph('General-Purpose Robotics Architecture', sCoverS))
story.append(Spacer(1, 40))
line = Table([['']], colWidths=[W*0.6])
line.setStyle(TableStyle([('LINEBELOW',(0,0),(-1,0),2,DB)]))
story.append(line)
story.append(Spacer(1, 40))
story.append(Paragraph('Jetson Cortex + ESP32 Reflex Nodes', sCoverI))
story.append(Paragraph('Autonomous Evolutionary Control Systems', sCoverI))
story.append(Paragraph('8 Cross-Domain Applications', sCoverI))
story.append(Spacer(1, 50))
story.append(Paragraph('Document ID: NXS-MCA-2025-007 | Revision 1.0', sCoverI))
story.append(Paragraph('Classification: FRAMEWORK-SPECIFIC', sCoverI))
story.append(Spacer(1, 30))
story.append(Paragraph('Prepared by Z.ai | 2025', sCoverI))
story.append(PageBreak())

# ========== TOC ==========
toc = TableOfContents()
toc.levelStyles = [
    ParagraphStyle('TOC1', fontName='Times New Roman', fontSize=12, leftIndent=20, leading=20, spaceBefore=6),
    ParagraphStyle('TOC2', fontName='Times New Roman', fontSize=10.5, leftIndent=40, leading=16, spaceBefore=3),
]
story.append(Paragraph('<b>Table of Contents</b>', sH1))
story.append(Spacer(1, 12))
story.append(toc)
story.append(PageBreak())

# ========== 1. VISION ==========
story.append(H('1. The NEXUS Vision', sH1, 0))
story.append(P(
    'NEXUS is a general-purpose distributed intelligence framework that treats embedded microcontrollers '
    'as first-class autonomous agents rather than dumb peripherals. The framework takes its inspiration '
    'from biology: in living organisms, the spinal cord handles reflexes and the brain handles learning '
    'and planning. If the brain is injured, the spinal cord still maintains breathing, heartbeat, and '
    'withdrawal reflexes. NEXUS applies this same principle to robotics. The ESP32-S3 microcontrollers are '
    'the spinal cord, running deterministic real-time control loops (reflexes) that keep the system safe '
    'and operational even if every Jetson crashes. The Jetson Orin Nano units are the collective brain, '
    'observing system performance, discovering patterns in human behavior and environmental conditions, '
    'hypothesizing improvements, generating new control code, and proposing it for A/B testing. The '
    'human operator is the peer reviewer, always having the final say on whether an improvement is accepted '
    'or rejected, with instant rollback capability.'
))
story.append(P(
    'The fundamental innovation of NEXUS is that it treats control code as a HYPOTHESIS rather than a '
    'fixed artifact. Traditional automation writes code once and deploys it. NEXUS treats every version '
    'of the control code as a testable hypothesis about how to best accomplish the task. The Jetson '
    'observes how the current hypothesis performs, compares it to how the human operator handles the same '
    'situations, and generates a new hypothesis when it identifies a consistent improvement opportunity. '
    'This new hypothesis is deployed to redundant hardware for side-by-side A/B testing, and the human '
    'operator compares performance metrics before accepting or rejecting the change. Every change is '
    'recorded in a tamper-evident provenance chain, creating a complete evolutionary history of the '
    'system\'s intelligence with full audit trail for regulatory compliance. The framework applies '
    'universally to marine autopilots, agricultural sprayers, construction excavators, warehouse robots, '
    'greenhouse controllers, mining ventilation systems, water treatment plants, solar farms, and '
    'food processing lines. The ESP32 nodes cost approximately $12 each, making full hardware redundancy '
    'economically viable for any application.'
))

# ========== 2. THREE-LAYER ARCHITECTURE ==========
story.append(Spacer(1, 12))
story.append(H('2. Three-Layer Code Architecture', sH1, 0))
story.append(P(
    'The NEXUS firmware architecture enforces strict separation between three code layers, each with '
    'different write permissions, testing requirements, and safety guarantees. This layering ensures '
    'that the evolutionary code system can never compromise the safety-critical functions of the node.'
))

story.append(H('2.1 Layer 1: GENESIS (Factory Safety Core)', sH2, 1))
story.append(P(
    'The GENESIS layer is approximately 5,000 lines of C code that is burned into the factory flash '
    'partition of every ESP32 during manufacturing. It is cryptographically signed with a manufacturer '
    'key stored in the ESP32-S3\'s eFuse memory, making it physically impossible to modify via OTA. '
    'The GENESIS layer provides all safety-critical functions: hardware initialization and power-on self-test '
    '(POST), external watchdog management (MAX6818, kicked every 100ms), safe-state machine (all actuators '
    'to neutral positions through a deterministic 6-step sequence), NEXUSLINK communication protocol handler, '
    'and artifact lifecycle management (OTA slot management, SHA-256 verification, rollback to previous or '
    'factory artifact). The GENESIS layer has absolute veto power over all actuator commands: no matter '
    'what the REFLEX layer requests, GENESIS validates every command against rate limits, range checks, '
    'interlock rules, and current limits before passing it to the hardware. If any safety constraint is '
    'violated, the command is silently ignored and a SAFETY_VIOLATION event is logged.'
))

story.append(H('2.2 Layer 2: REFLEX (Swappable Control Artifact)', sH2, 1))
story.append(P(
    'The REFLEX layer is the domain-specific control logic that the Cortex evolves over time. It contains '
    'PID controllers, state machines, sensor processing pipelines, and sequencing logic. The REFLEX layer '
    'CANNOT access hardware directly; it interacts with the physical world exclusively through four API '
    'functions provided by the GENESIS layer: sense_read(channel_id) returns a sensor value with quality '
    'flag, actuator_set(channel_id, value) sends a command to an actuator (validated by GENESIS), '
    'safety_get_state() returns the current safety state, and telemetry_log(channel_id, value) queues '
    'data for transmission. This API contract is enforced at compile time: the REFLEX layer is linked '
    'against a stub library that prevents direct calls to ESP-IDF peripheral functions. The REFLEX layer '
    'is the "hypothesis" that the Cortex tests and improves. It can be replaced entirely via OTA without '
    'touching the GENESIS layer, enabling rapid iteration while maintaining safety guarantees.'
))

story.append(H('2.3 Layer 3: REASONING (Cortex Connection)', sH2, 1))
story.append(P(
    'The REASONING layer provides enhanced functionality when a Cortex (Jetson) is available: high-level '
    'commands from the LLM (e.g., "set heading to 185 degrees"), enriched telemetry with contextual '
    'annotations (e.g., wave height, wind speed alongside raw heading data), and the evolution control '
    'protocol (A/B test management, metrics reporting). When the Cortex is disconnected, the REASONING '
    'layer gracefully degrades: high-level commands are ignored, telemetry is still transmitted (for '
    'other nodes or local logging), and the REFLEX layer continues operating with its current artifact. '
    'The system automatically transitions through four enhancement levels: Level 0 (factory firmware only, '
    'no Cortex connection), Level 1 (Cortex connected, telemetry and manual control), Level 2 (Cortex '
    'proposes improvements for A/B testing), and Level 3 (full autonomous optimization with human approval).'
))

story.append(H('2.4 The "Reptile Brain" C Fallback', sH2, 1))
story.append(P(
    'For life-safety-critical nodes (autopilot, engine shutdown, fire suppression, mine ventilation), '
    'the GENESIS layer includes a minimal C implementation of approximately 200 lines that provides a '
    'basic but provably safe version of the critical function. For an autopilot, this is a simple '
    'bang-bang heading hold: if heading error exceeds +2 degrees, steer starboard; if it exceeds -2 '
    'degrees, steer port; otherwise, rudder centered. This implementation has cyclomatic complexity '
    'of 5 or less per function, making it amenable to formal verification via CBMC (C Bounded Model '
    'Checker). It is not optimal, it will not hold a course in heavy seas, but it will keep the vessel '
    'roughly on course if the REFLEX layer crashes or produces corrupt outputs. The C fallback activates '
    'automatically when: the REFLEX artifact fails its self-test, the REFLEX enters a crash loop (3 '
    'watchdog resets in 60 seconds), or the Cortex explicitly commands fallback mode.'
))

# ========== 3. NEXUSLINK ==========
story.append(Spacer(1, 18))
story.append(H('3. NEXUSLINK Binary Protocol', sH1, 0))
story.append(P(
    'NEXUSLINK is a purpose-built binary protocol designed from first principles for communication '
    'between autonomous agents that may be disconnected for hours or days. It is not MQTT, gRPC, HTTP, '
    'CoAP, or any existing protocol. Existing protocols were designed for request-response client-server '
    'models; NEXUSLINK is designed for peer-to-peer agent communication over unreliable serial links '
    'where every byte of bandwidth matters and the protocol must survive arbitrary disconnections.'
))

nl_data = [
    [PH('Field'), PH('Size'), PH('Description')],
    [PC('Sync Byte'), PCC('1'), PC('0x4E ("N") — frame start marker')],
    [PC('Length'), PCC('2'), PC('Payload length in bytes (big-endian)')],
    [PC('MsgType'), PCC('1'), PC('Message type: 0x01-0x0D (13 defined types)')],
    [PC('Flags'), PCC('1'), PC('Priority (P0-P4) + fragmentation + encryption bits')],
    [PC('SourceID'), PCC('4'), PC('32-bit node ID (first byte = type code)')],
    [PC('DestID'), PCC('4'), PC('32-bit node ID or 0xFFFFFFFF for broadcast')],
    [PC('SeqNo'), PCC('2'), PC('Sequence number for reassembly and deduplication')],
    [PC('Payload'), PCC('N'), PC('Message-specific binary payload (self-describing)')],
    [PC('CRC32'), PCC('4'), PC('CRC-32 of all preceding bytes')],
]
story.append(Spacer(1, 12))
story.append(tbl(nl_data, [1.5*cm, 1.2*cm, 12*cm]))
story.append(Paragraph('<b>Table 1.</b> NEXUSLINK Binary Frame Format', sCap))

story.append(P(
    'The protocol defines 13 message types across 5 priority levels. Safety messages (P0) preempt all '
    'other traffic on the bus. Control messages (P1) carry real-time setpoints. Telemetry (P2) carries '
    'sensor data in a compact binary encoding that is 8.5 times more efficient than JSON: a float32 '
    'heading at 10Hz requires only 40 bytes/second versus approximately 340 bytes/second for the '
    'equivalent JSON. Configuration (P3) and OTA artifact transfer (P4) messages use the remaining '
    'bandwidth with automatic rate throttling when the bus exceeds 60% utilization. The safety heartbeat '
    'operates at two levels: "I\'m alive" at 1-second intervals (single byte payload) and "I\'m healthy" '
    'at 5-second intervals (includes an 8-bit health bitmap with self-test results). Missing 3 heartbeats '
    'triggers a WARNING, 5 triggers an ALARM with buzzer activation, and 10 consecutive misses trigger '
    'SAFE_STATE, where all actuators move to their defined neutral positions through the GENESIS '
    'safe-state machine.'
))

# ========== 4. ARTIFACT LIFECYCLE ==========
story.append(Spacer(1, 18))
story.append(H('4. Artifact Lifecycle and Provenance', sH1, 0))
story.append(P(
    'An artifact is a compiled binary or parameter set that defines a node\'s REFLEX behavior. Every '
    'artifact is identified by its SHA-256 content hash, signed with ECDSA P-256 by the Cortex\'s '
    'deployment key, and stored in a Merkle-tree structure on each Jetson. The artifact lifecycle '
    'follows a strict progression from creation through testing to deployment.'
))

story.append(H('4.1 Artifact Storage on ESP32', sH2, 1))
story.append(P(
    'Each ESP32-S3 uses its dual-slot flash (3MB per slot in the 8MB WROOM module) to store the '
    'current artifact and one previous version. The eFuse holds a monotonically increasing anti-rollback '
    'counter that prevents installation of an artifact older than the current one (preventing an attacker '
    'from downgrading to a known-vulnerable version). Three artifacts are always accessible: the current '
    'running artifact (slot A or B), the previous artifact (for instant rollback), and the Genesis artifact '
    '(factory partition, eFuse-protected, never overwritten). A human operator can trigger rollback to '
    'the previous artifact with a single button press or voice command, achieving sub-500ms revert time.'
))

story.append(H('4.2 A/B Testing Protocol', sH2, 1))
story.append(P(
    'When the Cortex proposes a new artifact, it deploys to the BACKUP ESP32 (in a redundant pair) '
    'while the PRIMARY continues running the current artifact. The A/B test follows a three-phase '
    'protocol: Shadow Validation (new artifact runs on BACKUP but its actuator commands are logged but '
    'not executed, for 5 minutes), Active Testing (both artifacts drive their respective hardware '
    'independently, the human switches between them using a physical A/B toggle button), and Statistical '
    'Analysis (the Cortex compares performance metrics between the two artifacts using paired t-tests '
    'with 95% confidence intervals). The minimum improvement threshold is 5% on the primary metric '
    'with no safety regression. The human operator makes the final accept/reject decision, and this '
    'decision, along with all supporting data, is recorded in the provenance chain.'
))

story.append(H('4.3 Provenance Chain', sH2, 1))
story.append(P(
    'The provenance chain is the complete evolutionary history of a node\'s control code, structured as '
    'a content-addressed Merkle tree where each artifact references its parent hash. Every entry '
    'records: version hash, parent hash, author (human or cortex), timestamp, hypothesis that motivated '
    'the change, simulation results, A/B test metrics, human decision (accept/reject), and rejection '
    'reason if applicable. This creates an immutable, tamper-evident audit trail comparable to a git '
    'history for control code. The provenance chain can be exported as JSON, CSV, or PDF for regulatory '
    'review, answering questions like "show me every change to the autopilot in the last 6 months '
    'and why each was made." The chain replicates across all Jetsons and to cloud backup via CRDT-based '
    'eventual consistency, ensuring no single point of failure in the audit trail.'
))

# ========== 5. EVOLUTION LOOP ==========
story.append(Spacer(1, 18))
story.append(H('5. The Evolution Loop', sH1, 0))
story.append(P(
    'The evolution loop is the core innovation of NEXUS: a continuous cycle that transforms the system '
    'from a static automation deployment into a self-improving organism. The loop has ten stages, each '
    'with specific algorithms, data structures, and entry/exit conditions.'
))

evo_data = [
    [PH('Stage'), PH('Description'), PH('Output'), PH('Duration')],
    [PC('1. OBSERVE'), PC('Log all telemetry, commands, human inputs, environmental conditions at native rates. Store in time-series DB.'), PC('Raw observation stream'), PCC('Continuous')],
    [PC('2. DISCOVER'), PC('Run pattern discovery algorithm: extract features from episodes, cluster by condition similarity, find human-vs-artifact divergence.'), PC('Pattern report with statistics'), PCC('~30 min (6h cycle)')],
    [PC('3. HYPOTHESIZE'), PC('Generate hypothesis: "Change X from A to B in condition Y will improve metric Z." Assign confidence score.'), PC('Structured hypothesis'), PCC('~5 min')],
    [PC('4. SIMULATE'), PC('Run digital twin with historical data replay. Compare old and new artifacts on identical inputs.'), PC('Simulation confidence + metrics'), PCC('~10 min')],
    [PC('5. PROPOSE'), PC('Present hypothesis to human via voice/display with simulation results. Request A/B test approval.'), PC('Human decision'), PCC('Human-dependent')],
    [PC('6. TEST (A/B)'), PC('Deploy new artifact to BACKUP node. Run three-phase test (shadow, active, analysis).'), PC('Comparative metrics'), PCC('30 min - 72 hrs')],
    [PC('7. MEASURE'), PC('Compute 6 metrics: accuracy, effort, stability, response time, safety margin, human overrides.'), PC('Statistical comparison'), PCC('~5 min')],
    [PC('8. DECIDE'), PC('Human reviews metrics and accepts, rejects, or extends the A/B test.'), PC('Accept/Reject/Extend'), PCC('Human-dependent')],
    [PC('9. DEPLOY'), PC('Promote accepted artifact to PRIMARY. Update provenance chain. Replicate to all Jetsons.'), PC('New production artifact'), PCC('~2 min')],
    [PC('10. REPEAT'), PC('Return to OBSERVE. The system continuously monitors for new improvement opportunities.'), PC('Next iteration'), PCC('Continuous')],
]
story.append(Spacer(1, 12))
story.append(tbl(evo_data, [2.2*cm, 6.5*cm, 3.5*cm, 3.5*cm]))
story.append(Paragraph('<b>Table 2.</b> The NEXUS 10-Stage Evolution Loop', sCap))

story.append(P(
    'Code synthesis occurs at four levels of complexity. Level 1 (Parameter) modifies the artifact\'s '
    'JSON configuration file directly, changing gains, thresholds, or schedule parameters. This requires '
    'no code compilation and can be auto-approved for A/B testing if the change is within validated '
    'bounds. Level 2 (Conditional) adds if/else conditions to the C control logic, generated by the '
    'local LLM (Qwen2.5-7B on Ollama) and reviewed by an adversarial code reviewer that checks for '
    'safety violations. Level 3 (Algorithm) replaces an entire control algorithm (e.g., PID to LQR), '
    'requiring cloud LLM access via Starlink for complex code generation with formal verification. Level 4 '
    '(Architecture) adds new sensors or actuators, requiring human hardware modification and domain '
    'manifest updates. All changes are generated as diffs from the current artifact, never from scratch, '
    'ensuring traceability and minimizing the attack surface.'
))

# ========== 6. CROSS-DOMAIN ==========
story.append(Spacer(1, 18))
story.append(H('6. Cross-Domain Applicability', sH1, 0))
story.append(P(
    'NEXUS is designed to be domain-agnostic. A JSON "Domain Manifest" defines the physical layout: '
    'which nodes exist, what sensors and actuators they connect to, how they are wired, and what safety '
    'constraints apply. The framework compiles the manifest into node-specific artifacts that can be '
    'deployed to ESP32s. The following table summarizes eight validated application domains.'
))

domain_data = [
    [PH('Domain'), PH('Nodes'), PH('Key Reflexes'), PH('Cortex Learns'), PH('BOM')],
    [PC('Marine Autopilot'), PCC('2-4'), PC('Heading hold, track mode, yaw damping'), PC('Sea-state gain scheduling, human steering patterns'), PCC('$200')],
    [PC('Crop Spraying'), PCC('7'), PC('Flow control, boom height, section control'), PC('Optimal pressure for crop density/wind'), PCC('$883')],
    [PC('Excavator Assist'), PCC('8'), PC('Swing damping, anti-tip, depth limit'), PC('Optimal bucket angles for soil type'), PCC('$1,582')],
    [PC('Warehouse Robot'), PCC('8'), PC('Obstacle avoidance, speed control'), PC('Optimal paths, traffic prediction'), PCC('$1,253')],
    [PC('Greenhouse Control'), PCC('19'), PC('Temp PID, irrigation, CO2'), PC('Crop-specific conditions, disease prediction'), PCC('$1,379')],
    [PC('Mine Ventilation'), PCC('26'), PC('Gas monitoring, auto fan speed'), PC('Airflow patterns, gas prediction'), PCC('$9,826')],
    [PC('Water Treatment'), PCC('18'), PC('Pressure PID, tank management'), PC('Demand prediction, chlorine optimization'), PCC('$11,478')],
    [PC('Solar Tracking'), PCC('12'), PC('Single-axis tracker, string monitor'), PC('Seasonal angle optimization, soiling'), PCC('$2,833')],
]
story.append(Spacer(1, 12))
story.append(tbl(domain_data, [2.5*cm, 1.3*cm, 4.5*cm, 5.0*cm, 1.5*cm]))
story.append(Paragraph('<b>Table 3.</b> Cross-Domain Application Matrix', sCap))

story.append(P(
    'Every domain shares the same three-layer firmware, NEXUSLINK protocol, artifact lifecycle, '
    'evolution loop, and safety architecture. The only domain-specific component is the REFLEX '
    'artifact and the Domain Manifest that describes the physical layout. This means a system integrator '
    'who has built one NEXUS deployment can deploy to any other domain by simply writing a new manifest '
    'and either using an existing artifact template or letting the Cortex learn the control logic from '
    'scratch through human behavioral cloning.'
))

# ========== 7. SAFETY ==========
story.append(Spacer(1, 18))
story.append(H('7. Seven-Layer Safety Architecture', sH1, 0))

safe_data = [
    [PH('Layer'), PH('Mechanism'), PH('Response to Failure')],
    [PC('1. Hardware'), PC('Spring-center valves, gate pull-downs, NC kill switch, TVS diodes, fuses'), PC('Actuators to neutral on power loss. Mechanical safe state with zero electronics dependency.')],
    [PC('2. Watchdog'), PC('MAX6818 external WDT (1.6s) + internal TWDT + IWDT'), PC('ESP32 hard reset if GENESIS stops kicking. Complete system restart in safe state.')],
    [PC('3. GENESIS'), PC('eFuse-protected factory code with safe-state machine'), PC('All actuators to neutral through deterministic 6-step sequence. No REFLEX code can override.')],
    [PC('4. API Contract'), PC('GENESIS validates every actuator command from REFLEX'), PC('Invalid commands silently blocked. SAFETY_VIOLATION logged. No hardware effect.')],
    [PC('5. C Fallback'), PC('200-line minimal controller in GENESIS for critical nodes'), PC('Basic safe operation continues even if REFLEX layer crashes or produces corrupt outputs.')],
    [PC('6. A/B Isolation'), PC('New artifact only on BACKUP node. Human must explicitly switch.'), PC('Failed artifact never affects PRIMARY. Human can always revert in under 500ms.')],
    [PC('7. Provenance'), PC('Hash chain of all artifact changes with human approval records'), PC('Complete audit trail for regulatory review. Tamper-evident history of all changes.')],
]
story.append(Spacer(1, 12))
story.append(tbl(safe_data, [1.5*cm, 5.5*cm, 8.0*cm]))
story.append(Paragraph('<b>Table 4.</b> Seven-Layer Safety Architecture', sCap))

# ========== 8. GLOSSARY ==========
story.append(Spacer(1, 18))
story.append(H('8. NEXUS Canonical Terminology', sH1, 0))

gloss_data = [
    [PH('Term'), PH('Definition')],
    [PC('Node'), PC('An ESP32-S3 microcontroller running NEXUS GENESIS firmware with a deployed REFLEX artifact. The fundamental unit of the reflex layer.')],
    [PC('Cortex'), PC('A Jetson Orin Nano unit running the NEXUS brain software. Serves as the collective intelligence for a group of Nodes.')],
    [PC('Artifact'), PC('A compiled binary or parameter set that defines a Node\'s REFLEX behavior. Identified by SHA-256 hash. Versioned and signed.')],
    [PC('Reflex'), PC('A deterministic real-time control loop running on a Node. Handles sensor processing, PID control, state machines. Operates at 10-100 Hz.')],
    [PC('Impulse'), PC('A command from Cortex or human to a Node. Triggers state changes, setpoint modifications, or calibration procedures.')],
    [PC('Sense'), PC('A telemetry data stream from a Node to Cortex. Carries sensor readings, actuator positions, and health status in binary encoding.')],
    [PC('Bind'), PC('A declared relationship connecting a Sense output (e.g., compass heading) to a Reflex input (e.g., autopilot error signal).')],
    [PC('Domain'), PC('The physical environment and its configuration. Defined by a JSON Manifest. Examples: vessel, farm, factory, mine.')],
    [PC('Manifest'), PC('A JSON configuration file defining a Domain: nodes, sensors, actuators, safety limits, and inter-node bindings.')],
    [PC('Genesis'), PC('The factory-default artifact burned into eFuse-protected flash. The ultimate fallback. Can never be overwritten by OTA.')],
    [PC('Evolution'), PC('The process by which the Cortex observes, hypothesizes, simulates, and proposes improvements to Node artifacts.')],
    [PC('Provenance'), PC('The complete history of artifact changes stored as a tamper-evident Merkle hash chain with human approval records.')],
    [PC('Nexus'), PC('The system as a whole: the network of Nodes, Cortex instances, their artifacts, bindings, and evolutionary history.')],
]
story.append(Spacer(1, 12))
story.append(tbl(gloss_data, [2.5*cm, 12.5*cm]))
story.append(Paragraph('<b>Table 5.</b> NEXUS Canonical Terminology', sCap))

# ========== 9. ROADMAP ==========
story.append(Spacer(1, 18))
story.append(H('9. Implementation Roadmap', sH1, 0))

road_data = [
    [PH('Phase'), PH('Timeline'), PH('Deliverables'), PH('Validation Criteria')],
    [PC('1: Marine MVP'), PCC('Wk 1-8'), PC('Single ESP32 autopilot + Jetson-Alpha. GENESIS + REFLEX layers. NEXUSLINK protocol. Dockside calibration. Iron Mike standalone.'), PC('PID hold within 3 deg. Standalone 72h test. Genesis rollback verified.')],
    [PC('2: Redundancy'), PCC('Wk 9-16'), PC('Dual-ESP32 autopilot. 3-Jetson cluster. Full vessel node network. Leader election. Artifact signing.'), PC('Failover under 100ms. All 21 failure modes tested. Cluster survives any Jetson loss.')],
    [PC('3: Evolution'), PCC('Wk 17-24'), PC('Observation pipeline. Pattern discovery. A/B testing protocol. Human approval interface. Provenance chain.'), PC('Successful parameter evolution demonstrated. A/B test cycle under 2 hours. Provenance export verified.')],
    [PC('4: Generalize'), PCC('Wk 25-36'), PC('Domain Manifest system. Cross-domain REFLEX templates. Cloud enhancement via Starlink. Multi-site artifact sharing.'), PC('Deployed to 2+ non-marine domains. Cloud training demonstrated. Regulatory audit trail accepted.')],
]
story.append(Spacer(1, 12))
story.append(tbl(road_data, [2.0*cm, 1.8*cm, 6.5*cm, 4.5*cm]))
story.append(Paragraph('<b>Table 6.</b> Four-Phase Implementation Roadmap', sCap))

story.append(P(
    'The roadmap is designed so that each phase produces a fully usable system. Phase 1 delivers a '
    'production-quality marine autopilot that exceeds ComNav/Simrad capabilities with AI voice control. '
    'Phase 2 adds the redundancy and networking that transforms it into a vessel-wide platform. Phase 3 '
    'introduces the evolutionary intelligence that makes NEXUS fundamentally different from any existing '
    'automation system. Phase 4 generalizes the framework beyond marine into the universal robotics '
    'platform it is designed to be. A single commercial fishing vessel serves as the development and '
    'validation platform throughout all four phases, ensuring the system is proven in the most demanding '
    'real-world environment before being offered for other domains.'
))

# ========== BUILD ==========
doc.multiBuild(story)
print(f"PDF generated: {OUT}")

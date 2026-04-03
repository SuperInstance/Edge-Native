#!/usr/bin/env python3
"""
Post-Coding Distributed Intelligence Platform - Annotated Developer Guide
Generates comprehensive PDF with architectural decision annotations.
"""

import os
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch, cm
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY
from reportlab.lib import colors
from reportlab.platypus import (
    Paragraph, Spacer, PageBreak, Table, TableStyle, KeepTogether
)
from reportlab.platypus.tableofcontents import TableOfContents
from reportlab.platypus import SimpleDocTemplate
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase.pdfmetrics import registerFontFamily

# ── Font Registration ──
pdfmetrics.registerFont(TTFont('Times New Roman', '/usr/share/fonts/truetype/english/Times-New-Roman.ttf'))
pdfmetrics.registerFont(TTFont('Calibri', '/usr/share/fonts/truetype/english/calibri-regular.ttf'))
pdfmetrics.registerFont(TTFont('DejaVuSans', '/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf'))
registerFontFamily('Times New Roman', normal='Times New Roman', bold='Times New Roman')
registerFontFamily('Calibri', normal='Calibri', bold='Calibri')
registerFontFamily('DejaVuSans', normal='DejaVuSans', bold='DejaVuSans')

# ── Colors ──
HDR_BG = colors.HexColor('#1F4E79')
HDR_TEXT = colors.white
ROW_ODD = colors.HexColor('#F5F5F5')
ROW_EVEN = colors.white
ACCENT = colors.HexColor('#2E75B6')
ANNOTATION_BG = colors.HexColor('#FFF3CD')
ANNOTATION_BORDER = colors.HexColor('#FFEEBA')

# ── Page dimensions ──
PAGE_W, PAGE_H = letter  # 612 x 792 pts
MARGIN = 0.75 * inch

# ── Styles ──
cover_title = ParagraphStyle('CoverTitle', fontName='Times New Roman', fontSize=36, leading=44, alignment=TA_CENTER, spaceAfter=24, textColor=colors.HexColor('#1F4E79'))
cover_sub = ParagraphStyle('CoverSub', fontName='Times New Roman', fontSize=18, leading=26, alignment=TA_CENTER, spaceAfter=12, textColor=colors.HexColor('#333333'))
cover_author = ParagraphStyle('CoverAuthor', fontName='Times New Roman', fontSize=13, leading=20, alignment=TA_CENTER, spaceAfter=8, textColor=colors.HexColor('#555555'))

h1 = ParagraphStyle('H1', fontName='Times New Roman', fontSize=22, leading=28, spaceBefore=18, spaceAfter=10, textColor=colors.HexColor('#1F4E79'))
h2 = ParagraphStyle('H2', fontName='Times New Roman', fontSize=16, leading=22, spaceBefore=14, spaceAfter=8, textColor=colors.HexColor('#2E75B6'))
h3 = ParagraphStyle('H3', fontName='Times New Roman', fontSize=13, leading=18, spaceBefore=10, spaceAfter=6, textColor=colors.HexColor('#333333'))

body = ParagraphStyle('Body', fontName='Times New Roman', fontSize=10.5, leading=16, alignment=TA_JUSTIFY, spaceAfter=6)
body_bold = ParagraphStyle('BodyBold', fontName='Times New Roman', fontSize=10.5, leading=16, alignment=TA_JUSTIFY, spaceAfter=6, textColor=colors.black)
annotation = ParagraphStyle('Annotation', fontName='Times New Roman', fontSize=9.5, leading=14, alignment=TA_LEFT, spaceAfter=4, leftIndent=18, rightIndent=12, textColor=colors.HexColor('#856404'), backColor=ANNOTATION_BG)
code_style = ParagraphStyle('Code', fontName='DejaVuSans', fontSize=8, leading=11, alignment=TA_LEFT, spaceAfter=4, leftIndent=12, textColor=colors.HexColor('#333333'))

tbl_hdr = ParagraphStyle('TblHdr', fontName='Times New Roman', fontSize=9.5, leading=13, alignment=TA_CENTER, textColor=colors.white)
tbl_cell = ParagraphStyle('TblCell', fontName='Times New Roman', fontSize=9, leading=12, alignment=TA_LEFT)
tbl_cell_c = ParagraphStyle('TblCellC', fontName='Times New Roman', fontSize=9, leading=12, alignment=TA_CENTER)
caption_s = ParagraphStyle('Caption', fontName='Times New Roman', fontSize=9, leading=12, alignment=TA_CENTER, textColor=colors.HexColor('#555555'))

toc_l0 = ParagraphStyle('TOCL0', fontName='Times New Roman', fontSize=12, leftIndent=20)
toc_l1 = ParagraphStyle('TOCL1', fontName='Times New Roman', fontSize=10, leftIndent=40)


# ── TocDocTemplate ──
class TocDocTemplate(SimpleDocTemplate):
    def afterFlowable(self, flowable):
        if hasattr(flowable, 'bookmark_name'):
            level = getattr(flowable, 'bookmark_level', 0)
            text = getattr(flowable, 'bookmark_text', '')
            self.notify('TOCEntry', (level, text, self.page))


def heading(text, style, level=0):
    p = Paragraph(f'<b>{text}</b>', style)
    p.bookmark_name = text
    p.bookmark_level = level
    p.bookmark_text = text
    return p


def para(text):
    return Paragraph(text, body)


def note(text):
    return Paragraph(f'<b>ARCHITECTURE NOTE:</b> {text}', annotation)


def make_table(headers, rows, col_widths=None):
    hdr = [Paragraph(f'<b>{h}</b>', tbl_hdr) for h in headers]
    data = [hdr]
    for row in rows:
        data.append([Paragraph(str(c), tbl_cell) for c in row])
    if col_widths is None:
        avail = PAGE_W - 2 * MARGIN - 20
        col_widths = [avail / len(headers)] * len(headers)
    t = Table(data, colWidths=col_widths)
    style_cmds = [
        ('BACKGROUND', (0, 0), (-1, 0), HDR_BG),
        ('TEXTCOLOR', (0, 0), (-1, 0), HDR_TEXT),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ]
    for i in range(1, len(data)):
        bg = ROW_ODD if i % 2 == 0 else ROW_EVEN
        style_cmds.append(('BACKGROUND', (0, i), (-1, i), bg))
    t.setStyle(TableStyle(style_cmds))
    return t


# ── Build Document ──
OUTPUT = '/home/z/my-project/download/post_coding_platform/Post_Coding_Platform_Developer_Guide.pdf'

doc = TocDocTemplate(
    OUTPUT, pagesize=letter,
    leftMargin=MARGIN, rightMargin=MARGIN,
    topMargin=MARGIN, bottomMargin=MARGIN,
    title='Post_Coding_Platform_Developer_Guide',
    author='Z.ai', creator='Z.ai',
    subject='Comprehensive annotated developer guide for the Post-Coding Distributed Intelligence Platform'
)

story = []

# ═══════════════════════════════════════════
# COVER PAGE
# ═══════════════════════════════════════════
story.append(Spacer(1, 100))
story.append(Paragraph('<b>Post-Coding Distributed</b>', cover_title))
story.append(Paragraph('<b>Intelligence Platform</b>', cover_title))
story.append(Spacer(1, 20))
story.append(Paragraph('Annotated Developer Guide', cover_sub))
story.append(Spacer(1, 10))
story.append(Paragraph('ESP32 Limbs. Jetson Brains. AI-Generated Code.', cover_sub))
story.append(Spacer(1, 50))
story.append(Paragraph('Architecture Decisions, Protocol Specifications, and', cover_author))
story.append(Paragraph('Implementation Guidance for a Universal Robotics Framework', cover_author))
story.append(Spacer(1, 60))
story.append(Paragraph('Version 1.0', cover_author))
story.append(Paragraph('March 2026', cover_author))
story.append(PageBreak())

# ═══════════════════════════════════════════
# TABLE OF CONTENTS
# ═══════════════════════════════════════════
story.append(Paragraph('<b>Table of Contents</b>', h1))
story.append(Spacer(1, 12))
toc = TableOfContents()
toc.levelStyles = [toc_l0, toc_l1]
story.append(toc)
story.append(PageBreak())

# ═══════════════════════════════════════════
# CHAPTER 1: PHILOSOPHY & VISION
# ═══════════════════════════════════════════
story.append(heading('1. Philosophy and Vision', h1, 0))

story.append(heading('1.1 The Post-Coding Premise', h2, 1))
story.append(para(
    'This platform is built on a single, radical premise: <b>the era of humans writing code for '
    'embedded systems is ending.</b> In the same way that computer-aided design replaced hand-drafted '
    'blueprints, and compilers replaced assembly language, we believe that the next generation of '
    'industrial robotics systems will be built by humans who never write a single line of code. '
    'Instead, they will describe their intent in natural language, wire physical components under '
    'AI guidance, and approve or reject system-proposed behaviors through demonstration and feedback.'
))
story.append(para(
    'The system we describe here takes this premise seriously. A human operator tells the AI chatbot '
    'running on a Jetson Orin Nano Super 8GB, "I want this ESP32 to control my throttle," and the '
    'AI handles everything else: determining what sensors and actuators are needed, guiding the human '
    'through the physical wiring process, generating the control logic, deploying it to the ESP32, '
    'and then watching the human operate the system to learn how to improve it. The human operates '
    'entirely at the level of wiring and function. They are the assembler, the teacher, and the '
    'safety officer, but never the programmer.'
))
story.append(para(
    'This is not a theoretical exercise. Every design decision in this guide has been evaluated against '
    'the constraints of real hardware: the ESP32-S3 with its 512KB SRAM and 8MB PSRAM, the Jetson '
    'Orin Nano with its 40 TOPS of AI inference, and the harsh physical environments where these '
    'systems must operate, from the salt spray of a marine deck to the vibration of a mining haul '
    'road. The architecture has been through six phases of expert review, covering embedded systems, '
    'machine learning, industrial automation, cloud infrastructure, and safety certification, with '
    'over 30 issues identified and resolved.'
))

story.append(heading('1.2 Humans as Assemblers, Not Programmers', h2, 1))
story.append(para(
    'The human role in this system is precisely defined: they are the physical integrator. They connect '
    'sensors to GPIO pins, mount actuators, run wire, and test that physical connections produce the '
    'expected electrical signals. When they want to add a new capability, they tell the AI in plain '
    'English what they want, and the AI responds with specific wiring instructions: "Connect the servo '
    'signal wire to GPIO 12, power to 5V, ground to GND. Add a 1000uF capacitor across the power '
    'pins to prevent voltage sag." The human performs the physical work and confirms completion.'
))
story.append(para(
    'After wiring, the AI takes over again: it auto-detects the connected hardware via I2C scanning '
    'and ADC probing, validates that the hardware matches expectations, generates the initial control '
    'logic, and presents it to the human for functional testing. The human says "move the rudder left" '
    'and watches it move. If it does not move correctly, the human says so, and the AI adjusts the '
    'calibration parameters and tries again. This loop continues until the human is satisfied. At '
    'no point does the human need to understand JSON schemas, PID controller theory, or C syntax. '
    'They need only understand their own domain: how a throttle works, what a heading should feel '
    'like, when a bilge pump should run.'
))
story.append(note(
    'Why this matters: Most industrial robotics projects fail not because the hardware cannot do the job, '
    'but because there are not enough skilled embedded software developers to configure, program, and '
    'maintain every node in the system. By eliminating the coding requirement, we expand the pool of '
    'people who can build and maintain these systems from "embedded C developers" to "anyone who can '
    'wire a relay and describe what they want in plain language." This is a 100x expansion in the '
    'available talent pool.'
))

story.append(heading('1.3 ESP32 as First-Class Citizens', h2, 1))
story.append(para(
    'A critical design principle of this platform is that the ESP32-S3 microcontrollers are not merely '
    'dumb I/O expanders for the Jetson. They are autonomous, intelligent agents with their own "muscle '
    'memory and reflexes." When the Jetson goes offline, when the network fails, when the Starlink '
    'dish loses its satellite, the ESP32 continues to operate using its last-known-good reflex behaviors. '
    'An autopilot ESP32 will continue holding heading. A bilge pump ESP32 will continue monitoring '
    'water levels and running the pump. A lighting ESP32 will continue its programmed scene cycle.'
))
story.append(para(
    'This is not just a nice-to-have feature; it is a fundamental architectural requirement. In marine '
    'and industrial environments, communication failures are not edge cases but expected events. Salt '
    'water corrodes connectors. Vibration loosens terminals. Starlink dishes lose satellite lock during '
    'heavy weather. The ESP32 nodes must be designed to survive and function independently for extended '
    'periods, because the alternative, which is that a bilge pump fails because the WiFi dropped, is '
    'not acceptable in any safety-critical application.'
))
story.append(note(
    'Architecture Decision: The ESP32 runs a fixed, compiled C firmware (the "runtime") that is never '
    'modified by AI. AI generates only the reflex configuration (JSON state machines and optional C '
    'extension modules) that the runtime interprets. This separation between trusted runtime and '
    'AI-generated behavior is the security foundation of the entire system. The runtime validates all '
    'AI-generated inputs, enforces safety constraints, and provides deterministic execution guarantees '
    'regardless of what the AI produces.'
))

story.append(heading('1.4 Jetson as System Improvers', h2, 1))
story.append(para(
    'The Jetson Orin Nano Super 8GB serves a fundamentally different role than the ESP32. While the '
    'ESP32 executes fast, deterministic reflex loops at 100Hz to 1kHz, the Jetson operates on a '
    'slower but deeper timescale: observing patterns, discovering correlations, and proposing '
    'improvements to the ESP32 reflex behaviors. The Jetson is the "system improver," not the '
    '"system operator." It does not drive the throttle in real time; the ESP32 does that. Instead, '
    'the Jetson watches how the human drives, discovers that the human always adds 200 RPM before '
    'turning into the wind, and proposes a reflex rule that automates this behavior.'
))
story.append(para(
    'This distinction is critical. If the Jetson were the real-time controller, any Jetson failure '
    '(memory pressure, thermal throttling, OS update, kernel panic) would immediately affect system '
    'operation. By keeping the Jetson in the "improver" role, its failure only means that the system '
    'stops getting better, not that the system stops working. The ESP32 reflexes continue running at '
    'their proven, validated behaviors until the Jetson comes back online and picks up where it left off.'
))
story.append(para(
    'The system supports multiple Jetson units operating in parallel, each dedicated to a specific '
    'cognitive function. One Jetson might run the chatbot interface and STT/TTS (speech-to-text, '
    'text-to-speech). Another might run computer vision models for fish species identification or '
    'collision avoidance. A third might run the learning and optimization pipeline, analyzing days '
    'of observation data to discover patterns and propose new reflex rules. This horizontal scaling '
    'means that adding more intelligence to the system is as simple as plugging in another Jetson, '
    'configuring its role, and letting it join the cluster.'
))
story.append(note(
    'Architecture Decision: The Jetson cluster communicates via gRPC for low-latency inter-node calls '
    'and MQTT for pub/sub telemetry. Redis provides shared state and message queuing. This combination '
    'was chosen over alternatives like raw TCP sockets (too low-level) or REST APIs (too much overhead) '
    'because gRPC provides strong typing and code generation, while MQTT provides the lightweight '
    'pub/sub pattern that the telemetry system needs. Redis was chosen over RabbitMQ because Redis is '
    'already used for caching observation data, and having a single in-memory data store reduces '
    'operational complexity.'
))

# ═══════════════════════════════════════════
# CHAPTER 2: SYSTEM ARCHITECTURE
# ═══════════════════════════════════════════
story.append(heading('2. System Architecture', h1, 0))

story.append(heading('2.1 Hardware Topology', h2, 1))
story.append(para(
    'The hardware architecture follows a three-tier model that maps naturally to the three types of '
    'computation the system needs: reflex (fast, deterministic, local), cognitive (slower, complex, '
    'centralized), and cloud (slowest, most capable, remote). The physical topology reflects this '
    'layering with clear boundaries and defined interfaces between each tier.'
))
story.append(para(
    '<b>Tier 1: ESP32 Nodes (Reflex Layer)</b> - These are the "limbs" of the system. Each ESP32-S3 '
    'connects directly to sensors and actuators via GPIO, ADC, PWM, I2C, SPI, UART, or RS-485. '
    'Multiple ESP32s are distributed throughout the platform: one for the autopilot, one for the '
    'throttle, one for lighting, one for the bilge system, one for the engine room sensors, and so '
    'on. Each ESP32 communicates with the Jetson via a dedicated RS-422 serial link at 921,600 baud '
    '(downgrading to 115,200 baud for runs over 50 meters). The RS-422 standard provides full-duplex '
    'communication with excellent noise immunity, making it suitable for the electrically harsh '
    'environments found on boats, in factories, and in agricultural settings.'
))
story.append(para(
    '<b>Tier 2: Jetson Cluster (Cognitive Layer)</b> - One or more NVIDIA Jetson Orin Nano Super 8GB '
    'units serve as the brain cluster. Each Jetson connects to multiple ESP32s via USB-to-RS-422 '
    'adapters or built-in serial ports. The Jetsons run Docker containers for isolation, communicate '
    'with each other via Ethernet, and connect to the internet via Starlink for cloud access. The '
    'Orin Nano Super variant provides 40 TOPS of INT8 inference performance, enabling it to run '
    'speech recognition (Whisper-small.en), vision models (YOLOv8-nano), and a local code generation '
    'model (Qwen2.5-Coder-7B at Q4 quantization, approximately 12 tokens per second) simultaneously.'
))
story.append(para(
    '<b>Tier 3: Cloud (Heavy Reasoning Layer)</b> - For tasks that exceed the Jetson\'s capabilities, '
    'such as complex firmware generation, large-scale simulation, and model training, the system '
    'offloads to cloud LLMs (Claude 3.5 Sonnet, GPT-4o) via Starlink. Cloud calls are made '
    'asynchronously and results are queued for delivery when bandwidth allows. The system is designed '
    'to operate indefinitely without cloud access; the cloud is an enhancement that makes the system '
    'better faster, not a dependency that makes the system work at all.'
))

story.append(Spacer(1, 18))
t = make_table(
    ['Tier', 'Hardware', 'Function', 'Latency', 'Failure Impact'],
    [
        ['Reflex', 'ESP32-S3', 'Real-time sensor/actuator loops', '< 1ms', 'Subsystem fails locally'],
        ['Cognitive', 'Jetson Orin Nano', 'Pattern discovery, learning, UI', '100ms - 5s', 'System stops improving'],
        ['Cloud', 'Remote LLM APIs', 'Code generation, simulation, training', '1-30s', 'Slower improvement cycle'],
    ],
    [1.0*inch, 1.3*inch, 2.2*inch, 0.9*inch, 1.5*inch]
)
story.append(t)
story.append(Spacer(1, 4))
story.append(Paragraph('<b>Table 1.</b> Three-Tier Architecture Comparison', caption_s))
story.append(Spacer(1, 18))

story.append(heading('2.2 The Universal Firmware Decision', h2, 1))
story.append(para(
    'Perhaps the most consequential architectural decision in this platform is the choice to run a '
    '<b>single, identical firmware binary</b> on every ESP32, regardless of its role. Every ESP32-S3 '
    'in the system runs the exact same ~320KB firmware image. The role that any particular ESP32 '
    'plays (autopilot, throttle controller, lighting system, bilge pump monitor) is determined '
    'entirely by the JSON configuration that the Jetson sends to it at boot time. This configuration '
    'declares which pins are used, what sensors are connected, what reflex behaviors should run, and '
    'what safety parameters apply.'
))
story.append(para(
    'The alternative approach, which is the conventional one, is to compile a separate firmware image '
    'for each role. The autopilot gets its own firmware, the throttle gets its own firmware, the '
    'lighting system gets its own firmware, and so on. This approach seems natural but creates '
    'significant operational problems. First, it multiplies the testing surface: every firmware must '
    'be individually tested, validated, and signed. Second, it complicates provisioning: when a human '
    'replaces a failed ESP32, they need to know which firmware to flash onto the replacement unit. '
    'Third, it prevents dynamic role reassignment: if you want to temporarily repurpose a lighting '
    'controller as an extra sensor hub, you cannot do so without recompiling and reflashing.'
))
story.append(note(
    'Architecture Decision: Universal firmware was chosen over per-role firmware because it reduces '
    'the number of firmware binaries that must be maintained and tested from N (one per role) to 1. '
    'The cost of this decision is a slightly larger firmware binary (~320KB vs ~150KB for a minimal '
    'per-role firmware), but this is negligible on the ESP32-S3 with its 4MB or larger flash. The '
    'runtime I/O abstraction adds approximately 40KB of code, the reflex engine adds approximately '
    '25KB, and the serial protocol adds approximately 15KB. These costs are fixed and do not '
    'increase with the number of supported roles.'
))

story.append(heading('2.3 Serial Protocol: COBS Framing', h2, 1))
story.append(para(
    'All communication between Jetson and ESP32 uses a binary protocol with Consistent Overhead Byte '
    'Stuffing (COBS) framing and CRC-16 validation. The protocol operates over RS-422 serial links '
    'at 921,600 baud by default (with automatic fallback to 115,200 baud for long cable runs). '
    'Each message consists of a 6-byte header (message type, length, sequence number, CRC), a '
    'variable-length JSON payload, and a 0x00 COBS delimiter byte.'
))
story.append(para(
    'The choice of COBS framing over the more common approach of newline-delimited JSON deserves '
    'explanation. Newline-delimited JSON works well for simple telemetry streams where every message '
    'is a self-contained JSON object, but it breaks down when binary payloads are needed, such as '
    'transferring observation buffer dumps (compressed binary frames) or firmware update chunks. '
    'COBS provides a clean delimiter mechanism that works for both text and binary data without '
    'requiring any escaping or encoding of the payload. The framing overhead is exactly 1 byte per '
    '255 bytes of payload (0.4%), which is negligible.'
))
story.append(note(
    'Architecture Decision: COBS was chosen over alternative framing schemes (SLIP, HDLC-like, '
    'length-prefixed) because COBS is byte-aligned (no bit-level processing needed), has bounded and '
    'predictable overhead (at most 1 extra byte per 254 payload bytes), and has well-tested open '
    'source implementations available in both C (for ESP32) and Python (for Jetson). SLIP was '
    'considered but rejected because it uses 0xC0 as both start and end delimiter, which can cause '
    'framing ambiguity if the transmitter crashes mid-message. HDLC was rejected as over-engineered '
    'for this application; its CRC-32 and bit-stuffing add complexity without meaningful benefit over '
    'COBS + CRC-16 for point-to-point serial links.'
))

story.append(heading('2.4 Memory Budget', h2, 1))
story.append(para(
    'The ESP32-S3 has two memory regions: 512KB of on-chip SRAM (fast, 240MHz bus) and up to 8MB '
    'of external PSRAM (slower, 80MHz bus via octal SPI). The firmware carefully partitions both '
    'regions to ensure deterministic behavior. No dynamic memory allocation (malloc/free) is permitted '
    'in the reflex execution path, as heap fragmentation is the number one cause of hard-to-debug '
    'crashes in long-running embedded systems.'
))

story.append(Spacer(1, 18))
t = make_table(
    ['Component', 'SRAM', 'PSRAM', 'Notes'],
    [
        ['FreeRTOS kernel + tasks', '32 KB', '-', '6 tasks at default stack sizes'],
        ['I/O abstraction layer', '24 KB', '-', 'Pin configs, driver state'],
        ['Reflex engine (bytecode VM)', '16 KB', '-', 'VM stack, opcode dispatch'],
        ['Serial protocol + COBS', '8 KB', '-', 'RX/TX buffers, CRC state'],
        ['JSON parser (jsmn)', '4 KB', '-', 'Zero-allocation token parser'],
        ['Safety monitor', '4 KB', '-', 'Watchdog, kill-switch ISR'],
        ['Observation buffer', '-', '5.5 MB', '180K frames at 32 bytes each'],
        ['Reflex storage (LittleFS)', '-', '1.0 MB', 'JSON reflex configs + bytecode'],
        ['Telemetry ring buffer', '-', '0.5 MB', 'Streaming buffer for Jetson queries'],
        ['Free (SRAM)', '~424 KB', '-', 'Stack, heap for non-critical paths'],
        ['Free (PSRAM)', '~1.0 MB', '-', 'Growth room for future features'],
    ],
    [1.8*inch, 0.8*inch, 0.8*inch, 3.5*inch]
)
story.append(t)
story.append(Spacer(1, 4))
story.append(Paragraph('<b>Table 2.</b> ESP32-S3 Memory Budget Breakdown', caption_s))
story.append(Spacer(1, 18))

story.append(note(
    'Architecture Decision: The observation buffer was placed in PSRAM rather than SRAM because a '
    '5.5MB buffer would consume the entire SRAM, leaving no room for the runtime. PSRAM access at '
    '80MHz octal SPI is approximately 320 MB/s, which is more than sufficient for writing 32-byte '
    'frames at 100Hz (3.2 KB/s). The 424KB of free SRAM provides generous headroom for worst-case '
    'stack usage and temporary allocations during configuration parsing, which is the only operation '
    'permitted to use the heap.'
))

# ═══════════════════════════════════════════
# CHAPTER 3: THE ESP32 UNIVERSAL LIMB
# ═══════════════════════════════════════════
story.append(heading('3. The ESP32 Universal Limb', h1, 0))

story.append(heading('3.1 One Firmware, Infinite Roles', h2, 1))
story.append(para(
    'The universal firmware implements five subsystems that together enable any ESP32-S3 to become '
    'any type of controller or sensor hub. The <b>I/O Abstraction Layer</b> configures GPIO pins, '
    'ADC channels, PWM outputs, I2C buses, SPI buses, and UART ports purely through JSON configuration '
    'received from the Jetson. The <b>Reflex Engine</b> executes deterministic control loops defined '
    'as JSON state machines, compiled to bytecode for performance. The <b>Observation Buffer</b> '
    'continuously records sensor readings and actuator commands into a PSRAM-backed ring buffer for '
    'later analysis. The <b>Provisioning Protocol</b> handles the boot-time identity announcement '
    'and role assignment handshake. The <b>Safety Monitor</b> implements hardware-enforced watchdog, '
    'kill-switch detection, and failsafe behaviors that operate independently of all other subsystems.'
))
story.append(para(
    'The boot sequence is designed to be as safe as possible. Within the first microsecond of power-on, '
    'before any software initializes, all GPIO pins are set to their safe states (outputs LOW, inputs '
    'with pull-ups disabled). This ensures that even if the firmware crashes during boot, the physical '
    'actuators connected to the ESP32 are in their safest possible positions. After the safe-state '
    'initialization, the firmware reads NVS (Non-Volatile Storage) for a cached role configuration. '
    'If a valid cached configuration exists, the ESP32 loads it immediately and begins operating on '
    'its last-known-good reflexes, even before communicating with the Jetson. This means that an '
    'ESP32 that reboots during operation (due to a power glitch, for example) will resume its reflex '
    'behavior within approximately 200 milliseconds, without waiting for the Jetson to respond.'
))

story.append(heading('3.2 I/O Abstraction Layer', h2, 1))
story.append(para(
    'The I/O abstraction layer is the mechanism by which a single firmware can control any combination '
    'of sensors and actuators. When the Jetson sends a role assignment to an ESP32, the configuration '
    'JSON includes a "pins" array that declares every peripheral attached to the ESP32. Each pin '
    'declaration specifies the pin number, the peripheral type (pwm_out, adc_in, digital_out, '
    'i2c_device, uart, etc.), and type-specific parameters such as PWM frequency, ADC attenuation, '
    'or I2C device address.'
))
story.append(para(
    'Before applying any configuration, the firmware validates it against a compile-time pin capability '
    'database. The ESP32-S3 has 45 physical GPIOs, but not all pins support all functions. GPIOs 26 '
    'through 32 are consumed by the Quad SPI flash interface and are input-only. GPIOs 33 through 37 '
    'are consumed by PSRAM and are also input-only. Strapping pins (0, 3, 8, 45, 46) have special '
    'boot-time behavior and require careful handling. The firmware rejects any configuration that '
    'attempts to use a pin for a function it does not support, such as requesting PWM output on an '
    'input-only pin, or requesting more than 8 PWM outputs (the ESP32-S3 LEDC hardware limit).'
))
story.append(para(
    'The I/O driver catalog includes pre-written drivers for common industrial components, instantiated '
    'purely through JSON configuration. For I2C devices, the firmware includes a driver registry with '
    'support for the HMC5883L/IST8310 compass, MPU6050/ICM20948 IMU, VL53L0X time-of-flight sensor, '
    'BME280 environmental sensor, INA219 power monitor, AS5600 magnetic encoder, and PCA9685 PWM '
    'expander. Each driver is registered with an initialization function, a read function, a self-test '
    'function, and a data schema that describes the telemetry format. Adding a new I2C driver requires '
    'a firmware update, but this is rare; the existing catalog covers the vast majority of common '
    'sensors used in marine, agricultural, and industrial applications.'
))

story.append(heading('3.3 Reflex Engine: Bytecode vs. JSON Interpretation', h2, 1))
story.append(para(
    'This is one of the most technically consequential design decisions in the entire platform. The '
    'question is: how should the ESP32 execute the reflex behaviors that the AI generates? There are '
    'two obvious options. The first is to have the ESP32 interpret JSON directly: the AI generates a '
    'JSON state machine, the ESP32 parses it with jsmn (a zero-allocation JSON token parser), and '
    'executes the corresponding actions on each tick. The second is to compile the JSON to bytecode '
    'at load time and execute the bytecode on a lightweight virtual machine.'
))
story.append(para(
    'JSON interpretation seems simpler and more transparent, and for reflex behaviors that run at 1Hz '
    'or 10Hz, it would work fine. The problem is that many reflex behaviors need to run at 100Hz or '
    'even 1kHz, and JSON parsing at those rates is too slow. Benchmarks show that parsing a typical '
    'reflex JSON (approximately 500 bytes) with jsmn takes approximately 0.5-2ms per cycle. At 1kHz, '
    'that leaves only 0-0.5ms for actual computation, which is not enough for PID control with '
    'anti-windup, state machine evaluation, and sensor filtering. By compiling the JSON to bytecode '
    'at load time (a one-time cost of approximately 10ms), the per-cycle execution cost drops to '
    'less than 100 microseconds, leaving 900 microseconds for computation at 1kHz.'
))
story.append(note(
    'Architecture Decision: Bytecode VM was chosen over direct JSON interpretation because it provides '
    'deterministic, bounded execution time regardless of JSON complexity. The VM has approximately 20 '
    'opcodes (PUSH, POP, ADD, SUB, MUL, DIV, COMPARE, READ_SENSOR, WRITE_ACTUATOR, JUMP, '
    'JUMP_IF_FALSE, CALL, RET, PID_COMPUTE, SET_STATE, GET_STATE, RECORD, LOG), each of which '
    'executes in 1-5 clock cycles on the ESP32-S3 at 240MHz. This determinism is essential for '
    'safety-critical systems where worst-case execution time must be known and guaranteed. The JSON '
    'reflex definitions are preserved as the human-readable source of truth; the bytecode is a '
    'compiled artifact that can be regenerated from JSON at any time.'
))

story.append(heading('3.4 Reflex Definition Format', h2, 1))
story.append(para(
    'Reflex behaviors are defined in JSON using a schema designed for both human readability and '
    'machine validation. Each reflex definition includes four sections: inputs (what sensors it reads), '
    'outputs (what actuators it controls), states (a named state machine with transitions), and '
    'selftest (a sequence of validation steps that run before the reflex is activated). Reflex '
    'definitions also carry metadata including a version number, priority (0 = kill-switch, 4 = '
    'background task), provenance (what human demonstration or AI inference created it), and resource '
    'budget declarations (maximum CPU time per cycle, maximum memory usage).'
))
story.append(para(
    'The state machine model was chosen over alternative representations like pure trigger-action '
    'rules or behavior trees because state machines provide the right balance of expressiveness and '
    'verifiability. A state machine with named states and explicit transitions can be visually '
    'inspected, formally verified for deadlock and reachability, and explained to a human operator '
    '("the system is in the CORRECTING state because the heading error exceeded 2 degrees"). Behavior '
    'trees offer more compositional flexibility but are harder to visualize in JSON and do not map '
    'naturally to the bytecode VM\'s execution model. Pure trigger-action rules are too limited for '
    'complex behaviors like the wind-compensated throttle example, which requires multi-step ramping '
    'with timing constraints and proportional modifiers.'
))

story.append(heading('3.5 Observation Buffer', h2, 1))
story.append(para(
    'The observation buffer is the mechanism by which the ESP32 records sensor and actuator data for '
    'the learning pipeline. It is a circular (ring) buffer stored in PSRAM that continuously records '
    'timestamped snapshots of all sensor readings and actuator commands. Each frame is 32 bytes in a '
    'compressed format using float16 delta encoding: only the changes from the previous frame are '
    'stored, rather than absolute values. This compression provides approximately 3x space savings '
    'compared to storing raw float32 values, allowing the buffer to hold approximately 180,000 '
    'frames, or about 31 minutes of data at the 100Hz tick rate.'
))
story.append(para(
    'The buffer operates in four recording modes. <b>Command-record mode</b> starts and stops on '
    'explicit Jetson commands, used when the human says "watch me do this." <b>Event-triggered mode</b> '
    'captures a window of frames around a specific event, such as an anomaly detection or a human '
    'override. <b>Circular always-on mode</b> continuously records and overwrites the oldest data, '
    'providing a rolling window of recent activity for on-demand analysis. <b>Heartbeat-synced mode</b> '
    'records one frame per Jetson heartbeat (typically every 500ms) for long-term trend monitoring.'
))
story.append(para(
    'When the Jetson requests observation data, the ESP32 dumps the buffer over serial in 512-byte '
    'chunks using COBS framing. At 921,600 baud, the effective throughput after framing overhead is '
    'approximately 80 KB/s, so a full buffer dump of 5.5MB takes approximately 70 seconds. This is '
    'acceptable because observation data is transferred asynchronously and does not block reflex '
    'execution. The ESP32 continues running its reflex loops at full speed while the dump proceeds.'
))

story.append(heading('3.6 Safety Architecture', h2, 1))
story.append(para(
    'Safety is implemented in three independent layers that provide defense in depth. The <b>hardware '
    'layer</b> consists of the physical NC (normally-closed) kill switch wired to a dedicated GPIO with '
    'interrupt service routine (ISR) priority, an external hardware watchdog timer that resets the '
    'ESP32 if the software watchdog fails to trigger within 1 second, overcurrent fuses and breakers '
    'on all power rails, and optoisolation on critical output channels to prevent ground loops and '
    'voltage spikes from propagating to the ESP32. The <b>firmware layer</b> consists of the safety '
    'monitor task, which runs at 200Hz as a FreeRTOS task with elevated priority, checks the kill '
    'switch state every cycle, monitors heartbeat from the Jetson, validates that all actuator '
    'outputs are within their configured safe ranges, and triggers failsafe behaviors if any safety '
    'condition is violated. The <b>reflex layer</b> consists of safety-critical reflex behaviors that '
    'run at the highest priority level (priority 0), including immediate actuator shutdown on kill '
    'switch activation and overcurrent protection.'
))
story.append(note(
    'Architecture Decision: The kill switch is implemented as a physical NC contact wired to a GPIO '
    'pin AND a hardware relay that cuts actuator power, rather than as a software-only mechanism, '
    'because software can crash. Even if the ESP32 firmware enters an infinite loop or the SRAM '
    'becomes corrupted, the physical NC contact will pull the GPIO low, triggering the hardware ISR, '
    'and the relay will cut power to all actuators. This is the "ultimate hardware failsafe" that '
    'cannot be bypassed by any software bug, including bugs in the safety monitor itself. The relay '
    'is powered by the same power supply as the actuators, so if the actuator power supply fails, '
    'the relay opens and actuators de-energize. This is fail-safe by physical construction.'
))

story.append(heading('3.7 OTA with Dual-Bank', h2, 1))
story.append(para(
    'The ESP32 flash is partitioned into four regions: a factory partition containing the fixed '
    'runtime (never modified by OTA), two OTA slots (ota_0 and ota_1) for AI-generated C extension '
    'modules and firmware updates, and a data partition containing LittleFS for reflex JSON storage '
    'and telemetry logs. The dual-bank OTA mechanism means that when a new firmware or extension '
    'module is deployed, it is written to the inactive OTA slot while the current slot continues '
    'running. Only after the new image passes its self-test sequence does the bootloader switch to '
    'it. If the self-test fails, the bootloader reverts to the previous slot, providing instant '
    'rollback without any Jetson involvement.'
))
story.append(para(
    'For reflex-only updates (which are the most common type of update and do not require firmware '
    'changes), the system uses LittleFS\'s atomic write mechanism. The new reflex JSON is written '
    'to a temporary file, validated, and then atomically renamed to replace the old reflex file. '
    'If the ESP32 reboots during the write, LittleFS\'s journaling ensures that either the old '
    'version or the new version is intact, never a corrupted partial write. Reflex updates are '
    'therefore safe to perform at any time, even while the reflex is actively running.'
))

# ═══════════════════════════════════════════
# CHAPTER 4: CONVERSATIONAL SETUP FLOW
# ═══════════════════════════════════════════
story.append(heading('4. The Conversational Hardware Setup Flow', h1, 0))

story.append(heading('4.1 Adding New Equipment', h2, 1))
story.append(para(
    'The setup flow is designed to be the primary interface between the human operator and the system. '
    'When a human wants to add new equipment, they initiate a conversation with the AI chatbot '
    'running on the Jetson. The conversation follows a structured but natural flow that has been '
    'designed to accommodate operators with no technical background in electronics or programming.'
))
story.append(para(
    'The flow begins with the human stating their intent: "I want to add a bilge pump to the system." '
    'The AI classifies this intent (new equipment addition), identifies what hardware is needed '
    '(a relay or MOSFET to switch the pump, a water level sensor, wiring, and connectors), and '
    'asks clarifying questions: "Is the pump 12V or 24V? How much current does it draw? Do you '
    'have a float switch or a conductive water sensor?" Based on the answers, the AI generates a '
    'step-by-step wiring guide with specific pin assignments: "Connect the pump positive wire to '
    'the relay COM terminal. Connect the relay NO terminal to the 12V bus. Connect the relay coil '
    'to GPIO 5 (signal) and GND. Connect the water sensor signal to GPIO 34 (ADC)."'
))
story.append(para(
    'After the human completes the wiring and confirms, the system enters the auto-detection phase. '
    'The ESP32 runs an I2C bus scan on all configured I2C ports (scanning addresses 0x08 through '
    '0x77), reads ADC values to detect connected analog sensors, and checks for PWM input signals '
    'to detect servo feedback or throttle position sensors. The results are compared against the '
    'expected configuration, and any discrepancies are flagged: "Expected compass at I2C address '
    '0x1E, found nothing. Expected temperature sensor at ADC1_CH3, reading 2.8V (within range). '
    'Check the compass wiring."'
))

story.append(heading('4.2 Auto-Detection and Validation', h2, 1))
story.append(para(
    'The auto-detection system uses a combination of active probing and passive measurement to '
    'identify connected hardware. For I2C devices, the ESP32 performs a bus scan by sending start '
    'conditions and address bytes to each of the 120 possible 7-bit I2C addresses. Devices that '
    'respond with an ACK are logged with their address. The I2C driver registry is then consulted '
    'to determine which driver can handle the detected device. For ADC inputs, the ESP32 takes '
    'multiple samples (64 by default) and computes the mean and standard deviation. A sensor that '
    'is stuck at 0V or 3.3V (the ADC rails) is flagged as likely disconnected, while a sensor '
    'with reasonable variance is flagged as likely connected. For PWM inputs, the ESP32 measures '
    'pulse width using the PCNT (pulse counter) peripheral to determine the servo or ESC signal range.'
))
story.append(para(
    'After auto-detection, the system runs a self-test sequence for each detected peripheral. For '
    'a PWM output (servo), the self-test sweeps the servo through its range (center, left, center, '
    'right, center) and verifies that the servo moves. For an I2C device, the self-test reads a '
    'known register (such as the WHO_AM_I register on an IMU) and verifies the expected value. '
    'For a relay, the self-test activates the relay for 100ms and verifies that the expected '
    'electrical change occurs (this may require a feedback signal from the load). The self-test '
    'results are reported back to the Jetson and displayed to the human operator.'
))

story.append(heading('4.3 The Learning-by-Demonstration Loop', h2, 1))
story.append(para(
    'Once the hardware is connected and validated, the human begins the process of teaching the '
    'system how to operate the new equipment. This is where the system\'s learning-from-demonstration '
    'capabilities come into play. The human tells the Jetson: "Watch me drive the boat for a while." '
    'The Jetson instructs the relevant ESP32s to start recording their observation buffers. As the '
    'human operates the throttle, steering, and other controls, every sensor reading and actuator '
    'command is timestamped and stored.'
))
story.append(para(
    'The human can also narrate their actions: "I always throttle up 200 RPM before turning into the '
    'wind to maintain trolling speed." This narration is captured by a deck-mounted microphone, '
    'transcribed in real-time by Whisper-small.en running on the Jetson (with TensorRT INT8 '
    'quantization for approximately 3x real-time transcription speed), and parsed by a local '
    'LLM (Qwen2.5-Coder-7B) that extracts structured policy rules from the natural language. '
    'The extracted rules are then validated against the recorded telemetry: the system checks '
    'whether the human\'s stated behavior ("throttle up before turning into the wind") actually '
    'matches what the telemetry shows ("in 23 out of 26 turns into the wind, the human increased '
    'RPM by 180-220 approximately 5 seconds before the turn").'
))
story.append(para(
    'This combination of stated intent (narration) and observed behavior (telemetry) creates a rich '
    'training signal that is much more informative than either alone. The narration provides the '
    '"why" (intent, goal, reasoning) while the telemetry provides the "what" (actual sensor readings '
    'and control inputs). When they agree, confidence in the learned rule is high. When they disagree, '
    'the system initiates a clarification dialogue: "Captain, you said you always throttle up 200 RPM, '
    'but in 3 of the last 26 turns you added 350 RPM. Was that because the wind was gusting over '
    '20 knots?" This iterative clarification continues until the system has a rule that matches both '
    'what the human says they do and what they actually do.'
))

# ═══════════════════════════════════════════
# CHAPTER 5: THE LEARNING LOOP
# ═══════════════════════════════════════════
story.append(heading('5. The Learning Loop', h1, 0))

story.append(heading('5.1 Multi-Modal Observation Pipeline', h2, 1))
story.append(para(
    'The observation pipeline fuses three data streams into a unified timeline. The <b>ESP32 telemetry '
    'stream</b> provides high-frequency sensor data (IMU at 100Hz, GPS at 10Hz, wind at 20Hz, engine '
    'RPM at 50Hz) as 104-byte frames timestamped to microsecond precision using the ESP32\'s 64-bit '
    'timer, which is disciplined to GPS PPS (pulse-per-second) via SNTP synchronization every 5 '
    'minutes, achieving an accuracy of approximately plus or minus 5 milliseconds. The <b>Jetson vision '
    'stream</b> provides contextual information from a deck-mounted camera running at 15fps, processed '
    'by MediaPipe Hands (for detecting when the human is touching the throttle or steering) and '
    'YOLOv8-nano (for environmental context such as sea state estimation and nearby vessel detection). '
    'The <b>Jetson audio stream</b> provides the human\'s narration, captured by a waterproof MEMS '
    'microphone and transcribed by Whisper-small.en with word-level timestamps.'
))
story.append(para(
    'All three streams are aligned to a common timeline using GPS PPS as the time reference. The '
    'combined worst-case alignment accuracy is approximately plus or minus 8 milliseconds, which is '
    'sufficient for correlating human actions with narration at speech timescales. The aligned '
    'observations are merged into UnifiedObservation records at 10Hz and stored in a Parquet-format '
    'time-series database on the Jetson\'s NVMe SSD. At 10Hz, each observation record is approximately '
    '2KB, producing approximately 72MB per hour of raw data, which compresses to approximately 15MB '
    'per hour in Parquet with column pruning. A 500GB NVMe SSD holds approximately 3 years of '
    'continuous operation data.'
))

story.append(heading('5.2 Pattern Discovery Engine', h2, 1))
story.append(para(
    'The pattern discovery engine operates on accumulated observation data to find behaviors that the '
    'human exhibits but may not be consciously aware of. While the narrative pipeline captures what '
    'the human says they do, the pattern discovery engine captures what they actually do, including '
    'unconscious habits and compensations that even experienced operators may not articulate. The '
    'engine uses three complementary analysis techniques.'
))
story.append(para(
    '<b>Cross-correlation analysis</b> computes the correlation between all control inputs (throttle, '
    'rudder) and environmental state variables (wind, sea state, heading error) across multiple time '
    'lags from minus 30 seconds to plus 30 seconds. When a significant correlation is found at a '
    'specific lag, it indicates that the human\'s action leads (or follows) an environmental change '
    'by that amount of time. For example, a correlation of 0.72 between RPM change and wind shift '
    'at a lag of minus 5.2 seconds indicates that the human increases RPM approximately 5 seconds '
    'before the wind shift reaches the bow, suggesting predictive behavior based on visual cues or '
    'experience that the telemetry sensors do not directly capture.'
))
story.append(para(
    '<b>Change-point detection</b> identifies moments when the human\'s control behavior shifts '
    'significantly, such as switching from gentle cruising to aggressive maneuvering. These change '
    'points are then analyzed to determine what environmental conditions triggered the behavioral '
    'shift. <b>Bayesian policy inference</b>, inspired by inverse reinforcement learning (IRL), models '
    'the human as optimizing a latent reward function with weighted features such as speed comfort, '
    'heading accuracy, fuel efficiency, smoothness, safety margin, and wind compensation. The weight '
    'vector that best explains the observed behavior is found via Maximum a Posteriori (MAP) inference, '
    'providing an interpretable representation of the human\'s priorities: a high weight on wind '
    'compensation means the human prioritizes maintaining speed in varying wind conditions.'
))

story.append(heading('5.3 A/B Testing Framework', h2, 1))
story.append(para(
    'When the learning pipeline generates a new or improved reflex rule, it must be validated before '
    'deployment. The A/B testing framework provides a structured methodology for comparing the old '
    'and new behaviors in the real world, with the human operator as the final judge. The framework '
    'uses an alternating-leg design: on even-numbered trip legs, the system runs the old behavior '
    '(condition A), and on odd-numbered legs, it runs the new behavior (condition B). This design '
    'controls for environmental variability (wind, sea state, traffic) by ensuring that both '
    'conditions are tested in similar conditions.'
))
story.append(para(
    'Seven standardized metrics are collected during each test leg: fuel efficiency (distance per '
    'unit of fuel), speed consistency (variance from target speed), heading accuracy (mean absolute '
    'error from commanded heading), ride comfort (IMU-derived heave and roll acceleration RMS), '
    'human override frequency (number of times the human took control), response latency (time from '
    'trigger event to actuator response), and actuator wear (total actuator travel distance, a proxy '
    'for mechanical wear). The results are analyzed using a paired t-test with Cohen\'s d effect '
    'size to determine statistical significance. The new behavior must show statistically significant '
    'improvement (p less than 0.05) in at least one metric without significant degradation in any '
    'safety-critical metric to be considered for permanent adoption.'
))
story.append(para(
    'The human operator provides qualitative feedback through a simple interface: after each A/B pair '
    'of legs, the system asks "Which felt better: the first leg or the second leg?" The human can '
    'respond via voice ("the second one was too aggressive"), dashboard button, or chat command. If '
    'the human prefers the old behavior, the new reflex is rejected and the learning pipeline is '
    'notified to try again with different parameters or after gathering more observation data. If '
    'the new behavior causes more than 3 human overrides in a 10-minute period, the system '
    'automatically reverts to the old behavior and flags the reflex as "needs revision."'
))

story.append(heading('5.4 Reflex Code Synthesis', h2, 1))
story.append(para(
    'The synthesis pipeline transforms validated hypotheses into ESP32-deployable reflex code through '
    'a multi-stage process. The first stage is a feasibility check: can this behavior run on an ESP32 '
    'given its memory and CPU constraints, and is it safe to automate? The second stage is '
    'representation selection: simple behaviors (threshold alarms, on/off control, basic sequences) '
    'are expressed as JSON state machines, while complex behaviors (non-linear control, multi-variable '
    'optimization, signal processing) require AI-generated C extension modules that are compiled by '
    'the ESP-IDF cross-compiler on the Jetson and deployed as OTA firmware updates.'
))
story.append(para(
    'Approximately 80% of reflex behaviors can be expressed as JSON state machines, which is the '
    'strongly preferred format because JSON reflexes are safer (validated by schema), transparent '
    '(human-readable), and easier to iterate on (no compilation needed). The remaining 20% that '
    'require C extensions go through a more rigorous pipeline: the cloud LLM generates the C code, '
    'which is then validated by static analysis (MISRA-C subset with cppcheck and clang-tidy), memory '
    'budget verification (zero heap allocation in the reflex path, stack usage under 4KB per function, '
    'total static allocation under 8KB per module), safety constraint verification (a separate LLM '
    'call, not the same model that generated the code, reviews against the safety policy), simulation '
    'against recorded telemetry data, and automated test generation.'
))
story.append(note(
    'Architecture Decision: A separate LLM call for safety validation (not the same model that '
    'generated the code) was chosen to prevent self-validation bias. When the same model both generates '
    'and validates code, it tends to approve its own work even when flaws exist, because the '
    'validation context includes the reasoning that led to the flawed design. Using a different model '
    '(or at minimum, a different conversation context) for validation forces a fresh perspective that '
    'is more likely to catch logic errors, missed edge cases, and safety violations. This separation '
    'adds approximately $0.01-0.03 per validation call in cloud costs, which is negligible compared '
    'to the risk of deploying unsafe code.'
))

# ═══════════════════════════════════════════
# CHAPTER 6: CLOUD CODING PIPELINE
# ═══════════════════════════════════════════
story.append(heading('6. Cloud Coding Pipeline', h1, 0))

story.append(heading('6.1 Intent to Code', h2, 1))
story.append(para(
    'The intent-to-code pipeline transforms a human\'s natural language request into deployed, '
    'validated code through a five-stage process. <b>Stage 1 (Capture)</b> records the human\'s '
    'request via the chat interface. <b>Stage 2 (Classify)</b> uses a lightweight local classifier '
    '(Phi-3-mini, 3.8B parameters at Q4 quantization) to categorize the request as one of seven '
    'types: new reflex, modify reflex, new Jetson module, diagnostic query, calibration adjustment, '
    'safety rule, or complex firmware. <b>Stage 3 (Clarify)</b> engages the human in a dialogue '
    'using the local LLM to resolve ambiguities and gather required parameters before any cloud '
    'call is made. <b>Stage 4 (Bundle)</b> assembles a structured context bundle containing the '
    'clarified intent, hardware capabilities, existing code, recent observation data, and safety '
    'constraints. <b>Stage 5 (Generate)</b> sends the context bundle to the appropriate cloud LLM '
    'for code generation.'
))
story.append(para(
    'The clarification stage is critical because it prevents expensive and slow cloud calls with '
    'incomplete information. When a human says "I want this ESP32 to control the throttle," the '
    'system needs to know: what sensor measures the current throttle position, what actuator drives '
    'the throttle, what the safe limits are, how fast the response should be, and whether this '
    'replaces or augments existing behavior. Asking these questions before calling the cloud saves '
    'both time (one cloud call with complete information versus multiple round-trips) and money '
    '(each cloud API call costs approximately $0.01-0.10 depending on the model and token count).'
))

story.append(heading('6.2 Code Generation Targets', h2, 1))
story.append(para(
    'The pipeline generates three types of artifacts. <b>ESP32 reflex JSON</b> (80% of use cases) '
    'are state machines, PID controllers, and trigger-action rules expressed in the declarative '
    'reflex schema and interpreted by the fixed runtime. Typical size: 1-4KB per reflex module. '
    '<b>ESP32 C extension modules</b> (15% of use cases) are compiled C code for complex behaviors '
    'that cannot be expressed as JSON, such as custom signal processing, Kalman filters, or '
    'non-linear control algorithms. These are cross-compiled on the Jetson using the ESP-IDF '
    'toolchain and deployed as OTA updates. Typical size: 2-16KB per module, with a hard limit of '
    '64KB. <b>Jetson Python modules</b> (5% of use cases) are Docker-contained Python services '
    'that run on the Jetson for monitoring, learning, or UI tasks. These are hot-reloaded without '
    'restarting the Jetson.'
))
story.append(note(
    'Architecture Decision: JSON reflexes were made the primary code generation target (rather than '
    'always generating C) because JSON reflexes are inherently safer. The fixed C runtime that '
    'interprets JSON has been extensively tested and validated; it enforces all safety constraints '
    'automatically (output bounds checking, rate limiting, timeout enforcement). When the AI generates '
    'C code directly, each generated module must go through the full validation pipeline independently, '
    'which is more expensive and more error-prone. By structuring the system so that 80% of behaviors '
    'use JSON, we reduce the attack surface for safety-critical bugs by a corresponding factor.'
))

story.append(heading('6.3 Validation Pipeline', h2, 1))
story.append(para(
    'The six-stage validation pipeline ensures that no AI-generated code reaches production hardware '
    'without passing rigorous automated checks. <b>Stage 1 (Syntax)</b> validates JSON schema '
    'compliance or compiles C code with zero warnings using the ESP-IDF toolchain. <b>Stage 2 '
    '(Static Analysis)</b> runs cppcheck and clang-tidy with a MISRA-C:2012 subset configuration '
    'enforcing 11 critical rules including no dynamic memory allocation, no undefined behavior, and '
    'explicit error handling. <b>Stage 3 (Memory Budget)</b> verifies that compiled code fits within '
    'its allocated memory (stack, static, and PSRAM budgets) and contains no heap allocation calls. '
    '<b>Stage 4 (Safety)</b> uses a separate LLM call to review the generated code against the system '
    'safety policy, checking for violations such as missing failsafe states or disabled watchdogs. '
    '<b>Stage 5 (Simulation)</b> replays the code against recorded telemetry data to verify that it '
    'produces reasonable outputs and meets timing deadlines. <b>Stage 6 (Testing)</b> generates and '
    'runs automated unit tests and edge-case tests.'
))
story.append(para(
    'If any stage fails, the pipeline either regenerates the code (for syntax and static analysis '
    'failures, up to 3 attempts with the failure context included in the prompt), blocks deployment '
    'and requires human review (for safety and memory failures), or deploys to a test ESP32 rather '
    'than production (for simulation failures). Only code that passes all six stages is presented to '
    'the human operator for final approval and deployment.'
))

story.append(heading('6.4 Deployment and Rollback', h2, 1))
story.append(para(
    'Deployment to ESP32 nodes uses serial OTA via the Jetson, not WiFi. This choice was made because '
    'WiFi is unreliable in the environments where these systems operate: metal hulls attenuate signals, '
    'water absorbs RF energy, and industrial environments have high electromagnetic interference. A '
    'wired RS-422 serial connection is physically reliable and immune to these issues. At 921,600 baud, '
    'a 500KB firmware update takes approximately 5 seconds. At 115,200 baud (for long cable runs), '
    'it takes approximately 40 seconds. Both are acceptable for a maintenance operation that happens '
    'infrequently.'
))
story.append(para(
    'Every deployment includes a 60-second monitoring window after activation. During this window, '
    'the Jetson watches the ESP32\'s telemetry for anomalies: unexpected sensor readings, actuator '
    'commands outside expected ranges, increased loop timing variance, or watchdog resets. If any '
    'anomaly is detected, the system automatically rolls back to the previous version and logs the '
    'failure with a full diagnostic dump. This "canary deployment" approach catches issues that '
    'the validation pipeline missed because they only manifest under real-world conditions, such as '
    'electrical noise on an ADC input or mechanical resonance in a servo at a specific RPM.'
))

story.append(heading('6.5 Starlink and Offline Operation', h2, 1))
story.append(para(
    'The system is designed to operate indefinitely without cloud connectivity. Starlink provides '
    'typical latency of 20-40ms and bandwidth of 50-200 Mbps, but it is subject to outages during '
    'heavy rain, satellite handoffs, and obstructions. The system handles this through a three-tier '
    'connectivity model. When Starlink is available, the system uses cloud LLMs for complex code '
    'generation and sends observation summaries for cloud-based pattern analysis. When Starlink is '
    'unavailable but the Jetson is running, the local Qwen2.5-Coder-7B model handles approximately '
    '70% of code generation requests (simple reflex modifications and parameter tuning) at 12 tokens '
    'per second. When even the Jetson is down, the ESP32s continue running their last-known-good '
    'reflex behaviors autonomously.'
))
story.append(note(
    'Architecture Decision: Qwen2.5-Coder-7B-Instruct at Q4_K_M quantization was chosen as the '
    'local model because it provides the best quality-to-speed tradeoff on the Jetson Orin Nano 8GB. '
    'At approximately 4GB of VRAM for the model weights, it leaves approximately 4GB for the OS, '
    'Docker runtime, Whisper inference, and other services. At 12 tokens per second, it can generate '
    'a typical reflex JSON (approximately 500 tokens) in approximately 40 seconds, which is acceptable '
    'for an interactive coding session. Alternatives considered: CodeLlama-7B (lower quality), '
    'DeepSeek-Coder-6.7B (similar quality, slightly faster but less tested on Jetson), and '
    'StarCoder2-7B (good quality but poor at following system prompts for embedded constraints).'
))

story.append(heading('6.6 Security Model', h2, 1))
story.append(para(
    'The security model is built on three principles: least privilege, defense in depth, and '
    'human-controlled trust boundaries. <b>Least privilege</b>: the ESP32 runtime executes AI-generated '
    'code in a sandboxed environment with no network access, no filesystem write access (except to the '
    'designated LittleFS partition), and no ability to modify its own firmware. <b>Defense in depth</b>: '
    'all AI-generated code is signed with ECDSA-P256 using a key stored in the Jetson\'s TPM (Trusted '
    'Platform Module). The ESP32 verifies the signature before accepting any code update. Even if an '
    'attacker intercepts and modifies a code update in transit, the signature verification will fail '
    'and the ESP32 will reject the update. <b>Human-controlled trust boundaries</b>: no AI-generated '
    'code can be deployed without explicit human approval. The system presents the proposed change to '
    'the human, explains what it does in plain language, and waits for a "Deploy" command. A physical '
    'NC kill switch provides a hardware-level override that disconnects all AI-generated code changes.'
))
story.append(para(
    'The estimated monthly cloud cost for a typical installation is approximately $3 per month '
    '(approximately $36 per year), based on an estimated 30 cloud API calls per month at an average '
    'of $0.10 per call. With the local model handling 70% of requests, this drops to approximately '
    '$1 per month. These costs are negligible compared to the labor savings of not needing a human '
    'embedded software developer for every configuration change and reflex behavior modification.'
))

# ═══════════════════════════════════════════
# CHAPTER 7: INCREMENTAL AUTONOMY
# ═══════════════════════════════════════════
story.append(heading('7. Incremental Autonomy (INCREMENTS Framework)', h1, 0))

story.append(heading('7.1 The Six-Level Taxonomy', h2, 1))
story.append(para(
    'The INCREMENTS framework defines six levels of autonomy (0 through 5) that apply on a '
    'per-subsystem basis. This is a critical distinction from autonomy frameworks like SAE J3016 '
    '(which defines levels for the entire vehicle): in this system, the bilge pump can be at Level 4 '
    '(autonomous) while the throttle is at Level 2 (assisted), simultaneously. Each subsystem has '
    'two level values: a <b>current level</b> (what the system is currently doing, earned through '
    'demonstrated reliability) and a <b>maximum allowed level</b> (a ceiling set by the human that '
    'the system can never exceed, regardless of its trust score).'
))

story.append(Spacer(1, 18))
t = make_table(
    ['Level', 'Name', 'System Authority', 'Human Role', 'Min Observation'],
    [
        ['0', 'Manual', 'Records data only', 'All decisions and actuation', '0 hours'],
        ['1', 'Advisory', 'Displays suggestions', 'All actuation, acknowledges alerts', '72 hours'],
        ['2', 'Assisted', 'Prepares actions for approval', 'Reviews and approves each action', '168 hours (7 days)'],
        ['3', 'Supervised', 'Acts autonomously, human can override', 'Available to override anytime', '720 hours (30 days)'],
        ['4', 'Autonomous', 'Acts without human availability', 'Notified of significant events', '2160 hours (90 days)'],
        ['5', 'Fully Autonomous', 'Self-maintaining, strategic decisions', 'Administrator/owner only', '4320 hours (180 days)'],
    ],
    [0.5*inch, 1.0*inch, 1.8*inch, 1.6*inch, 1.2*inch]
)
story.append(t)
story.append(Spacer(1, 4))
story.append(Paragraph('<b>Table 3.</b> INCREMENTS Autonomy Level Definitions', caption_s))
story.append(Spacer(1, 18))

story.append(heading('7.2 Trust Score Algorithm', h2, 1))
story.append(para(
    'Each subsystem maintains a continuous trust score T in the range [0, 1] computed as a weighted '
    'exponential moving average with asymmetric gain and loss rates. When a subsystem performs well '
    '(successful action with no override), trust increases slowly: delta_T = 0.002 x (1 - T) x quality. '
    'When a subsystem performs poorly (override, anomaly, failure), trust decreases rapidly: delta_T = '
    '-0.05 x T x severity. This creates an asymmetric trust model with a 25:1 loss-to-gain ratio, '
    'meaning that gaining 0.1 trust from 0.5 requires approximately 50 consecutive good evaluations, '
    'while losing 0.1 trust from 0.9 requires only 2 bad evaluations.'
))
story.append(para(
    'This asymmetry is grounded in human trust psychology research (Lee and See, 2004), which shows '
    'that humans trust automation slowly but distrust it quickly. A single frightening event (such '
    'as the autopilot making an unexpected hard turn) can undermine weeks of reliable operation. The '
    'mathematical model reflects this reality: the system must demonstrate sustained excellence over '
    'long periods to earn trust, but a single significant failure immediately erodes that trust. The '
    'exponential approach to the ceiling (multiplied by 1 - T) means that reaching Level 5 (T > 0.97) '
    'requires not just a streak of good behavior but sustained excellence, because gains become '
    'increasingly difficult as trust approaches 1.0.'
))
story.append(note(
    'Architecture Decision: The specific parameter values (alpha_gain = 0.002, alpha_loss = 0.05) '
    'were chosen based on simulation of the advancement timeline. With daily evaluations, a subsystem '
    'starting at T = 0.3 (Level 1 threshold) takes approximately 60 days of flawless operation to '
    'reach T = 0.55 (Level 2 threshold), 120 days to reach T = 0.75 (Level 3), and 300 days to '
    'reach T = 0.90 (Level 4). These timelines are intentionally long because they reflect the '
    'reality that earning trust for safety-critical autonomous systems should take months, not days. '
    'The parameters are configurable per-subsystem to allow faster advancement for low-risk subsystems '
    '(like lighting) and slower advancement for high-risk subsystems (like throttle).'
))

story.append(heading('7.3 Advancement Criteria', h2, 1))
story.append(para(
    'Advancing from one autonomy level to the next requires meeting both quantitative metrics and '
    'qualitative criteria. Quantitative metrics include sensor uptime (greater than 99.9% for '
    'Level 3 advancement), false alarm rate (less than 2% for Level 2), human override rate (less '
    'than 0.5% for Level 3), and consecutive days without any safety incident (30 days for Level 3). '
    'Qualitative criteria include a human comfort survey (the operator must rate comfort at 4 out of '
    '5 or higher for 3 consecutive weekly surveys), an A/B comparison demonstrating statistically '
    'significant improvement over the previous level (p less than 0.05 in a paired t-test over at '
    'least 48 hours of controlled comparison), and explicit human verbal confirmation: "I am comfortable '
    'with [subsystem] advancing to Level [N]."'
))
story.append(para(
    'Revocation is immediate and asymmetric. Any single safety incident, override burst (more than 3 '
    'overrides in 10 minutes), or sensor failure (loss of any required sensor for more than 30 seconds) '
    'causes an immediate drop to the previous level. After revocation, the subsystem must re-earn the '
    'dropped level from scratch, including the full observation period. This is intentional: trust '
    'that has been broken must be rebuilt, not restored.'
))

story.append(heading('7.4 Fallback Hierarchy', h2, 1))
story.append(para(
    'The fallback hierarchy defines what happens when each layer of the system fails. The hierarchy '
    'has four tiers. <b>Tier 0 (Reflex)</b> is the ESP32 running pre-programmed reflex behaviors. If '
    'the Jetson fails, the ESP32 continues on its last-known-good reflexes. Response time: less than '
    '10ms. <b>Tier 1 (Smart)</b> is the Jetson running AI-based behaviors. If the Jetson becomes '
    'unresponsive for more than 2 seconds, the ESP32 detects the heartbeat timeout and activates its '
    'failsafe reflexes. <b>Tier 2 (Human)</b> is the human operator. If the system encounters a '
    'situation outside its confidence envelope, it pauses and alerts the human. <b>Tier 3 (Safe '
    'State)</b> is the hardware-enforced safe state. If multiple simultaneous failures occur, the '
    'hardware kill switch and watchdog timer force all actuators to their safe positions.'
))
story.append(para(
    'Each fallback tier is tested on a regular schedule. Reflex triggers are tested weekly by '
    'injecting simulated sensor values. Jetson failure tests are performed monthly by stopping the '
    'Jetson process and verifying ESP32 takeover within 2 seconds. Kill switch tests are performed '
    'weekly by manual activation. Full failure simulations (cascading failures) are performed quarterly '
    'by trained personnel. Any test failure grounds the system until resolved.'
))

story.append(heading('7.5 Human Override Interface', h2, 1))
story.append(para(
    'The human override system provides five physical and five digital override mechanisms, all '
    'available simultaneously. Physical overrides include a mushroom-head kill switch (response time '
    'less than 100ms, cuts all actuator power), a manual override lever per subsystem (detects human '
    'input and cedes control within 200ms), a key-operated bypass switch that electrically bypasses '
    'the ESP32 entirely, and standard circuit breakers. Digital overrides include voice commands '
    '(processed by on-device ASR with 95% confidence threshold), dashboard buttons, chat commands, '
    'mobile app controls (with biometric authentication), and geofence triggers.'
))
story.append(para(
    'After every override, the system asks (non-blocking) why the human overrode: "System was making '
    'wrong decision," "I wanted more direct control," "I did not trust the system in this situation," '
    "or 'I was testing.' These reasons are logged and feed into the trust score calculation. 'System "
    "was making wrong decision' triggers a high-severity trust penalty, while 'I was testing' triggers "
    'a minimal penalty. This feedback loop ensures that the trust score accurately reflects the '
    'human\'s actual confidence in the system, not just statistical reliability metrics.'
))

# ═══════════════════════════════════════════
# CHAPTER 8: CROSS-DOMAIN APPLICATION
# ═══════════════════════════════════════════
story.append(heading('8. Cross-Domain Application', h1, 0))

story.append(heading('8.1 Generalization Strategy', h2, 1))
story.append(para(
    'The platform is designed to be domain-agnostic. The core architecture (ESP32 universal firmware, '
    'Jetson cognitive layer, cloud coding pipeline, INCREMENTS autonomy framework) does not contain '
    'any marine-specific logic. All domain-specific knowledge is encapsulated in three pluggable '
    'components: the <b>equipment library</b> (JSON templates for common sensors and actuators in each '
    'domain), the <b>reflex template library</b> (pre-built control patterns like PID, state machines, '
    'and threshold alarms), and the <b>safety policy</b> (domain-specific safety rules that constrain '
    'what the AI is allowed to generate). To adapt the platform to a new domain, you add equipment '
    'templates, reflex templates, and safety rules. You do not modify the firmware, the runtime, '
    'or the learning pipeline.'
))

story.append(Spacer(1, 18))
t = make_table(
    ['Domain', 'Example Sensors', 'Example Actuators', 'Autonomy Path'],
    [
        ['Marine', 'Compass, GPS, wind, depth, AIS', 'Rudder servo, throttle, winch, bilge', 'Bilge > Lights > Anchor > Throttle > Autopilot > Nav'],
        ['Agriculture', 'Soil moisture, GPS, temp, camera', 'Irrigation valve, fertilizer valve, planter', 'Monitoring > Irrigation > Fertilizer > Spraying > Harvesting'],
        ['HVAC', 'Temp, humidity, pressure, CO2', 'Damper, VFD, compressor relay', 'Monitoring > Scheduling > Zone Control > Demand Response'],
        ['Factory', 'Proximity, load cell, limit switch', 'Conveyor motor, pneumatic valve, robot', 'Monitoring > Alarm > Handling > Quality Control'],
        ['Mining', 'Gas sensor, vibration, temperature', 'Hydraulic valve, conveyor, ventilation', 'Monitoring > Ventilation > Equipment > Haulage'],
    ],
    [0.9*inch, 1.7*inch, 1.7*inch, 2.1*inch]
)
story.append(t)
story.append(Spacer(1, 4))
story.append(Paragraph('<b>Table 4.</b> Cross-Domain Equipment and Autonomy Paths', caption_s))
story.append(Spacer(1, 18))

story.append(heading('8.2 Equipment Library', h2, 1))
story.append(para(
    'The equipment library provides pre-built JSON templates for common industrial components. Each '
    'template specifies the pin mapping, driver configuration, calibration procedure, and self-test '
    'sequence for a specific device. When a human says "I want to add a HMC5883L compass," the system '
    'looks up the template and generates the complete wiring and configuration guide from it. The '
    'template includes the I2C address (0x1E), the required pull-up resistor value (4.7k ohm for 100kHz '
    'I2C), the expected output format (heading in degrees, raw X/Y/Z magnetometer values), and the '
    'self-test procedure (verify WHO_AM_I register, check that heading changes when the sensor is '
    'rotated). Templates exist for over 100 common devices across all five supported domains, and '
    'new templates can be added by the AI itself based on datasheet analysis.'
))
story.append(para(
    'The AI can also generate new equipment templates from datasheets. When a human says "I have a '
    'sensor I bought online, it is a Sensirion SHT40 temperature and humidity sensor," the AI can '
    'search its training data for the SHT40 datasheet, extract the I2C address (0x44), the command '
    'sequence for reading temperature and humidity, the accuracy specifications, and the wiring '
    'requirements, and generate a complete equipment template. The human then validates the '
    'auto-detected hardware against the template, and if they match, the template is added to the '
    'library for future use. This bootstrapping capability means the system can learn about new '
    'hardware without any pre-existing template, as long as the AI has been trained on the relevant '
    'datasheet or the human can provide key specifications.'
))

story.append(heading('8.3 Scalability: Adding Brains and Limbs', h2, 1))
story.append(para(
    'The system scales in two dimensions. <b>Horizontal scaling</b> (more ESP32s) is as simple as '
    'wiring a new ESP32 to the Jetson\'s serial port and letting the provisioning protocol assign '
    'it a role. The Jetson automatically discovers the new node, queries its capabilities, and makes '
    'it available for configuration through the chat interface. Each additional ESP32 adds negligible '
    'load to the Jetson because the reflex execution happens on the ESP32, not the Jetson. A single '
    'Jetson can comfortably manage 20-30 ESP32 nodes, limited primarily by the number of available '
    'serial ports (USB-to-RS-422 adapters can be daisy-chained via USB hubs).'
))
story.append(para(
    '<b>Vertical scaling</b> (more Jetsons) is achieved by adding Jetson units to the cluster and '
    'assigning them dedicated roles. Adding a vision Jetson with a camera enables object detection '
    'and scene understanding. Adding a STT/TTS Jetson enables voice interaction even when the primary '
    'Jetson is under heavy computational load. Adding a learning Jetson enables long-running pattern '
    'analysis without impacting real-time operation. Jetsons communicate via Ethernet and coordinate '
    'through Redis shared state and gRPC service calls. The cluster has no single point of failure: '
    'if any Jetson fails, the ESP32s continue running their reflex behaviors, and the remaining '
    'Jetsons absorb the failed unit\'s responsibilities (or gracefully degrade non-essential functions).'
))

# ═══════════════════════════════════════════
# CHAPTER 9: GETTING STARTED
# ═══════════════════════════════════════════
story.append(heading('9. Getting Started', h1, 0))

story.append(heading('9.1 Bill of Materials', h2, 1))
story.append(para(
    'A minimum viable system requires one Jetson Orin Nano Super 8GB developer kit ($249), one '
    'ESP32-S3-WROOM-1-N8R8 development board ($8), a USB-to-RS-422 adapter ($15), and a 5V 3A '
    'USB-C power supply for the Jetson ($12). Total hardware cost for the minimum system: '
    'approximately $284. For a more realistic deployment, add one ESP32 per controlled subsystem '
    '($8 each), sensors and actuators appropriate to the domain (highly variable), RS-422 cabling '
    '(approximately $0.50 per meter), and optionally a Starlink dish for cloud connectivity ($599). '
    'A typical marine installation with autopilot, throttle, bilge monitoring, and lighting control '
    'would require approximately 5 ESP32s, bringing the total hardware cost to approximately $750 '
    'excluding sensors, actuators, and wiring.'
))

story.append(heading('9.2 First Boot', h2, 1))
story.append(para(
    'The first boot sequence is designed to be as seamless as possible. Flash the universal firmware '
    'to the ESP32 using the ESP-IDF flash tool (esptool.py). Connect the ESP32 to the Jetson via '
    'USB-to-RS-422 adapter. Power on the Jetson and boot the Docker container stack. The Jetson '
    'will detect the ESP32 on the serial port, receive the device identity message, and display a '
    'configuration prompt in the chat interface: "New ESP32 detected (MAC: AA:BB:CC:DD:EE:FF, firmware '
    'v0.1.0). What would you like this node to do?" The human responds in natural language, and the '
    'conversational setup flow begins.'
))

story.append(heading('9.3 Adding Your First Limb', h2, 1))
story.append(para(
    'As a worked example, consider adding a simple LED lighting controller. The human says: "I want '
    'to control 4 LED lights with dimming." The AI responds: "I will configure GPIO pins 12, 13, 14, '
    '15 as PWM outputs at 5kHz for LED dimming. Wire each LED to a GPIO pin through a 220-ohm '
    'resistor. Do you have the LEDs and resistors ready?" The human wires the LEDs and confirms. '
    'The system auto-detects the outputs (no explicit sensor detection needed for simple GPIO outputs), '
    'generates the configuration JSON, deploys it to the ESP32, and runs a self-test that blinks '
    'each LED in sequence. The human confirms the LEDs blink, and the basic lighting node is operational. '
    'The total time from intent to working hardware: approximately 5 minutes.'
))

story.append(heading('9.4 Teaching Your First Reflex', h2, 1))
story.append(para(
    'After the hardware is connected, the human teaches the system the desired behavior. For the '
    'lighting example, the human might say: "When I say lights on, turn all LEDs to 80% brightness. '
    'When I say lights off, fade them down over 3 seconds." The AI generates the corresponding reflex '
    'JSON: a state machine with two states (ON and OFF), a voice command trigger for each state '
    'transition, and a 3-second fade-out sequence in the OFF state. The reflex is deployed to the '
    'ESP32 and activated. The human tests it by saying "lights on" and "lights off" and watching the '
    'LEDs respond. If the fade is too slow or too fast, the human says "make the fade 2 seconds '
    'instead," and the AI modifies the reflex parameter and redeploys. The entire teaching cycle takes '
    'approximately 2 minutes, and at no point does the human write any code.'
))
story.append(para(
    'For more complex behaviors, the human demonstrates rather than describes. For a throttle '
    'controller, the human says "watch me drive" while the observation buffer records. After the '
    'demonstration, the Jetson analyzes the data, discovers the patterns, and proposes a reflex rule. '
    'The human reviews the proposal ("I noticed you increase RPM by approximately 200 when turning '
    'into the wind. Should I automate this?"), approves it, and the A/B test begins. Over the next '
    'several trips, the system compares its automated throttle adjustments to the human\'s manual '
    'control. If the automated version matches or exceeds human performance across the seven '
    'standardized metrics, the human approves permanent adoption, and the system begins earning '
    'trust toward higher autonomy levels.'
))

# ═══════════════════════════════════════════
# CHAPTER 10: KEY ARCHITECTURE DECISIONS SUMMARY
# ═══════════════════════════════════════════
story.append(heading('10. Architecture Decision Records', h1, 0))
story.append(para(
    'This chapter provides a consolidated summary of the major architectural decisions made during '
    'the design of this platform, organized as a reference table for developers who need to understand '
    'the rationale behind specific design choices without reading the full annotated chapters above.'
))

story.append(Spacer(1, 18))
t = make_table(
    ['Decision', 'Choice', 'Alternative Rejected', 'Key Reason'],
    [
        ['Firmware model', 'Universal single binary', 'Per-role firmware', 'Reduces N binaries to 1, enables hot-swap'],
        ['Reflex execution', 'Bytecode VM', 'JSON interpretation', '10x faster, deterministic timing'],
        ['Wire protocol', 'COBS framing + CRC-16', 'Newline-delimited JSON', 'Supports binary payloads, bounded overhead'],
        ['Jetson-ESP32 link', 'RS-422 serial', 'WiFi / BLE', 'Reliable in harsh environments'],
        ['Local LLM', 'Qwen2.5-Coder-7B Q4', 'CodeLlama-7B / StarCoder2', 'Best quality/speed on Orin Nano 8GB'],
        ['Safety validation', 'Separate LLM call', 'Same model self-validates', 'Prevents self-validation bias'],
        ['Trust model', 'Asymmetric 25:1', 'Symmetric', 'Matches human trust psychology research'],
        ['Autonomy levels', '6 levels (0-5)', '5 levels (SAE J3016)', 'More granularity at low end for industrial'],
        ['Kill switch', 'Hardware NC contact + relay', 'Software-only', 'Software can crash; hardware cannot'],
        ['OTA channel', 'Serial via Jetson', 'WiFi OTA', 'Wired is immune to RF interference'],
        ['Observation storage', 'PSRAM ring buffer', 'SRAM buffer', '5.5MB buffer does not fit in 512KB SRAM'],
        ['JSON parser', 'jsmn (runtime) + cJSON (config)', 'cJSON everywhere', 'jsmn is zero-alloc; cJSON fragments heap'],
        ['Factory partition', 'Never OTA modified', 'Updatable', 'Immutable trusted compute base'],
        ['Reflex format', 'JSON state machines', 'Behavior trees', 'Easier to verify, visualize, and explain'],
        ['Code generation', '80% JSON, 15% C, 5% Python', 'All C', 'JSON is safer; C only when necessary'],
    ],
    [1.3*inch, 1.3*inch, 1.5*inch, 2.3*inch]
)
story.append(t)
story.append(Spacer(1, 4))
story.append(Paragraph('<b>Table 5.</b> Consolidated Architecture Decision Records', caption_s))
story.append(Spacer(1, 18))

story.append(para(
    'These decisions were not made in isolation. Each was evaluated against the others and against '
    'the overall system constraints: the ESP32-S3\'s limited memory and processing power, the Jetson\'s '
    'finite inference capacity, the harsh physical environments, the requirement for deterministic '
    'real-time behavior, and the principle that the human operator should never need to write code. '
    'In several cases, the chosen approach required more upfront complexity (such as building a bytecode '
    'VM instead of using a JSON interpreter) but paid dividends in safety, performance, and '
    'maintainability that justified the investment. This is the nature of platform architecture: '
    'good decisions are often the ones that make the system harder to build but easier to trust.'
))


# ── BUILD ──
doc.multiBuild(story)
print(f"PDF generated: {OUTPUT}")

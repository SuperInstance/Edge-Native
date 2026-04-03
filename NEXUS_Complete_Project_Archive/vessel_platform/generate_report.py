#!/usr/bin/env python3
"""
Generate the Vessel Robotics Platform comprehensive PDF report.
Master architecture document synthesized from 6 expert briefs.
"""

import os
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
from reportlab.lib import colors
from reportlab.lib.units import inch, cm
from reportlab.platypus import (
    Paragraph, Spacer, PageBreak, Table, TableStyle, Image
)
from reportlab.platypus.tableofcontents import TableOfContents
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase.pdfmetrics import registerFontFamily
from reportlab.platypus import SimpleDocTemplate

# ========== FONT REGISTRATION ==========
pdfmetrics.registerFont(TTFont('Times New Roman', '/usr/share/fonts/truetype/english/Times-New-Roman.ttf'))
pdfmetrics.registerFont(TTFont('Calibri', '/usr/share/fonts/truetype/english/calibri-regular.ttf'))
pdfmetrics.registerFont(TTFont('DejaVuSans', '/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf'))
registerFontFamily('Times New Roman', normal='Times New Roman', bold='Times New Roman')
registerFontFamily('Calibri', normal='Calibri', bold='Calibri')
registerFontFamily('DejaVuSans', normal='DejaVuSans', bold='DejaVuSans')

# ========== COLORS ==========
DARK_BLUE = colors.HexColor('#1F4E79')
MEDIUM_BLUE = colors.HexColor('#2E75B6')
LIGHT_BLUE = colors.HexColor('#D6E4F0')
LIGHT_GRAY = colors.HexColor('#F5F5F5')
ACCENT_ORANGE = colors.HexColor('#ED7D31')

# ========== STYLES ==========
styles = getSampleStyleSheet()

cover_title = ParagraphStyle(
    name='CoverTitle', fontName='Times New Roman', fontSize=36,
    leading=44, alignment=TA_CENTER, spaceAfter=24, textColor=DARK_BLUE
)
cover_subtitle = ParagraphStyle(
    name='CoverSubtitle', fontName='Times New Roman', fontSize=18,
    leading=24, alignment=TA_CENTER, spaceAfter=12, textColor=MEDIUM_BLUE
)
cover_info = ParagraphStyle(
    name='CoverInfo', fontName='Times New Roman', fontSize=13,
    leading=20, alignment=TA_CENTER, spaceAfter=8, textColor=colors.HexColor('#555555')
)

h1_style = ParagraphStyle(
    name='H1', fontName='Times New Roman', fontSize=18,
    leading=24, spaceBefore=18, spaceAfter=10, textColor=DARK_BLUE
)
h2_style = ParagraphStyle(
    name='H2', fontName='Times New Roman', fontSize=14,
    leading=18, spaceBefore=14, spaceAfter=8, textColor=MEDIUM_BLUE
)
h3_style = ParagraphStyle(
    name='H3', fontName='Times New Roman', fontSize=12,
    leading=16, spaceBefore=10, spaceAfter=6, textColor=colors.black
)
body_style = ParagraphStyle(
    name='Body', fontName='Times New Roman', fontSize=10.5,
    leading=16, alignment=TA_JUSTIFY, spaceAfter=6
)
body_left = ParagraphStyle(
    name='BodyLeft', fontName='Times New Roman', fontSize=10.5,
    leading=16, alignment=TA_LEFT, spaceAfter=6
)
bullet_style = ParagraphStyle(
    name='Bullet', fontName='Times New Roman', fontSize=10.5,
    leading=16, alignment=TA_LEFT, spaceAfter=3,
    leftIndent=20, bulletIndent=8
)
code_style = ParagraphStyle(
    name='Code', fontName='DejaVuSans', fontSize=8.5,
    leading=12, alignment=TA_LEFT, spaceAfter=4,
    leftIndent=12, backColor=colors.HexColor('#F0F0F0'),
    borderWidth=0.5, borderColor=colors.grey, borderPadding=4
)
caption_style = ParagraphStyle(
    name='Caption', fontName='Times New Roman', fontSize=9.5,
    leading=14, alignment=TA_CENTER, textColor=colors.HexColor('#555555'),
    spaceBefore=4, spaceAfter=6
)
tbl_header = ParagraphStyle(
    name='TblHeader', fontName='Times New Roman', fontSize=9.5,
    leading=13, alignment=TA_CENTER, textColor=colors.white
)
tbl_cell = ParagraphStyle(
    name='TblCell', fontName='Times New Roman', fontSize=9,
    leading=12, alignment=TA_LEFT
)
tbl_cell_c = ParagraphStyle(
    name='TblCellC', fontName='Times New Roman', fontSize=9,
    leading=12, alignment=TA_CENTER
)

# ========== TOC TEMPLATE ==========
class TocDocTemplate(SimpleDocTemplate):
    def afterFlowable(self, flowable):
        if hasattr(flowable, 'bookmark_name'):
            level = getattr(flowable, 'bookmark_level', 0)
            text = getattr(flowable, 'bookmark_text', '')
            self.notify('TOCEntry', (level, text, self.page))

def add_heading(text, style, level=0):
    p = Paragraph(f'<b>{text}</b>', style)
    p.bookmark_name = text
    p.bookmark_level = level
    p.bookmark_text = text
    return p

def make_table(data, col_widths, has_header=True):
    t = Table(data, colWidths=col_widths, repeatRows=1 if has_header else 0)
    style_cmds = [
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ]
    if has_header:
        style_cmds.append(('BACKGROUND', (0, 0), (-1, 0), DARK_BLUE))
        style_cmds.append(('TEXTCOLOR', (0, 0), (-1, 0), colors.white))
        for i in range(1, len(data)):
            bg = colors.white if i % 2 == 1 else LIGHT_GRAY
            style_cmds.append(('BACKGROUND', (0, i), (-1, i), bg))
    t.setStyle(TableStyle(style_cmds))
    return t

def P(text, style=body_style):
    return Paragraph(text, style)

def H(text, style=tbl_header):
    return Paragraph(f'<b>{text}</b>', style)

def TC(text):
    return Paragraph(text, tbl_cell)

def TCC(text):
    return Paragraph(text, tbl_cell_c)

# ========== BUILD DOCUMENT ==========
OUTPUT_PATH = '/home/z/my-project/download/Vessel_Robotics_Platform_Architecture.pdf'
os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)

doc = TocDocTemplate(
    OUTPUT_PATH,
    pagesize=letter,
    topMargin=0.75*inch, bottomMargin=0.75*inch,
    leftMargin=0.85*inch, rightMargin=0.85*inch,
    title='Vessel_Robotics_Platform_Architecture',
    author='Z.ai',
    creator='Z.ai',
    subject='Comprehensive vessel robotics platform architecture for commercial fishing vessels'
)

story = []
W = doc.width  # available width

# ========== COVER PAGE ==========
story.append(Spacer(1, 100))
story.append(Paragraph('<b>VESSEL ROBOTICS PLATFORM</b>', cover_title))
story.append(Spacer(1, 16))
story.append(Paragraph('Comprehensive Architecture Document', cover_subtitle))
story.append(Spacer(1, 8))
story.append(Paragraph('Commercial Fishing Vessel Integration', cover_subtitle))
story.append(Spacer(1, 40))

cover_line_data = [['']]
cover_line = Table(cover_line_data, colWidths=[W * 0.6])
cover_line.setStyle(TableStyle([
    ('LINEBELOW', (0, 0), (-1, 0), 2, DARK_BLUE),
]))
story.append(cover_line)
story.append(Spacer(1, 40))

story.append(Paragraph('3x Jetson Orin Nano Super Cluster', cover_info))
story.append(Paragraph('14x ESP32-S3 Sensor/Control Nodes (8 deployed + 6 spares)', cover_info))
story.append(Paragraph('Dual-Redundant Autopilot with Hot-Swap', cover_info))
story.append(Paragraph('Marine AI: Fish Species ID, Catch Tracking, Vision', cover_info))
story.append(Paragraph('STT/TTS Voice Interface with "Hey Helm" Wake Word', cover_info))
story.append(Spacer(1, 50))
story.append(Paragraph('Document ID: VRP-MCA-2025-016 | Revision 1.0', cover_info))
story.append(Paragraph('Classification: BUILD-AUTHORITATIVE', cover_info))
story.append(Paragraph('Target Vessel: 30-60ft Commercial Fishing Vessel', cover_info))
story.append(Spacer(1, 30))
story.append(Paragraph('Prepared by Z.ai | 2025', cover_info))
story.append(PageBreak())

# ========== TABLE OF CONTENTS ==========
toc = TableOfContents()
toc.levelStyles = [
    ParagraphStyle(name='TOC1', fontName='Times New Roman', fontSize=12, leftIndent=20, leading=20, spaceBefore=6),
    ParagraphStyle(name='TOC2', fontName='Times New Roman', fontSize=10.5, leftIndent=40, leading=16, spaceBefore=3),
]
story.append(Paragraph('<b>Table of Contents</b>', h1_style))
story.append(Spacer(1, 12))
story.append(toc)
story.append(PageBreak())

# ========== SECTION 1: EXECUTIVE SUMMARY ==========
story.append(add_heading('1. Executive Summary', h1_style, 0))
story.append(P(
    'The Vessel Robotics Platform transforms a commercial fishing vessel into a fully integrated '
    'robotic system where ESP32-S3 microcontrollers serve as the essential physical interface layer '
    'between the vessel and a cluster of NVIDIA Jetson Orin Nano Super AI computers. This document '
    'presents the comprehensive architecture synthesized from six expert-domain technical briefs, '
    'resolving all contradictions and establishing a single build-authoritative reference for the '
    'entire system. The philosophy is simple: a boat is merely a robot that humans can ride. Every '
    'ESP32 is an intelligent node that functions independently if the AI brain crashes, and can be '
    'hot-swapped in under two minutes by pulling a fresh unit from a waterproof package.'
))
story.append(P(
    'The platform comprises three Jetson Orin Nano Super units (8GB each, 67 TOPS, 201 TOPS total) '
    'serving as the ship\'s distributed AI brain. Jetson-Alpha at the navigation station runs '
    'OpenCPN, the NMEA multiplexer, the autopilot MCP server, and the Qwen2.5-7B chatbot LLM. '
    'Jetson-Bravo on the back deck handles all vision processing including YOLOv8-nano object detection, '
    'Whisper speech-to-text, and Piper text-to-speech. Jetson-Charlie in the engine room runs fish '
    'species identification, depth sounder ML processing, and engine telemetry analysis. All three '
    'Jetsons communicate over a managed Gigabit Ethernet switch using gRPC for synchronous RPC calls '
    'and MQTT for asynchronous telemetry. Redis provides shared state and leader election, ensuring '
    'that if any single Jetson fails, the remaining units seamlessly assume its responsibilities.'
))
story.append(P(
    'The ESP32-S3 node network connects to the Jetsons via RS-422 serial links at 115200 baud using '
    'the VesselLink JSON protocol with CRC-16 framing. Each node runs a common VesselNode firmware '
    'framework written in C with ESP-IDF v5.2+, with role-specific modules for autopilot control, '
    'lighting management, engine monitoring, deck equipment, camera interfaces, environmental sensing, '
    'bilge monitoring, and navigation aids. A unified M12 8-pin connector standard means any ESP32 '
    'can plug into any cable location on the vessel; the Jetson cluster automatically identifies the '
    'node by its MAC address, pushes the appropriate firmware via serial OTA, and loads saved '
    'calibration settings from the node database. For critical systems like the autopilot and engine '
    'monitoring, dual-redundant ESP32 pairs operate on opposite sides of the cabin with independent '
    'sensor suites, cross-checking each other every second and achieving sub-100ms failover.'
))
story.append(P(
    'The dockside onboarding procedure mimics professional ComNav and Simrad autopilot commissioning '
    'with an 8-step guided wizard covering vessel configuration, compass calibration (BNO085 hard/soft '
    'iron correction), rudder calibration (center, limits, counter-rudder), yaw damping tuning, '
    'response speed optimization, circle test validation, and alarm system verification. All '
    'calibration data is persisted in ESP-IDF NVS flash with dual-copy integrity protection, '
    'versioned settings, and automatic backup to the Jetson SQLite database. The marine AI subsystem '
    'includes fish species identification through bin-based weakly-supervised learning (the camera '
    'observes which bin a fish goes into, automatically creating species labels), catch rate tracking '
    'with weight and length measurement, person-overboard detection, and automated regulatory '
    'compliance logging. The total electronics budget is estimated at $8,000-$12,000, with the '
    'complete spare parts inventory costing approximately $600-$800.'
))

# ========== SECTION 2: SYSTEM OVERVIEW ==========
story.append(Spacer(1, 12))
story.append(add_heading('2. System Architecture Overview', h1_style, 0))

story.append(add_heading('2.1 Three-Tier Network Architecture', h2_style, 1))
story.append(P(
    'The vessel network is organized into three distinct tiers, each optimized for its specific '
    'communication requirements and physical characteristics. Tier 0 is the NMEA 0183 Instrument '
    'Bus operating at 4800 baud (38400 for AIS), carrying standard marine data from GPS, compass, '
    'depth sounder, wind sensor, and AIS receiver to the Jetson cluster via listener tees. Tier 1 '
    'is the Jetson Cluster LAN, a managed Gigabit Ethernet network on the 10.0.0.0/24 subnet '
    'connecting all three Jetson units through a Netgear GS308T managed switch. This tier carries '
    'gRPC RPC calls, MQTT telemetry, database replication, and model artifact transfers. Tier 2 '
    'is the ESP32 Node Bus, using RS-422 differential serial at 115200 baud in a star topology '
    'with FTDI FT4232H quad-port USB-serial adapters on each Jetson providing 16 total ports. '
    'WiFi (5 GHz, WPA2-PSK) exists only on a dedicated access point at 10.0.0.200 for crew tablet '
    'monitoring; no safety-critical traffic ever traverses WiFi.'
))

story.append(add_heading('2.2 Jetson Cluster Roles', h2_style, 1))

jetson_data = [
    [H('Jetson'), H('IP'), H('Location'), H('Primary Services'), H('Models')],
    [TC('Alpha'), TCC('10.0.0.1'), TC('Wheelhouse'), TC('OpenCPN, NMEA Mux, MCP Server,<br/>Redis Leader, MQTT Broker,<br/>Provisioning Server'), TC('Qwen2.5-7B<br/>(4.7GB VRAM)')],
    [TC('Bravo'), TCC('10.0.0.2'), TC('Back Deck'), TC('DeepStream, YOLOv8-nano,<br/>Whisper STT, Piper TTS,<br/>Deck Safety, gRPC Server'), TC('YOLOv8-nano (6MB),<br/>Whisper-sm (500MB),<br/>Piper (50MB)')],
    [TC('Charlie'), TCC('10.0.0.3'), TC('Engine Room'), TC('Fish Species ID, Depth ML,<br/>Radar Analysis, Engine Telemetry,<br/>Provisioning Backup'), TC('YOLOv8 fine-tuned<br/>(50MB), XGBoost')],
]
story.append(Spacer(1, 12))
story.append(make_table(jetson_data, [1.1*cm, 2.0*cm, 2.5*cm, 5.5*cm, 4.0*cm]))
story.append(Paragraph('<b>Table 1.</b> Jetson Cluster Node Assignments', caption_style))
story.append(Spacer(1, 12))

story.append(add_heading('2.3 ESP32 Node Roles and Assignment', h2_style, 1))
story.append(P(
    'Each ESP32-S3 node runs the common VesselNode firmware framework and is assigned a specific '
    'role by the Jetson provisioning server. The role determines which sensors are connected, which '
    'actuators are controlled, which commands are accepted, and how the node behaves during standalone '
    'operation (when all Jetsons are unavailable). Eight node roles are defined: autopilot (PID heading '
    'control with compass and rudder), lighting controller (multi-zone deck and cabin lighting), engine '
    'monitor (RPM, temperature, oil pressure, coolant), deck equipment (winch, pot hauler, crane status), '
    'camera interface (PTZ control, power management), environmental sensor (wind, temp, humidity, barometer), '
    'bilge monitor (level sensing, pump control, flood alarm), and navigation aid (running lights, anchor '
    'light, day shape controller). Critical roles (autopilot, engine monitor) are deployed as dual-redundant '
    'pairs with independent sensor suites. All other roles use single ESP32s that are hot-swappable.'
))

node_data = [
    [H('Role'), H('Qty'), H('Redundant'), H('Connected To'), H('Standalone Behavior')],
    [TC('Autopilot'), TCC('2'), TCC('Yes'), TC('Compass, Rudder Encoder, Solenoids, Buttons, OLED'), TC('Full Iron Mike mode with buttons + OLED')],
    [TC('Lighting'), TCC('1'), TCC('No'), TC('MOSFET drivers x8, Physical override switches'), TC('Remembers last state, manual switches work')],
    [TC('Engine Mon.'), TCC('2'), TCC('Yes'), TC('Temp x3, Oil press., RPM, Coolant, Alarms'), TC('Independent alarm buzzer + LED warnings')],
    [TC('Deck Equip.'), TCC('1'), TCC('No'), TC('Winch relay, Pot hauler, Crane status, Load cell'), TC('Physical controls bypass ESP32 entirely')],
    [TC('Camera IF'), TCC('1'), TCC('No'), TC('PTZ motors x2, Camera power x4, Heater control'), TC('Fixed default PTZ position, cameras always on')],
    [TC('Env. Sensor'), TCC('1'), TCC('No'), TC('Anemometer, Barometer, Temp/Humidity, Rain gauge'), TC('Local display on OLED, alarm thresholds')],
    [TC('Bilge Mon.'), TCC('1'), TCC('No'), TC('Bilge level x2, Pump relay x2, Flood sensor'), TC('Autonomous pump control with high-water alarm')],
    [TC('Nav Aid'), TCC('1'), TCC('No'), TC('Running lights, Anchor light, Day shapes, Horn relay'), TC('Physical override switch, COLREGs compliance')],
]
story.append(Spacer(1, 12))
story.append(make_table(node_data, [2.2*cm, 0.8*cm, 1.8*cm, 5.0*cm, 5.3*cm]))
story.append(Paragraph('<b>Table 2.</b> ESP32 Node Roles and Standalone Behavior', caption_style))

# ========== SECTION 3: SOFTWARE STACK ==========
story.append(Spacer(1, 18))
story.append(add_heading('3. Software Stack and Language Choices', h1_style, 0))

story.append(add_heading('3.1 ESP32 Firmware: C with ESP-IDF', h2_style, 1))
story.append(P(
    'The ESP32 firmware is written entirely in C (C11 standard) using the ESP-IDF v5.2+ framework '
    'with FreeRTOS 10.5.1. This choice was made after careful evaluation of alternatives. Arduino '
    'was rejected because its hidden scheduler tasks introduce unpredictable timing jitter that is '
    'unacceptable for PID control loops, its String class causes heap fragmentation over long '
    'deployments, and it lacks proper dual-slot OTA support. MicroPython was rejected because the '
    'interpreter overhead consumes 40-60% of CPU time, garbage collection pauses of 10-50ms violate '
    'real-time deadlines, and it provides no access to ESP-IDF security features. Rust on ESP32 was '
    'rejected due to incomplete ESP32 peripheral support in the HAL, limited community examples for '
    'marine-specific peripherals, and significantly longer development cycles. The cJSON library '
    '(single-file, approximately 600 lines of code) handles JSON parsing with arena allocation to '
    'prevent heap fragmentation. The build system uses CMake with ESP-IDF\'s component system for '
    'modular role code.'
))

story.append(add_heading('3.2 Jetson Software: Python 3.11+', h2_style, 1))
story.append(P(
    'Python 3.11+ is the primary language for all Jetson software, selected for its native integration '
    'with the ML/AI ecosystem. Ollama provides the LLM runtime for Qwen2.5-7B with GPU acceleration via '
    'llama.cpp. TensorRT 10.x handles quantized inference (FP16/INT8) for all vision models. DeepStream '
    '7.0+ manages multi-camera video pipelines with hardware-accelerated decoding. faster-whisper with '
    'CTranslate2 runs speech-to-text on the GPU, while Piper TTS runs on the CPU cores (no GPU needed '
    'for voice synthesis). Porcupine provides the "Hey Helm" wake word detection. The NMEA multiplexer '
    'is the one component written in C (approximately 2000 lines using epoll()) because Python\'s '
    'asyncio serial handling cannot guarantee the sub-100-microsecond forwarding latency required '
    'by the autopilot. Redis 7.x provides shared state caching and leader election. Mosquitto MQTT '
    'handles telemetry pub/sub. gRPC (Protocol Buffers over HTTP/2) handles synchronous inter-Jetson '
    'RPC calls. SQLite 3 stores node settings, calibration data, and catch records.'
))

sw_data = [
    [H('Layer'), H('Technology'), H('Version'), H('Purpose')],
    [TC('ESP32 Language'), TC('C (C11)'), TC('-'), TC('Real-time firmware, hardware control')],
    [TC('ESP32 Framework'), TC('ESP-IDF'), TC('v5.2+'), TC('RTOS, drivers, OTA, NVS')],
    [TC('ESP32 RTOS'), TC('FreeRTOS'), TC('10.5.1'), TC('Task scheduling, IPC')],
    [TC('ESP32 JSON'), TC('cJSON'), TC('1.7.x'), TC('Protocol parsing, arena alloc')],
    [TC('Jetson OS'), TC('Ubuntu LTS'), TC('22.04'), TC('Base operating system')],
    [TC('JetPack SDK'), TC('NVIDIA JetPack'), TC('6.0+'), TC('CUDA, cuDNN, TensorRT')],
    [TC('LLM Runtime'), TC('Ollama'), TC('latest'), TC('Qwen2.5-7B inference')],
    [TC('Vision Pipeline'), TC('DeepStream'), TC('7.0+'), TC('Multi-camera GPU decode')],
    [TC('Object Detection'), TC('Ultralytics YOLO'), TC('v8.x'), TC('Fish, POB, debris detection')],
    [TC('Speech-to-Text'), TC('faster-whisper'), TC('1.0+'), TC('Voice command recognition')],
    [TC('Text-to-Speech'), TC('Piper TTS'), TC('1.2+'), TC('Voice response output')],
    [TC('Wake Word'), TC('Porcupine'), TC('3.0+'), TC('"Hey Helm" detection')],
    [TC('Shared State'), TC('Redis'), TC('7.x'), TC('Cache, leader election')],
    [TC('Message Bus'), TC('Mosquitto MQTT'), TC('2.0+'), TC('Telemetry pub/sub')],
    [TC('RPC'), TC('gRPC'), TC('1.60+'), TC('Inter-Jetson synchronous calls')],
    [TC('Database'), TC('SQLite'), TC('3.x'), TC('Node DB, catch records')],
    [TC('NMEA Mux'), TC('Custom C daemon'), TC('1.0'), TC('Instrument data routing')],
    [TC('Chartplotter'), TC('OpenCPN'), TC('5.8+'), TC('Navigation, route planning')],
]
story.append(Spacer(1, 12))
story.append(make_table(sw_data, [3.0*cm, 3.8*cm, 2.5*cm, 6.0*cm]))
story.append(Paragraph('<b>Table 3.</b> Complete Software Stack', caption_style))

# ========== SECTION 4: HOT-SWAP AND PROVISIONING ==========
story.append(Spacer(1, 18))
story.append(add_heading('4. Hot-Swap Provisioning System', h1_style, 0))

story.append(add_heading('4.1 Node Identity and Auto-Provisioning', h2_style, 1))
story.append(P(
    'Every ESP32-S3 has a unique identity derived from its factory-programmed MAC address, optionally '
    'supplemented by an external AT24C256 EEPROM chip that stores a persistent node ID assigned during '
    'initial commissioning. On power-up, each ESP32 runs a Power-On Self-Test (POST) lasting approximately '
    '800 milliseconds, verifying flash integrity (CRC-32), RAM functionality (walking ones test), I2C bus '
    'scan (device detection at known addresses), NVS integrity (namespace checksums), and sensor reads '
    '(compass heading, rudder angle, power voltage). After POST, the node announces itself on the RS-422 '
    'bus with a JSON identity message containing its MAC address, firmware version, and NVS role assignment. '
    'If the NVS contains a valid role and firmware version matches the Jetson database, the node enters '
    'normal CONNECTED operation immediately. If the node is unknown (new ESP32 from the spare kit) or has '
    'a firmware version mismatch, the Jetson provisioning server takes over.'
))
story.append(P(
    'The provisioning workflow proceeds as follows: (1) The provisioning server receives the announce '
    'message and queries the node database (SQLite on Jetson-Alpha, replicated to Bravo and Charlie every '
    '5 minutes via rsync). (2) If the MAC address is found in the database, the server checks the stored '
    'firmware version against the node\'s reported version. (3) If a firmware update is needed, the server '
    'initiates a chunked binary transfer over the serial link at 115200 baud, sending 4KB chunks with '
    'per-chunk CRC-16 verification and a final SHA-256 hash of the complete image. (4) The ESP32 writes '
    'the image to the inactive OTA slot (dual-slot flash: factory 4MB + ota_0 4MB), verifies the hash, '
    'and reboots into the new firmware. (5) After reboot, the node re-announces, and the server pushes '
    'calibration data from the database to NVS. (6) The node runs its role-specific self-tests, and if '
    'passing, enters normal operation. The entire provisioning cycle from power-on to operational takes '
    'approximately 2 minutes, most of which is the firmware transfer at serial baud rates. For previously '
    'provisioned nodes that only need calibration data refresh, the time drops to under 10 seconds.'
))

story.append(add_heading('4.2 Captain Hot-Swap Workflow', h2_style, 1))
story.append(P(
    'The hot-swap procedure is designed to be executable by a captain at sea with no tools beyond '
    'the spare parts kit. When an autopilot PRIMARY ESP32 fails, the BACKUP unit takes over in under '
    '100 milliseconds through an automatic failover mechanism: the STANDBY ESP32 detects the absence '
    'of the PRIMARY\'s heartbeat GPIO pulse for 500ms, enables its own relay on the relay selector '
    'board (which physically connects the STANDBY\'s output drivers to the solenoid MOSFET gates), '
    'and assumes PID control using its own sensor readings and heading target. The captain sees '
    '"BACKUP ACTIVE" on the STANDBY\'s OLED display and a single-beep alert. At the next convenient '
    'moment (which could be immediately at sea if conditions allow), the captain retrieves a pre-packaged '
    '"AUTOPILOT NODE" ESP32 from the waterproof Pelican case, removes the failed unit (M12 connector '
    'plus two mounting screws), plugs in the replacement, and the system auto-provisions it as described '
    'above. The new unit becomes PRIMARY after self-test validation, and the old BACKUP returns to '
    'standby mode. Total captain intervention time: approximately 2 minutes. The backup ESP32 kept the '
    'boat on course throughout the entire process.'
))

# ========== SECTION 5: DUAL REDUNDANCY ==========
story.append(Spacer(1, 18))
story.append(add_heading('5. Dual-Redundant Architecture', h1_style, 0))

story.append(add_heading('5.1 True Sensor Redundancy', h2_style, 1))
story.append(P(
    'The critical design decision for the dual-redundant autopilot architecture is true sensor '
    'redundancy: each ESP32 in the pair has its own independent BNO085 compass, AS5048A rudder '
    'encoder, SSD1306 OLED display, and TMP117 temperature sensor. This approach was chosen over '
    'shared-sensor architectures because sharing an I2C bus between two ESP32 masters creates '
    'arbitration complexity and a single sensor failure would disable both units. With independent '
    'sensors, a compass failure on one ESP32 does not affect the other, and the cross-check protocol '
    'can detect sensor disagreements. The two ESP32s communicate via a dedicated 3-wire UART link '
    '(TX, RX, GND at 115200 baud) plus three GPIO lines: a heartbeat line (PRIMARY pulls LOW for '
    '10ms every 100ms), a role-assert line (HIGH = asserting ACTIVE), and a preference jumper '
    '(strap HIGH on the designated PRIMARY unit).'
))

story.append(add_heading('5.2 Relay Selector Board', h2_style, 1))
story.append(P(
    'The output stage uses a relay selector board with two electromechanical relays (Omron '
    'G6B-1114P-US-DC5) that physically connect one ESP32\'s solenoid drive outputs to the MOSFET '
    'gate driver inputs at a time. The relay selector provides hardware-enforced mutual exclusion: '
    'both relay coils are in a break-before-make configuration, meaning there is a brief period '
    '(approximately 10ms) where neither ESP32 is connected to the solenoid drivers during a failover '
    'transition. During this 10ms window, the MOSFET gate pull-down resistors hold the gates LOW, '
    'keeping all solenoids de-energized. This is safe because the spring-center hydraulic valve '
    'maintains rudder position during brief power interruptions. The relay coils are driven by the '
    'role-assert GPIO on each ESP32: only the ACTIVE ESP32 asserts its GPIO HIGH, which energizes '
    'its relay and connects its drive signals to the MOSFET gates. A hardware interlock prevents '
    'both relays from being energized simultaneously even if both GPIOs go HIGH due to a firmware bug.'
))

story.append(add_heading('5.3 Failover State Machine and Timing', h2_style, 1))
story.append(P(
    'The failover detection and transition process is tightly specified. The STANDBY ESP32 monitors '
    'the PRIMARY\'s heartbeat GPIO line with an interrupt-driven timer. If no heartbeat edge is '
    'detected within 500ms, the STANDBY initiates failover. The transition timing is as follows: '
    'heartbeat timeout detection (500ms worst case, typically detects within 100-200ms), role-assert '
    'GPIO activation and relay coil energization (10ms relay actuation time), solenoid driver '
    'connection verification (reading relay status contact, 5ms), PID state initialization '
    '(capture current heading as target, 1ms), and first PID cycle execution (100ms period). '
    'The total worst-case transition time from PRIMARY failure to STANDBY actively controlling the '
    'rudder is approximately 616ms, with typical performance around 216ms. During the transition, '
    'the heading error accumulates at the vessel\'s natural rate of turn (typically 1-5 degrees per '
    'second in moderate seas), resulting in a heading deviation of approximately 0.2-0.5 degrees '
    'that the PID controller corrects within one to two cycles after assuming control.'
))

# ========== SECTION 6: CALIBRATION ==========
story.append(Spacer(1, 18))
story.append(add_heading('6. Dockside Onboarding and Calibration', h1_style, 0))

story.append(add_heading('6.1 Eight-Step Commissioning Wizard', h2_style, 1))
story.append(P(
    'The dockside setup procedure is designed to replicate the professional commissioning experience '
    'of modern ComNav and Simrad high-end autopilots. The wizard can be driven entirely from the '
    'ESP32\'s OLED display and four buttons (no laptop required), or from the Jetson\'s enhanced '
    'display with real-time data graphs. A voice-guided option is also available through the "Hey Helm" '
    'wake word interface. The eight steps are: (1) Vessel Configuration, where the captain enters '
    'vessel type, length, displacement, max speed, steering type, and number of engines; (2) Compass '
    'Calibration, where the BNO085 performs hard and soft iron correction during a 360-degree rotation '
    'of the vessel (or a handheld swing at dock), producing a 36-point deviation table stored in NVS; '
    '(3) Rudder Calibration, with three sub-steps for center finding (median filter over AS5048A raw '
    'readings with wheel centered), port and starboard limit detection (drive to mechanical stops with '
    'a 2-degree software margin), and counter-rudder measurement (engage autopilot, command three '
    'different headings, measure overshoot, iteratively adjust counter-rudder gain); (4) Yaw Damping '
    'Setup, where FFT-based oscillation detection identifies yaw instability and the D gain is '
    'increased until dampened; (5) Response Speed Testing, where a full 30-degree heading change '
    'benchmark measures latency, rise time, overshoot, settling time, and steady-state error; '
    '(6) Circle Test, where the vessel completes a full 360-degree turn at cruise speed while the '
    'system verifies compass linearity (quadrant-by-quadrant pass/fail with a 5-degree threshold); '
    '(7) Alarm Tests, including kill switch, power cycle (must boot to STANDBY), and off-course '
    'timeout verification; and (8) Save and Finalize, where all calibration data is atomically '
    'written to NVS with CRC-32 integrity protection on both ESP32s and backed up to the Jetson '
    'SQLite database.'
))

story.append(add_heading('6.2 NVS Persistence Architecture', h2_style, 1))
story.append(P(
    'The ESP-IDF Non-Volatile Storage (NVS) system provides wear-leveled key-value storage with '
    'approximately 100,000 write cycles per sector. The autopilot node uses 48+ NVS keys across '
    'three namespaces: "identity" (node_id, role, firmware_version, provisioning_state), "settings" '
    '(rudder_center_raw, rudder_port_limit, rudder_stbd_limit, pid_gains P/I/D/DD/PR/FF, compass_'
    'calibration_blob, deviation_table, counter_rudder_gain, yaw_damping_gain, vessel_type, profile_'
    'presets), and "settings_backup" (mirror copy for integrity verification). Write timing is '
    'strategically managed: calibration data (compass, rudder) is written immediately upon successful '
    'calibration with a dual-copy strategy (write to backup namespace first, verify read-back, then '
    'write to primary). Runtime state (last heading, last mode) uses deferred writes, flushed to NVS '
    'only on graceful shutdown or mode change. PID gains and profile presets, which change rarely, '
    'are written immediately on change. A monotonic settings_version counter is maintained in both '
    'NVS and the Jetson database; the ESP32 accepts only settings updates with a version number '
    'greater than its current value, preventing stale overwrites during database synchronization.'
))

# ========== SECTION 7: MARINE AI ==========
story.append(Spacer(1, 18))
story.append(add_heading('7. Marine AI and Vision Systems', h1_style, 0))

story.append(add_heading('7.1 Fish Species Identification', h2_style, 1))
story.append(P(
    'The fish species identification system employs a novel bin-based weakly-supervised learning '
    'approach that eliminates the need for manual image labeling by the crew during normal fishing '
    'operations. Four USB3 cameras (Arducam IMX477, 1080p, with global shutter options) are positioned '
    'on the back deck: two overlooking the sorting table and fish bins, one providing forward-looking '
    'navigation aid, and one monitoring the engine room. The key innovation is that the sorting table '
    'cameras observe both the fish being processed and which bin they are placed into. When a crew '
    'member places a fish into the "cod bin," the system automatically associates that fish\'s visual '
    'appearance (captured frame) with the "cod" species label. This creates a continuously growing '
    'training dataset specific to this boat\'s catch, this camera angle, and this lighting condition, '
    'without requiring any additional effort from the crew.'
))
story.append(P(
    'The training pipeline runs overnight on Jetson-Charlie. A base YOLOv8-nano model pre-trained '
    'on COCO is fine-tuned using transfer learning on the accumulated dataset. The fine-tuning process '
    'uses an 80/20 train/validation split, trains for 100 epochs with early stopping (patience=15), '
    'and evaluates using mean Average Precision (mAP@0.5). If validation accuracy exceeds 90%, the '
    'new model is exported to TensorRT format (FP16 quantization) and deployed to Jetson-Bravo via '
    'rsync. If accuracy is below 90%, the system logs the result and requests more data. The model '
    'versioning scheme uses sequential numbering (model_v001.pt, model_v002.pt) with metadata '
    'recording the training date, species count, accuracy metrics, and number of training images. '
    'Rollback is supported: if a newly deployed model produces anomalous results (detected by a '
    'statistical divergence check on prediction confidence scores), the previous model is automatically '
    'restored. The target performance is greater than 85% species identification accuracy after 4 weeks '
    'of normal fishing operations, improving to greater than 90% after 8 weeks as the training dataset '
    'grows and captures seasonal and lighting variations.'
))

story.append(add_heading('7.2 Catch Rate Tracking and Compliance', h2_style, 1))
story.append(P(
    'The vision system integrates with vessel instrumentation to produce comprehensive catch reports. '
    'If a serial-connected scale is available (common on commercial fishing vessels), its weight readings '
    'are associated with individual fish or bin totals via the camera timestamp. A measuring board with '
    'visual reference markers allows OpenCV-based length measurement from the camera image (calibrated '
    'to within plus or minus 1 centimeter using checkerboard calibration). The automated haul report '
    'includes species breakdown (count, weight, average size per species), catch rate (fish per hour and '
    'kilograms per hour), geographic location (from GPS NMEA data), time-stamped entries for fisheries '
    'compliance, and length-frequency distributions for stock assessment. For quota tracking, the system '
    'maintains running totals by species and alerts the captain when approaching quota limits with '
    'progressive warnings at 75%, 90%, and 100% of allocated quota. The automated VTR (Vessel Trip '
    'Report) / electronic logbook generation produces regulatory-compliant reports that can be '
    'transmitted via satellite when connectivity is available.'
))

story.append(add_heading('7.3 Crew Safety Systems', h2_style, 1))
story.append(P(
    'Person-overboard (POB) detection uses the YOLOv8 "person" class with dedicated alert logic. '
    'The forward-looking camera continuously scans the water surface around the vessel. When a person '
    'is detected in the water (distinguished from crew on deck by position analysis relative to vessel '
    'geometry), the system triggers an immediate multi-modal alert: a loud alarm through the deck '
    'speaker, a visual alert on all displays, a voice announcement ("MAN OVERBOARD"), and automatic '
    'GPS waypoint marking of the detection location. The alert-to-detection latency target is under '
    '2 seconds. Winch and gear monitoring uses optical character recognition (OCR) on the winch tension '
    'gauge display to detect overload conditions and alert the crew. Engine room cameras combined with '
    'temperature sensor data enable predictive maintenance alerts (e.g., "Coolant temperature trending '
    'up - check raw water intake"). Night operations are supported by 850nm IR LED illumination arrays '
    'on the sorting table, enabling 24-hour fish counting and species identification even when the '
    'visible-light cameras would be ineffective.'
))

# ========== SECTION 8: FAILURE MODES ==========
story.append(Spacer(1, 18))
story.append(add_heading('8. Failure Mode Analysis', h1_style, 0))
story.append(P(
    'The system is designed around the principle of graceful degradation: every failure mode has been '
    'analyzed, and the automatic response ensures the vessel remains safe and controllable. The following '
    'table summarizes the 21 identified failure modes with their detection methods, automatic responses, '
    'and required captain actions. The failure modes are organized by severity: Critical failures require '
    'immediate captain awareness, Major failures degrade functionality but maintain safety, and Minor '
    'failures reduce convenience features only.'
))

fail_data = [
    [H('ID'), H('Failure'), H('Detection'), H('Auto Response'), H('Captain Action')],
    [TCC('F01'), TC('ESP32 PRIMARY dies'), TC('Heartbeat timeout 500ms'), TC('BACKUP takes over <100ms'), TC('Replace at convenience')],
    [TCC('F02'), TC('Both ESP32s die'), TC('No heartbeat on either'), TC('Solenoids spring-center'), TC('Manual steering, replace ASAP')],
    [TCC('F03'), TC('Compass failure'), TC('No I2C data for 500ms'), TC('Alarm, disengage AP'), TC('Replace compass sensor')],
    [TCC('F04'), TC('Rudder encoder fail'), TC('SPI read timeout'), TC('Alarm, disengage AP'), TC('Replace encoder')],
    [TCC('F05'), TC('Jetson-Alpha dies'), TC('No ICMP 3x (3s)'), TC('Bravo becomes leader'), TC('Repair Alpha at dock')],
    [TCC('F06'), TC('All Jetsons die'), TC('No MQTT brokers (10s)'), TC('ESP32 standalone mode'), TC('Buttons + OLED work')],
    [TCC('F07'), TC('All power lost'), TC('Voltage < 8V'), TC('Everything stops'), TC('Restore power')],
    [TCC('F08'), TC('NMEA bus fails'), TC('No valid sentences 5s'), TC('I2C compass still works'), TC('Heading hold works, track lost')],
    [TCC('F09'), TC('RS-422 link fails'), TC('No Jetson heartbeat 2s'), TC('Standalone mode'), TC('Repair cable')],
    [TCC('F10'), TC('Kill switch activated'), TC('GPIO interrupt'), TC('Immediate disengage'), TC('Reset kill switch')],
    [TCC('F11'), TC('Solenoid stuck ON'), TC('Current > 4A, no rudder move'), TC('Force OFF, alarm'), TC('Manual steering')],
    [TCC('F12'), TC('Clutch won\'t engage'), TC('Current < 0.5A after 500ms'), TC('CLUTCH_FAULT alarm'), TC('Check hydraulics')],
    [TCC('F13'), TC('Overvoltage > 16V'), TC('ADC reads > 16V'), TC('Disengage, alarm'), TC('Check alternator')],
    [TCC('F14'), TC('Undervoltage < 8V'), TC('ADC reads < 8V'), TC('Disengage, alarm'), TC('Check battery')],
    [TCC('F15'), TC('GPS fix lost'), TC('GGA fix_quality = 0'), TC('Track to AUTO mode'), TC('Check GPS antenna')],
    [TCC('F16'), TC('WiFi down'), TC('No MQTT connect 30s'), TC('No effect on safety'), TC('No action needed')],
    [TCC('F17'), TC('OLED display fails'), TC('I2C NACK on 0x3C'), TC('Buzzer/LED backup'), TC('Replace at dock')],
    [TCC('F18'), TC('EEPROM corrupt'), TC('NVS CRC mismatch'), TC('Use defaults, flag'), TC('Re-calibrate')],
    [TCC('F19'), TC('OTA flash fails'), TC('SHA-256 mismatch'), TC('Rollback to old fw'), TC('Retry or replace')],
    [TCC('F20'), TC('Watchdog timeout'), TC('MAX6818 WDO'), TC('ESP32 hard reset'), TC('Check for cause')],
    [TCC('F21'), TC('I2C bus lockup'), TC('SCL LOW > 25ms'), TC('9 clock recovery'), TC('Check wiring')],
]
story.append(Spacer(1, 12))
story.append(make_table(fail_data, [1.1*cm, 3.5*cm, 3.5*cm, 4.0*cm, 4.0*cm]))
story.append(Paragraph('<b>Table 4.</b> Complete Failure Mode Analysis (21 Modes)', caption_style))

# ========== SECTION 9: BOM ==========
story.append(Spacer(1, 18))
story.append(add_heading('9. Bill of Materials and Cost Estimate', h1_style, 0))

bom_data = [
    [H('Category'), H('Item'), H('Qty'), H('Unit Cost'), H('Total')],
    [TC('Compute'), TC('Jetson Orin Nano Super 8GB (module + carrier + NVMe + PSU + enclosure)'), TCC('3'), TCC('$350'), TCC('$1,050')],
    [TC('MCU Nodes'), TC('ESP32-S3-WROOM-1-N8R8 (module + PCB + passives + enclosure)'), TCC('14'), TCC('$12'), TCC('$168')],
    [TC('Compass'), TC('BNO085 9-DOF IMU'), TCC('4'), TCC('$15'), TCC('$60')],
    [TC('Rudder'), TC('AS5048A Magnetic Rotary Encoder (14-bit)'), TCC('3'), TCC('$12'), TCC('$36')],
    [TC('Display'), TC('SSD1306 OLED 128x64'), TCC('8'), TCC('$3'), TCC('$24')],
    [TC('Solenoid Driver'), TC('IRLZ44N MOSFET + TC4420 gate driver + flyback + relay board'), TCC('2'), TCC('$45'), TCC('$90')],
    [TC('Current Sense'), TC('ACS712-5A + ADS1115 I2C ADC'), TCC('3'), TCC('$8'), TCC('$24')],
    [TC('Watchdog'), TC('MAX6818 external hardware watchdog'), TCC('8'), TCC('$4'), TCC('$32')],
    [TC('RS-422'), TC('FTDI FT4232H quad-port USB-serial + SN75176 transceivers'), TCC('4'), TCC('$35'), TCC('$140')],
    [TC('Power'), TC('LM2596 buck + LM1117 LDO + TVS + fuse + wiring per node'), TCC('8'), TCC('$8'), TCC('$64')],
    [TC('Ethernet'), TC('Netgear GS308T managed Gigabit switch'), TCC('1'), TCC('$40'), TCC('$40')],
    [TC('WiFi AP'), TC('Marine-grade 5GHz access point'), TCC('1'), TCC('$50'), TCC('$50')],
    [TC('UPS'), TC('LiFePO4 12V 20Ah battery + diode-OR + charge controller'), TCC('1'), TCC('$250'), TCC('$250')],
    [TC('Cameras'), TC('Arducam IMX477 USB3 + IR LED arrays + mounting'), TCC('4'), TCC('$65'), TCC('$260')],
    [TC('Audio'), TC('USB audio interface + marine speakers + microphone'), TCC('1'), TCC('$80'), TCC('$80')],
    [TC('Connectors'), TC('M12 8-pin connectors + cable + glands (per node)'), TCC('8'), TCC('$15'), TCC('$120')],
    [TC('Enclosures'), TC('IP67 aluminum enclosures (Jetsons, custom ESP32 boxes)'), TCC('11'), TCC('$25'), TCC('$275')],
    [TC('Cable'), TC('Marine-grade RS-422, Ethernet, NMEA, power cable'), TCC('1 lot'), TCC('$200'), TCC('$200')],
    [TC('Sensors'), TC('Temp, pressure, bilge, anemometer, load cells, etc.'), TCC('1 lot'), TCC('$300'), TCC('$300')],
    [TC('Spares'), TC('Spare ESP32s, compasses, encoders, MOSFET boards, fuses'), TCC('1 kit'), TCC('$700'), TCC('$700')],
    [TC(''), TC('<b>TOTAL ESTIMATED</b>'), TCC(''), TCC(''), TCC('<b>$3,963</b>')],
]
story.append(Spacer(1, 12))
story.append(make_table(bom_data, [2.2*cm, 7.0*cm, 1.0*cm, 2.2*cm, 2.2*cm]))
story.append(Paragraph('<b>Table 5.</b> Bill of Materials Estimate', caption_style))
story.append(P(
    'Note: This BOM represents the core electronics and computing components only. It excludes the '
    'vessel\'s existing hydraulic steering system, NMEA instruments (GPS, depth sounder, wind sensor), '
    'and physical vessel modifications. The $3,963 total demonstrates that the complete vessel '
    'robotics platform is achievable at a cost comparable to a single high-end commercial autopilot '
    'system, while providing exponentially more capability. For vessels requiring enhanced vision '
    'performance, upgrading Jetson-Bravo from an Orin Nano Super (8GB) to an Orin NX 16GB adds '
    'approximately $400 but doubles VRAM capacity for larger AI models. The spare parts kit at $700 '
    'ensures that any single component failure can be resolved at sea without waiting for shore-based '
    'suppliers, a critical capability for commercial fishing operations that may remain at sea for '
    'weeks at a time.'
))

# ========== SECTION 10: IMPLEMENTATION ROADMAP ==========
story.append(Spacer(1, 18))
story.append(add_heading('10. Implementation Roadmap', h1_style, 0))
story.append(P(
    'The implementation is organized into four phases, designed to deliver increasing capability '
    'while ensuring each phase produces a usable system on its own. Phase 1 (weeks 1-4) establishes '
    'the core autopilot with a single ESP32 and Jetson-Alpha: VesselNode firmware framework, autopilot '
    'role module with PID control, basic NMEA integration, JSON serial protocol, and the dockside '
    'calibration wizard. By the end of Phase 1, the system provides a fully functional Iron Mike '
    'autopilot with Jetson voice control, equivalent to a commercial ComNav unit but with AI enhancement. '
    'Phase 2 (weeks 5-8) adds the dual-redundant autopilot, the second and third Jetsons with cluster '
    'communication (Ethernet, gRPC, MQTT, Redis), leader election, and the remaining ESP32 node roles '
    '(lighting, engine monitor, bilge, environmental, navigation aid). By the end of Phase 2, the full '
    'vessel network is operational with redundancy on critical systems.'
))
story.append(P(
    'Phase 3 (weeks 9-12) deploys the vision and AI systems: camera installation on Jetson-Bravo, '
    'YOLOv8-nano deployment with TensorRT, Whisper STT and Piper TTS integration, the "Hey Helm" '
    'wake word interface, and initial fish species data collection. Phase 4 (weeks 13-16) focuses '
    'on AI training and optimization: fish species model fine-tuning, catch rate tracking, regulatory '
    'compliance logging, POB detection, and long-duration sea trials with performance validation. '
    'Each phase concludes with a documented set of acceptance criteria and a sign-off process that '
    'validates the system against the failure mode table and redundancy requirements before proceeding '
    'to the next phase.'
))

road_data = [
    [H('Phase'), H('Weeks'), H('Deliverables'), H('Acceptance Criteria')],
    [TC('1: Core AP'), TCC('1-4'), TC('Single ESP32 autopilot + Jetson-Alpha voice control,<br/>NMEA integration, dockside calibration, Iron Mike mode'), TC('PID heading hold within 3 degrees,<br/>Jetson commands work, fails to standalone')],
    [TC('2: Cluster'), TCC('5-8'), TC('Dual-redundant autopilot, 3x Jetson cluster,<br/>all ESP32 roles, leader election, MQTT telemetry'), TC('Failover <100ms, all nodes operational,<br/>cluster survives any single Jetson failure')],
    [TC('3: Vision'), TCC('9-12'), TC('Camera system, YOLOv8 deployment, STT/TTS,<br/>wake word, initial fish data collection'), TC('30fps object detection, <3s voice latency,<br/>IR night operation verified')],
    [TC('4: AI Train'), TCC('13-16'), TC('Fish ID model fine-tuning, catch tracking,<br/>POB detection, compliance logging, sea trials'), TC('>85% fish ID after 4 weeks data,<br/>all 21 failure modes tested')],
]
story.append(Spacer(1, 12))
story.append(make_table(road_data, [2.0*cm, 1.5*cm, 5.5*cm, 5.5*cm]))
story.append(Paragraph('<b>Table 6.</b> Four-Phase Implementation Roadmap', caption_style))

# ========== SECTION 11: CONFIGURATION FILES ==========
story.append(Spacer(1, 18))
story.append(add_heading('11. Configuration File Inventory', h1_style, 0))
story.append(P(
    'The system is configured through a comprehensive set of JSON files maintained on the Jetson '
    'cluster and selectively pushed to ESP32 nodes during provisioning. On the Jetson side, YAML '
    'files define service configurations (Docker Compose, systemd units) while JSON files define '
    'runtime parameters for the ESP32 nodes, cluster communication, and calibration data. The ESP32 '
    'stores its relevant configuration subset in NVS flash for standalone operation. The following '
    'table documents every configuration file in the system with its location, format, purpose, and '
    'the subsystem that consumes it.'
))

config_data = [
    [H('File'), H('Location'), H('Format'), H('Purpose')],
    [TC('firmware_config.json'), TC('/config/'), TC('JSON'), TC('PID gains, sensor config, serial baud rates, safety thresholds')],
    [TC('pin_config.json'), TC('/config/'), TC('JSON'), TC('Complete GPIO pin assignments per node')],
    [TC('safety_config.json'), TC('/config/'), TC('JSON'), TC('Watchdog, solenoid limits, alarm definitions, fail-safe behaviors')],
    [TC('jetson_mcp_tools.json'), TC('/config/'), TC('JSON'), TC('MCP tool definitions for LLM voice interface')],
    [TC('task_config.json'), TC('/config/'), TC('JSON'), TC('FreeRTOS task definitions, queues, mutexes, event groups')],
    [TC('nmea_sentence_map.json'), TC('/config/'), TC('JSON'), TC('NMEA sentence parsing and generation rules')],
    [TC('node_roles.json'), TC('/vessel_platform/config/'), TC('JSON'), TC('All 8 ESP32 role definitions with commands and calibration steps')],
    [TC('vessel_network_config.json'), TC('/vessel_platform/config/'), TC('JSON'), TC('Jetson IPs, ESP32 assignments, MQTT topics, gRPC services')],
    [TC('cluster_config.json'), TC('/vessel_platform/config/'), TC('JSON'), TC('Jetson cluster services, models, leader election, failover rules')],
    [TC('ota_provisioning_config.json'), TC('/vessel_platform/config/'), TC('JSON'), TC('Firmware vault paths, OTA protocol, node database schema')],
    [TC('calibration_config.json'), TC('/vessel_platform/config/'), TC('JSON'), TC('Vessel type presets, PID presets, NVS key definitions')],
    [TC('redundancy_config.json'), TC('/vessel_platform/config/'), TC('JSON'), TC('Dual-ESP32 failover timing, self-test, relay config')],
    [TC('docker-compose.yml'), TC('/opt/vessel/'), TC('YAML'), TC('Jetson service container definitions')],
    [TC('nmea_mux.conf'), TC('/opt/vessel/nmea/'), TC('INI'), TC('NMEA multiplexer daemon serial port and forwarding config')],
]
story.append(Spacer(1, 12))
story.append(make_table(config_data, [4.0*cm, 4.0*cm, 1.5*cm, 5.5*cm]))
story.append(Paragraph('<b>Table 7.</b> Complete Configuration File Inventory', caption_style))

# ========== SECTION 12: CONTRADICTION RESOLUTION ==========
story.append(Spacer(1, 18))
story.append(add_heading('12. Contradiction Resolution Summary', h1_style, 0))
story.append(P(
    'During the synthesis of six expert briefs and the original autopilot consensus document, 15 '
    'contradictions were identified and resolved. The most architecturally significant resolutions '
    'are summarized below. The complete resolution log with detailed rationale for each item is '
    'included in the full technical brief at /download/vessel_platform/16_master_consensus_architecture.txt.'
))

contra_data = [
    [H('#'), H('Conflict'), H('Resolution'), H('Rationale')],
    [TCC('1'), TC('Jetson model selection (Nano vs NX vs AGX)'), TC('Orin Nano Super 8GB for all 3 units'), TC('67 TOPS each, 201 total, $750 total cost. Upgrade path to NX if needed')],
    [TCC('4'), TC('Communication bus (CAN vs RS-422)'), TC('RS-422 serial at 115200 baud'), TC('Simpler, longer runs, debuggable with terminal. 2.5x headroom')],
    [TCC('6'), TC('Rudder encoder bus (I2C vs SPI)'), TC('SPI (HSPI) for AS5048A'), TC('Eliminates I2C contention with compass on dual-ESP32 systems')],
    [TCC('7'), TC('Database (Redis only vs InfluxDB+PG)'), TC('Redis + SQLite (PG/Influx optional Phase 3)'), TC('Redis for cache/election, SQLite for records. Minimal footprint')],
    [TCC('8'), TC('Network addressing (flat vs VLANs)'), TC('Flat 10.0.0.0/24'), TC('3 Jetsons do not justify VLAN complexity. WiFi AP isolated')],
    [TCC('9'), TC('Camera connection (USB vs PoE vs ESP32 bridge)'), TC('USB3 directly to Jetson-Bravo'), TC('Simpler, lower latency, no ESP32 overhead for video')],
    [TCC('11'), TC('Vision frame protocol (binary vs JSON)'), TC('TensorRT zero-copy, no serial'), TC('Cameras on USB, not on ESP32 serial bus. JSON for control only')],
    [TCC('14'), TC('WiFi on ESP32 nodes (yes vs no)'), TC('WiFi disabled on all ESP32s'), TC('Marine RF interference, reliability. WiFi AP on Jetson for monitoring only')],
]
story.append(Spacer(1, 12))
story.append(make_table(contra_data, [0.8*cm, 4.5*cm, 4.5*cm, 5.0*cm]))
story.append(Paragraph('<b>Table 8.</b> Key Contradiction Resolutions (15 Total)', caption_style))

# ========== BUILD ==========
doc.multiBuild(story)
print(f"PDF generated: {OUTPUT_PATH}")
print(f"Total story elements: {len(story)}")

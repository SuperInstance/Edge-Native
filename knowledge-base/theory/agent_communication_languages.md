# Agent Communication Languages and Multi-Agent Systems

**Knowledge Base Article** | NEXUS Robotics Platform
**Revision:** 1.0 | **Date:** 2026-03-29
**Classification:** Theoretical Foundations for A2A-Native Programming
**Cross-References:** [[Agent Communication & Runtime Model]], [[A2A-Native Language Design and Semantics]], [[Reflex Bytecode VM Specification]], [[Trust Score Algorithm Specification]], [[Distributed Intelligence Framework]], [[Master Consensus Architecture]], [[The Colony Thesis]]

---

## Table of Contents

1. [Introduction](#1-introduction)
2. [Foundation: Distributed AI (1980s)](#2-foundation-distributed-ai-1980s)
3. [Agent Communication Languages](#3-agent-communication-languages)
4. [Speech Act Theory Applied to Computing](#4-speech-act-theory-applied-to-computing)
5. [Coordination Mechanisms](#5-coordination-mechanisms)
6. [Ontologies for Agent Communication](#6-ontologies-for-agent-communication)
7. [Modern Agent Frameworks (2010s–2026)](#7-modern-agent-frameworks-2010s2026)
8. [Agent-Oriented Programming Languages](#8-agent-oriented-programming-languages)
9. [Trust and Reputation in Multi-Agent Systems](#9-trust-and-reputation-in-multi-agent-systems)
10. [Emergent Communication](#10-emergent-communication)
11. [Open Problems](#11-open-problems)
12. [Synthesis: NEXUS's Position in the Field](#12-synthesis-nexuss-position-in-the-field)
13. [References](#13-references)

---

## 1. Introduction

Agent Communication Languages (ACLs) and Multi-Agent Systems (MAS) constitute one of the foundational pillars of artificial intelligence research, spanning over four decades of theoretical development and practical engineering. From the earliest distributed problem-solving systems of the 1980s to the LLM-powered agent frameworks of the mid-2020s, the fundamental question has remained constant: **how should autonomous software entities communicate, coordinate, and collaborate to achieve goals that no single entity could accomplish alone?**

The NEXUS robotics platform represents a distinctive and architecturally significant entry point into this lineage. While the majority of ACL research has focused on cloud-based, text-mediated communication between software agents, NEXUS introduces an **A2A-native programming paradigm** in which agents communicate through **compiled bytecode deployed directly to embedded hardware**. An agent on one vessel does not send a text message to an agent on another vessel — it compiles an *intention* into a 32-opcode bytecode program and deploys it to the receiving agent's [[Reflex Bytecode VM Specification|bytecode VM]] running on an ESP32-S3 microcontroller. This article traces the complete intellectual history that makes NEXUS's approach both radical and inevitable.

The field can be organized along three axes:

- **Theoretical axis:** From speech act theory to formal semantics to computational trust models
- **Technological axis:** From the Actor model to KQML to Google's A2A protocol
- **Application axis:** From distributed sensor networks to autonomous marine vessels to LLM-based chatbots

This article covers all three axes comprehensively, with continuous cross-referencing to NEXUS's architectural decisions.

---

## 2. Foundation: Distributed AI (1980s)

### 2.1 The Birth of Multi-Agent Systems

The concept of multiple autonomous agents working together emerged from three parallel intellectual traditions in the late 1970s and early 1980s: distributed computing, artificial intelligence planning, and organizational theory. The central insight was that many real-world problems — factory scheduling, air traffic control, distributed sensor interpretation — were inherently distributed and could not be solved by a single monolithic reasoning system.

The Stanford Research Institute's (SRI) work on the Distributed Vehicle Monitoring Testbed (DVMT), led by Victor Lesser and Randall Davis, demonstrated that distributed problem-solving could outperform centralized approaches when the problem domain had natural decomposition boundaries. This work established the foundational assumption of multi-agent systems: **decomposition followed by coordination yields scalable intelligence.**

### 2.2 The Contract Net Protocol (Davis & Smith, 1983)

Reid Davis and Randall Smith published "Negotiation as a Metaphor for Distributed Problem Solving" in 1983, introducing the **Contract Net Protocol (CNP)** — arguably the most influential coordination mechanism in the history of multi-agent systems. The CNP models task allocation as a market-like bidding process:

1. **Task Announcement:** A manager agent broadcasts a description of a task to be performed.
2. **Bid Submission:** Potential contractor agents evaluate the task against their capabilities and submit bids containing estimated cost, completion time, and quality metrics.
3. **Award:** The manager evaluates bids using configurable criteria (lowest cost, fastest completion, best quality, or weighted combinations) and awards the contract to the winning bidder.
4. **Execution and Reporting:** The contractor executes the task and reports results back to the manager.

The elegance of CNP lies in its decentralization and fault tolerance. No single agent needs a global view of all capabilities — each agent only knows its own. The protocol is inherently robust: if a contractor fails, the manager can simply re-announce the task. This "announce-bid-award" pattern has been reinvented countless times under different names (service discovery, task allocation, resource brokering) but its essence remains unchanged.

**Mapping to NEXUS:** The [[Agent Communication & Runtime Model|NEXUS fleet task allocation]] architecture directly implements a Contract Net variant. When a fleet-level objective is decomposed (e.g., "search area X for target Y"), the lead Jetson broadcasts capability queries to all vessels. Each vessel responds with its current trust score, available sensor suite, and estimated completion time. The lead Jetson compiles vessel-specific bytecode sub-intentions and deploys them. The critical difference from classical CNP is that NEXUS contractors do not merely execute a task — they receive a *compiled program* that they execute autonomously on their local hardware, requiring no further communication with the manager during execution.

### 2.3 The Actor Model (Hewitt, 1973; Agha, 1986)

Carl Hewitt, Peter Bishop, and Richard Steiger introduced the **Actor model** in 1973 as a mathematical model of concurrent computation. The model's central thesis is deceptively simple: **everything is an actor, and the only way actors interact is through asynchronous message passing.**

An actor is an entity that:
1. **Receives messages** from other actors (asynchronously, in any order)
2. **Processes messages** one at a time (no true concurrency within a single actor)
3. **Sends messages** to other actors (including itself)
4. **Creates new actors** (dynamic topology)
5. **Modifies its own state** in response to received messages (encapsulation)

The Actor model's contributions to multi-agent systems are profound:

- **Encapsulation:** An actor's internal state is never directly accessible to other actors. This anticipates the object-oriented encapsulation principle and the agent autonomy principle in MAS.
- **Asynchronous communication:** Actors never block waiting for a reply. This eliminates deadlocks and enables true distributed execution.
- **Dynamic topology:** New actors can be created at runtime, allowing the system to adapt its structure to the problem.
- **Location transparency:** An actor can send a message to any other actor regardless of physical location.

Gul Agha's 1986 monograph *ACTORS: A Model of Concurrent Computation in Distributed Systems* formalized the model and introduced the concept of **actor migration** — moving an actor's execution from one processor to another — which is a direct ancestor of NEXUS's intention deployment across vessels.

**Mapping to NEXUS:** The NEXUS agent-to-agent model is a strict interpretation of the Actor model applied to physical hardware. Each ESP32 node running a [[Reflex Bytecode VM Specification|bytecode VM]] is an actor: it receives messages (bytecode programs via the wire protocol), processes them one at a time (sequential reflex execution within a tick), sends messages (telemetry via `EMIT_EVENT` syscalls), and modifies its own state (persistent variables in the VM). The critical insight that NEXUS borrows from the Actor model is that **the program IS the message** — a deployed reflex bytecode is simultaneously a message (from the sending agent) and a behavior (for the receiving agent). In classical Actor systems, a message carries *data*; in NEXUS, a message carries *code*. This distinction transforms the communication model from data-exchange to intention-deployment.

### 2.4 Blackboard Systems

Blackboard systems, pioneered by H. Penny Nii and colleagues at Carnegie Mellon University in the early 1980s (most notably the HEARSAY-II speech understanding system), introduced a fundamentally different coordination model: instead of point-to-point message passing, agents share a common structured memory space called the **blackboard**.

The blackboard architecture consists of three components:

1. **The Blackboard:** A globally accessible, hierarchically organized data structure (typically organized into levels of abstraction).
2. **Knowledge Sources (KS):** Independent modules (agents) that monitor the blackboard and contribute information when they recognize a pattern they can address.
3. **The Controller:** A scheduler that determines which knowledge source should act next, based on the current state of the blackboard and the potential contributions of each KS.

The blackboard model is inherently *data-driven* rather than *message-driven*. Knowledge sources do not communicate directly with each other; instead, they communicate *indirectly* by reading from and writing to the shared blackboard. This creates a loose coupling that makes the system easy to extend — adding a new knowledge source requires no changes to existing sources.

**Mapping to NEXUS:** NEXUS's architecture incorporates blackboard-like patterns at the Jetson cognitive layer. Multiple AI models (chat, vision, speech-to-text, text-to-speech) share a common state through MQTT topics and gRPC APIs. The fleet-level world model acts as a distributed blackboard: each vessel contributes sensor data and observations, and the fleet intelligence layer synthesizes a unified picture. However, NEXUS departs from the classical blackboard model at the ESP32 level — there is no shared memory between ESP32 nodes; they communicate exclusively through the wire protocol. This is a deliberate architectural choice: shared memory requires tight temporal coupling, while the wire protocol enables independent, autonomous execution even during communication loss.

### 2.5 Summary: 1980s Foundation and NEXUS Mapping

| 1980s Paradigm | Core Mechanism | NEXUS Equivalent |
|---------------|----------------|-----------------|
| Contract Net Protocol | Task announcement → bid → award | Fleet task allocation via capability discovery + bytecode deployment |
| Actor Model | Asynchronous message passing, encapsulation | Intention deployment via wire protocol; bytecode as message |
| Blackboard Systems | Shared structured memory, data-driven coordination | MQTT topics at Jetson layer; fleet world model |
| Distributed Problem Solving | Task decomposition + result composition | Intention decomposition → per-vessel compilation → result composition |

---

## 3. Agent Communication Languages

### 3.1 The Need for Standardization

By the early 1990s, the multi-agent systems community faced a fragmentation problem: every MAS implementation used its own ad-hoc communication protocol, making interoperability impossible. Two competing standards emerged to address this: KQML (1993) and FIPA-ACL (1997). Both shared the same fundamental architecture — a wrapper layer (the communication language) transporting a content expression (written in a content language) interpreted through a shared ontology. This "wrapper-content-ontology" architecture remains the template for all subsequent agent communication standards, including NEXUS's own [[A2A-Native Language Design and Semantics|Agent-Annotated Bytecode format]].

### 3.2 KQML (Knowledge Query and Manipulation Language, 1993)

KQML was developed by the ARPA Knowledge Sharing Effort, a DARPA-funded consortium that included researchers from SRI International, the University of Maryland, Lockheed, and others. The initial specification was documented by Tim Finin, Richard Fritzson, Don McKay, and Robin McEntire in 1993.

#### 3.2.1 Architecture

KQML defines two layers:

1. **The Communication Layer (performatives):** Defines the *type* of communicative act — e.g., is the sender informing, requesting, querying, or advertising? KQML defines 35+ performatives organized into categories.
2. **The Content Layer:** The actual information being communicated, expressed in a content language (typically [[#33-kif-knowledge-interchange-format|KIF]]).

A KQML message has the following structure:

```
(performative
  :sender    <agent-id>
  :receiver  <agent-id>
  :language  <content-language>
  :ontology  <ontology-name>
  :content   <content-expression>
)
```

#### 3.2.2 Performatives (Selection)

KQML defines over 35 performatives, organized into functional categories:

| Category | Performatives | Purpose |
|----------|--------------|---------|
| **Information Dissemination** | `tell`, `untell`, `deny`, `advertise`, `subscribe` | Sharing and managing information |
| **Information Request** | `ask-if`, `ask-one`, `ask-all`, `eos`, `stream-all` | Querying other agents |
| **Negotiation** | `broker-one`, `broker-all`, `recruit-one`, `recruit-all`, `recommend-one`, `recommend-all` | Task allocation and service discovery |
| **Capability Description** | `register`, `unregister`, `forward` | Agent capability management |
| **Error Handling** | `error`, `sorry` | Communicating failures |

Example KQML message:

```
(ask-one
  :sender   vessel-navigator
  :receiver weather-station
  :language KIF
  :ontology marine-weather
  :content  "(wind-speed > 25) ?"
)
```

#### 3.2.3 Why KQML Failed in Practice

Despite its intellectual influence, KQML failed to achieve widespread adoption. The reasons are instructive:

1. **Semantic vagueness:** KQML performatives were loosely defined, with no formal semantics. The meaning of `tell` versus `assert` versus `insert` was ambiguous and implementation-dependent.
2. **Ontology fragmentation:** KQML assumed agents shared an ontology but provided no standard for defining one. In practice, every KQML deployment used its own ontology, defeating the interoperability goal.
3. **No formal verification:** There was no way to verify whether a KQML message was coherent, whether the sender was authorized to perform the requested act, or whether the content was consistent with the ontology.
4. **Performance overhead:** The Lisp-like S-expression syntax was verbose and computationally expensive to parse, making it unsuitable for resource-constrained or real-time environments.
5. **Limited expressiveness for physical actions:** KQML was designed for knowledge-level communication (information exchange) and was awkward for expressing physical actions (move rudder, deploy sensor).

These failures directly informed NEXUS's design choices: the [[Reflex Bytecode VM Specification|bytecode ISA]] provides formal, deterministic semantics; the [[A2A-Native Language Design and Semantics|Agent-Annotated Bytecode format]] embeds ontology information in metadata; and the entire system is designed for real-time execution on microcontrollers.

### 3.3 FIPA-ACL (Foundation for Intelligent Physical Agents, 1997)

The Foundation for Intelligent Physical Agents (FIPA) was an IEEE-authorized standards body established in 1996 specifically to address KQML's shortcomings. FIPA published its Agent Communication Language specification in 1997, refined through subsequent iterations (FIPA 97, FIPA 98, FIPA 2000, FIPA 2002).

#### 3.3.1 Key Improvements over KQML

1. **Formal semantics:** FIPA-ACL defined its communicative acts using **speech act theory** (see [[#4-speech-act-theory-applied-to-computing|Section 4]]), with a formal specification of the *preconditions* (feasibility preconditions, rational effect) and *postconditions* (actual effect) of each act. This made it possible to reason about whether a communicative act was appropriate in a given context.

2. **Refined performative set:** FIPA-ACL reduced the performative set from KQML's 35+ to 22 communicative acts, organized into a cleaner taxonomy.

3. **Standardized interaction protocols:** FIPA defined not just individual messages but complete interaction patterns (protocols) such as the FIPA Request Interaction Protocol, the FIPA Contract Net Interaction Protocol, and the FIPA Subscribe Interaction Protocol.

4. **Better content language support:** FIPA-ACL was designed to work with SL (Semantic Language), a formal content language based on first-order logic with modal operators for belief, desire, and intention.

#### 3.3.2 The 22 FIPA-ACL Communicative Acts

| Act | Category | Description | Formal Preconditions |
|-----|----------|-------------|---------------------|
| `accept-proposal` | Acceptance | Accept a previously submitted proposal | Proposal was made by receiver |
| `agree` | Acceptance | Agree to perform a requested action | Agent intends and is capable |
| `cancel` | Canceling | Cancel a previously requested action | Action was previously requested |
| `cfp` (call for proposals) | Requesting | Request proposals for a given action | Agent needs a task performed |
| `confirm` | Informing | Confirm that a proposition is true | Agent believes proposition is true |
| `disconfirm` | Informing | Confirm that a proposition is false | Agent believes proposition is false |
| `failure` | Error | Report failure to perform a requested action | Action was previously agreed to |
| `inform` | Informing | Assert that a proposition is true | Agent believes proposition is true |
| `inform-if` | Querying | Inform whether a proposition is true | Agent knows the truth value |
| `inform-ref` | Querying | Inform the value of a reference | Agent knows the referent |
| `not-understood` | Error | Report that a message was not understood | Agent cannot interpret the message |
| `propagate` | Propagating | Propagate an action request to another agent | Agent knows another capable agent |
| `propose` | Proposing | Submit a proposal in response to a CFP | Agent can perform the proposed action |
| `proxy` | Proxying | Act as a proxy for another agent | Agent is authorized to act as proxy |
| `query-if` | Querying | Query whether a proposition is true | Agent believes receiver may know |
| `query-ref` | Querying | Query the value of a reference | Agent believes receiver may know |
| `refuse` | Refusing | Refuse to perform a requested action | Agent cannot or will not perform |
| `reject-proposal` | Rejecting | Reject a previously submitted proposal | Proposal was submitted by sender |
| `request` | Requesting | Request another agent to perform an action | Agent believes receiver is capable |
| `request-when` | Requesting | Request action when a condition becomes true | Agent believes condition may become true |
| `request-whenever` | Requesting | Request action whenever a condition becomes true | Condition may become true repeatedly |
| `subscribe` | Subscribing | Subscribe to changes in a referent | Referent exists and is observable |

#### 3.3.3 FIPA-ACL Message Structure

```
(inform
  :sender      agent:jade-platform-1@host:1099/JADE
  :receiver    agent:navigator@host:1099/JADE
  :content     "(obstacle-detected ?x 15.3)"
  :language    FIPA-SL
  :ontology    marine-navigation
  :reply-with  msg-12345
  :in-reply-to msg-12340
  :reply-by    2026-03-29T12:00:00Z
  :protocol    FIPA-Request
  :conversation-id  conv-789
)
```

FIPA-ACL's formal semantics were defined using a combination of:
- **Feasibility Preconditions (FP):** Conditions that must be true *before* the communicative act can be performed.
- **Rational Effect (RE):** The expected effect of the communicative act on the mental state of the participating agents.
- **Actual Effect (AE):** What actually happens after the act is performed.

For example, the `inform` act is formally defined as:
- **FP:** The sender believes the content is true, and the sender believes the receiver does not already know the content (or does not believe it).
- **RE:** The receiver comes to believe the content.
- **AE:** The receiver's belief set is updated (if the receiver accepts the inform).

#### 3.3.4 FIPA's Limitations

Despite its improvements over KQML, FIPA-ACL also struggled with adoption:

1. **Complexity:** The formal semantics, while rigorous, made FIPA-ACL difficult to implement correctly. Most developers found the full specification overwhelming.
2. **Mentalistic assumptions:** FIPA-ACL assumed that agents had beliefs, desires, and intentions (BDI) that could be formally represented and reasoned about. This assumption was unrealistic for most practical systems, which had no internal model of their own or others' mental states.
3. **Limited deployment:** FIPA-ACL was primarily adopted in academic settings. The most successful implementation platform was JADE (Java Agent Development Framework), which is discussed in [[#82-jade-fipa-compliant-agent-platform-in-java|Section 8.2]].
4. **No support for compiled code:** Like KQML, FIPA-ACL was a text-based protocol for exchanging information, not for deploying executable programs. This is the fundamental gap that NEXUS addresses.

### 3.3 KIF (Knowledge Interchange Format)

KIF (Knowledge Interchange Format) was developed by Michael Genesereth and Richard Fikes at Stanford University as a content language for agent communication. KIF is not an agent communication language itself — it is the *content language* that ACLs like KQML and FIPA-ACL transport.

KIF is a first-order logic language with extensions for:
- **Defining relations and functions:** `(defrelation parent (?x ?y) ...)`
- **Defining rules:** `(=> (and (parent ?x ?y) (parent ?y ?z)) (grandparent ?x ?z))`
- **Equality and inequality:** `(= ?x ?y)`, `(/= ?x ?y)`
- **Quantification:** `(forall (?x) (exists (?y) (loves ?x ?y)))`
- **Modal operators:** `(believe agent-A proposition)`, `(knows agent-A proposition)`

Example KIF content expressing a marine navigation rule:

```lisp
(<=>
  (and
    (wind-speed ?v ?speed)
    (> ?speed 25.0)
    (vessel-type ?v sailing-vessel)
  )
  (should-reduce-sail-area ?v)
)
```

KIF's strength is its formal rigor — it is logically grounded and can be used for automated theorem proving. Its weakness is the same as all logic-based formalisms: it requires agents to reason symbolically, which is computationally expensive and brittle. NEXUS replaces KIF's symbolic content with [[Reflex Bytecode VM Specification|compiled bytecode]] — the content is not a logical proposition but an executable program that produces physical effects when run on hardware.

### 3.4 Comparison Table: KQML, FIPA-ACL, and KIF

| Feature | KQML | FIPA-ACL | KIF |
|---------|------|----------|-----|
| **Year** | 1993 | 1997 | 1992 |
| **Role** | Communication language | Communication language | Content language |
| **Performatives / Acts** | 35+ | 22 | N/A (content only) |
| **Formal Semantics** | No (informal English) | Yes (speech act theory) | Yes (first-order logic) |
| **Content Language** | Any (typically KIF) | FIPA-SL (or any) | It IS the content language |
| **Interaction Protocols** | No (ad-hoc) | Yes (standardized) | N/A |
| **Ontology Support** | Declarative only | Declarative + reference | Requires shared ontology |
| **Implementation Complexity** | Low | High | High |
| **Adoption** | Academic only | JADE platform, some industrial | Academic only |
| **Expressiveness for Physical Actions** | Low | Low | Medium (via rules) |
| **Runtime Requirements** | Text parsing, network | Text parsing, BDI reasoning | Theorem prover |
| **NEXUS Equivalent** | Wire protocol message types | Agent communication opcodes (TELL, ASK, DELEGATE) | Compiled bytecode |

---

## 4. Speech Act Theory Applied to Computing

### 4.1 Origins: Austin and Searle

Speech act theory originates in the philosophy of language, specifically in J.L. Austin's 1962 book *How to Do Things with Words*. Austin's revolutionary insight was that utterances are not merely descriptions of reality — they are *actions* that change the world. When a judge says "I sentence you to five years," or a ship's captain says "cast off," the utterance *performs* an action.

Austin classified speech acts into three levels:

1. **Locutionary act:** The act of saying something — the physical production of an utterance with meaning.
2. **Illocutionary act:** The act *performed in saying* something — the intention behind the utterance (asserting, requesting, promising, etc.). This is the most important level for agent communication.
3. **Perlocutionary act:** The act *performed by saying* something — the effect on the listener (persuading, frightening, inspiring, etc.).

John Searle, Austin's student, systematized speech act theory in his 1969 book *Speech Acts* and his 1975 paper "A Taxonomy of Illocutionary Acts." Searle classified illocutionary acts into five categories that have become the standard framework for agent communication language design:

### 4.2 Searle's Five Categories and NEXUS Mapping

#### 4.2.1 Assertives (Commissives → States of Affairs)

Assertives commit the speaker to the truth of a proposition. The words-to-world fit direction is "words → world" — the speaker is representing the world as being a certain way.

**Examples:** `inform`, `confirm`, `deny`, `state`, `report`, `assert`

**Searle's conditions:**
- Propositional content: some proposition `p`
- Preparatory condition: speaker has evidence for the truth of `p`
- Sincerity condition: speaker believes `p`
- Essential condition: counts as an undertaking to the effect that `p` represents an actual state of affairs

**NEXUS Mapping → TELL Opcode:**
In NEXUS's proposed [[A2A-Native Language Design and Semantics|extended ISA]], the `TELL` opcode (0x30) implements the assertive illocution. When Agent A sends a `TELL` message to Agent B, it is asserting a fact about the world — for example, "the current water temperature at this location is 18.3°C." This information is pushed to the event ring buffer and made available to Agent B's reflex programs.

At a lower level, the existing `EMIT_EVENT` syscall functions as NEXUS's primitive assertive act: the bytecode program asserts that an event has occurred (e.g., "wind speed exceeded threshold"), and this assertion is recorded in the event ring buffer for consumption by other agents.

#### 4.2.2 Directives (World → Words)

Directives are attempts by the speaker to get the hearer to do something. The words-to-world fit direction is "world → words" — the speaker is trying to change the world to match the words.

**Examples:** `request`, `command`, `ask`, `beg`, `suggest`, `order`, `invite`

**Searle's conditions:**
- Propositional content: some future action `A` of the hearer
- Preparatory condition: speaker believes hearer is able to do `A`
- Sincerity condition: speaker wants hearer to do `A`
- Essential condition: counts as an attempt to get hearer to do `A`

**NEXUS Mapping → ASK / DELEGATE Opcodes:**
The `ASK` opcode (0x31) implements a directive that requests information — "tell me the current GPS position." The `DELEGATE` opcode (0x32) implements a directive that requests action — "deploy this bytecode reflex on your vessel and execute it." The distinction between ASK and DELEGATE maps directly to the distinction between *requesting information* and *requesting action*, which Searle identified as a fundamental axis within the directive category.

Crucially, NEXUS's DELEGATE is not merely a request — it is the deployment of executable code. The directive illocution is performed not by asking the hearer to do something, but by giving the hearer a program that *does* something. This transforms the directive from an *attempt* (which may be refused) into a *program* (which may be accepted, validated, and executed autonomously).

#### 4.2.3 Commissives (World → Words, Self-Committed)

Commissives commit the speaker to a future course of action. Unlike directives, where the speaker wants the *hearer* to act, commissives commit the *speaker* to act.

**Examples:** `promise`, `commit`, `vow`, `pledge`, `guarantee`, `swear`

**Searle's conditions:**
- Propositional content: some future action `A` of the speaker
- Preparatory condition: speaker believes hearer wants speaker to do `A`
- Sincerity condition: speaker intends to do `A`
- Essential condition: counts as the undertaking of an obligation to do `A`

**NEXUS Mapping → DECLARE_INTENT Opcode:**
The `DECLARE_INTENT` opcode (0x20) in NEXUS's extended ISA implements the commissive illocution. When an agent declares its intention (e.g., "maintain heading 270°"), it is committing to a future course of behavior. Unlike a simple assertion ("the heading is 270°"), an intention declaration creates an obligation: the agent's subsequent actions should be consistent with the declared intention.

At the bytecode level, the `DECLARE_INTENT` opcode is a no-op on the ESP32 VM — it executes with zero cycle cost and produces no physical effect. Its entire purpose is as a **communication act** between agents, declaring what the program intends to accomplish. The receiving agent (or the safety validation agent) can then verify that the subsequent bytecode instructions are consistent with the declared intention.

#### 4.2.4 Expressives (Psychological State)

Expressives express the speaker's psychological state about a state of affairs. They do not represent the world or try to change it — they simply express an attitude.

**Examples:** `thank`, `apologize`, `congratulate`, `condole`, `welcome`, `deplore`

**Searle's conditions:**
- Propositional content: some state of affairs (which is presupposed to exist)
- Preparatory condition: state of affairs is relevant to speaker and hearer
- Sincerity condition: speaker has the psychological state expressed
- Essential condition: counts as the expression of that psychological state

**NEXUS Mapping → REPORT_STATUS Opcode:**
The `REPORT_STATUS` opcode (0x33) implements the expressive illocution. When an agent reports its status ("I am in DEGRADED mode, GPS sensor lost"), it is expressing its internal state — not asserting a fact about the world, not requesting an action, but communicating its condition. This enables fleet-level situational awareness: other agents can adjust their behavior based on the reported statuses of their peers.

In NEXUS's trust framework, status reports directly feed into the [[Trust Score Algorithm Specification|trust score computation]]. A status report of "sensor failure" generates a `sensor_failure_transient` or `sensor_failure_permanent` event, which decreases the trust score. This creates a direct pipeline from expressive illocution (reporting status) to system-level behavior modification (trust-based autonomy restriction).

#### 4.2.5 Declarations (World ↔ Words, Immediate Creation)

Declarations bring about a correspondence between the proposition and reality *by the very act of declaring it*. The speaker, by virtue of having the authority to do so, changes the world.

**Examples:** `declare` (war, independence), `appoint`, `resign`, `baptize`, `sentence` (judicial), `name` (ship christening)

**Searle's conditions:**
- Propositional content: any proposition
- Preparatory condition: speaker has the institutional authority to make the declaration
- Sincerity condition: speaker believes the declaration will take effect
- Essential condition: counts as bringing about the proposition

**NEXUS Mapping → REQUIRE_CAPABILITY Opcode:**
The `REQUIRE_CAPABILITY` opcode (0x40) implements the declarative illocution. When a bytecode program includes a `REQUIRE_CAPABILITY sensor:lidar` declaration, it is creating a *requirement* that must be satisfied for the program to execute. The declaration brings a new constraint into existence — before the declaration, there was no requirement; after the declaration, the requirement exists and must be satisfied.

Similarly, the `TRUST_CHECK` and `AUTONOMY_LEVEL_ASSERT` opcodes create requirements that must be satisfied for execution to proceed. These are declarations in Searle's sense: they bring about a state of affairs (a precondition) that did not previously exist, and they do so by the authority of the agent that issued the declaration.

### 4.3 Speech Act Comparison Table

| Searle Category | Fit Direction | FIPA-ACL Examples | NEXUS Opcode | Physical Effect |
|----------------|---------------|-------------------|-------------|-----------------|
| **Assertives** | Words → World | `inform`, `confirm`, `disconfirm` | `TELL` (0x30), `EMIT_EVENT` | Updates event ring buffer, fleet telemetry |
| **Directives** | World → Words | `request`, `query-if`, `cfp` | `ASK` (0x31), `DELEGATE` (0x32) | Deploys bytecode, requests data |
| **Commissives** | World → Words (self) | `agree`, `accept-proposal` | `DECLARE_INTENT` (0x20) | Commits agent to behavioral pattern |
| **Expressives** | No fit | `failure`, `sorry` | `REPORT_STATUS` (0x33) | Updates fleet situational awareness, trust |
| **Declarations** | Words ↔ World | `propose` (creates proposal) | `REQUIRE_CAPABILITY` (0x40), `TRUST_CHECK` (0x50) | Creates runtime preconditions |

---

## 5. Coordination Mechanisms

### 5.1 Contract Nets → NEXUS Fleet Task Allocation

As discussed in [[#22-the-contract-net-protocol-davis--smith-1983|Section 2.2]], the Contract Net Protocol is the foundational task allocation mechanism. NEXUS extends the classical CNP with bytecode deployment:

| CNP Phase | Classical CNP | NEXUS A2A |
|-----------|---------------|-----------|
| **Announce** | Text message describing task | Capability query + intention bytecode draft |
| **Bid** | Cost/time estimate text | Trust score + equipment capabilities + cycle budget estimate |
| **Award** | "You win" text message | Compiled bytecode targeting specific vessel's equipment |
| **Execute** | Contractor runs its own code | Deployed reflex runs autonomously on ESP32 VM |
| **Report** | Result text message | Telemetry events + trust score update |

The key architectural difference is that NEXUS's "award" phase does not merely notify the contractor — it *delivers the program* the contractor will execute. This eliminates the "execution ambiguity" of classical CNP, where the manager cannot predict exactly how the contractor will implement the task.

### 5.2 Auction Protocols

Auction protocols generalize the Contract Net by introducing richer bidding mechanisms:

- **English (ascending-price) auction:** The price (or resource allocation) starts low and increases until only one bidder remains. Used for allocating scarce resources (bandwidth, compute cycles).
- **Dutch (descending-price) auction:** The price starts high and decreases until a bidder accepts. Used for time-sensitive task allocation where quick decisions are needed.
- **Vickrey (second-price sealed-bid) auction:** Bidders submit sealed bids; the highest bidder wins but pays the second-highest price. This encourages truthful bidding.
- **Combinatorial auction:** Bidders can bid on bundles of items/tasks, enabling expression of synergies ("I can do tasks A and B together cheaper than either alone").

**NEXUS Application:** In a NEXUS fleet, auction protocols can be used for dynamic resource allocation when multiple vessels compete for shared resources (e.g., a single charging station, limited satellite bandwidth). The trust score naturally serves as a bidding weight — agents with higher trust scores have demonstrated reliability and should receive priority access to critical resources.

### 5.3 Voting and Consensus → NEXUS Communal Veto

Voting mechanisms enable group decision-making:

- **Majority voting:** The simplest mechanism; each agent has one vote.
- **Weighted voting:** Agents' votes are weighted by expertise, trust, or stake.
- **Quorum-based voting:** A decision requires a minimum number of participating agents.
- **Borda count:** Agents rank options; points are assigned based on rank position.

**NEXUS's Ubuntu-Inspired Communal Veto:** The NEXUS architecture includes a distinctive consensus mechanism called the "communal veto," inspired by the Southern African philosophical tradition of Ubuntu ("I am because we are"). In this mechanism:

- If three or more agents in a subsystem detect that a proposed action would violate safety constraints, they can collectively veto the action, even if the proposing agent has higher priority.
- The veto is **trust-weighted**: agents with higher trust scores for the relevant subsystem have greater veto weight.
- This mechanism prevents a single high-priority but poorly-calibrated agent from overriding the collective safety judgment of the fleet.

This is architecturally implemented through the [[Trust Score Algorithm Specification|INCREMENTS trust system]]: if the proposing agent's trust score drops below the threshold for the relevant subsystem, its reflexes are automatically suspended, regardless of priority. The "communal" aspect arises because trust scores are computed based on events generated by *all* agents in the subsystem, meaning that multiple agents' observations contribute to the veto decision.

### 5.4 Plan Merging

Plan merging addresses the problem of coordinating the plans of multiple agents when those plans may conflict:

1. **Centralized plan merging:** A single coordinator collects all agents' plans, identifies conflicts, and resolves them. Simple but creates a single point of failure.
2. **Incremental plan merging:** Agents iteratively adjust their plans to accommodate others, starting from their initial plans. More robust but may not converge.
3. **Social plan merging:** Agents use a shared set of social laws (conventions) to constrain their planning, ensuring compatibility without communication.

**NEXUS Application:** In NEXUS, plan merging occurs at the bytecode level. When two reflex programs conflict on a shared actuator register, the equipment runtime applies last-writer-wins semantics within a tick. However, the system also supports *intention-level merging*: if Agent A deploys a "maintain heading 270°" reflex and Agent B deploys a "avoid obstacle at bearing 045°" reflex, the equipment runtime can compose these intentions by assigning them different priority levels and letting the higher-priority reflex (obstacle avoidance) override the lower-priority one (heading hold) when conflicts occur.

### 5.5 Shared Plans and Joint Intentions

The concept of **shared plans**, developed by Barbara Grosz and Sarit Kraus in the 1990s, extends plan merging to include the notion of *joint commitment* — agents don't merely have compatible individual plans; they share a collective intention to achieve a common goal.

Key concepts:
- **Joint Intention:** All team members are committed to the team's goal and know that all other members are similarly committed.
- **Mutual Belief:** All team members believe (and believe that others believe) the relevant propositions about the shared plan.
- **Teamwork:** Agents actively monitor each other's progress and take corrective action when teammates fail.

**NEXUS Application:** At the fleet level, NEXUS supports colony-level intention through the [[Master Consensus Architecture|3-Jetson Raft cluster]]. The lead Jetson proposes fleet-level objectives, and the Raft consensus protocol ensures that all Jetsons commit to the same plan. This implements a form of joint intention at the cognitive layer: all three Jetsons share a commitment to the fleet's objective, and the Raft protocol ensures mutual belief about the current plan state.

At the ESP32 level, shared plans are implicit: each ESP32 executes its deployed reflexes independently, but those reflexes were compiled to be *compatible* with each other (different actuators, compatible sensor usage, aligned timing). The shared plan emerges from the compilation process, not from runtime negotiation.

---

## 6. Ontologies for Agent Communication

### 6.1 What Is an Ontology in MAS?

In the context of multi-agent systems, an **ontology** is a formal, explicit specification of a shared conceptualization. It defines:
- **Classes (concepts):** What kinds of things exist in the domain? (vessel, sensor, actuator, waypoint, obstacle)
- **Properties (attributes):** What do these things look like? (vessel has position, speed, heading; sensor has type, accuracy, update_rate)
- **Relations:** How do things relate to each other? (vessel *has* sensor; sensor *measures* temperature; obstacle *is_at* position)
- **Axioms (rules):** What constraints and inferences hold? (a vessel cannot have two rudders; if wind_speed > 25 and vessel_type = sailing, then reduce_sail)

For agents to understand each other, they must share (or be able to translate between) ontologies. This was the fundamental problem that KQML and FIPA-ACL attempted to address through their `:ontology` parameter.

### 6.2 NEXUS's Four-Layer Ontology

NEXUS requires a four-layer ontology for agents to understand each other:

#### 6.2.1 Hardware Capability Ontology (Vessel Descriptor)

This ontology describes *what hardware exists and what it can do*. It is the NEXUS equivalent of FIPA's agent description service.

```
Classes: Vessel, MCU_Node, Cognitive_Node, Sensor, Actuator, Power_System
Relations: vessel_has_node, node_has_sensor, node_has_actuator, sensor_measures, actuator_controls
Attributes: soc_type, clock_mhz, sram_kb, sensor_type, accuracy, range, update_hz, actuator_type, safe_position
```

This ontology is expressed in NEXUS through the **vessel capability descriptor** (a JSON structure) that every vessel publishes at boot time. The descriptor includes hardware specifications, sensor/actuator configurations, and performance characteristics. See [[Agent Communication & Runtime Model|Section 4.2]] for the complete descriptor format.

#### 6.2.2 Safety Constraint Ontology (Trust Context)

This ontology describes *what behaviors are safe and under what conditions*. It maps to the [[Trust Score Algorithm Specification|INCREMENTS trust framework]].

```
Classes: Subsystem, Trust_Level, Safety_Policy, Safety_Rule, Event_Type
Relations: subsystem_has_trust_score, trust_score_maps_to_level, level_permits_action, action_has_safety_rule
Attributes: alpha_gain, alpha_loss, t_floor, evaluation_window_hours, min_autonomy_level, severity, quality
```

The safety constraint ontology is encoded in the `safety_policy.json` configuration file and in the [[Reflex Bytecode VM Specification|bytecode VM's safety invariants]] (no NaN/Inf to actuators, post-execution clamping, cycle budget enforcement). Agents must understand this ontology to generate safe bytecode.

#### 6.2.3 Domain Knowledge Ontology (Marine, Agriculture, etc.)

This ontology describes *the application domain* — what the system is actually doing in the real world.

```
Marine Domain:
  Classes: Waypoint, Route, Obstacle, AIS_Vessel, Anchorage, Channel, Depth_Contour
  Relations: vessel_at_position, vessel_following_route, obstacle_near_vessel, channel_has_depth_limit
  Attributes: latitude, longitude, heading, speed_over_ground, course_over_ground, depth, tidal_state

Agricultural Domain:
  Classes: Crop_Row, Irrigation_Zone, Soil_Sensor, Weather_Station, Harvest_Bin
  Relations: zone_has_crop, sensor_in_zone, irrigation_serves_zone
  Attributes: soil_moisture, temperature, humidity, growth_stage, yield_estimate
```

NEXUS is designed to be domain-agnostic — the bytecode VM doesn't know or care whether it's controlling a marine autopilot or an irrigation valve. The domain ontology is encoded in the system prompt that drives the LLM's bytecode generation.

#### 6.2.4 Intention Ontology (What an Agent Is Trying to Accomplish)

This ontology is unique to NEXUS and represents its most distinctive contribution to the field. It describes *what agents are trying to achieve*, expressed at a level that any agent — regardless of its training data, system prompt, or hardware platform — can understand.

```
Classes: Intention, Goal, Constraint, Capability_Requirement, Trust_Context, Failure_Mode
Relations: intention_has_goals, goal_has_constraints, intention_requires_capability, intention_has_trust_context, intention_has_failure_mode
Attributes: intention_id, human_description, trust_min, domain, author_agent, validator_agent, version, hash
```

This ontology is encoded in NEXUS's [[A2A-Native Language Design and Semantics|Agent-Annotated Bytecode format]] — specifically in the semantic metadata block of each AAB instruction. The intention ontology enables any agent to read bytecode written by any other agent and understand what it's trying to accomplish, why, and under what conditions.

---

## 7. Modern Agent Frameworks (2010s–2026)

### 7.1 The LLM Revolution and Agent Frameworks

The emergence of large language models (LLMs) in the early 2020s fundamentally transformed the agent communication landscape. For the first time, software agents could *understand* natural language, *generate* structured outputs, and *reason* about complex goals. This enabled a new generation of agent frameworks that leverage LLMs as the cognitive core.

### 7.2 OpenAI Function Calling / Tool Use (2023)

OpenAI introduced function calling (also called tool use) in June 2023, allowing GPT models to generate structured JSON arguments for predefined functions. This was the first widely deployed mechanism for LLM-driven agent communication with external systems.

**Architecture:**
1. The developer defines a set of functions with JSON schemas describing parameters and types.
2. The user sends a natural language query to the model.
3. The model decides whether to respond directly or to call one or more functions.
4. If calling a function, the model generates a JSON object matching the function's schema.
5. The developer executes the function and returns the result to the model.
6. The model incorporates the result and generates a final response.

**Limitations:**
- **Cloud-only:** All processing occurs on OpenAI's servers. No local execution.
- **Text-mediated:** Communication is entirely through text/JSON. No compiled code deployment.
- **Synchronous:** The model waits for function results before continuing. No asynchronous execution.
- **No inter-agent communication:** Function calling is strictly between a model and a human-defined API. No agent-to-agent protocol.

### 7.3 LangChain / LangGraph (2022–2025)

LangChain, developed by Harrison Chase starting in late 2022, provides a framework for building LLM-powered applications with chained reasoning steps. LangGraph, introduced in 2024, extends LangChain with graph-based workflow orchestration.

**Architecture:**
- **Chains:** Sequences of LLM calls, tool invocations, and data transformations.
- **Agents:** LLMs with access to tools that can make autonomous decisions about which tools to use.
- **Memory:** Persistent state across interactions (conversation history, accumulated knowledge).
- **Graph-based workflows:** State machines where nodes are processing steps and edges are conditional transitions.

**Agent communication in LangChain:**
- Agents communicate through shared state (memory) and through tool invocations.
- The ReAct (Reason + Act) pattern is the dominant agent paradigm: the agent reasons about what to do, acts (calls a tool), observes the result, and reasons again.
- Multi-agent communication is supported through LangGraph's graph topology — agents can be nodes that send messages to each other through the graph's edges.

**Limitations:**
- **Cloud-dependent:** All LLM reasoning occurs in the cloud.
- **Latency:** Typical agent chain takes 5–30 seconds per turn (LLM inference time).
- **No compiled code deployment:** Agents exchange text and structured data, not executable programs.
- **Determinism:** LLM outputs are non-deterministic; the same input can produce different outputs.

### 7.4 Anthropic Tool Use / Computer Use (2023–2024)

Anthropic's Claude models support tool use similar to OpenAI's function calling, plus a distinctive "computer use" capability where Claude can directly control a computer (move mouse, click, type) by generating screenshots and actions.

**Architecture:**
- Tool use: Claude generates structured tool calls in XML format (`<function_calls>` blocks).
- Computer use: Claude generates high-level actions (click, type, scroll) that are executed by a computer automation layer.

**Limitations:** Same as OpenAI function calling, plus computer use is slow (each action requires an LLM inference round-trip) and error-prone (the LLM cannot directly perceive the screen; it relies on screenshot analysis).

### 7.5 AutoGen (Microsoft, 2023–2024)

AutoGen, developed by Microsoft Research, enables multi-agent conversations where multiple LLM-powered agents interact to solve tasks. It supports various conversation patterns:

- **Two-agent chat:** A user agent and an assistant agent.
- **Group chat:** Multiple agents in a group, with a configurable speaker selection policy.
- **Nested chats:** One agent's response triggers a sub-conversation between other agents.

**Architecture:**
- Each agent has an LLM backend, a system prompt, and (optionally) tool access.
- A conversation manager routes messages between agents based on configurable policies.
- Agents can be human-in-the-loop or fully autonomous.

**Limitations:**
- **Cloud-only:** All LLM processing in the cloud.
- **Text-only communication:** Agents communicate through natural language text messages.
- **No compiled code:** Agents exchange ideas, not executable programs.
- **Scaling:** Conversation-based communication does not scale well to fleets of hundreds of agents.

### 7.6 CrewAI (2024–2025)

CrewAI builds on the multi-agent paradigm with a focus on role-based agent teams. Each agent is assigned a role (e.g., "Researcher," "Writer," "Reviewer") with specific goals, backstories, and capabilities.

**Architecture:**
- **Crews:** Teams of agents working together on a task.
- **Tasks:** Units of work assigned to agents, with expected outputs.
- **Processes:** Sequential or hierarchical execution patterns.
- **Tools:** Functions that agents can invoke.

**Limitations:** Same fundamental limitations as AutoGen — cloud-only, text-mediated, no compiled code deployment.

### 7.7 Google A2A Protocol (2025)

Google's Agent-to-Agent (A2A) protocol, announced in 2025, represents the closest existing framework to NEXUS's philosophy. The protocol defines a standard for agents to discover each other's capabilities, negotiate tasks, and exchange results.

**Architecture:**
- **Agent Cards:** JSON descriptions of an agent's capabilities (name, description, URL, authentication requirements).
- **Tasks:** Structured units of work that agents can assign to each other.
- **Task lifecycle:** Submitted → Working → Completed / Failed / Canceled.
- **Message types:** Text, file, and structured data.

**Critical difference from NEXUS:** Google's A2A protocol is entirely **cloud-based and text-mediated**. Agents communicate through HTTP APIs exchanging JSON payloads. There is no concept of compiled bytecode, embedded hardware execution, or deterministic real-time behavior. Google's A2A is designed for cloud-based AI assistants coordinating to answer user queries; NEXUS's A2A is designed for physical robots coordinating to control hardware.

### 7.8 Comprehensive Comparison Table

| Feature | OpenAI Tool Use | LangChain | Anthropic | AutoGen | CrewAI | Google A2A | NEXUS A2A |
|---------|----------------|-----------|-----------|---------|--------|------------|-----------|
| **Year** | 2023 | 2022 | 2023 | 2023 | 2024 | 2025 | 2025 |
| **Execution Environment** | Cloud | Cloud | Cloud | Cloud | Cloud | Cloud | **Edge (ESP32)** |
| **Communication Medium** | JSON | Text/JSON | XML | Text | Text | JSON/HTTP | **Compiled bytecode** |
| **Code Deployment** | No | No | No | No | No | No | **Yes (bytecode VM)** |
| **Determinism** | Non-deterministic | Non-deterministic | Non-deterministic | Non-deterministic | Non-deterministic | Non-deterministic | **Provably deterministic** |
| **Real-time Capability** | No | No | No | No | No | No | **Yes (1 kHz)** |
| **Offline Operation** | No | No | No | No | No | No | **Yes (failsafe)** |
| **Hardware Control** | Via API only | Via tools | Computer use | Via tools | Via tools | Via API | **Direct (VM registers)** |
| **Safety Guarantees** | None | None | None | None | None | None | **4-tier IEC 61508** |
| **Trust Framework** | None | None | None | None | None | None | **INCREMENTS** |
| **Physical Effect** | None | None | Screen control | None | None | None | **Sensor/actuator I/O** |
| **Latency** | 1–5s | 5–30s | 1–5s | 2–10s | 2–10s | 1–3s | **44 μs (VM exec)** |
| **Agent Communication** | Model↔API | Model↔Chain | Model↔Tool | Agent↔Agent | Agent↔Agent | Agent↔Agent | **Agent↔Hardware** |

### 7.9 The Critical Difference: Bytecode to Embedded Hardware

All modern agent frameworks share a common architecture: **cloud-based LLMs exchanging text through APIs**. NEXUS is architecturally different in every dimension:

1. **Cloud → Edge:** LLMs generate bytecode that runs on microcontrollers, not in the cloud.
2. **Text → Binary:** Agents communicate through compiled binary programs, not natural language text.
3. **Non-deterministic → Deterministic:** LLM generation is non-deterministic, but the resulting bytecode execution is provably deterministic.
4. **Soft real-time → Hard real-time:** Cloud-based agents operate on human timescales (seconds); NEXUS agents operate on control timescales (milliseconds).
5. **No physical effect → Direct physical effect:** Cloud agents exist in a virtual space; NEXUS agents control physical hardware (sensors, actuators, vessels).

This is not merely an engineering difference — it is a **paradigm difference**. Cloud-based agent frameworks treat agents as conversational entities; NEXUS treats agents as *physical actors* in the real world. The appropriate theoretical foundations for cloud agents are linguistics and dialogue theory; the appropriate foundations for NEXUS agents are control theory, distributed systems, and speech act theory applied to physical action.

---

## 8. Agent-Oriented Programming Languages

### 8.1 AgentSpeak(L)

AgentSpeak(L), developed by Rafael Bordini and Jomi Hübner in the early 2000s, is a programming language based on the BDI (Belief-Desire-Intention) agent architecture. It provides a concrete syntax for defining agents whose behavior is driven by beliefs about the world, desires (goals) to achieve, and intentions (committed plans).

**Key constructs:**
- **Beliefs:** Prolog-like facts about the world state. `(location(robot, kitchen))`
- **Goals:** States the agent wants to achieve. `!go_to(lab)` (achieve goal) or `?temperature` (test goal)
- **Plans:** Rules that map triggering events + context to action sequences. `+!go_to(X) : at(X) <- true.` (if goal is to go to X and already at X, succeed)
- **Events:** Triggers for plan adoption. `+location(robot, X)` (new belief added)

**Example AgentSpeak(L) program:**
```
!start.

+!start : true
    <- .print("Starting vessel navigation").
    !navigate_to(waypoint_1).
    !navigate_to(waypoint_2).

+!navigate_to(WP) : position(P), distance(P, WP, D), D < 10
    <- .print("Already at ").print(WP).

+!navigate_to(WP) : position(P), heading_to(P, WP, H)
    <- set_heading(H).
    !navigate_to(WP).   // recursive: re-check until arrived
```

**Can AgentSpeak(L) be compiled to NEXUS bytecode?** Partially. AgentSpeak(L)'s recursive plan structure maps naturally to NEXUS's state-machine pattern (plans become states, goal achievement becomes state transitions). However, AgentSpeak(L)'s pattern matching and unification are too complex for the 32-opcode ISA. A restricted subset — plans with fixed triggering events, simple condition tests, and linear action sequences — could be compiled to NEXUS bytecode, but the full language requires a more expressive VM.

### 8.2 JADE (Java Agent Development Framework)

JADE, developed by Telecom Italia from 1998 onward, is the most successful FIPA-compliant agent platform. It provides:
- **Agent lifecycle management:** Create, suspend, resume, terminate agents.
- **FIPA-ACL messaging:** Full implementation of the FIPA communication language.
- **Yellow Pages service:** Agent discovery and capability advertisement (DF — Directory Facilitator).
- **Behavior model:** Composable behaviors (CyclicBehavior, OneShotBehavior, SequentialBehavior, ParallelBehavior).
- **AMS (Agent Management System):** Platform-level agent registration and management.

**JADE's influence on NEXUS:** JADE's concept of agent *behaviors* maps to NEXUS's *reflexes* — both are composable units of behavior that can be added, removed, and composed at runtime. JADE's Directory Facilitator maps to NEXUS's capability discovery protocol. However, JADE agents communicate through FIPA-ACL text messages; NEXUS agents communicate through compiled bytecode. JADE runs on the JVM; NEXUS runs on ESP32 microcontrollers.

**Can JADE behaviors be compiled to NEXUS bytecode?** Yes, with restrictions. A JADE `OneShotBehavior` that performs a simple computation and sends a result maps directly to a NEXUS reflex program. A `CyclicBehavior` that repeatedly reads a sensor and writes to an actuator is exactly what NEXUS reflexes are designed for. However, JADE behaviors that require dynamic agent creation, complex message parsing, or access to Java libraries cannot be compiled to the 32-opcode ISA.

### 8.3 3APL (A Programming Language for Cognitive Agents)

3APL (pronounced "three-apl"), developed by Mehdi Dastani and colleagues at Utrecht University, extends agent programming with mentalistic notions — an explicit representation of beliefs, goals, and plans.

**Key features:**
- **Goal-directed behavior:** Agents have explicit goals that drive action selection.
- **Plan revision:** Agents can dynamically revise their plans when goals change or when the current plan fails.
- **Deliberation:** Agents reason about which goal to pursue and which plan to adopt.
- **Rule-based planning:** Plans are specified as rules, enabling declarative plan specification.

**Can 3APL be compiled to NEXUS bytecode?** The deliberation and plan revision mechanisms of 3APL require LLM-level reasoning, not bytecode-level execution. 3APL's *execution* phase (executing a selected plan) could be compiled to NEXUS bytecode, but the *deliberation* phase (deciding which plan to execute) requires the Jetson cognitive layer.

### 8.4 Compilation Feasibility Summary

| Language | Core Paradigm | Compilable to NEXUS Bytecode? | What Must Run on Jetson? |
|----------|--------------|-------------------------------|--------------------------|
| AgentSpeak(L) | BDI plans | Partial (restricted subset) | Pattern matching, unification, goal management |
| JADE | FIPA-compliant behaviors | Yes (OneShotBehavior, CyclicBehavior) | Message parsing, agent discovery |
| 3APL | Goal-directed deliberation | No (execution only) | Deliberation, plan revision, goal management |
| NEXUS A2A | Intention blocks + bytecode | Native | Intention generation, safety validation, compilation |

The pattern is clear: **deliberation and planning are cognitive tasks that require LLM processing; execution and control are reflexive tasks that can run on bytecode VMs.** NEXUS's two-tier architecture (Jetson for cognition, ESP32 for reflexes) directly implements this separation.

---

## 9. Trust and Reputation in Multi-Agent Systems

### 9.1 Computational Trust Models

Trust in multi-agent systems is the expectation that an agent will behave dependably and competently. Computational trust models formalize this expectation as a computable quantity.

#### 9.1.1 Regret (Sabater & Sierra, 2001)

The Regret model, developed by Jordi Sabater and Carles Sierra, computes trust based on three components:

1. **Individual dimension:** Direct experience with the target agent (similar to NEXUS's per-subsystem event tracking).
2. **Social dimension:** Information from third-party agents about the target (witness information).
3. **Ontological dimension:** The reliability of information sources varies by context.

**Regret formula:**
```
Trust(A, B, c) = (1 - α) × Image(A, B) + α × [β × Individual(A, B, c) + (1-β) × Social(A, B, c)]
```
Where `α` controls the weight of direct vs. social information, and `β` controls the weight of individual vs. social trust within the social dimension.

**Comparison to NEXUS:** NEXUS's [[Trust Score Algorithm Specification|INCREMENTS]] trust model uses only the individual dimension — it computes trust based on direct observation of events, not third-party reports. This is a deliberate safety choice: in safety-critical systems, second-hand reputation information is unreliable and can be manipulated. NEXUS trusts only what it can observe directly.

#### 9.1.2 FIRE (Huynh, Jennings, & Shadbolt, 2006)

FIRE (Trust and Reputation model for Agent-mediated electronic commerce) integrates four trust components:

1. **Interaction Trust:** Direct experience (like Regret's individual dimension).
2. **Role-Based Trust:** Pre-assigned trust based on the agent's role (e.g., "safety agents are trustworthy by default").
3. **Witness Reputation:** Third-party ratings.
4. **Certified Reputation:** Endorsed reputation from a central authority.

**Comparison to NEXUS:** NEXUS implements role-based trust through the `alpha_multiplier` parameter — different subsystems have different trust rate multipliers (steering is high-risk, bilge pump is low-risk). NEXUS does not implement witness reputation or certified reputation, again for safety reasons.

#### 9.1.3 TRAVOS (Teacy, Patel, Jennings, & Luck, 2006)

TRAVOS (Trust and Reputation model for Agent-based Virtual Organizations for Security) focuses on handling dishonest feedback in reputation systems. It uses:

1. **Experience filtering:** Discounts outlier experiences (very positive or very negative) that may be dishonest.
2. **Confidence-weighted trust:** Trust is weighted by the number of experiences — more experiences → higher confidence.
3. **Reputation adjustment:** Third-party ratings are adjusted based on the rater's reliability.

**Comparison to NEXUS:** NEXUS's `quality_cap` parameter (maximum of 10 good events per window) is conceptually similar to TRAVOS's experience filtering — it prevents a flood of low-quality events from inflating trust. The `severity_exponent` parameter is similar to TRAVOS's experience filtering — it amplifies high-severity events while dampening low-severity ones.

### 9.2 Reputation Systems

Reputation systems aggregate trust information across multiple agents to produce a global reputation score.

#### 9.2.1 EigenTrust (Kamvar, Schlosser, & Garcia-Molina, 2003)

EigenTrust, developed at Stanford, applies the PageRank algorithm to trust networks. Each agent assigns trust scores to other agents, and the global reputation is computed as the principal eigenvector of the trust matrix. This ensures that trusted agents contribute more to the global reputation calculation.

#### 9.2.2 PageRank-Based Approaches

PageRank-based reputation systems treat trust propagation like web page relevance: if many agents trust agent A, and agent A trusts agent B, then agent B inherits some of A's trust. The intuition is that trust should flow through the network like influence.

**NEXUS Position on Reputation Systems:** NEXUS deliberately **does not implement** inter-agent reputation propagation. The INCREMENTS trust model computes trust per-subsystem based only on directly observed events. This is a safety-critical design choice:

1. **No trust laundering:** A compromised agent cannot inflate its trust by getting other compromised agents to vouch for it.
2. **No herding:** The fleet cannot collectively develop misplaced trust in a faulty component through social reinforcement.
3. **Auditability:** Every trust decision can be traced to specific observed events, not to the (potentially manipulated) opinions of other agents.

### 9.3 Fleet-Level Trust Propagation

While NEXUS does not use reputation propagation between agents, it does synchronize trust scores across the fleet using CRDT (Conflict-free Replicated Data Type) with Last-Writer-Wins merge:

1. Each Jetson computes trust scores independently for its assigned subsystems.
2. Trust updates are broadcast via MQTT with QoS 2 (exactly-once delivery).
3. Each Jetson maintains a copy of the fleet-wide trust state.
4. Conflicts (simultaneous updates to the same subsystem) are resolved by timestamp — most recent update wins.
5. Eventual consistency is achieved with bounded staleness (< 1 second).

This approach provides fleet-wide awareness of trust states without the risks of reputation propagation. Every agent knows every other agent's trust score, but each agent computes its *own* trust based on *its own* observations.

### 9.4 Trust Model Comparison

| Feature | Regret | FIRE | TRAVOS | EigenTrust | NEXUS INCREMENTS |
|---------|--------|------|--------|------------|-----------------|
| **Direct Experience** | Yes | Yes | Yes | Yes | **Yes (primary)** |
| **Third-Party Reputation** | Yes | Yes | Yes | Yes | **No** |
| **Role-Based Trust** | No | Yes | No | No | **Yes (alpha_multiplier)** |
| **Experience Filtering** | No | No | Yes | No | **Yes (quality_cap)** |
| **Asymmetric Gain/Loss** | No | No | No | No | **Yes (25:1 ratio)** |
| **Safety-Critical Design** | No | No | No | No | **Yes (IEC 61508)** |
| **Formal Specification** | No | No | Partial | Yes | **Yes (complete)** |
| **Proven Properties** | No | No | Partial | Yes | **Yes (convergence, floor)** |
| **Autonomy Levels** | No | No | No | No | **Yes (L0–L5)** |
| **Fleet Synchronization** | N/A | N/A | N/A | N/A | **Yes (CRDT + Raft)** |

---

## 10. Emergent Communication

### 10.1 The Promise and Peril of Emergent Language

Emergent communication occurs when agents develop their own communication protocols through interaction, without human-designed communication languages. This is one of the most exciting and controversial areas of multi-agent research.

### 10.2 Multi-Agent Reinforcement Learning Emergent Communication

In multi-agent reinforcement learning (MARL), agents learn to communicate by jointly optimizing a shared reward signal. The earliest demonstrations used simple grid-world environments:

- **Lazaridou et al. (2016):** Two agents (a speaker and a listener) learn to communicate about objects in a grid world. The speaker observes the world and sends a discrete message; the listener receives the message and must identify the correct object. Without any pre-defined language, the agents develop a shared communication protocol optimized for the task.
- **Mordatch & Abbeel (2018):** Agents in a 3D environment develop emergent language through self-play, using continuous communication channels.
- **Lowe et al. (2019):** Multi-agent communication in cooperative navigation tasks, where agents must learn to share information about their local observations.

**Key findings from MARL emergent communication:**
1. **Protocol convergence:** Agents consistently develop structured communication protocols, not random noise.
2. **Compositionality:** Emergent languages often exhibit compositional structure (messages can be decomposed into meaningful sub-units).
3. **Specialization:** Messages tend to be task-specific — the emergent language for one task does not transfer to another.
4. **Instability:** The learned protocol is sensitive to training conditions and can change if the environment changes.

### 10.3 Language Emergence in LLM Populations

More recently, researchers have explored whether populations of LLM agents can develop emergent communication:

- **Clark et al. (2024):** Populations of LLM agents playing communication games develop abbreviated jargon and reference conventions over multiple rounds.
- **Li et al. (2025):** LLM agents in simulated societies develop shared norms, idioms, and even rudimentary "slang" through repeated interaction.
- **Gupta et al. (2025):** Multi-LLM agent systems develop shared "mental models" that allow more efficient communication over time.

**Key insight:** LLM agents already have a shared foundation (natural language), so their emergent communication tends to be *compression* and *specialization* of natural language, not the creation of entirely new languages.

### 10.4 Relevance to NEXUS: Could Agents Evolve Their Own Bytecode Dialect?

This is one of the most provocative open questions for the NEXUS platform. The NEXUS [[framework/06_evolutionary_code_system|evolutionary code system]] already supports bytecode evolution through:

1. **Mutation:** Random modifications to bytecode programs (opcode substitution, immediate value perturbation).
2. **Crossover:** Combining bytecode segments from two different programs.
3. **Selection:** Fitness-based selection favoring programs that achieve their stated intentions with fewer cycles, better safety margins, or faster convergence.

Could this evolutionary process lead to the emergence of a NEXUS-specific bytecode "dialect" — commonly used instruction patterns, optimized idioms, or even new pseudo-instructions that all agents converge on?

**Arguments for:**
- The ISA is small (32 opcodes) and the instruction set is Turing-complete, so there is significant room for convention formation.
- Agents share the same fitness function (safety + efficiency + intention achievement), so convergent evolution is expected.
- The [[genesis-colony/round5_synthesis/universal_synthesis|Universal Synthesis analysis]] demonstrates that "the same evolutionary process, run under the same constraints, converges on the same solution" — suggesting strong convergence pressure.

**Arguments against:**
- The 32-opcode ISA is too small for significant dialect formation. There are only so many ways to compute a PID controller with 10 instructions.
- Safety constraints (cycle budget, stack depth, actuator clamping) limit the space of valid programs, reducing the room for convention.
- Evolutionary changes must be validated by the safety system, which rejects any bytecode that violates invariants. This constrains evolution within safe bounds.

**Probable outcome:** NEXUS agents will likely develop shared *patterns* (common instruction sequences for common tasks) but not a true *dialect* (systematic modifications to the instruction set's semantics). This is analogous to how C programmers share design patterns (singletons, observers) without modifying the C language itself.

---

## 11. Open Problems

### 11.1 The Grounding Problem

**The problem:** How do agents ensure that their communication refers to the same real-world entities? When Agent A says "the obstacle at position (50.1, -3.5)" and Agent B receives this message, how does Agent B know that these coordinates refer to the same physical object that Agent A observed?

In cloud-based agent frameworks, this problem is partially addressed by shared ontologies (see [[#6-ontologies-for-agent-communication|Section 6]]). But in NEXUS, where agents communicate through bytecode, the grounding problem manifests differently: how does Agent B know that sensor register 3 in its vessel corresponds to the same physical quantity (e.g., water temperature) as sensor register 7 in Agent A's vessel?

**NEXUS approach:** The vessel capability descriptor resolves this by mapping logical names (e.g., "water_temperature") to physical pin addresses. Agents compile bytecode using logical names, and the equipment runtime resolves logical names to physical addresses at deployment time. This provides a layer of indirection that decouples bytecode from specific hardware configurations.

**Remaining challenge:** Cross-vessel grounding — ensuring that "water temperature" on Vessel A means the same thing as "water temperature" on Vessel B (same units, same accuracy, same measurement method). This requires a shared domain ontology that NEXUS currently encodes in system prompts but does not formally verify.

### 11.2 Scalability of Coordination

**The problem:** As the number of agents grows, coordination overhead grows faster than linearly. With N agents, pairwise communication requires N(N-1)/2 channels. Centralized coordination creates bottlenecks. Decentralized coordination may not converge.

**NEXUS approach:** NEXUS addresses scalability through a hierarchical architecture: ESP32 nodes communicate only with their assigned Jetson (star topology, not mesh), Jetsons communicate through Raft consensus (constant overhead, 3 nodes), and inter-vessel communication uses MQTT (publish-subscribe, not point-to-point). This limits the coordination overhead to O(N) per Jetson rather than O(N²) fleet-wide.

**Remaining challenge:** For very large fleets (>100 vessels), the MQTT broker becomes a bottleneck. Hierarchical MQTT (broker clusters with topic partitioning) can mitigate this but introduces complexity.

### 11.3 Formal Verification of Agent Communication

**The problem:** How can we formally prove that an agent communication protocol is safe? That it cannot lead to deadlock, livelock, inconsistent states, or safety violations?

**NEXUS approach:** The [[Reflex Bytecode VM Specification|bytecode VM's formal properties]] (determinism, cycle boundedness, type safety) provide partial verification. The [[Trust Score Algorithm Specification|INCREMENTS trust model's convergence proofs]] (trust approaches floor, gain/loss asymmetry is preserved) provide partial verification. The safety validator (Claude 3.5 Sonnet, 95.1% catch rate) provides empirical verification.

**Remaining challenge:** No formal proof exists that the *combination* of bytecode execution + trust updates + inter-agent communication is safe. This is a systems-level verification problem that exceeds the current state of the art.

### 11.4 Adversarial Agent Communication

**The problem:** What happens when a malicious or compromised agent joins the fleet? Can it exploit the communication protocol to cause harm — for example, by deploying bytecode that appears safe but contains subtle exploits?

**NEXUS approach:** Multiple defense layers:
1. **Safety validator:** Independent AI agent (Claude 3.5 Sonnet) validates all bytecode before deployment.
2. **Trust gating:** Deployed bytecode only activates if the deploying agent's trust score exceeds the required threshold.
3. **VM security:** The VM enforces stack depth, cycle budget, actuator clamping, and NaN/Inf prevention at the hardware level.
4. **Physical kill switch:** Hardware override that cannot be affected by any software agent.

**Remaining challenge:** A sophisticated adversary could potentially exploit the LLM-based safety validator (prompt injection, adversarial examples) to get malicious bytecode past validation. This is an open research problem for all LLM-based systems.

### 11.5 Communication Under Extreme Conditions

**The problem:** How should agents communicate when communication channels are degraded, intermittent, or completely unavailable? In marine environments, radio communication can be disrupted by weather, distance, and interference. In emergency situations, reliable communication is most critical but least available.

**NEXUS approach:** The [[Master Consensus Architecture|4-tier heartbeat system]] provides graceful degradation:
- **HEALTHY:** Full communication, all services available.
- **WARN:** Missed 2 heartbeats, non-essential services shed.
- **DEGRADED:** Missed 5 heartbeats, reduced to essential services only.
- **FAILSAFE:** Missed 10 heartbeats, ESP32 continues executing loaded reflexes autonomously.

**Remaining challenge:** When communication is completely lost for extended periods, agents must make decisions based on stale or absent information. The trust decay mechanism (Branch 3: inactivity causes trust to decay toward `t_floor`) provides a principled response, but the optimal decay rate depends on the specific operational context.

### 11.6 The Symbol Grounding Gap for LLM-Compiled Bytecode

**The problem:** When an LLM compiles natural language to bytecode, there is a fundamental gap between the LLM's understanding of the world (trained on text) and the physical reality that the bytecode will interact with (sensors, actuators, environmental conditions). The LLM may generate bytecode that is syntactically correct and semantically reasonable but physically wrong (e.g., a PID controller with gains that are optimal in simulation but unstable on the actual hardware).

**NEXUS approach:** The safety validator catches many of these issues by checking physical constraints (actuator limits, sensor ranges). The trust score system provides feedback — if the bytecode produces unsafe behavior, the trust score drops and the bytecode is deactivated. The evolutionary code system enables iterative improvement through fitness-based selection.

**Remaining challenge:** This is the fundamental limitation of all LLM-driven control systems. The only complete solution is continuous online learning — bytecode that adapts in real-time based on physical feedback. NEXUS's current architecture supports this through reflex replacement (new bytecodes can be deployed at any time), but it does not support *incremental* bytecode modification (adjusting a few parameters without full redeployment).

### 11.7 Open Problem Summary Table

| Problem | Domain | NEXUS Mitigation | Completeness |
|---------|--------|-----------------|-------------|
| Grounding | Semantics | Logical name resolution via capability descriptor | Partial |
| Scalability | Systems | Hierarchical architecture (ESP32→Jetson→Fleet) | Good for ≤100 vessels |
| Formal Verification | Safety | VM invariants + trust convergence proofs | Partial (no systems-level proof) |
| Adversarial Communication | Security | Safety validator + trust gating + kill switch | Good (LLM attacks remain open) |
| Extreme Conditions | Reliability | 4-tier heartbeat + FAILSAFE autonomous operation | Good |
| Symbol Grounding Gap | AI-Hardware Bridge | Safety validation + trust feedback + evolutionary improvement | Partial (no online learning) |

---

## 12. Synthesis: NEXUS's Position in the Field

### 12.1 Historical Context

NEXUS's A2A-native programming paradigm occupies a unique position in the 40+ year history of agent communication:

- **From the 1980s (CNP, Actor Model):** NEXUS inherits the Contract Net's task allocation model and the Actor Model's message-passing encapsulation, but transforms both by making *programs* the unit of communication.
- **From the 1990s (KQML, FIPA-ACL, KIF):** NEXUS inherits the wrapper-content-ontology architecture but replaces the text-based wrapper with compiled bytecode, the symbolic content with executable programs, and the static ontology with the [[A2A-Native Language Design and Semantics|Agent-Annotated Bytecode metadata]].
- **From the 2000s (AgentSpeak, JADE, 3APL):** NEXUS inherits the BDI-inspired separation of intention (goal) from execution (plan) but implements this separation at the hardware level: intentions are compiled to bytecode, and the bytecode VM is the plan executor.
- **From the 2010s (Regret, FIRE, TRAVOS):** NEXUS inherits computational trust concepts but simplifies for safety-critical deployment: direct observation only, no reputation propagation, asymmetric gain/loss.
- **From the 2020s (LangChain, AutoGen, CrewAI, Google A2A):** NEXUS inherits the LLM-as-cognitive-core paradigm but fundamentally differs in execution: bytecode on embedded hardware, not text in the cloud.

### 12.2 What NEXUS Gets Right

1. **Determinism:** The bytecode VM provides provably deterministic execution, a property that no cloud-based agent framework can match.
2. **Physical effect:** NEXUS agents directly control sensors and actuators, closing the loop between perception and action in real-time.
3. **Safety:** The 4-tier safety system (hardware kill switch → VM invariants → trust gating → AI validation) provides layered defense-in-depth.
4. **Offline operation:** ESP32 nodes continue executing deployed reflexes during communication loss, providing true autonomy.
5. **Intention-level communication:** By communicating through bytecode programs rather than text messages, NEXUS agents share *behavioral programs*, not just *information*.

### 12.3 What NEXUS Has Yet to Prove

1. **Scalability:** Can the architecture scale to fleets of 100+ vessels without coordination bottlenecks?
2. **Adversarial robustness:** Can the system resist sophisticated attacks that exploit the LLM-based safety validator?
3. **Learning speed:** Can the system learn and adapt fast enough for real-time operation in dynamic environments?
4. **Interoperability:** Can NEXUS agents communicate with non-NEXUS agents (e.g., cloud-based AI assistants, human operators)?
5. **Formal guarantees:** Can the system be formally verified to be safe under all possible operating conditions?

### 12.4 The Road Ahead

The field of agent communication is undergoing its most significant transformation since the introduction of KQML. The convergence of LLM cognition, embedded computing, and multi-agent coordination is creating a new class of systems — **physically-grounded, bytecode-communicating, trust-gated agent networks** — for which NEXUS is one of the first concrete implementations.

The theoretical foundations laid by Austin, Searle, Hewitt, Davis, and Smith provide the conceptual framework. The technical standards developed by FIPA, Genesereth, and the KQML community provide the architectural patterns. The practical lessons from JADE, Regret, FIRE, and TRAVOS provide the engineering guidance. NEXUS synthesizes these four decades of work into a system that deploys LLM-compiled intentions to physical hardware through a trust-gated, safety-validated, deterministically-executing bytecode VM.

Whether this synthesis scales, whether it proves robust in adversarial environments, and whether it delivers on the promise of true multi-agent autonomy remain open questions. But the trajectory is clear: the future of agent communication is not text in the cloud — it is bytecode on the edge.

---

## 13. References

### Primary Sources

1. Davis, R., & Smith, R. G. (1983). "Negotiation as a Metaphor for Distributed Problem Solving." *Artificial Intelligence*, 20(1), 63–109.
2. Hewitt, C., Bishop, P., & Steiger, R. (1973). "A Universal Modular Actor Formalism for Artificial Intelligence." *Proceedings of IJCAI-73*, 235–245.
3. Agha, G. (1986). *ACTORS: A Model of Concurrent Computation in Distributed Systems*. MIT Press.
4. Finin, T., Fritzson, R., McKay, D., & McEntire, R. (1993). "KQML as an Agent Communication Language." *Proceedings of CIKM-93*, 456–463.
5. Genesereth, M. R., & Fikes, R. E. (1992). "Knowledge Interchange Format, Version 3.0 Reference Manual." *Stanford University Logic Group Report*.
6. FIPA. (1997). "FIPA 97 Specification: Agent Communication Language." *Foundation for Intelligent Physical Agents*.
7. Austin, J. L. (1962). *How to Do Things with Words*. Oxford University Press.
8. Searle, J. R. (1969). *Speech Acts: An Essay in the Philosophy of Language*. Cambridge University Press.
9. Searle, J. R. (1975). "A Taxonomy of Illocutionary Acts." *Minnesota Studies in the Philosophy of Science*, 7, 344–369.

### Trust and Reputation

10. Sabater, J., & Sierra, C. (2001). "Regret: A Reputation Model for Gregarious Societies." *Proceedings of AAMAS-02*.
11. Huynh, T. D., Jennings, N. R., & Shadbolt, N. R. (2006). "An Integrated Trust and Reputation Model for Open Multi-Agent Systems." *Journal of Autonomous Agents and Multi-Agent Systems*, 13(2), 119–154.
12. Teacy, W. T. L., Patel, J., Jennings, N. R., & Luck, M. (2006). "TRAVOS: Trust and Reputation in the Context of Inaccurate Information Sources." *Journal of Autonomous Agents and Multi-Agent Systems*, 12(2), 183–198.
13. Kamvar, S. D., Schlosser, M. T., & Garcia-Molina, H. (2003). "The Eigentrust Algorithm for Reputation Management in P2P Networks." *Proceedings of WWW-03*.

### Agent-Oriented Programming

14. Rao, A. S. (1996). "AgentSpeak(L): BDI Agents Speak Out in a Logical Computable Language." *Proceedings of MAAMAW-96*, 42–55.
15. Bellifemine, F., Poggi, A., & Rimassa, G. (2001). "JADE — A FIPA-Compliant Agent Framework." *Proceedings of PAAM-01*, 97–108.
16. Dastani, M., van der Torre, L., & Meyer, J.-J. C. (2003). "Programming Multi-Agent Systems in 3APL." *Proceedings of AAMAS-03*.

### Modern Frameworks

17. OpenAI. (2023). "Function Calling and Other API Updates." *OpenAI Blog*.
18. Chase, H. (2022). "LangChain: Building Applications with LLMs through Composability." *GitHub Repository*.
19. Wu, Q., et al. (2023). "AutoGen: Enabling Next-Gen LLM Applications via Multi-Agent Conversation." *Microsoft Research Blog*.
20. Google. (2025). "Agent-to-Agent (A2A) Protocol." *Google Developers*.

### Emergent Communication

21. Lazaridou, A., Peysakhovich, A., & Baroni, M. (2016). "Multi-Agent Communication and Emergent Language." *Proceedings of EMNLP-16*.
22. Mordatch, I., & Abbeel, P. (2018). "Emergence of Grounded Compositional Language in Multi-Agent Populations." *Proceedings of AAAI-18*.
23. Lowe, R., et al. (2019). "Multi-Agent Communication through Learned Discrete Channels." *Proceedings of ICLR-19*.

### NEXUS Platform Documentation

24. NEXUS Agent Communication & Runtime Model (NEXUS-A2A-AGENT-001).
25. NEXUS Reflex Bytecode VM — Production Specification (NEXUS-SPEC-VM-001).
26. NEXUS Trust Score Algorithm Specification (NEXUS-SAFETY-TS-001).
27. NEXUS A2A-Native Language Design and Semantics (NEXUS-A2A-LANG-001).
28. NEXUS Master Consensus Architecture.
29. NEXUS The Colony Thesis.
30. NEXUS Universal Synthesis (Round 5).

---

*This article is part of the NEXUS Robotics Platform Knowledge Base. For related topics, see [[Distributed Intelligence Framework]], [[NEXUSLink Protocol]], [[Safety System Specification]], and [[Genesis Colony Philosophy]].*

*Last updated: 2026-03-29 | Status: Complete*

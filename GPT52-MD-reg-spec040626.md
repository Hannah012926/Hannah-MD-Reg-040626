Agentic Medical Device Reviewer – Improved System Technical Specification (v2)
Target platform: Hugging Face Spaces (Streamlit) • Config-driven agents via agents.yaml • Multi-LLM (OpenAI, Gemini, Anthropic, Grok)

1. Purpose & Scope
This specification defines an improved design for the Agentic Medical Device Reviewer system. It preserves all original features (multi-tab Streamlit app, WOW UI themes/styles, agent pipeline execution with editable handoffs, TFDA premarket workflows, FDA 510(k) intelligence and review pipeline, PDF→Markdown conversion, Note Keeper with AI Magics, agents.yaml studio, dashboard/history) and adds new features for:

Published Guidance Ingestion + FDA/International Regulatory Research Report Generation
Users can paste or upload published guidance in TXT / Markdown / PDF.
Users select output language: Traditional Chinese (default) or English.
A research agent analyzes the provided document, searches and retrieves FDA-related information (e.g., 510(k) summaries, FDA guidance, FDA Recognized Consensus Standards), plus relevant international regulations and industry standards, then synthesizes everything into a grounded, citation-rich Markdown report (2000–3000 words).
Users can modify prompts and select models (restricted for this feature to Gemini: gemini-2.5-flash, gemini-3-flash-preview).
Users can edit results and download as .txt or .md.
2. Template-Based Report Rewriter

Users can provide a regulatory report template (paste/upload) or select a default template library (including the provided Orthopedic External Fixators guidance+checklist template).
A second agent rewrites the comprehensive report to match the chosen template, still grounded, with consistent section mapping.
Users can modify prompt/model (Gemini models above), edit outputs, and download.
3. Skill Generator (skill.md) for New Agent Skill Creation

From the final template-based report + the original guidance structure, a third agent generates a skill.md file content that defines a new agent skill in the standard skill-creator format.
Output language matches the user selection (TC/EN).
Users can modify prompt and select models (gemini-2.5-flash, gemini-3-flash-preview, gemini-3.1-flash-lite-preview).
Adds 3 “WOW” features inside the generated skill (defined in §8.3).
Additionally, the system adds 3 new “WOW AI features” across the product (beyond existing Note Keeper Magics), and upgrades the dashboard/status indicators, while maintaining the existing API key handling behavior with an enhancement: users can input keys on the webpage if environment keys are absent, and environment-provided keys are never displayed.

2. Baseline (Original) Capabilities – Must Remain Intact
2.1 UI & Experience
Streamlit multi-tab application with a “WOW UI” layer:
Light/Dark theme toggle
English / Traditional Chinese UI language
20 painter-inspired styles and a Jackpot random style picker
Global sidebar settings: default model, temperature, max tokens
Status indicators (pending/running/done/error) for agent runs
An interactive dashboard with run history and charts
2.2 LLM & Agent Orchestration
Multi-provider LLM routing:
OpenAI: gpt-4o-mini, gpt-4.1-mini
Gemini: gemini-2.5-flash, gemini-3-flash-preview, gemini-2.5-flash-lite, gemini-3.1-flash-lite-preview
Anthropic models (configurable)
Grok: grok-4-fast-reasoning, grok-3-mini
Agent definitions loaded from agents.yaml with a UI editor/studio
Sequential agent execution:
Users can edit prompt and choose model per agent
Users can edit outputs (text/markdown modes) and pass as input to the next agent
2.3 Regulatory Workflows
TFDA premarket tab:
Application import/export (JSON/CSV), completeness indicator
Guidance ingestion and pre-screening agents
Application markdown drafting and improvement
FDA 510(k) intelligence and review pipeline
PDF → Markdown conversion
Note Keeper:
Paste note → organized Markdown with highlighted keywords
User-editable note views
AI Magics (including AI Keywords with user-defined color)
2.4 Deployment & Ops
Deployed on Hugging Face Spaces using Streamlit
Uses environment variables for secrets when available; session state for runtime values
Works without code modifications through agents.yaml extensibility
3. New Capability A: Published Guidance Ingestion + Regulatory Research Report
3.1 User Goals
Upload/paste a published guidance (e.g., TFDA review guidance, internal SOP, public regulatory guidance).
Produce a credible, grounded report that:
Extracts key requirements from the input guidance
Identifies FDA-aligned pathways and evidence expectations
Cross-references FDA sources (510(k) summaries, guidance, recognized standards)
Extends to international regulations (EU MDR/IVDR as applicable, IMDRF, ISO/IEC standards, etc.)
Outputs in Traditional Chinese (default) or English
Includes citations and a research trail suitable for regulatory teams
3.2 Input Types & Ingestion Requirements
Supported inputs (single or multiple):

Paste: plain text / Markdown
Upload: .txt, .md, .pdf
Ingestion processing (design requirements):

PDF text extraction:
Page-by-page extraction with page boundary markers for traceability
Store extracted text plus metadata: filename, upload timestamp, page count, extraction warnings
Markdown/TXT normalization:
Preserve headings and lists if present
Detect encoding issues (e.g., mixed Chinese punctuation) and normalize
Document fingerprinting:
Compute a “structure signature” (e.g., heading outline + section keywords) used later for template mapping and skill creation
Language detection (non-blocking):
Detect primary language of input to guide bilingual term consistency, but output language is always user-selected
3.3 Output Language Control
Output language selector on the feature panel:
繁體中文 (default)
English
The selection must propagate to:
Prompts (system/user)
Report headings and table labels
Generated skill.md language
4. New Capability B: FDA + International Research (Search & Grounding)
4.1 Research Sources (Target Corpus)
The research agent must prioritize official and reputable sources:

FDA-related (required emphasis):

FDA Guidance documents (device-specific and general)
FDA Recognized Consensus Standards database
FDA 510(k) database:
510(k) summaries (when publicly available)
device classification/product code context (when applicable)
International regulations & standards (grounded mapping):

EU MDR (2017/745) / IVDR (2017/746) where relevant
IMDRF guidance (e.g., clinical evaluation, SaMD)
ISO standards (e.g., ISO 10993, ISO 14971, ISO 13485, IEC 62304, IEC 60601 series) depending on device type
ASTM standards where appropriate (e.g., orthopedic mechanical testing)
4.2 Search Strategy (Design, Not Code)
The system must support two modes (selectable by deployment constraints):

Live Search Mode (preferred if allowed)
Uses a configurable web search connector or curated endpoint list (FDA pages, standards database pages).
Query generation must be derived from:
extracted device type / components / claims in the uploaded guidance
keywords and acronyms
identified risk areas (biocompatibility, sterilization, mechanical testing, software, cybersecurity, MRI, etc.)
2. Curated Offline Mode (fallback)

Uses a bundled or periodically refreshed curated dataset (e.g., a small index of FDA guidance titles + URLs + key excerpts; recognized standards snapshots).
This mode must still produce citations, but may be limited in coverage.
4.3 Grounding & Citation Requirements
The report must be citation-driven:

Every major requirement or recommendation must be supported by:
(a) the provided guidance text, or
(b) an external authoritative source, or
(c) clearly labeled expert synthesis (explicitly marked as interpretation)
Citation format (Markdown standard):

Inline numeric citations: ...text...[1][2]
A “References” section listing:
Title
Organization (FDA/ISO/IMDRF/TFDA/etc.)
URL
Access date
Notes on relevance
Traceability appendix (required):

A table mapping:
Input guidance section → extracted requirement → external corroborating source(s) → recommended evidence/artifacts
5. New Capability C: Two-Stage Report Generation Workflow
5.1 Stage 1 Agent: “Comprehensive Research Report” (2000–3000 words)
User controls (must exist):

Prompt editor (pre-filled with a robust default)
Model selector (Gemini only: gemini-2.5-flash, gemini-3-flash-preview)
Output language selector (TC/EN)
Max tokens & temperature controls (bounded defaults)
Agent responsibilities:

Summarize the uploaded guidance and extract:
scope, device type, intended use, key technical requirements, testing expectations, document checklist themes
Conduct FDA/international research as per §4
Produce a report in Markdown, 2000–3000 words, with:
Executive summary
Document synopsis (what the uploaded guidance is requiring)
FDA alignment analysis (potential pathways; 510(k) relevance; typical submission elements)
Standards landscape (recognized consensus standards + ISO/IEC/ASTM mapping)
International regulatory mapping (EU MDR/IMDRF highlights)
Risk & evidence expectations (biocompatibility/sterilization/mechanical/software, as applicable)
A practical checklist (derived, not copied blindly)
Traceability matrix + references
Post-processing UX:

Output shown in Markdown view with an optional “Text view”
User can edit directly
Download buttons: .md, .txt
5.2 Stage 2 Agent: “Template-Based Regulatory Report Rewriter”
Inputs:

Stage 1 report (editable, user-approved)
A template:
user-provided template (paste/upload)
or default templates library
Default template library (must include):

骨外固定器查驗登記審查指引與審查清單 (the provided guidance + checklist format)
Additional built-in templates (design requirement):
“FDA 510(k) Review Memo”
“Standards & Test Evidence Plan”
“Clinical/Nonclinical Evidence Summary”
Behavior:

Preserve the content fidelity but restructure into the template’s headings/tables
If the template contains a checklist table, populate it using the extracted requirements and research findings
Maintain references; ensure citations remain attached after restructuring
User controls:

Prompt/model selection (Gemini: gemini-2.5-flash, gemini-3-flash-preview)
Editable output + download .md/.txt
6. New Capability D: Skill Generator (skill.md) Creation Flow
6.1 Purpose
Enable users to automatically create a reusable agent skill definition (skill.md) that can generate new medical device guidance documents consistent with the structure and style found in the provided guidance.

6.2 Inputs
Original uploaded guidance (or its extracted structured outline)
Stage 2 template-based report
User-selected output language (TC/EN)
Optional user notes: “what to generalize,” “what must remain device-specific”
6.3 Output Requirements (skill-creator format)
The generated skill.md content must include:

YAML frontmatter:
name: stable, lowercase kebab-case
description: “pushy” trigger guidance (when to use)
optional compatibility (tools/dependencies)
A clear workflow section:
intent capture
input parsing
outline extraction
generation steps
quality checks
Output format template(s) for produced guidances
Example prompts (2–3)
Evaluation hints (qualitative checks)
6.4 Model Controls
Prompt editor and model selector:
gemini-2.5-flash
gemini-3-flash-preview
gemini-3.1-flash-lite-preview
Output editable; download as skill.md
6.5 “Ultrathink” Quality Constraints (Product Requirements)
The system must encourage “depth-first” generation:
Extract structure → identify requirement categories → generate reusable patterns → include checklists and traceability
Must avoid hallucinated citations in the skill content:
If including references, label them as “examples” unless sourced from the uploaded materials
7. API Key Handling (Enhanced, Must Match Requirements)
7.1 Environment-first, UI fallback
If an API key exists in the environment, the UI must:
indicate “loaded from environment”
not display the secret value
If not found, the UI must provide a secure password input on the webpage for:
OpenAI, Gemini, Anthropic, Grok
Keys entered in UI are:
stored only in Streamlit session state
never written to logs, downloads, or YAML exports
7.2 Key Visibility & Redaction
Any “Run History” or debugging panel must redact secrets.
If a user pastes a key into a document input, the system must warn and offer redaction assistance (see WOW feature in §9.2).
8. Agent & Pipeline Design (agents.yaml-driven)
8.1 New Agents (Conceptual Definitions)
Add new agent entries (configuration-only, no code changes implied) with parameters:

system_prompt (role, grounding rules, output language instructions)
default_model (Gemini for research/skill generator steps)
max_tokens defaults (higher for 2000–3000 words)
temperature defaults (lower for regulatory accuracy)
New agents:

guidance_research_agent – performs document analysis + external research plan + source retrieval summary
regulatory_report_agent – writes 2000–3000 word grounded report
template_report_agent – restructures into chosen template + checklist
skill_md_generator_agent – generates skill.md in skill-creator format
8.2 Agent Chaining UX (Preserve & Extend)
Each agent step runs “one-by-one”
Before executing each step:
user can edit prompt
user can select model
user can edit the previous step output (as the next step input)
Provide “Use Output as Next Input” convenience controls
Provide a “Diff vs Previous” viewer for iterative refinement (see WOW feature §9.1)
8.3 Three “WOW” Features Embedded Inside Generated skill.md
The skill generated by skill_md_generator_agent must include these 3 advanced features as explicit instructions:

Guidance Structure Fingerprinting + Auto-Outline Recovery
The skill instructs the model to derive a normalized outline from any similar guidance (even messy PDFs), recover missing headings, and maintain consistent numbering.
2. Requirement-to-Evidence Traceability Builder

The skill mandates generating a traceability matrix mapping each requirement to:
suggested evidence artifacts
applicable standards
verification method (test/inspection/analysis)
3. Bilingual Terminology Consistency Table (TC/EN)

Even when output is single-language, the skill produces a terminology table to ensure consistent translations of technical terms (device parts, tests, standards names), reducing regulatory ambiguity.
9. Three Additional WOW AI Features (Product-Level Additions)
These are new AI features added to the system (separate from Note Keeper Magics) and available as optional tools in the regulatory workspace.

9.1 WOW Feature #1: “Regulatory Diff & Version Timeline”
Every agent run can be snapshotted as a version.
Users can compare:
prompt changes
output diffs (Markdown-aware diff)
citation/reference changes
Includes a “what changed and why it matters” AI summary (user-controlled prompt/model).
9.2 WOW Feature #2: “Prompt Injection & Secret Leakage Shield”
When ingesting uploaded guidance or pasted content, run a safety scan that:
detects prompt-injection patterns (e.g., “ignore previous instructions”)
detects accidental secrets (API keys, tokens)
Produces a redaction suggestion report and a “sanitized copy” output users can adopt before running research agents.
9.3 WOW Feature #3: “Standards Crosswalk Matrix Generator”
From the report, automatically generate a matrix:
Requirement category → candidate standards (ISO/IEC/ASTM) → rationale → expected test evidence
Exports to Markdown and CSV.
Supports user keyword constraints (e.g., “focus on sterilization + biocompatibility only”).
10. Dashboard & Status Indicators (Enhanced)
10.1 Status Indicators
Maintain existing run statuses and expand to a “pipeline status bar” per workflow:

Ingestion: ready/processing/done
Research: queued/running/done/error
Report: queued/running/done/error
Template rewrite: queued/running/done/error
Skill creation: queued/running/done/error
10.2 Interactive Dashboard Additions
Add dashboard widgets (visual + functional):

“Active Workspace” card: current document, language, template selected
“Citation Coverage Meter”: % of paragraphs containing citations, plus warnings for unsupported claims
“Token/Cost Awareness” panel (estimates): per agent step token estimate and run count
11. Data Model & Artifact Management (Session + Downloads)
11.1 Core Artifacts
The system should treat each workflow output as a named artifact:

source_guidance_raw
source_guidance_extracted
research_sources_list
report_v1_comprehensive
report_v2_template
skill_md_v1
Artifacts must support:

editable text buffers
metadata: model, prompt hash, time, language, template ID
export to .md, .txt, and for some matrices .csv
11.2 References Store (Conceptual)
Maintain a reference list associated with a report:

each entry: title, org, url, access date, excerpt/snippet, relevance tags
used to regenerate references and traceability tables consistently
12. Quality, Compliance, and Safety Requirements
12.1 Non-Hallucination Guardrails
The report must clearly separate:
extracted content from user-provided guidance
external sourced statements (with citations)
interpretation (explicitly labeled)
12.2 Medical/Regulatory Disclaimer
Outputs must include a footer disclaimer:
informational use; not legal advice; verify with official sources
12.3 Reproducibility
Each generated report should include a “Generation Metadata” appendix:
date/time
model ID
language
template used
list of queries (if allowed) or at least query themes
13. Deployment on Hugging Face Spaces (Operational Requirements)
Streamlit app configured for HF Space environment
Environment secrets supported (HF “Secrets”)
Outbound network policy considered:
if live search is blocked, system switches to curated offline mode
Rate limiting and retries per provider
Observability:
run logs exclude secrets
capture errors with user-friendly remediation hints
14. Acceptance Criteria (High-Level)
Users can upload a PDF guidance and get a grounded 2000–3000 word Markdown report with references.
Users can switch output language TC/EN and see full localization of headings and narrative.
Users can apply the default Orthopedic External Fixators template and produce a matching checklist structure.
Users can generate skill.md in the selected language with the 3 embedded WOW features.
Users can override prompt and choose models for all LLM-related functions.
API keys: environment keys never shown; UI input appears only when missing.
20 Comprehensive Follow-Up Questions
For “FDA search,” do you want strictly FDA domains (fda.gov) or also include partner sources (e.g., accessdata.fda.gov, Federal Register, govinfo.gov, NIH/NLM) when relevant?
Should the system store a local cache of retrieved pages/excerpts for reproducibility, or only store URLs + snippets?
Do you require a strict citation rule such as “every paragraph must have at least one citation,” or only for normative requirements and recommendations?
When the uploaded guidance is not device-specific (e.g., general quality system guidance), should the report still infer a device category, or remain device-agnostic?
How should the system behave when it cannot find any relevant 510(k) summaries—omit the section, or include a “search performed but none found” statement?
For international mapping, which jurisdictions are highest priority beyond FDA/Taiwan: EU MDR, UKCA, Canada (Health Canada), Japan (PMDA), Australia (TGA), others?
Do you want the report to explicitly distinguish regulatory requirements vs recommended best practices vs common reviewer expectations?
Should the default template library be editable by users via the Agents Config Studio (stored in YAML/text), or kept as fixed built-ins?
In the Orthopedic External Fixators default checklist, do you want the system to preserve the exact table columns and checkbox style, or is a “structurally similar” checklist acceptable?
Do you want the system to generate an additional “submission-ready evidence index” (documents + filenames + responsible owner) as part of the template-based output?
For prompt injection shielding, should the system automatically sanitize content before running agents, or only suggest a sanitized copy and let the user choose?
Should users be able to run the research in two phases: (a) produce a research plan + queries, (b) confirm, then execute retrieval/synthesis?
What level of detail should standards mapping include—just standard numbers and titles, or also clause-level mappings (e.g., ISO 10993-1 endpoints and rationale)?
Should the system support device software/cybersecurity sections by default (IEC 62304, IEC 81001-5-1, FDA cybersecurity guidance), or only when the input guidance indicates software/network features?
How should the system handle paywalled standards (ISO/IEC full text)? Should it cite titles only and avoid implying access to the full document?
For the skill.md generation, do you want the skill to be generic across device types, or optimized to the uploaded guidance’s domain (e.g., orthopedic implants/fixators)?
Should the generated skill include built-in evaluation prompts and a scoring rubric (qualitative checklist) to help users test skill performance?
Do you want “Diff & Version Timeline” to persist across sessions (requiring storage) or be session-only (simpler, ephemeral)?
For file downloads, do you also need .docx export (in addition to .txt/.md), or must the system remain Markdown-first?
What are your preferred success metrics: time saved per review, citation completeness rate, checklist accuracy (human judged), or alignment with internal QA/regulatory standards?

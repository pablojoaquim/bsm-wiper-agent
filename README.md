# BSM Wiper Agent

**AI-assisted Systems and Software Engineering project for an automotive Body Control Module (BCM/BSM) wiper system.**

## 1. Project Overview

### Objective

BSM Wiper Agent is an experimental multi-agent AI system designed to support the development lifecycle of an automotive windshield wiper controller.

The project explores how specialized AI agents can collaborate throughout the engineering process, from requirements analysis to system modeling, software implementation, code generation and verification.

The objective is to demonstrate an engineering workflow inspired by **Automotive SPICE (ASPICE)**, with requirements traceability, engineering artifacts and human approval at relevant stages.

The system uses a simplified but realistic fictional automotive wiper controller as its reference project.

### Main goals

- Automate requirements analysis and classification.
- Generate and validate system and software requirements.
- Maintain traceability between system and software requirements.
- Identify ambiguous, incomplete or inconsistent requirements.
- Propose derived requirements when necessary.
- Model the system behavior using OpenModelica.
- Generate C code from the system model.
- Verify generated artifacts against engineering requirements.
- Maintain engineering documentation and traceability.
- Keep a human engineer involved in reviewing and approving deliverables.

### Project principles

1. **Human in the loop:** AI-generated engineering artifacts must be reviewed and approved by a human engineer.
2. **Traceability:** Every software requirement must be linked to an appropriate system requirement.
3. **Separation of concerns:** Each agent has a clearly defined engineering responsibility.
4. **Reproducibility:** Engineering artifacts must be stored in version-controlled files.
5. **Simplicity:** Prefer readable, maintainable Python code and straightforward implementations.
6. **Standards-oriented:** Follow engineering practices inspired by Automotive SPICE.

---

## 2. Reference System

The reference system is a fictional automotive BSM windshield wiper controller.

The system is intentionally simplified to make it possible to experiment with AI agents and engineering workflows without requiring a real vehicle, ECU or automotive development environment.

The controller model represents the production system behavior.

The project also includes a separate test model used to simulate and evaluate the controller.

The reference system can be extended with additional features, such as:

- Intermittent wiping.
- Low-speed and high-speed wiping.
- Wiper park position.
- Washer activation.
- Automatic wiping requests.
- Input signal validation.
- Fault handling and safe states.

---

## 3. Development Approach

The project is developed incrementally.

### Increment 1 — Requirements Engineering

Objective: implement the initial requirements engineering workflow.

Current scope:

- Read system requirements.
- Analyze and classify requirements.
- Generate software requirements using an LLM.
- Validate generated requirements using Pydantic.
- Check references between software and system requirements.
- Export software requirements to YAML.

Current implementation includes a Requirements Agent using LangChain and Google Gemini.

Machine Learning requirements are outside the scope of Increment 1.

### Subsequent increments

The architecture is intended to evolve towards the following capabilities:

- System engineering and architecture agents.
- Software design and implementation agents.
- OpenModelica model generation and execution.
- C code generation and compilation.
- Automated verification and validation.
- Traceability across engineering activities.
- Human review and approval workflows.

These capabilities are planned extensions and should not be considered fully implemented merely because their directories or initial experiments exist.

---

## 4. Technologies and Tools

### Required software

| Tool | Purpose |
|---|---|
| Python 3.11 or newer | Main development language |
| pip | Python dependency management |
| Python venv | Isolated development environment |
| Google Gemini API | LLM inference |
| LangChain | LLM integration and agent workflows |
| Pydantic | Data validation |
| PyYAML | YAML requirements management |
| OpenModelica 1.26.3 | System modeling and C code generation |
| Git | Version control |
| Visual Studio Code | Recommended development environment |

### Python dependencies

Dependencies are managed through `requirements.txt`.

The current dependency list includes:

- `black`: Python code formatting.
- `google-genai`: Google Gemini API client.
- `isort`: Import organization.
- `langchain-core`: LangChain core components.
- `langchain-google-genai`: Gemini integration for LangChain.
- `python-dotenv`: Environment variable loading.

Additional libraries required by the implementation, such as Pydantic, YAML and pytest, should be included in the dependency file when they are not already available through installed dependencies.

### OpenModelica

The project uses OpenModelica version 1.26.3.

Expected executable:

`C:\jpablo\03_Tools\OpenModelica\bin\omc.exe`

OpenModelica is used to:

1. Load the Modelica controller.
2. Translate the model.
3. Generate simulation C code.
4. Produce the associated simulation files.

**Important:** The C code generated by this workflow is simulation code. It is not automatically production-ready embedded ECU code.

### C compiler

A C compiler such as GCC will be required for the planned automated compilation and execution of generated C code.

---

## 5. Repository Structure

The proposed repository structure is:

```text
bsm-wiper-agent/
│
├── .env
├── .env.example
├── .gitignore
├── requirements.txt
├── README.md
│
├── src/
│   ├── main.py
│   │
│   └── agents/
│       ├── requirements_agent.py
│       ├── system/
│       └── software/
│
├── requirements/
│   ├── system/
│   │   └── bsm_system_requirements.yaml
│   │
│   └── software/
│       └── bsm_software_requirements.yaml
│
├── config/
│   └── application configuration files
│
├── scripts/
│   └── generate_c.mos
│
├── models/
│   ├── BSMWiperController.mo
│   └── BSMWiperTest.mo
│
├── artifacts/
│   ├── requirements/
│   ├── system/
│   ├── software/
│   ├── architecture/
│   └── design/
│
├── generated/
│   └── c/
│
└── tests/
    └── Python automated tests
```

### Directory description

#### `src/`

Contains the Python application and agent implementations.

- `main.py`: Application entry point.
- `agents/`: Specialized AI agents.

#### `src/agents/`

Contains the individual engineering agents.

- `requirements_agent.py`: Requirements Engineering Agent.
- `system/`: Future system engineering agents.
- `software/`: Future software engineering agents.

Each agent should have a well-defined responsibility and produce identifiable engineering outputs.

#### `requirements/`

Contains the input and output requirements used by the current workflow.

- `system/`: System requirements.
- `software/`: Software requirements.

Requirements are stored in YAML format to make them easy to read, validate, compare and version.

#### `config/`

Contains application configuration files, such as agent settings and workflow configuration.

Sensitive information, including API keys, must not be stored here.

#### `scripts/`

Contains automation scripts.

- `generate_c.mos`: OpenModelica script used to load the controller model and generate C simulation code.

#### `models/`

Contains the Modelica system models.

- `BSMWiperController.mo`: Production controller model.
- `BSMWiperTest.mo`: Test bench model.

The test bench is kept separate from the production controller.

#### `artifacts/`

Contains engineering deliverables produced throughout the development process.

- `requirements/`: Requirements engineering deliverables.
- `system/`: System engineering deliverables.
- `software/`: Software engineering deliverables.
- `architecture/`: System and software architecture documentation.
- `design/`: Detailed design documentation.

#### `generated/`

Contains automatically generated files.

- `c/`: C source files and associated OpenModelica simulation artifacts.

Generated files should not be manually edited.

#### `tests/`

Contains automated Python tests used to validate the application and its components.

---

## 6. Installation and Environment Setup

The following instructions assume Windows and PowerShell.

### Step 1 — Install Python

Install Python 3.11 or newer.

Verify the installation:

```powershell
python --version
```

### Step 2 — Clone or open the repository

Expected local project directory:

```text
C:\jpablo\00_Projects\bsm-wiper-agent
```

Open the directory in Visual Studio Code.

### Step 3 — Create the virtual environment

From the project root:

```powershell
python -m venv .venv
```

Activate it:

```powershell
.\.venv\Scripts\Activate.ps1
```

Verify the Python version:

```powershell
python --version
```

### Step 4 — Install Python dependencies

Upgrade pip:

```powershell
python -m pip install --upgrade pip
```

Install project dependencies:

```powershell
pip install -r requirements.txt
```

### Step 5 — Configure Google Gemini

Create a `.env` file in the repository root.

Example:

```env
GOOGLE_API_KEY=your_google_api_key
GEMINI_MODEL=your_gemini_model
```

Replace the values with your actual Google Gemini API credentials and configured model.

The API key can be obtained through Google AI Studio.

Never commit `.env` to Git.

### Step 6 — Install OpenModelica

Install OpenModelica 1.26.3.

Verify the executable exists:

```powershell
Test-Path "C:\jpablo\03_Tools\OpenModelica\bin\omc.exe"
```

Expected result:

```text
True
```

The OpenModelica installation directory can be changed, but the corresponding path used by automation scripts must be updated.

### Step 7 — Create the project directories

Create any missing directories from the repository root:

```powershell
$directories = @(
    "src\agents\system",
    "src\agents\software",
    "requirements\system",
    "requirements\software",
    "config",
    "scripts",
    "models",
    "artifacts\requirements",
    "artifacts\system",
    "artifacts\software",
    "artifacts\architecture",
    "artifacts\design",
    "generated\c",
    "tests"
)

foreach ($directory in $directories) {
    New-Item -ItemType Directory -Force $directory | Out-Null
}
```

The `generated\c` directory must exist before executing the OpenModelica generation script.

---

## 7. Running the Application

### Activate the virtual environment

```powershell
.\.venv\Scripts\Activate.ps1
```

### Execute the application

From the repository root:

```powershell
python .\src\main.py
```

The current Increment 1 workflow reads the system requirements, invokes the Requirements Agent and generates software requirements.

Expected input:

```text
requirements/system/bsm_system_requirements.yaml
```

Expected output:

```text
requirements/software/bsm_software_requirements.yaml
```

The generated requirements are validated before being saved.

### Run automated tests

Execute:

```powershell
python -m pytest
```

To obtain detailed output:

```powershell
python -m pytest -v
```

---

## 8. Running OpenModelica

The Modelica controller and test bench are maintained separately.

### Generate C simulation code

First, make sure the destination directory exists:

```powershell
New-Item -ItemType Directory -Force .\generated\c
```

Execute the OpenModelica script:

```powershell
& "C:\jpablo\03_Tools\OpenModelica\bin\omc.exe" .\scripts\generate_c.mos
```

The script loads:

```text
models/BSMWiperController.mo
```

And translates the controller into C simulation code under:

```text
generated/c/
```

The generation process produces several files, including C source files, header files and simulation configuration files.

If generation fails, check:

1. OpenModelica is correctly installed.
2. The executable path is correct.
3. The Modelica source file exists.
4. The `generated/c` directory exists.
5. The model compiles without errors.

---

## 9. Requirements Format

Requirements are stored in YAML.

The requirements engineering workflow distinguishes between:

- SYS: System Requirements.
- SWE: Software Requirements.

A software requirement must reference an existing system requirement.

Example of a simplified software requirement:

```yaml
requirements:
  - id: SWE-001
    title: Wiper low-speed activation
    description: >
      The controller shall activate the wiper motor
      in low-speed mode when the corresponding request
      is active.
    parent_system_requirement: SYS-001
```

The exact schema is defined and validated by the Requirements Agent.

The YAML format provides a lightweight alternative to a requirements management tool such as Codebeamer.

---

## 10. AI Agent Architecture

The long-term objective is to implement specialized agents that collaborate throughout the engineering process.

Proposed responsibilities:

| Agent | Responsibility |
|---|---|
| Requirements Agent | Analyze and generate requirements |
| System Engineering Agent | Define system architecture and behavior |
| Software Engineering Agent | Derive software design and implementation |
| Modeling Agent | Create and update Modelica models |
| Code Generation Agent | Execute code generation workflows |
| Verification Agent | Check requirements compliance and test results |

Agents should exchange structured engineering artifacts rather than relying exclusively on unstructured conversations.

Each engineering activity should preserve its inputs, outputs and requirement references.

Human approval is required at relevant engineering milestones.

---

## 11. Traceability and Engineering Workflow

The intended engineering workflow is:

```text
System Requirements
        |
        v
Requirements Analysis
        |
        v
Software Requirements
        |
        v
System Architecture
        |
        v
System Modeling
        |
        v
Software Design
        |
        v
Code Generation
        |
        v
Verification and Validation
        |
        v
Engineering Review
```

Each stage should produce version-controlled artifacts.

The traceability mechanism must allow an engineer to identify:

- Which system requirement originated a software requirement.
- Which design element implements a requirement.
- Which model or software component realizes that design.
- Which verification activity demonstrates compliance.
- Whether the engineering artifact has been reviewed and approved.

---

## 12. Development Guidelines

The following guidelines apply to the Python implementation:

- Prefer simple procedural code.
- Use descriptive variable and function names.
- Keep functions small and focused.
- Avoid unnecessary abstractions and complex frameworks.
- Use comments to explain Python-specific constructs when useful.
- Keep dependencies to a minimum.
- Separate agent responsibilities.
- Validate structured data before generating engineering artifacts.
- Handle API and file errors explicitly.

For engineering artifacts:

- Use English for technical documentation and generated deliverables.
- Use YAML for structured requirements.
- Use Modelica for system behavior modeling.
- Use C for generated simulation code.
- Use Git to track changes to source files and engineering deliverables.

---

## 13. Version Control

Git is used to manage the project.

Recommended workflow:

```powershell
git status
git add .
git commit -m "Describe the implemented feature"
```

The following items should not be committed:

- `.env`
- `.venv/`
- `__pycache__/`
- `.pytest_cache/`
- Temporary files.
- Unnecessary generated simulation files.

Generated engineering deliverables should be version-controlled when they are relevant to the development and traceability process.

---

## 14. Project Status

The project is under incremental development.

Current baseline:

- [x] Python virtual environment configured.
- [x] Dependencies managed with pip.
- [x] Google Gemini integration configured.
- [x] Initial Requirements Agent implemented.
- [x] System requirements loaded from YAML.
- [x] Software requirements generated using Gemini.
- [x] Pydantic validation implemented.
- [x] System-to-software requirement reference validation.
- [x] Initial automated tests passing.
- [x] OpenModelica installed.
- [x] Modelica C-generation workflow initiated.

Future work:

- [ ] Complete and validate the full OpenModelica generation workflow.
- [ ] Implement system engineering agents.
- [ ] Implement software engineering agents.
- [ ] Automate model execution and simulation.
- [ ] Integrate generated code compilation.
- [ ] Implement automated verification.
- [ ] Extend end-to-end engineering traceability.
- [ ] Implement human review and approval workflows.

---

## 15. Disclaimer

This project is an experimental engineering prototype.

It demonstrates how AI agents can support automotive systems and software engineering activities.

It is not intended to replace qualified engineering review, automotive safety processes, formal verification or production ECU development practices.

All generated engineering artifacts must be reviewed before being considered valid engineering deliverables.

---

**Project:** BSM Wiper Agent  
**Domain:** Automotive Embedded Systems  
**Main Language:** Python  
**LLM:** Google Gemini  
**Orchestration:** LangChain  
**System Modeling:** OpenModelica  
**Requirements Format:** YAML  
**Engineering Approach:** Multi-Agent AI + Human-in-the-Loop  
**Process Reference:** Automotive SPICE

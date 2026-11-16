
import json
from pathlib import Path

import yaml
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate

from requirement_models import RequirementDocument
from process_evidence import write_process_evidence


def generate_software_architecture(
    system_document: RequirementDocument,
    software_document: RequirementDocument,
    model,
    output_path: str | Path,
) -> dict:

    # Convert requirements to JSON for the prompt.
    system_requirements_json = system_document.model_dump_json(indent=2)
    software_requirements_json = software_document.model_dump_json(indent=2)

    # Define the architecture generation prompt.
    prompt_template = ChatPromptTemplate.from_messages([
        (
            "system",
            """
            You are an automotive software architect.

            Your task is to define a high-level software architecture
            based on the provided system and software requirements.

            Rules:
            - Define a simple and understandable software architecture.
            - Divide the software into logical components.
            - Each component must have a clear responsibility.
            - Define the interfaces between components.
            - Allocate software requirements to the components responsible
              for implementing them.
            - Every SWE requirement must be allocated to at least one component.
            - Do not invent functionality that is not supported by the requirements.
            - Avoid unnecessary complexity.
            - Continue architecture design when requirements are incomplete or ambiguous.
            - Record technical decisions as assumptions, separate from customer-confirmed requirements.
            - Record unresolved information as an open issue without blocking output.

            Return ONLY valid JSON, without Markdown formatting.

            The JSON structure must be:

            {{
                "architecture": {{
                    "name": "BSM Software Architecture",
                    "description": "High-level software architecture.",
                    "components": [
                        {{
                            "id": "SWC-001",
                            "name": "ExampleComponent",
                            "responsibility": "Component responsibility.",
                            "allocated_requirements": ["SWE-001"]
                        }}
                    ],
                    "interfaces": [
                        {{
                            "id": "IF-001",
                            "source_component": "SWC-001",
                            "target_component": "SWC-002",
                            "signals": ["ExampleSignal"]
                        }}
                    ]
                }},
                "assumptions": [
                    {{
                        "id": "ASM-SWE2-001",
                        "requirement_ids": ["SWE-001"],
                        "missing_information": "Information needed for an architecture decision.",
                        "decision": "The technical assumption used in the architecture.",
                        "rationale": "Why the assumption is reasonable."
                    }}
                ],
                "open_issues": [
                    {{
                        "id": "OI-SWE2-001",
                        "requirement_ids": ["SWE-001"],
                        "missing_information": "Information still requiring clarification.",
                        "reason_unresolved": "Why it remains open."
                    }}
                ]
            }}
            """
        ),
        (
            "user",
            """
            Define the software architecture using the following requirements.

            SYSTEM REQUIREMENTS:
            {system_requirements}

            SOFTWARE REQUIREMENTS:
            {software_requirements}
            """
        ),
    ])

    # Convert the model response into a plain string.
    output_parser = StrOutputParser()

    # Build the LangChain pipeline.
    chain = prompt_template | model | output_parser

    # Execute the pipeline.
    response_text = chain.invoke({
        "system_requirements": system_requirements_json,
        "software_requirements": software_requirements_json,
    })

    # Convert the JSON string into a Python dictionary.
    architecture_document = json.loads(response_text)
    assumptions = architecture_document.pop("assumptions")
    open_issues = architecture_document.pop("open_issues")

    # Create the output directory if it does not exist.
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Save the architecture as YAML.
    with output_path.open("w", encoding="utf-8") as file:
        yaml.safe_dump(
            architecture_document,
            file,
            sort_keys=False,
            allow_unicode=True,
        )

    write_process_evidence(
        output_path,
        stage="SWE.2 Software Architectural Design",
        assumptions=assumptions,
        open_issues=open_issues,
        validation="Architecture JSON parsed and saved as YAML.",
        known_requirement_ids={
            requirement.id
            for requirement in system_document.requirements + software_document.requirements
        },
    )

    return architecture_document


import json
from pathlib import Path

import yaml
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate

from requirement_models import RequirementDocument


def generate_software_design(
    software_document: RequirementDocument,
    architecture_document: dict,
    model,
    output_path: str | Path,
) -> dict:

    # Convert requirements and architecture to JSON for the prompt.
    software_requirements_json = software_document.model_dump_json(indent=2)

    architecture_json = json.dumps(
        architecture_document,
        indent=2,
    )

    # Define the detailed design prompt.
    prompt_template = ChatPromptTemplate.from_messages([
        (
            "system",
            """
            You are an automotive embedded software designer.

            Your task is to create the detailed software design for
            a windshield wiper control system (BSM).

            Use the provided software requirements and architecture.

            Rules:
            - Define software units within the existing architecture components.
            - Each unit must have a clear and limited responsibility.
            - Define inputs and outputs for each unit.
            - Describe the unit behavior using clear sequential steps.
            - Include relevant conditions and decision logic.
            - Allocate SWE requirements to the units.
            - Do not invent functionality that is not supported by the requirements.
            - Keep the design simple and suitable for implementation in Simulink.
            - Use meaningful and consistent names.

            Return ONLY valid JSON, without Markdown formatting.

            The JSON structure must be:

            {{
                "software_detailed_design": {{
                    "name": "BSM Software Detailed Design",
                    "description": "Detailed design of the BSM software.",
                    "units": [
                        {{
                            "id": "UNIT-001",
                            "name": "ExampleUnit",
                            "component_id": "SWC-001",
                            "responsibility": "Unit responsibility.",
                            "inputs": [
                                {{
                                    "name": "ExampleInput",
                                    "type": "boolean",
                                    "description": "Input description."
                                }}
                            ],
                            "outputs": [
                                {{
                                    "name": "ExampleOutput",
                                    "type": "boolean",
                                    "description": "Output description."
                                }}
                            ],
                            "behavior": [
                                "Step 1: Read the input.",
                                "Step 2: Evaluate the condition.",
                                "Step 3: Set the output."
                            ],
                            "allocated_requirements": ["SWE-001"]
                        }}
                    ]
                }}
            }}
            """
        ),
        (
            "user",
            """
            Create the detailed software design using the following inputs.

            SOFTWARE REQUIREMENTS:
            {software_requirements}

            SOFTWARE ARCHITECTURE:
            {architecture}
            """
        ),
    ])

    # Convert the model response into a plain string.
    output_parser = StrOutputParser()

    # Build the LangChain pipeline.
    chain = prompt_template | model | output_parser

    # Execute the pipeline.
    response_text = chain.invoke({
        "software_requirements": software_requirements_json,
        "architecture": architecture_json,
    })

    # Convert the JSON string into a Python dictionary.
    design_document = json.loads(response_text)

    # Create the output directory if it does not exist.
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Save the detailed design as YAML.
    with output_path.open("w", encoding="utf-8") as file:
        yaml.safe_dump(
            design_document,
            file,
            sort_keys=False,
            allow_unicode=True,
        )

    return design_document

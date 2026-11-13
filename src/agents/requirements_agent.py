
import json
from pathlib import Path

import yaml
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate

from requirement_models import RequirementDocument


def generate_software_requirements(
    system_document: RequirementDocument,
    model,
    output_path: str | Path,
) -> RequirementDocument:

    # Convert system requirements to JSON for the prompt.
    system_requirements_json = system_document.model_dump_json(indent=2)

    # Define the prompt.
    prompt_template = ChatPromptTemplate.from_messages([
        (
            "system",
            """
            You are an automotive software requirements engineer.

            Your task is to derive software requirements (SWE) from
            the provided system requirements (SYS).

            Rules:
            - Generate clear, specific and verifiable software requirements.
            - Every SWE requirement must have level "software".
            - Generate unique IDs: SWE-001, SWE-002, etc.
            - The parent field must reference the corresponding SYS requirement.
            - The derived_from field must contain the source SYS requirement ID.
            - Use status "proposed".
            - Do not invent functionality that is not supported by the SYS requirements.
            - Do not repeat system requirements as software requirements.
            - Generate a reasonable number of requirements.
            - Avoid unnecessary detail.

            Return ONLY valid JSON, without Markdown formatting.

            The JSON structure must be:

            {{
                "requirements": [
                    {{
                        "id": "SWE-001",
                        "title": "Example title",
                        "level": "software",
                        "statement": "The software shall ...",
                        "status": "proposed",
                        "priority": "high",
                        "verification_method": "test",
                        "parent": "SYS-001",
                        "derived_from": ["SYS-001"],
                        "rationale": "Reason for this requirement."
                    }}
                ]
            }}
            """
        ),
        (
            "user",
            """
            Derive software requirements from the following system requirements:

            {system_requirements}
            """
        ),
    ])

    # Convert the model response into a plain string.
    output_parser = StrOutputParser()

    # Build the LangChain pipeline.
    chain = prompt_template | model | output_parser

    # Execute the pipeline.
    response_text = chain.invoke({
        "system_requirements": system_requirements_json
    })

    # Convert the JSON string into a Python dictionary.
    generated_data = json.loads(response_text)

    # Validate the generated requirements with Pydantic.
    software_document = RequirementDocument.model_validate(generated_data)

    # Collect the IDs of the system requirements.
    system_ids = [
        requirement.id
        for requirement in system_document.requirements
    ]

    # Check that generated requirements reference existing SYS IDs.
    for requirement in software_document.requirements:

        if requirement.level != "software":
            raise ValueError(
                f"{requirement.id} is not a software requirement."
            )

        if requirement.parent not in system_ids:
            raise ValueError(
                f"{requirement.id} references an invalid parent: "
                f"{requirement.parent}"
            )

        for source_id in requirement.derived_from:
            if source_id not in system_ids:
                raise ValueError(
                    f"{requirement.id} references an invalid source: "
                    f"{source_id}"
                )

    # Create the output directory if it does not exist.
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Save the generated requirements as YAML.
    with output_path.open("w", encoding="utf-8") as file:
        yaml.safe_dump(
            software_document.model_dump(mode="json"),
            file,
            sort_keys=False,
            allow_unicode=True,
        )

    return software_document

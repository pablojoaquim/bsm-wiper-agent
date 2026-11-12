
import os
from pathlib import Path

from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI

from agents.requirement_loader import load_requirements
from agents.requirement_validator import validate_requirements
from agents.requirements_agent import generate_software_requirements


# Project root is the parent directory of src.
PROJECT_ROOT = Path(__file__).resolve().parents[1]


def main():

    # Load environment variables from the project root.
    load_dotenv(PROJECT_ROOT / ".env")

    # Initialize Gemini.
    model = ChatGoogleGenerativeAI(
        model=os.getenv("GEMINI_MODEL"),
        google_api_key=os.getenv("GOOGLE_API_KEY"),
        temperature=0.2,
    )

    # Load system requirements.
    system_document = load_requirements(
        PROJECT_ROOT / "requirements/system/bsm_system_requirements.yaml"
    )

    print(f"Loaded {len(system_document.requirements)} system requirements")

    # Validate the system requirements.
    errors = validate_requirements(system_document)

    if errors:
        print("\nSystem requirement validation FAILED:")
        for error in errors:
            print(f" - {error}")
        return

    print("System requirement validation PASSED")

    # Generate software requirements using Gemini.
    software_document = generate_software_requirements(
        system_document,
        model,
        PROJECT_ROOT / "requirements/software/bsm_software_requirements.yaml",
    )

    print(
        f"\nGenerated {len(software_document.requirements)} "
        "software requirements"
    )

    for requirement in software_document.requirements:
        print(f"{requirement.id}: {requirement.title}")

    print("\nSoftware requirements saved successfully.")


if __name__ == "__main__":
    main()

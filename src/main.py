
import os
from pathlib import Path

from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI

from agents.requirement_loader import load_requirements
from agents.requirement_validator import validate_requirements
from agents.SWE1_software_requirements_agent import generate_software_requirements
from agents.architecture_agent import generate_software_architecture
from agents.design_agent import generate_software_design

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

    # Define artifact paths.
    system_path = PROJECT_ROOT / "processes/SYS.2_system_requirements_analysis/SYS.2_system_requirements.yaml"
    software_path = PROJECT_ROOT / "processes/SWE.1_software_requirements_analysis/SWE.1_software_requirements.yaml"
    architecture_path = PROJECT_ROOT / "processes/SWE.2_software_architectural_design/SWE.2_software_architecture.yaml"
    design_path = PROJECT_ROOT / "processes/SWE.3_software_detailed_design/SWE.3_software_detailed_design.yaml"
    
    # Load system requirements.
    system_document = load_requirements(system_path)

    print(f"Loaded {len(system_document.requirements)} system requirements")

    # Validate system requirements.
    errors = validate_requirements(system_document)

    if errors:
        print("\nSystem requirement validation FAILED:")
        for error in errors:
            print(f" - {error}")
        return

    print("System requirement validation PASSED")

    # Load or generate software requirements.
    if software_path.exists():

        print("\nSoftware requirements already exist. Reusing artifact.")

        software_document = load_requirements(software_path)

    else:

        print("\nGenerating software requirements...")

        software_document = generate_software_requirements(
            system_document,
            model,
            software_path,
        )

    print(f"Software requirements: {len(software_document.requirements)}")

    # Load or generate software architecture.
    if architecture_path.exists():

        print("\nSoftware architecture already exists. Reusing artifact.")

        with architecture_path.open("r", encoding="utf-8") as file:
            import yaml
            architecture = yaml.safe_load(file)

    else:

        print("\nGenerating software architecture...")

        architecture = generate_software_architecture(
            system_document,
            software_document,
            model,
            architecture_path,
        )

    components = architecture["architecture"]["components"]

    print(f"\nSoftware architecture components: {len(components)}")

    for component in components:
        print(f"{component['id']}: {component['name']}")

    # Load or generate software detailed design.
    if design_path.exists():

        print("\nSoftware detailed design already exists. Reusing artifact.")

        with design_path.open("r", encoding="utf-8") as file:
            design = yaml.safe_load(file)

    else:

        print("\nGenerating software detailed design...")

        design = generate_software_design(
            software_document,
            architecture,
            model,
            design_path,
        )

    units = design["software_detailed_design"]["units"]

    print(f"\nSoftware design units: {len(units)}")

    for unit in units:
        print(f"{unit['id']}: {unit['name']}")

    print("\nWorkflow completed successfully.")


if __name__ == "__main__":
    main()


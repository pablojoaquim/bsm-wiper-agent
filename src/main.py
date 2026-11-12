import os

import sys
from pathlib import Path

from dotenv import load_dotenv
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI

from agents.requirement_loader import load_requirements
from agents.requirement_validator import validate_requirements

PROJECT_ROOT = Path(__file__).resolve().parents[1]

def main():

    requirements = load_requirements(
        PROJECT_ROOT / "requirements/system/bsm_system_requirements.yaml"
    )

    print(f"Loaded {len(requirements.requirements)} requirements")

    for requirement in requirements.requirements:
        print(f"{requirement.id}: {requirement.title}")

    errors = validate_requirements(requirements)

    if errors:
        print("\nRequirement validation FAILED:")
        for error in errors:
            print(f" - {error}")
        return

    print("Requirement validation PASSED")

    # # Load the API key from the project's .env file.
    # load_dotenv()
    # model = ChatGoogleGenerativeAI(
    #     model=os.getenv("GEMINI_MODEL"),
    #     google_api_key=os.getenv("GOOGLE_API_KEY"),
    #     temperature=0.7,
    # )

    # # Build a prompt that accepts a topic at invocation time.
    # prompt_template = ChatPromptTemplate.from_messages([
    #     ("system", "You are a helpful AI assistant that explains coding concepts simply."),
    #     ("user", "What is {topic} and why should I care?"),
    # ])

    # # Convert the model's message into a plain string.
    # output_parser = StrOutputParser()

    # # Compose the prompt, model, and parser with LCEL.
    # chain = prompt_template | model | output_parser

    # response = chain.invoke({"topic": "LangChain"})
    # print(response)


if __name__ == "__main__":
    main()
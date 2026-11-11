import os

from dotenv import load_dotenv
from google import genai


def main():
    # Load the API key and send a small request to verify Gemini access.
    load_dotenv()
    client = genai.Client(
        api_key=os.getenv("GOOGLE_API_KEY"),
        http_options={"timeout": 15000},
    )

    print("Sending request to Gemini...", flush=True)
    response = client.models.generate_content(
        model="gemini-3.5-flash",
        contents="Say hello in one sentence.",
    )
    print(response.text)


if __name__ == "__main__":
    main()
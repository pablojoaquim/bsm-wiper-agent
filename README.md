# LangChain Course

Small Python examples using LangChain and Google's Gemini API.

## Setup

Install Python 3.11 or newer, create a virtual environment, and install the dependencies:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

On macOS or Linux, activate the environment with `source .venv/bin/activate` instead.

If an existing virtual environment does not have pip, run `python -m ensurepip --upgrade` after activating it.

Create a `.env` file in the project root containing your Gemini API key:

```dotenv
GOOGLE_API_KEY=your_api_key_here
```

Obtain a key from [Google AI Studio](https://aistudio.google.com/apikey). Keep the key private; `.env` is ignored by Git.

## Run

From the project root, check the Gemini connection:

```sh
python src/test_connection.py
```

Run the LangChain example:

```sh
python src/main.py
```

Both examples use `gemini-3.5-flash`; access depends on your API key and the models available to your account.

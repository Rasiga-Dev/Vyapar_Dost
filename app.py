# import os
# from flask import Flask, request, jsonify, render_template
# from dotenv import load_dotenv
# from openai import OpenAI

# load_dotenv()
# app = Flask(__name__)
# LANGUAGES = {'en':'English','hi':'Hindi','ta':'Tamil','ml':'Malayalam','te':'Telugu','kn':'Kannada','bn':'Bengali','mr':'Marathi','gu':'Gujarati','pa':'Punjabi','ur':'Urdu','or':'Odia','as':'Assamese'}

# @app.get('/')
# def home():
#     return render_template('index.html')

# @app.post('/api/chat')
# def chat():
#     data = request.get_json(silent=True) or {}
#     question = str(data.get('message', '')).strip()
#     if not question or len(question) > 4000:
#         return jsonify(error='Please enter a question of up to 4000 characters.'), 400
#     key = os.getenv('OPENAI_API_KEY', '').strip()
#     if not key or key.startswith('paste_'):
#         return jsonify(error='Add your OpenAI API key to the .env file and restart Python.'), 503
#     language = LANGUAGES.get(data.get('language'), 'English')
#     system = (f'You are Vyapar Dost, a friendly, practical AI helper for Indian street vendors, small shops and other users. '
#               f'Reply in {language} unless the user explicitly requests another language. '
#               'Use simple everyday words and short actionable steps, suitable for people with limited formal education. '
#               'Help with sales, profit, loss, stock, prices, business strategies and general questions. '
#               'For numerical analysis, show your calculations and assumptions. Do not invent business data or promise profits. '
#               'When relevant, use INR and Indian examples. Be respectful and honest about uncertainty.')
#     messages = [{'role':'system','content':system}]
#     history = data.get('history', [])
#     if isinstance(history, list):
#         for item in history[-12:]:
#             if isinstance(item, dict) and item.get('role') in ('user','assistant') and isinstance(item.get('content'), str):
#                 messages.append({'role':item['role'],'content':item['content'][:4000]})
#     messages.append({'role':'user','content':question})
#     try:
#         client = OpenAI(api_key=key, timeout=35.0)
#         response = client.chat.completions.create(model=os.getenv('OPENAI_MODEL','gpt-4o-mini'), messages=messages, max_tokens=900)
#         answer = response.choices[0].message.content or 'Sorry, I could not generate a reply.'
#         return jsonify(answer=answer)
#     except Exception as exc:
#         # Avoid leaking secrets or provider details into browser responses
#         app.logger.warning('AI request failed: %s', type(exc).__name__)
#         return jsonify(error='AI connection failed. Check your API key, billing, internet connection, and model name.'), 502

# if __name__ == '__main__':
#     app.run(host='127.0.0.1', port=5000, debug=False)



import os

from flask import Flask, request, jsonify, render_template
from dotenv import load_dotenv
from openai import OpenAI, APIConnectionError, APITimeoutError
from openai import AuthenticationError, RateLimitError, NotFoundError
from openai import APIStatusError

# Load environment variables from .env
load_dotenv()

app = Flask(__name__)

LANGUAGES = {
    "en": "English",
    "hi": "Hindi",
    "ta": "Tamil",
    "ml": "Malayalam",
    "te": "Telugu",
    "kn": "Kannada",
    "bn": "Bengali",
    "mr": "Marathi",
    "gu": "Gujarati",
    "pa": "Punjabi",
    "ur": "Urdu",
    "or": "Odia",
    "as": "Assamese"
}


@app.get("/")
def home():
    return render_template("index.html")


@app.post("/api/chat")
def chat():
    # Read incoming JSON payload
    data = request.get_json(silent=True) or {}

    question = str(data.get("message", "")).strip()

    # Validate the user's question
    if not question or len(question) > 4000:
        return jsonify(
            error="Please enter a question of up to 4000 characters."
        ), 400

    # Read API key from .env
    api_key = os.getenv("OPENAI_API_KEY", "").strip()

    if (
        not api_key
        or api_key.lower().startswith("paste_")
        or api_key == "YOUR_NEW_API_KEY"
    ):
        app.logger.error("OPENAI_API_KEY is missing or is a placeholder.")

        return jsonify(
            error="OpenAI API key is missing. Add a valid key to .env and restart the server."
        ), 503

    # Read model name from .env
    model = os.getenv("OPENAI_MODEL", "gpt-4o-mini").strip()

    # Choose response language
    language_code = str(data.get("language", "en")).lower()
    language = LANGUAGES.get(language_code, "English")

    # AI instructions
    system_prompt = (
        "You are Vyapar Dost, a friendly, practical AI helper for "
        "Indian street vendors, small shops, and small business owners. "
        f"Reply in {language}, unless the user explicitly requests another language. "
        "Use simple everyday words and short, actionable steps. "
        "Help with sales, profit, loss, stock, prices, business strategies, "
        "and general questions. "
        "For numerical analysis, show calculations and assumptions. "
        "Do not invent business data or promise profits. "
        "When relevant, use INR and Indian examples. "
        "Be respectful and honest about uncertainty."
    )

    # Build conversation messages
    messages = [
        {
            "role": "system",
            "content": system_prompt
        }
    ]

    history = data.get("history", [])

    if isinstance(history, list):
        for item in history[-12:]:
            if (
                isinstance(item, dict)
                and item.get("role") in ("user", "assistant")
                and isinstance(item.get("content"), str)
            ):
                content = item["content"].strip()

                if content:
                    messages.append({
                        "role": item["role"],
                        "content": content[:4000]
                    })

    messages.append({
        "role": "user",
        "content": question
    })

    try:
        # Create OpenAI client
        client = OpenAI(
            api_key=api_key,
            timeout=35.0,
            max_retries=1
        )

        # Send request to OpenAI
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            max_tokens=900
        )

        answer = response.choices[0].message.content

        if not answer:
            answer = "Sorry, I could not generate a reply. Please try again."

        return jsonify(answer=answer), 200

    except AuthenticationError:
        app.logger.exception("OpenAI authentication failed.")

        return jsonify(
            error="Invalid API key. Check OPENAI_API_KEY in your .env file."
        ), 401

    except RateLimitError as exc:
        # Log details in terminal, not in the browser response
        app.logger.error(
            "OpenAI rate/quota error. Type=%s Code=%s Message=%s",
            type(exc).__name__,
            getattr(exc, "code", None),
            getattr(exc, "message", None) or str(exc)
        )

        return jsonify(
            error=(
                "OpenAI API quota or rate limit reached. "
                "Check your API billing, credits, and usage limits."
            )
        ), 429

    except NotFoundError:
        app.logger.exception("OpenAI model or resource not found.")

        return jsonify(
            error="Model not found. Check OPENAI_MODEL in your .env file."
        ), 404

    except (APIConnectionError, APITimeoutError) as exc:
        app.logger.error(
            "OpenAI connection/timeout error. Type=%s Details=%s",
            type(exc).__name__,
            str(exc)
        )

        return jsonify(
            error="Could not connect to OpenAI. Check your internet connection and try again."
        ), 502

    except APIStatusError as exc:
        app.logger.error(
            "OpenAI API status error. Status=%s Type=%s Code=%s Message=%s",
            exc.status_code,
            type(exc).__name__,
            getattr(exc, "code", None),
            getattr(exc, "message", None) or str(exc)
        )

        return jsonify(
            error=f"OpenAI API returned an error (HTTP {exc.status_code}). Check the server terminal."
        ), 502

    except Exception as exc:
        # Keep detailed errors in the terminal only
        app.logger.exception(
            "Unexpected AI request failure. Type=%s",
            type(exc).__name__
        )

        return jsonify(
            error="Unexpected AI error. Check the Python terminal for details."
        ), 500


if __name__ == "__main__":
    app.run(
        host="127.0.0.1",
        port=5000,
        debug=False
    )

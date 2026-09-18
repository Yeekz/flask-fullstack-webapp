"""
WSGI entry point — used by `flask run` and production WSGI servers.
Loads .env if present (python-dotenv).
"""
from dotenv import load_dotenv

load_dotenv()

from app import create_app  # noqa: E402

app = create_app()

if __name__ == "__main__":
    app.run(host="127.0.0.1", debug=False)

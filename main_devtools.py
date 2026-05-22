"""Runtime entrypoint that enables Phone Dev tools without rewriting main.py."""
from main import app, log_system
from devtools import devtools_bp


if "devtools" not in app.blueprints:
    app.register_blueprint(devtools_bp)


if __name__ == "__main__":
    log_system("Server Starting on 0.0.0.0:5000")
    app.run(host="0.0.0.0", port=5000)

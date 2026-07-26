from app import create_app, db

from app.schema import ensure_clipboard_schema

app = create_app()

with app.app_context():
    db.create_all()
    ensure_clipboard_schema()


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5006, debug=True)

from sqlalchemy import inspect, text

from app import db
from app.models import CloudClipboardItem


def ensure_clipboard_schema():
    engine = db.engine
    if engine.dialect.name not in ('mysql', 'mariadb'):
        return

    table_name = CloudClipboardItem.__tablename__
    inspector = inspect(engine)
    if not inspector.has_table(table_name):
        return

    columns = {
        column['name']: str(column['type']).lower()
        for column in inspector.get_columns(table_name)
    }
    content_type = columns.get('content', '')
    if 'mediumtext' in content_type or 'longtext' in content_type:
        return

    db.session.execute(text(f'ALTER TABLE `{table_name}` MODIFY `content` MEDIUMTEXT NOT NULL'))
    db.session.commit()

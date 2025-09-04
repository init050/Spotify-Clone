from django.db import migrations

def create_gin_index(apps, schema_editor):
    # The GIN index is a PostgreSQL-specific feature.
    # We only apply this migration if the database backend is PostgreSQL.
    if schema_editor.connection.vendor == 'postgresql':
        schema_editor.execute(
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_notifications_payload_gin ON notifications_notification USING gin (payload);"
        )

def drop_gin_index(apps, schema_editor):
    if schema_editor.connection.vendor == 'postgresql':
        schema_editor.execute(
            "DROP INDEX CONCURRENTLY IF EXISTS idx_notifications_payload_gin;"
        )

class Migration(migrations.Migration):

    # This migration is not atomic because creating an index concurrently
    # cannot be done inside a transaction.
    atomic = False

    dependencies = [
        ('notifications', '0001_initial'),
    ]

    operations = [
        # We use RunPython to make the operation conditional on the database backend.
        migrations.RunPython(create_gin_index, reverse_code=drop_gin_index),
    ]

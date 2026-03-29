from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('knowledge', '0002_alter_knowledgebase_user_id'),
    ]

    operations = [
        migrations.RunSQL(
            "CREATE EXTENSION IF NOT EXISTS vector",
            reverse_sql="DROP EXTENSION IF EXISTS vector"
        ),
    ]

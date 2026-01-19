from django.db import migrations, models
import django.contrib.postgres.operations


class Migration(migrations.Migration):

    dependencies = [
        ('knowledge', '0003_enable_pgvector'),
    ]

    operations = [
        # 修改embedding列的维度
        migrations.RunSQL(
            "ALTER TABLE tcm_embedding ALTER COLUMN embedding TYPE vector(768)",
            reverse_sql="ALTER TABLE tcm_embedding ALTER COLUMN embedding TYPE vector"
        ),
    ]

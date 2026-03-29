from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('knowledge', '0004_alter_embedding_column_dimension'),
    ]

    operations = [
        # 修改source_type字段的长度
        migrations.AlterField(
            model_name='embedding',
            name='source_type',
            field=models.CharField(db_index=True, max_length=20, verbose_name='资源类型'),
        ),
    ]

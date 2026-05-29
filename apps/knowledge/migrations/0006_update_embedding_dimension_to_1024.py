from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('knowledge', '0005_alter_source_type_length'),
    ]

    operations = [
        # 修改embedding列的维度从768到1024（适配bge-m3模型）
        migrations.RunSQL(
            "ALTER TABLE tcm_embedding ALTER COLUMN embedding TYPE vector(1024)",
            reverse_sql="ALTER TABLE tcm_embedding ALTER COLUMN embedding TYPE vector(768)"
        ),
        # 更新KnowledgeBase表的默认值（数据层面，新记录会使用新默认值）
        migrations.RunSQL(
            "UPDATE tcm_knowledge_base SET embedding_model = 'bge-m3', embedding_dimension = 1024 WHERE embedding_model = 'shibing624/text2vec-base-chinese'",
            reverse_sql="UPDATE tcm_knowledge_base SET embedding_model = 'shibing624/text2vec-base-chinese', embedding_dimension = 768 WHERE embedding_model = 'bge-m3'"
        ),
    ]

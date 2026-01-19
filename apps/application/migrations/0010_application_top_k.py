from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('application', '0009_application_enable_file_upload'),
    ]

    operations = [
        migrations.AddField(
            model_name='application',
            name='top_k',
            field=models.IntegerField(default=5, verbose_name='知识库检索返回的最大段落数'),
        ),
    ]

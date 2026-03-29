from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('application', '0008_remove_application_top_k_alter_application_icon_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='application',
            name='enable_file_upload',
            field=models.BooleanField(default=True, verbose_name='是否启用文件上传功能'),
        ),
    ]

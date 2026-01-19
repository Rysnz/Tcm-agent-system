from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('chat', '0002_file_alter_chatmessage_options_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='chatmessage',
            name='satisfaction',
            field=models.IntegerField(blank=True, choices=[(0, '不满意'), (1, '满意')], null=True, verbose_name='用户满意度评分'),
        ),
        migrations.AddField(
            model_name='chatmessage',
            name='tokens',
            field=models.IntegerField(default=0, verbose_name='消耗的tokens数'),
        ),
    ]

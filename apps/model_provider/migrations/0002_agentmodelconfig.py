from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('model_provider', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='AgentModelConfig',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('agent_name', models.CharField(max_length=100, unique=True, verbose_name='Agent名称')),
                ('is_delete', models.BooleanField(default=False, verbose_name='是否删除')),
                ('create_time', models.DateTimeField(auto_now_add=True, verbose_name='创建时间')),
                ('update_time', models.DateTimeField(auto_now=True, verbose_name='更新时间')),
                ('model', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='agent_bindings', to='model_provider.modelconfig', verbose_name='绑定模型')),
            ],
            options={
                'verbose_name': 'Agent模型配置',
                'verbose_name_plural': 'Agent模型配置',
                'ordering': ['agent_name'],
            },
        ),
    ]

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
                ('agent_name', models.CharField(
                    help_text='如：IntakeAgent、InquiryAgent',
                    max_length=100,
                    unique=True,
                    verbose_name='Agent名称'
                )),
                ('update_time', models.DateTimeField(auto_now=True, verbose_name='更新时间')),
                ('model_config', models.ForeignKey(
                    blank=True,
                    null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='agent_assignments',
                    to='model_provider.modelconfig',
                    verbose_name='分配的模型配置'
                )),
            ],
            options={
                'verbose_name': 'Agent模型配置',
                'verbose_name_plural': 'Agent模型配置',
            },
        ),
    ]

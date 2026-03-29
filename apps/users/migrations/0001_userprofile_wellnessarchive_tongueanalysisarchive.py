from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='UserProfile',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('display_name', models.CharField(blank=True, default='', max_length=64)),
                ('phone', models.CharField(blank=True, default='', max_length=32)),
                ('avatar', models.TextField(blank=True, default='')),
                ('create_time', models.DateTimeField(auto_now_add=True)),
                ('update_time', models.DateTimeField(auto_now=True)),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='profile', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'db_table': 'user_profile',
                'verbose_name': '用户档案',
                'verbose_name_plural': '用户档案',
            },
        ),
        migrations.CreateModel(
            name='WellnessArchive',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('constitution', models.CharField(max_length=64)),
                ('cycle_days', models.IntegerField(default=7)),
                ('source_syndrome', models.CharField(blank=True, default='', max_length=128)),
                ('plan_json', models.JSONField(default=dict)),
                ('create_time', models.DateTimeField(auto_now_add=True)),
                ('update_time', models.DateTimeField(auto_now=True)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='wellness_archives', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'db_table': 'wellness_archive',
                'verbose_name': '养生档案',
                'verbose_name_plural': '养生档案',
                'ordering': ['-create_time'],
            },
        ),
        migrations.CreateModel(
            name='TongueAnalysisArchive',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('session_id', models.CharField(blank=True, default='', max_length=128)),
                ('image_name', models.CharField(blank=True, default='', max_length=256)),
                ('analysis_json', models.JSONField(default=dict)),
                ('create_time', models.DateTimeField(auto_now_add=True)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='tongue_archives', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'db_table': 'tongue_analysis_archive',
                'verbose_name': '舌象分析档案',
                'verbose_name_plural': '舌象分析档案',
                'ordering': ['-create_time'],
            },
        ),
        migrations.CreateModel(
            name='ConsultArchive',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('session_id', models.CharField(db_index=True, max_length=128)),
                ('title', models.CharField(default='问诊会话', max_length=128)),
                ('current_stage', models.CharField(default='inquiry', max_length=32)),
                ('latest_question', models.TextField(blank=True, default='')),
                ('latest_answer', models.TextField(blank=True, default='')),
                ('is_high_risk', models.BooleanField(default=False)),
                ('create_time', models.DateTimeField(auto_now_add=True)),
                ('update_time', models.DateTimeField(auto_now=True)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='consult_archives', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'db_table': 'consult_archive',
                'verbose_name': '问诊档案',
                'verbose_name_plural': '问诊档案',
                'ordering': ['-update_time'],
            },
        ),
        migrations.AddConstraint(
            model_name='consultarchive',
            constraint=models.UniqueConstraint(fields=('user', 'session_id'), name='uniq_consult_archive_user_session'),
        ),
    ]

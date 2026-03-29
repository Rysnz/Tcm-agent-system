# Generated migration for agents app

from django.db import migrations, models
import django.utils.timezone
import uuid


class Migration(migrations.Migration):
    """
    创建Agent会话持久化表
    """

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name='ConsultationSession',
            fields=[
                ('session_id', models.CharField(db_index=True, default=uuid.uuid4, max_length=64, primary_key=True, serialize=False, unique=True, verbose_name='会话ID')),
                ('state_data', models.JSONField(default=dict, help_text='存储完整的SessionState序列化数据', verbose_name='会话状态数据')),
                ('current_stage', models.CharField(default='intake', help_text='问诊流程当前阶段', max_length=32, verbose_name='当前阶段')),
                ('is_high_risk', models.BooleanField(default=False, help_text='标记是否检测到高风险症状', verbose_name='是否高风险')),
                ('chief_complaint', models.TextField(blank=True, default='', help_text='患者主要不适描述', verbose_name='主诉')),
                ('primary_syndrome', models.CharField(blank=True, default='', help_text='辨证结果的主证型', max_length=128, verbose_name='主证型')),
                ('patient_age_group', models.CharField(blank=True, default='', max_length=32, verbose_name='年龄段')),
                ('patient_gender', models.CharField(blank=True, default='', max_length=16, verbose_name='性别')),
                ('is_pregnant', models.BooleanField(default=False, verbose_name='是否妊娠期')),
                ('is_minor', models.BooleanField(default=False, verbose_name='是否未成年')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='创建时间')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='更新时间')),
                ('last_active_at', models.DateTimeField(default=django.utils.timezone.now, help_text='用于会话超时清理', verbose_name='最后活跃时间')),
                ('is_completed', models.BooleanField(default=False, help_text='问诊流程是否已完成', verbose_name='是否已完成')),
                ('is_archived', models.BooleanField(default=False, help_text='用于会话归档管理', verbose_name='是否已归档')),
                ('message_count', models.IntegerField(default=0, verbose_name='消息数量')),
                ('agent_step_count', models.IntegerField(default=0, verbose_name='Agent执行步数')),
                ('user_id', models.CharField(blank=True, db_index=True, default='', help_text='关联的用户标识，匿名用户为空', max_length=64, verbose_name='用户ID')),
                ('client_ip', models.GenericIPAddressField(blank=True, null=True, verbose_name='客户端IP')),
                ('user_agent', models.TextField(blank=True, default='', verbose_name='User-Agent')),
            ],
            options={
                'verbose_name': '问诊会话',
                'verbose_name_plural': '问诊会话',
                'db_table': 'agents_consultation_session',
                'ordering': ['-updated_at'],
            },
        ),
        migrations.CreateModel(
            name='AgentExecutionLog',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('agent_name', models.CharField(max_length=64, verbose_name='Agent名称')),
                ('stage', models.CharField(max_length=32, verbose_name='执行阶段')),
                ('started_at', models.DateTimeField(verbose_name='开始时间')),
                ('finished_at', models.DateTimeField(blank=True, null=True, verbose_name='结束时间')),
                ('success', models.BooleanField(default=False, verbose_name='是否成功')),
                ('error_message', models.TextField(blank=True, default='', verbose_name='错误信息')),
                ('retry_count', models.IntegerField(default=0, verbose_name='重试次数')),
                ('duration_ms', models.IntegerField(blank=True, null=True, verbose_name='执行时长(毫秒)')),
                ('input_summary', models.TextField(blank=True, default='', verbose_name='输入摘要')),
                ('output_summary', models.TextField(blank=True, default='', verbose_name='输出摘要')),
                ('trace_id', models.CharField(blank=True, default='', max_length=64, verbose_name='追踪ID')),
                ('session', models.ForeignKey(on_delete=models.deletion.CASCADE, related_name='execution_logs', to='agents.consultationsession', verbose_name='关联会话')),
            ],
            options={
                'verbose_name': 'Agent执行日志',
                'verbose_name_plural': 'Agent执行日志',
                'db_table': 'agents_execution_log',
                'ordering': ['-started_at'],
            },
        ),
        migrations.AddIndex(
            model_name='consultationsession',
            index=models.Index(fields=['-updated_at'], name='idx_session_updated'),
        ),
        migrations.AddIndex(
            model_name='consultationsession',
            index=models.Index(fields=['user_id', '-updated_at'], name='idx_session_user'),
        ),
        migrations.AddIndex(
            model_name='consultationsession',
            index=models.Index(fields=['current_stage'], name='idx_session_stage'),
        ),
        migrations.AddIndex(
            model_name='consultationsession',
            index=models.Index(fields=['is_completed', '-updated_at'], name='idx_session_status'),
        ),
        migrations.AddIndex(
            model_name='agentexecutionlog',
            index=models.Index(fields=['session', '-started_at'], name='idx_log_session'),
        ),
        migrations.AddIndex(
            model_name='agentexecutionlog',
            index=models.Index(fields=['agent_name', '-started_at'], name='idx_log_agent'),
        ),
        migrations.AddIndex(
            model_name='agentexecutionlog',
            index=models.Index(fields=['success', '-started_at'], name='idx_log_success'),
        ),
    ]

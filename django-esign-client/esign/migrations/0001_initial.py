import uuid
import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name='ESignTransaction',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('transaction_id', models.CharField(db_index=True, max_length=200, unique=True)),
                ('pre_signed_temp_file', models.CharField(max_length=1000)),
                ('gateway_parameter', models.TextField(blank=True)),
                ('signer_id', models.CharField(blank=True, max_length=255)),
                ('doc_info', models.CharField(blank=True, max_length=500)),
                ('esign_type', models.CharField(default='V2', max_length=10)),
                ('auth_mode', models.CharField(default='OTP', max_length=30)),
                ('response_xml', models.TextField(blank=True)),
                ('signed_file_paths', models.TextField(blank=True)),
                ('status', models.CharField(
                    choices=[('initiated', 'Initiated'), ('completed', 'Completed'), ('failed', 'Failed')],
                    default='initiated',
                    max_length=20,
                )),
                ('error_code', models.CharField(blank=True, max_length=100)),
                ('error_message', models.TextField(blank=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('completed_at', models.DateTimeField(blank=True, null=True)),
            ],
            options={
                'verbose_name': 'eSign Transaction',
                'verbose_name_plural': 'eSign Transactions',
                'ordering': ['-created_at'],
            },
        ),
    ]

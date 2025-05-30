# Generated by Django 5.2 on 2025-04-06 09:40

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='AccessToken',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('token', models.CharField(max_length=255)),
                ('token_end_time', models.DateTimeField()),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'verbose_name': 'Access Token',
                'verbose_name_plural': 'Access Tokens',
            },
        ),
        migrations.CreateModel(
            name='ErrorLog',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('error_data', models.TextField()),
                ('timestamp', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'verbose_name': 'Error Log',
                'verbose_name_plural': 'Error Logs',
            },
        ),
        migrations.CreateModel(
            name='Profile',
            fields=[
                ('unique_identifier', models.CharField(max_length=20, primary_key=True, serialize=False)),
                ('person_type', models.CharField(choices=[('IranianPrivatePerson', 'Iranian Private Person'), ('IranianLegalPerson', 'Iranian Legal Person')], max_length=30)),
                ('mobile', models.CharField(max_length=15)),
                ('email', models.EmailField(blank=True, max_length=254, null=True)),
                ('first_name', models.CharField(blank=True, max_length=100, null=True)),
                ('last_name', models.CharField(blank=True, max_length=100, null=True)),
                ('father_name', models.CharField(blank=True, max_length=100, null=True)),
                ('gender', models.CharField(blank=True, max_length=10, null=True)),
                ('birth_date', models.CharField(blank=True, max_length=20, null=True)),
                ('place_of_birth', models.CharField(blank=True, max_length=100, null=True)),
                ('place_of_issue', models.CharField(blank=True, max_length=100, null=True)),
                ('company_name', models.CharField(blank=True, max_length=200, null=True)),
                ('economic_code', models.CharField(blank=True, max_length=30, null=True)),
                ('register_date', models.CharField(blank=True, max_length=20, null=True)),
                ('register_place', models.CharField(blank=True, max_length=100, null=True)),
                ('register_number', models.CharField(blank=True, max_length=30, null=True)),
                ('trade_code', models.CharField(blank=True, max_length=30, null=True)),
                ('sheba', models.CharField(blank=True, max_length=30, null=True)),
                ('bank_name', models.CharField(blank=True, max_length=100, null=True)),
                ('bank_branch_code', models.CharField(blank=True, max_length=20, null=True)),
                ('bank_branch_name', models.CharField(blank=True, max_length=100, null=True)),
                ('bank_branch_city', models.CharField(blank=True, max_length=100, null=True)),
                ('bank_account_number', models.CharField(blank=True, max_length=30, null=True)),
                ('raw_data', models.JSONField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'verbose_name': 'User Profile',
                'verbose_name_plural': 'User Profiles',
            },
        ),
        migrations.CreateModel(
            name='Shareholder',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('unique_identifier', models.CharField(max_length=20)),
                ('first_name', models.CharField(max_length=100)),
                ('last_name', models.CharField(max_length=100)),
                ('position', models.CharField(max_length=50)),
                ('profile', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='shareholders', to='profiling.profile')),
            ],
            options={
                'verbose_name': 'Shareholder',
                'verbose_name_plural': 'Shareholders',
                'unique_together': {('profile', 'unique_identifier')},
            },
        ),
    ]

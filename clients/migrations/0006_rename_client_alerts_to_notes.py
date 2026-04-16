from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("clients", "0005_alter_client_alerts"),
    ]

    operations = [
        migrations.RenameField(
            model_name="client",
            old_name="alerts",
            new_name="notes",
        ),
        migrations.AlterField(
            model_name="client",
            name="notes",
            field=models.TextField(blank=True, verbose_name="Notes"),
        ),
    ]

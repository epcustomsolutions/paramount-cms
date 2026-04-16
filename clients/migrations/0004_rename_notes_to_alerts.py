from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("clients", "0003_split_client_name"),
    ]

    operations = [
        migrations.RenameField(
            model_name="client",
            old_name="notes",
            new_name="alerts",
        ),
    ]

from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("clients", "0001_initial"),
    ]

    operations = [
        migrations.RenameModel(
            old_name="Owner",
            new_name="Client",
        ),
    ]

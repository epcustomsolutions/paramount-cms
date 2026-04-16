from django.db import migrations, models


def split_name(apps, schema_editor):
    Client = apps.get_model("clients", "Client")
    for c in Client.objects.all():
        raw = (getattr(c, "name", None) or "").strip()
        if not raw:
            first, last = "", ""
        else:
            parts = raw.split()
            if len(parts) == 1:
                first, last = parts[0], ""
            else:
                first = parts[0]
                last = " ".join(parts[1:])
        c.first_name = first
        c.last_name = last
        c.save(update_fields=["first_name", "last_name"])


class Migration(migrations.Migration):
    dependencies = [
        ("clients", "0002_rename_owner_client"),
    ]

    operations = [
        migrations.AddField(
            model_name="client",
            name="first_name",
            field=models.CharField(default="", max_length=100),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="client",
            name="last_name",
            field=models.CharField(default="", max_length=100),
            preserve_default=False,
        ),
        migrations.RunPython(split_name, migrations.RunPython.noop),
        migrations.RemoveField(
            model_name="client",
            name="name",
        ),
        migrations.AlterModelOptions(
            name="client",
            options={"ordering": ["last_name", "first_name", "id"]},
        ),
    ]


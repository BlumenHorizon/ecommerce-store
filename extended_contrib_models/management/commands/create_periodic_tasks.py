import json

from django.conf import settings
from django.core.management import BaseCommand
from django.db import transaction
from django_celery_beat.models import CrontabSchedule, PeriodicTask


class Command(BaseCommand):
    help = "Register periodic tasks in Celery Beat dynamically."

    TASKS = [
        {
            "name": "make_db_dump",
            "task_path": "extended_contrib_models.tasks.make_db_dump",
            "description": "Создаёт дамп MySQL с уникальным именем, сжимает его и отправляет админам в Telegram.",
            "hour": "2",
            "minute": "0",
            "args": [],
            "kwargs": {},
        },
        {
            "name": "make_bills_archive",
            "task_path": "extended_contrib_models.tasks.make_bills_archive",
            "description": "Создаёт архив папки media/bills и отправляет админам в Telegram.",
            "hour": "3",
            "minute": "0",
            "args": [],
            "kwargs": {},
        },
    ]

    def handle(self, *args, **options):
        for task_info in self.TASKS:
            self.register_task(task_info)

    def register_task(self, task_info: dict):
        try:
            with transaction.atomic():
                schedule, _ = CrontabSchedule.objects.get_or_create(
                    hour=task_info.get("hour", "0"),
                    minute=task_info.get("minute", "0"),
                    timezone=settings.TIME_ZONE,
                )

                task_name = task_info["name"]
                task_path = task_info["task_path"]

                task, created = PeriodicTask.objects.get_or_create(
                    name=f"{task_info.get('description_prefix', 'Задача')} - {task_name}",
                    defaults={
                        "task": task_path,
                        "crontab": schedule,
                        "enabled": True,
                        "args": json.dumps(task_info.get("args", [])),
                        "kwargs": json.dumps(task_info.get("kwargs", {})),
                        "description": task_info.get("description", ""),
                    },
                )

                if created:
                    print(f"[INFO] PeriodicTask '{task.name}' создана успешно.")
                else:
                    print(f"[WARNING] PeriodicTask '{task.name}' уже существует.")

        except Exception as e:
            print(
                f"[ERROR] Ошибка при создании PeriodicTask '{task_info['name']}': {e}"
            )

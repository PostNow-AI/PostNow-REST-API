from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from Analytics.models import AnalyticsEvent


class Command(BaseCommand):
    help = "Remove AnalyticsEvent antigos para controle de volume/retenção."

    def add_arguments(self, parser):
        parser.add_argument(
            "--days",
            type=int,
            default=90,
            help="Manter somente eventos com occurred_at nos últimos N dias (default: 90).",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Não deleta nada; apenas mostra quantos seriam removidos.",
        )

    def handle(self, *args, **options):
        days = int(options["days"])
        dry_run = bool(options["dry_run"])

        if days < 1:
            self.stderr.write(self.style.ERROR("--days deve ser >= 1"))
            return

        cutoff = timezone.now() - timedelta(days=days)
        qs = AnalyticsEvent.objects.filter(occurred_at__lt=cutoff)
        to_delete = qs.count()

        if dry_run:
            self.stdout.write(
                self.style.WARNING(
                    f"DRY RUN: removeria {to_delete} eventos com occurred_at < {cutoff.isoformat()}."
                )
            )
            return

        deleted, _details = qs.delete()
        self.stdout.write(
            self.style.SUCCESS(
                f"Removidos {deleted} registros (AnalyticsEvent) com occurred_at < {cutoff.isoformat()}."
            )
        )


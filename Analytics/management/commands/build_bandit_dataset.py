from datetime import timedelta

from django.core.management.base import BaseCommand
from django.db.models import Count
from django.utils import timezone

from Analytics.models import AnalyticsEvent, Decision, DecisionOutcome
from CreditSystem.models import CreditTransaction


class Command(BaseCommand):
    help = "Agrega eventos por decision_id e calcula recompensa (DecisionOutcome)."

    def add_arguments(self, parser):
        parser.add_argument("--decision-type", default="image_pregen")
        parser.add_argument("--policy-id", default=None)
        parser.add_argument("--min-age-minutes", type=int, default=60)
        parser.add_argument("--limit", type=int, default=500)
        parser.add_argument("--dry-run", action="store_true")

    def handle(self, *args, **options):
        decision_type = options["decision_type"]
        policy_id = options["policy_id"]
        min_age_minutes = options["min_age_minutes"]
        limit = options["limit"]
        dry_run = options["dry_run"]

        cutoff = timezone.now() - timedelta(minutes=min_age_minutes)

        qs = (
            Decision.objects.filter(decision_type=decision_type, occurred_at__lt=cutoff)
            .filter(outcome__isnull=True)
            .order_by("occurred_at")
        )
        if policy_id:
            qs = qs.filter(policy_id=policy_id)

        decisions = list(qs[:limit])
        if not decisions:
            self.stdout.write(self.style.SUCCESS("Nada para agregar."))
            return

        # Penalidade de custo: aproxima valor por crédito.
        # Mantemos preço fixo centralizado no CreditSystem.
        image_cost = float(CreditTransaction.get_fixed_price("image_generation"))

        created = 0
        for decision in decisions:
            counts = dict(
                AnalyticsEvent.objects.filter(decision_id=decision.id)
                .values("event_name")
                .annotate(c=Count("event_name"))
                .values_list("event_name", "c")
            )

            download_ok = int(counts.get("image_download_succeeded", 0))
            download_fail = int(counts.get("image_download_failed", 0))
            generate = int(counts.get("image_generate_clicked", 0))
            regen = int(counts.get("image_regenerate_clicked", 0))

            # Recompensa:
            # - valor: downloads bem-sucedidos
            # - fricção: regeneração/erro de download
            # - custo: pré-geração (se action=pre_generate) e cada geração on-demand/regeneração
            pregen_cost_units = 1 if decision.action == "pre_generate" else 0
            cost_penalty = image_cost * float(pregen_cost_units + generate + regen)

            reward = (2.0 * download_ok) + (-1.0 * regen) + (-1.0 * download_fail) - cost_penalty
            success = download_ok > 0

            metrics = {
                "download_succeeded": download_ok,
                "download_failed": download_fail,
                "image_generate_clicked": generate,
                "image_regenerate_clicked": regen,
                "image_cost": image_cost,
                "cost_penalty": cost_penalty,
                "events_total": int(sum(counts.values())),
                "counts": counts,
            }

            if dry_run:
                continue

            DecisionOutcome.objects.create(
                decision=decision,
                reward=reward,
                success=success,
                metrics=metrics,
            )
            created += 1

        if dry_run:
            self.stdout.write(
                self.style.WARNING(
                    f"DRY RUN: agregaria {len(decisions)} decisões ({decision_type})."
                )
            )
            return

        self.stdout.write(self.style.SUCCESS(f"Outcomes criados: {created}"))


from collections import defaultdict

from django.core.management.base import BaseCommand

from Analytics.models import BanditArmStat, Decision
from Analytics.services.image_pregen_policy import (
    ACTION_ON_DEMAND,
    ACTION_PRE_GENERATE,
    DECISION_TYPE_IMAGE_PREGEN,
)


class Command(BaseCommand):
    help = "Recalcula alpha/beta (Thompson) a partir de DecisionOutcome."

    def add_arguments(self, parser):
        parser.add_argument("--policy-id", default="image_pregen_bandit_v1")
        parser.add_argument("--dry-run", action="store_true")

    def handle(self, *args, **options):
        policy_id = options["policy_id"]
        dry_run = options["dry_run"]

        qs = (
            Decision.objects.filter(decision_type=DECISION_TYPE_IMAGE_PREGEN, policy_id=policy_id)
            .select_related("outcome")
            .filter(outcome__isnull=False)
        )

        counts = defaultdict(lambda: {"success": 0, "failure": 0})

        for decision in qs.iterator():
            bucket = (decision.context or {}).get("bucket") or "type=unknown|obj=unknown"
            key = (bucket, decision.action)

            if decision.outcome.success:
                counts[key]["success"] += 1
            else:
                counts[key]["failure"] += 1

        actions = [ACTION_PRE_GENERATE, ACTION_ON_DEMAND]
        buckets = {bucket for (bucket, _action) in counts.keys()}
        touched = 0

        for (bucket, action) in [
            (bucket, action) for bucket in buckets for action in actions
        ]:
            # garantir ambas ações por bucket
            s = counts[(bucket, action)]["success"]
            f = counts[(bucket, action)]["failure"]

            alpha = 1.0 + float(s)
            beta = 1.0 + float(f)

            if dry_run:
                touched += 1
                continue

            BanditArmStat.objects.update_or_create(
                decision_type=DECISION_TYPE_IMAGE_PREGEN,
                policy_id=policy_id,
                bucket=bucket,
                action=action,
                defaults={"alpha": alpha, "beta": beta},
            )
            touched += 1

        if dry_run:
            self.stdout.write(
                self.style.WARNING(f"DRY RUN: recalcularia {touched} arms para {policy_id}")
            )
            return

        self.stdout.write(self.style.SUCCESS(f"Arms atualizados: {touched} ({policy_id})"))


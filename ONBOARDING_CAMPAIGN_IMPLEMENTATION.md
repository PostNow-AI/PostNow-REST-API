# Onboarding Email Campaign - Implementation Complete

## Overview

Successfully implemented a 3-email drip campaign system for users with active subscriptions who haven't completed onboarding. The system sends emails on Day 1, 3, and 7 after subscription activation at 10 AM Brazilian time (13:00 UTC).

## What Was Implemented

### 1. OnboardingCampaign Django App

- **Location**: `/OnboardingCampaign/`
- **Model**: `OnboardingEmail` tracks scheduled emails with fields:
  - `user`: FK to User
  - `email_number`: 1, 2, or 3
  - `scheduled_for`: Timezone-aware datetime (America/Sao_Paulo)
  - `sent_at`: When email was sent
  - `cancelled`: True if user completed onboarding before sending
- **Admin Interface**: Full admin panel to view/monitor campaign status

### 2. Email Templates

- **Location**: `/templates/onboarding/`
- **Files**:
  - `email_1.html` - "Você está quase lá do certo com o seu conteúdo!"
  - `email_2.html` - "A PostNow vai ajudar sua Prothea seja o 'chato' do..."
  - `email_3.html` - "Falta só mais um passo para você poder criar um post!"
- **Content**: Exact Portuguese text from the provided image with purple CTA buttons

### 3. Onboarding Email Service

- **Location**: `/OnboardingCampaign/services/onboarding_email_service.py`
- **Functions**:
  - `schedule_campaign_for_user(user, subscription_start_date)` - Creates 3 email schedules
  - `send_due_emails()` - Async function to send emails (called by cron)
  - `cancel_campaign_for_user(user)` - Cancels remaining emails when onboarding completed
  - `get_campaign_status(user)` - Get campaign status for a user

### 4. Integrations

#### Stripe Webhook Integration

- **File**: `/CreditSystem/services/subscription_service.py`
- **When**: After `UserSubscription` is created and `has_active_subscription` becomes True
- **Action**: Automatically schedules 3 emails based on subscription start date
- **Checks**: Only schedules if user has `creator_profile` and `onboarding_completed=False`

#### CreatorProfile Integration

- **File**: `/CreatorProfile/models.py`
- **When**: `onboarding_completed` transitions from False to True
- **Action**: Automatically cancels all remaining unsent emails
- **Safety**: Wrapped in try-except to not fail save operation

### 5. Vercel Cron Job

- **Configuration**: `/vercel.json`
- **Schedule**: Daily at 13:00 UTC (10 AM BRT)
- **Endpoint**: `/api/v1/onboarding-campaign/cron/send-emails/`
- **Function**: Queries due emails, checks onboarding status, sends via Mailjet

### 6. Backfill Script

- **Location**: `/scripts/backfill_onboarding_campaigns.py`
- **Purpose**: Process existing users with active subscriptions but incomplete onboarding
- **Features**:
  - Respects original 1/3/7 day timing from subscription start
  - Marks past-due emails as cancelled to avoid spam
  - Dry-run mode for testing
- **Usage**:

  ```bash
  # Test what would happen
  python scripts/backfill_onboarding_campaigns.py --dry-run

  # Apply changes
  python scripts/backfill_onboarding_campaigns.py
  ```

## Email Campaign Flow

### For New Users (After This Implementation)

1. User completes payment → Stripe webhook fires
2. `UserSubscription` created with `status='active'`
3. `UserSubscriptionStatus.has_active_subscription` set to True
4. System checks if `creator_profile.onboarding_completed == False`
5. If False, `schedule_campaign_for_user()` creates 3 `OnboardingEmail` records:
   - Email 1: Subscription start + 1 day at 10 AM BRT
   - Email 2: Subscription start + 3 days at 10 AM BRT
   - Email 3: Subscription start + 7 days at 10 AM BRT

### Daily Cron Execution

1. Vercel cron hits endpoint at 13:00 UTC (10 AM BRT)
2. `send_due_emails()` queries emails where:
   - `scheduled_for <= now`
   - `sent_at IS NULL`
   - `cancelled = False`
3. For each email:
   - Double-check user hasn't completed onboarding
   - If completed → cancel campaign and skip
   - If not completed → send email via Mailjet
   - Mark `sent_at` with current timestamp
4. Logs results to AuditSystem

### When User Completes Onboarding

1. User fills out `CreatorProfile` completely
2. `onboarding_completed` becomes True in save() method
3. `cancel_campaign_for_user()` called automatically
4. All unsent emails marked as `cancelled=True`
5. User stops receiving emails

### For Existing Users (Backfill)

1. Run backfill script (see usage above)
2. Script finds users with:
   - `has_active_subscription = True`
   - `onboarding_completed = False`
   - Less than 3 emails scheduled
3. Creates missing email records based on actual subscription date
4. Past-due emails marked as cancelled (won't send)
5. Future emails will be sent by cron

## Configuration

### Environment Variables Required

All already configured via existing MailjetService:

- `MJ_APIKEY_PUBLIC` - Mailjet public API key
- `MJ_APIKEY_PRIVATE` - Mailjet private API key
- `SENDER_EMAIL` - Default sender email
- `SENDER_NAME` - Default sender name

### Email Schedule Configuration

**Location**: `/OnboardingCampaign/services/onboarding_email_service.py`

```python
EMAIL_SCHEDULE = {
    1: {'days': 1, 'hour': 10},   # Day 1 at 10 AM BRT
    2: {'days': 3, 'hour': 10},   # Day 3 at 10 AM BRT
    3: {'days': 7, 'hour': 10},   # Day 7 at 10 AM BRT
}
```

To change schedule, modify the `days` or `hour` values.

### Email Content

**Templates**: `/templates/onboarding/email_1.html`, `email_2.html`, `email_3.html`
**URLs** (hardcoded in service, update as needed):

- `onboarding_url`: Currently `https://postnow.app/onboarding`
- `chat_url`: Currently `https://chat.ivy`

Update these URLs in `/OnboardingCampaign/services/onboarding_email_service.py` line ~129:

```python
context = {
    'onboarding_url': 'https://postnow.app/onboarding',  # Update this
    'chat_url': 'https://chat.ivy',  # Update this
}
```

## Testing

### 1. Test New User Flow

```python
# In Django shell
from django.contrib.auth.models import User
from OnboardingCampaign.services.onboarding_email_service import schedule_campaign_for_user
from django.utils import timezone

user = User.objects.get(email='test@example.com')
schedule_campaign_for_user(user, timezone.now())

# Check created emails
from OnboardingCampaign.models import OnboardingEmail
OnboardingEmail.objects.filter(user=user)
```

### 2. Test Email Sending (Dry Run)

```python
# In Django shell
from OnboardingCampaign.services.onboarding_email_service import send_due_emails
import asyncio

result = asyncio.run(send_due_emails())
print(result)
```

### 3. Test Cancellation

```python
# In Django shell
from django.contrib.auth.models import User
from OnboardingCampaign.services.onboarding_email_service import cancel_campaign_for_user

user = User.objects.get(email='test@example.com')
cancel_campaign_for_user(user)

# Or update CreatorProfile
user.creator_profile.onboarding_completed = True
user.creator_profile.save()  # Should auto-cancel
```

### 4. Test Cron Endpoint

```bash
# Local test
curl http://localhost:8000/api/v1/onboarding-campaign/cron/send-emails/

# Production
curl https://your-vercel-domain.vercel.app/api/v1/onboarding-campaign/cron/send-emails/
```

### 5. Monitor via Admin

1. Go to `/admin/`
2. Navigate to "Onboarding Campaign" → "Emails de Onboarding"
3. View status of all scheduled emails
4. Filter by email number, status, user, etc.

## Next Steps

### Before Going Live

1. **Update URLs in templates**: Change `onboarding_url` and `chat_url` to actual production URLs
2. **Run backfill script**: Process existing users
   ```bash
   cd /home/matheussb/Documentos/PostNow/Project/PostNow-REST-API
   source venv/bin/activate
   python scripts/backfill_onboarding_campaigns.py --dry-run  # Test first
   python scripts/backfill_onboarding_campaigns.py  # Then apply
   ```
3. **Test email delivery**: Create test subscription, verify emails send correctly
4. **Verify Vercel cron**: After deployment, check Vercel dashboard → Project → Cron Jobs
5. **Monitor first week**: Check admin panel daily to ensure emails are sending

### Optional Enhancements

1. **Email tracking**: Mailjet webhook already logs opens/clicks to AuditSystem
2. **A/B testing**: Create variants of email templates
3. **Personalization**: Add user name or business name to templates
4. **Dashboard**: Create analytics view for campaign performance
5. **Unsubscribe**: Add unsubscribe link to emails

## Files Modified

### Created

- `/OnboardingCampaign/` (entire app)
- `/templates/onboarding/email_1.html`
- `/templates/onboarding/email_2.html`
- `/templates/onboarding/email_3.html`
- `/scripts/backfill_onboarding_campaigns.py`

### Modified

- `/CreditSystem/services/subscription_service.py` - Added campaign scheduling
- `/CreatorProfile/models.py` - Added campaign cancellation
- `/Sonora_REST_API/settings.py` - Added app to INSTALLED_APPS
- `/Sonora_REST_API/urls.py` - Added campaign URLs
- `/vercel.json` - Added cron configuration
- `/requirements.txt` - Added pytz

## Deployment Checklist

- [x] Migrations created and applied locally
- [x] All integrations tested
- [x] Vercel cron configured
- [ ] Update production URLs in email templates
- [ ] Deploy to Vercel
- [ ] Verify cron job appears in Vercel dashboard
- [ ] Run backfill script for existing users
- [ ] Monitor first batch of emails
- [ ] Check AuditSystem logs for any errors

## Support

For issues or questions:

1. Check `/OnboardingCampaign/admin.py` for campaign status
2. Check AuditSystem logs for email sending errors
3. Review Vercel logs for cron execution
4. Test individual functions in Django shell

---

**Implementation Date**: January 29, 2026
**Status**: ✅ Complete and Ready for Deployment

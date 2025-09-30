#!/usr/bin/env python3
"""
Comprehensive test to debug webhook issues and subscription cancellation
"""

from django.urls import reverse
from django.contrib.auth import get_user_model
from CreditSystem.services.subscription_service import SubscriptionService
from CreditSystem.models import UserSubscription
import hashlib
import hmac
import json
import os
import sys
import time

import django
from django.conf import settings

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Sonora_REST_API.settings')
sys.path.append('/home/matheussb/Documents/Sonora/Project/Sonora-REST-API')
django.setup()


def check_webhook_configuration():
    """Check webhook configuration and URLs"""
    print("🔧 Checking Webhook Configuration")
    print("=" * 50)

    # Check webhook secret
    webhook_secret = getattr(settings, 'STRIPE_WEBHOOK_SECRET', None)
    if webhook_secret:
        print("✅ STRIPE_WEBHOOK_SECRET configured")
        print(f"   Secret starts with: {webhook_secret[:10]}...")
    else:
        print("❌ STRIPE_WEBHOOK_SECRET not configured")

    # Check webhook URL
    try:
        webhook_url = reverse('credit_system:stripe-subscription-webhook')
        print(f"✅ Subscription webhook URL: {webhook_url}")
        print(f"   Full URL would be: http://your-domain.com{webhook_url}")
    except Exception as e:
        print(f"❌ Webhook URL error: {e}")

    # Check Stripe configuration
    stripe_secret = getattr(settings, 'STRIPE_SECRET_KEY', None)
    if stripe_secret:
        print("✅ STRIPE_SECRET_KEY configured")
        if stripe_secret.startswith('sk_test_'):
            print("   ⚠️  Using TEST mode")
        elif stripe_secret.startswith('sk_live_'):
            print("   ✅ Using LIVE mode")
    else:
        print("❌ STRIPE_SECRET_KEY not configured")


def check_current_subscriptions():
    """Check current user subscriptions"""
    print("\n🔧 Checking Current Subscriptions")
    print("=" * 50)

    User = get_user_model()
    user = User.objects.first()

    if not user:
        print("❌ No users found in database")
        return None

    print(f"👤 User: {user.email}")

    # All subscriptions
    all_subs = UserSubscription.objects.filter(
        user=user).order_by('-start_date')
    print(f"📊 Total subscriptions: {all_subs.count()}")

    # Active subscriptions
    active_subs = UserSubscription.objects.filter(user=user, status='active')
    print(f"🟢 Active subscriptions: {active_subs.count()}")

    for i, sub in enumerate(active_subs):
        print(f"   Active #{i+1}:")
        print(f"     ID: {sub.id}")
        print(f"     Plan: {sub.plan.name} ({sub.plan.interval})")
        print(f"     Stripe ID: {sub.stripe_subscription_id}")
        print(f"     Start: {sub.start_date}")
        print(f"     End: {sub.end_date}")

    # Recent cancelled subscriptions
    cancelled_subs = UserSubscription.objects.filter(
        user=user, status='cancelled'
    ).order_by('-end_date')[:3]
    print(f"🔴 Recent cancelled subscriptions: {cancelled_subs.count()}")

    for i, sub in enumerate(cancelled_subs):
        print(f"   Cancelled #{i+1}:")
        print(f"     ID: {sub.id}")
        print(f"     Plan: {sub.plan.name}")
        print(f"     Stripe ID: {sub.stripe_subscription_id}")
        print(f"     Cancelled: {sub.end_date}")

    return user


def test_manual_webhook_trigger():
    """Test manual webhook trigger for subscription deletion"""
    print("\n🔧 Testing Manual Webhook Trigger")
    print("=" * 50)

    User = get_user_model()
    user = User.objects.first()

    # Find the most recent cancelled subscription with Stripe ID
    cancelled_sub = UserSubscription.objects.filter(
        user=user,
        status='cancelled',
        stripe_subscription_id__isnull=False
    ).order_by('-end_date').first()

    if not cancelled_sub:
        print("❌ No cancelled subscription with Stripe ID found")
        return

    print(
        f"📋 Testing webhook for subscription: {cancelled_sub.stripe_subscription_id}")
    print(f"   Current status: {cancelled_sub.status}")
    print(f"   End date: {cancelled_sub.end_date}")

    # Temporarily reactivate subscription to test cancellation webhook
    print("🔄 Temporarily reactivating subscription for webhook test...")
    original_status = cancelled_sub.status
    original_end_date = cancelled_sub.end_date

    cancelled_sub.status = 'active'
    cancelled_sub.end_date = None
    cancelled_sub.save()
    print(f"   Status changed to: {cancelled_sub.status}")

    # Create webhook payload
    webhook_payload = {
        "id": "evt_test_webhook_cancel",
        "object": "event",
        "api_version": "2020-08-27",
        "created": int(time.time()),
        "data": {
            "object": {
                "id": cancelled_sub.stripe_subscription_id,
                "object": "subscription",
                "status": "canceled",
                "customer": "cus_test_customer",
                "metadata": {
                    "user_id": str(user.id),
                    "plan_id": str(cancelled_sub.plan.id)
                }
            }
        },
        "livemode": False,
        "pending_webhooks": 1,
        "request": {
            "id": "req_test_cancel",
            "idempotency_key": None
        },
        "type": "customer.subscription.deleted"
    }

    payload_json = json.dumps(webhook_payload)
    webhook_secret = getattr(
        settings, 'STRIPE_WEBHOOK_SECRET', 'whsec_test_secret')

    # Create signature
    timestamp = str(int(time.time()))
    signed_payload = f"{timestamp}.{payload_json}"
    signature = hmac.new(
        webhook_secret.encode('utf-8'),
        signed_payload.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()
    sig_header = f"t={timestamp},v1={signature}"

    try:
        # Process webhook
        subscription_service = SubscriptionService()
        result = subscription_service.process_webhook(
            payload_json.encode(), sig_header)

        print("✅ Webhook processed successfully")
        print(f"   Result: {result}")

        # Check final status
        cancelled_sub.refresh_from_db()
        print(f"   Final status: {cancelled_sub.status}")
        print(f"   Final end date: {cancelled_sub.end_date}")

        if cancelled_sub.status == 'cancelled':
            print("✅ Webhook successfully cancelled the subscription")
        else:
            print("❌ Webhook did not cancel the subscription")

    except Exception as e:
        print(f"❌ Webhook processing failed: {str(e)}")
        # Restore original state
        cancelled_sub.status = original_status
        cancelled_sub.end_date = original_end_date
        cancelled_sub.save()


def check_stripe_webhook_logs():
    """Check for Stripe webhook logs"""
    print("\n🔧 Checking Webhook Logs")
    print("=" * 50)

    log_files = [
        '/tmp/stripe_subscription_webhook_debug.log',
        '/tmp/stripe_webhook_debug.log'
    ]

    for log_file in log_files:
        if os.path.exists(log_file):
            print(f"📁 Found log file: {log_file}")
            try:
                with open(log_file, 'r') as f:
                    content = f.read()
                    if content:
                        lines = content.split('\n')
                        print(f"   Lines: {len(lines)}")
                        print("   Recent entries:")
                        for line in lines[-10:]:  # Last 10 lines
                            if line.strip():
                                print(f"     {line}")
                    else:
                        print("   File is empty")
            except Exception as e:
                print(f"   Error reading file: {e}")
        else:
            print(f"📁 Log file not found: {log_file}")


def provide_troubleshooting_guide():
    """Provide troubleshooting steps"""
    print("\n🛠️ Troubleshooting Guide")
    print("=" * 50)

    webhook_url = "Unknown"
    try:
        webhook_url = reverse('credit_system:stripe-subscription-webhook')
    except:
        pass

    print("📋 Common issues and solutions:")
    print()
    print("1. ❌ Webhooks not reaching your server:")
    print("   • Make sure your server is publicly accessible")
    print("   • Check if webhook URL is correctly set in Stripe Dashboard")
    print(f"   • Webhook URL should be: https://your-domain.com{webhook_url}")
    print("   • Test webhook URL accessibility with curl or browser")
    print()
    print("2. ❌ Webhook signature verification failing:")
    print("   • Verify STRIPE_WEBHOOK_SECRET matches Stripe Dashboard")
    print("   • Check webhook endpoint is using correct secret")
    print()
    print("3. ❌ Test mode vs Live mode mismatch:")
    print("   • Test webhooks only work with test API keys")
    print("   • Live webhooks only work with live API keys")
    print()
    print("4. ❌ Subscription not found in webhook:")
    print("   • Check subscription ID exists in database")
    print("   • Verify subscription is linked to correct user")
    print()
    print("📋 Manual webhook testing:")
    print("   • Use Stripe CLI: stripe listen --forward-to localhost:8000/credit-system/webhook/subscription/")
    print("   • Test webhook from Stripe Dashboard")
    print("   • Check server logs for webhook attempts")


def main():
    print("🚀 Comprehensive Webhook & Subscription Debug")
    print("=" * 70)

    check_webhook_configuration()
    user = check_current_subscriptions()

    if user:
        test_manual_webhook_trigger()

    check_stripe_webhook_logs()
    provide_troubleshooting_guide()

    print("\n✅ Debug Complete!")
    print("Next steps:")
    print("1. Check Stripe Dashboard webhook configuration")
    print("2. Verify webhook URL is publicly accessible")
    print("3. Test webhook manually from Stripe Dashboard")
    print("4. Check server logs during webhook attempts")


if __name__ == "__main__":
    main()

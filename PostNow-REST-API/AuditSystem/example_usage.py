"""
Example usage of the AuditSystem

This file demonstrates how to integrate audit logging throughout the application.
"""

from AuditSystem.services import AuditService, AuditTimer


# Example 1: Basic audit logging
def create_post_example(user, post_data, request=None):
    """Example of logging post creation"""
    try:
        # Your post creation logic here
        post = create_post_logic(user, post_data)

        # Log successful post creation
        AuditService.log_post_operation(
            user=user,
            action='post_created',
            post_id=str(post.id),
            status='success',
            request=request,
            details={
                'post_type': post.post_type,
                'has_image': bool(post.image_url)
            }
        )

        return post

    except Exception as e:
        # Log failed post creation
        AuditService.log_post_operation(
            user=user,
            action='post_created',
            post_id='',  # No post_id for failed creation
            status='error',
            request=request,
            error_message=str(e),
            details={'post_data': post_data}
        )
        raise

# Example 2: Using AuditTimer for automatic timing


def generate_content_example(user, prompt, request=None):
    """Example of logging content generation with timing"""
    with AuditTimer(
        AuditService.log_content_generation,
        user=user,
        action='content_generated',
        status='success',  # Will be overridden if exception occurs
        request=request,
        details={'prompt_length': len(prompt)}
    ) as timer:
        # Your content generation logic here
        content = generate_content_logic(prompt)

        # Update timer with additional details
        timer.audit_log.details.update({
            'content_length': len(content),
            'model_used': 'gemini-pro'
        })

        return content

# Example 3: Subscription operations


def create_subscription_example(user, subscription_data, request=None):
    """Example of logging subscription creation"""
    try:
        subscription = create_subscription_logic(user, subscription_data)

        AuditService.log_subscription_operation(
            user=user,
            action='subscription_created',
            status='success',
            request=request,
            details={
                'plan_type': subscription.plan_type,
                'amount': str(subscription.amount)
            }
        )

        return subscription

    except Exception as e:
        AuditService.log_subscription_operation(
            user=user,
            action='subscription_created',
            status='error',
            request=request,
            error_message=str(e)
        )
        raise

# Example 4: Email operations


def send_welcome_email_example(user, request=None):
    """Example of logging email sending"""
    try:
        # Your email sending logic here
        send_email_logic(user.email, 'Welcome to PostNow!',
                         'welcome_template.html')

        AuditService.log_email_operation(
            user=user,
            action='email_sent',
            status='success',
            request=request,
            details={
                'email_type': 'welcome',
                'recipient': user.email
            }
        )

    except Exception as e:
        AuditService.log_email_operation(
            user=user,
            action='email_failed',
            status='error',
            request=request,
            error_message=str(e),
            details={
                'email_type': 'welcome',
                'recipient': user.email
            }
        )
        raise

# Example 5: Credit operations


def purchase_credits_example(user, amount, request=None):
    """Example of logging credit purchase"""
    try:
        transaction = purchase_credits_logic(user, amount)

        AuditService.log_credit_operation(
            user=user,
            action='credit_purchased',
            status='success',
            request=request,
            details={
                'amount': amount,
                'transaction_id': transaction.id,
                'payment_method': transaction.payment_method
            }
        )

        return transaction

    except Exception as e:
        AuditService.log_credit_operation(
            user=user,
            action='credit_purchased',
            status='error',
            request=request,
            error_message=str(e),
            details={'amount': amount}
        )
        raise

# Example 6: Authentication operations (usually handled by middleware)
# These are typically handled automatically by the AuditMiddleware,
# but you can log additional details if needed


def custom_login_example(user, request=None):
    """Example of additional logging during custom authentication"""
    # Basic login is handled by middleware, but you can add custom details
    AuditService.log_auth_operation(
        user=user,
        action='login',
        status='success',
        request=request,
        details={
            'login_method': 'custom_auth',
            'device_info': get_device_info(request)
        }
    )

# Example 7: System operations


def daily_content_generation_job():
    """Example of logging system-level operations"""
    try:
        results = run_daily_content_generation()

        AuditService.log_system_operation(
            action='daily_generation_completed',
            status='success',
            details={
                'posts_generated': results['count'],
                'users_processed': results['users']
            }
        )

    except Exception as e:
        AuditService.log_system_operation(
            action='daily_generation_completed',
            status='error',
            error_message=str(e)
        )
        raise

# Helper functions (these would be your actual business logic)


def create_post_logic(user, post_data):
    # Placeholder for actual post creation
    return type('Post', (), {'id': 123, 'post_type': 'image', 'image_url': 'http://example.com/image.jpg'})()


def generate_content_logic(prompt):
    # Placeholder for content generation
    return "Generated content based on prompt"


def create_subscription_logic(user, subscription_data):
    # Placeholder for subscription creation
    return type('Subscription', (), {'plan_type': 'premium', 'amount': 29.99})()


def send_email_logic(email, subject, template):
    # Placeholder for email sending
    pass


def purchase_credits_logic(user, amount):
    # Placeholder for credit purchase
    return type('Transaction', (), {'id': 'txn_123', 'payment_method': 'stripe'})()


def get_device_info(request):
    # Placeholder for device detection
    return "Desktop - Chrome"


def run_daily_content_generation():
    # Placeholder for daily content generation
    return {'count': 50, 'users': 25}

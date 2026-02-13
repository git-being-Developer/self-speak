"""
Billing Service - Lemon Squeezy Integration
Handles subscription checkout, webhooks, and plan management.
"""

import os
import hmac
import hashlib
import json
from typing import Dict, Any, Optional
from datetime import datetime
import requests
from supabase import Client

class BillingService:
    """Handles Lemon Squeezy subscription payments and webhooks."""

    LEMON_API_KEY = os.getenv("LEMON_SQUEEZY_API_KEY")
    LEMON_WEBHOOK_SECRET = os.getenv("LEMON_SQUEEZY_WEBHOOK_SECRET")
    LEMON_STORE_ID = os.getenv("LEMON_SQUEEZY_STORE_ID")

    # Product variant IDs (set these from your Lemon Squeezy dashboard)
    MONTHLY_VARIANT_ID = os.getenv("LEMON_MONTHLY_VARIANT_ID")
    ANNUAL_VARIANT_ID = os.getenv("LEMON_ANNUAL_VARIANT_ID")

    LEMON_API_BASE = "https://api.lemonsqueezy.com/v1"

    def __init__(self, supabase: Client):
        self.supabase = supabase

        if not self.LEMON_API_KEY:
            raise ValueError("LEMON_SQUEEZY_API_KEY environment variable not set")
        if not self.LEMON_WEBHOOK_SECRET:
            raise ValueError("LEMON_SQUEEZY_WEBHOOK_SECRET environment variable not set")

    def create_checkout_session(
        self,
        user_id: str,
        user_email: str,
        plan_type: str = "monthly"
    ) -> Dict[str, Any]:
        """
        Create a Lemon Squeezy checkout session.

        Args:
            user_id: Authenticated user ID
            user_email: User's email address
            plan_type: 'monthly' or 'annual'

        Returns:
            Dict with checkout_url

        Raises:
            ValueError: If plan type is invalid or API call fails
        """
        # Select variant based on plan type
        if plan_type == "monthly":
            variant_id = self.MONTHLY_VARIANT_ID
        elif plan_type == "annual":
            variant_id = self.ANNUAL_VARIANT_ID
        else:
            raise ValueError(f"Invalid plan type: {plan_type}")

        if not variant_id:
            raise ValueError(f"Variant ID not configured for plan: {plan_type}")

        # Prepare checkout data
        checkout_data = {
            "data": {
                "type": "checkouts",
                "attributes": {
                    "checkout_data": {
                        "email": user_email,
                        "custom": {
                            "user_id": user_id  # Critical: passed to webhook
                        }
                    },
                    "product_options": {
                        "enabled_variants": [variant_id]
                    },
                    "checkout_options": {
                        "button_color": "#7B9E9D"  # Selfspeak brand color
                    }
                },
                "relationships": {
                    "store": {
                        "data": {
                            "type": "stores",
                            "id": self.LEMON_STORE_ID
                        }
                    },
                    "variant": {
                        "data": {
                            "type": "variants",
                            "id": variant_id
                        }
                    }
                }
            }
        }

        # Call Lemon Squeezy API
        headers = {
            "Authorization": f"Bearer {self.LEMON_API_KEY}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }

        response = requests.post(
            f"{self.LEMON_API_BASE}/checkouts",
            json=checkout_data,
            headers=headers
        )

        if response.status_code != 201:
            raise ValueError(f"Lemon Squeezy API error: {response.text}")

        result = response.json()
        checkout_url = result["data"]["attributes"]["url"]

        return {
            "checkout_url": checkout_url,
            "plan_type": plan_type
        }

    def verify_webhook_signature(self, payload: bytes, signature: str) -> bool:
        """
        Verify Lemon Squeezy webhook signature.

        Args:
            payload: Raw webhook payload bytes
            signature: X-Signature header value

        Returns:
            True if signature is valid
        """
        if not signature:
            return False

        # Compute HMAC signature
        computed_signature = hmac.new(
            self.LEMON_WEBHOOK_SECRET.encode(),
            payload,
            hashlib.sha256
        ).hexdigest()

        # Constant-time comparison
        return hmac.compare_digest(computed_signature, signature)

    def process_webhook(self, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process Lemon Squeezy webhook event.

        Args:
            event_data: Parsed webhook JSON

        Returns:
            Processing result

        Raises:
            ValueError: If event is invalid or missing required data
        """
        meta = event_data.get("meta", {})
        event_name = meta.get("event_name")
        event_id = meta.get("event_id")

        if not event_id:
            raise ValueError("Missing event_id in webhook")

        # Check if event already processed (idempotency)
        existing = self.supabase.table("lemon_webhook_events").select("id").eq(
            "event_id", event_id
        ).execute()

        if existing.data:
            return {"status": "already_processed", "event_id": event_id}

        # Extract subscription data
        data = event_data.get("data", {})
        attributes = data.get("attributes", {})

        subscription_id = data.get("id")
        customer_id = attributes.get("customer_id")
        status = attributes.get("status")
        renewal_date_str = attributes.get("renews_at")

        # Extract user_id from custom data (passed during checkout)
        custom_data = attributes.get("first_subscription_item", {}).get("custom_data", {})
        user_id = custom_data.get("user_id")

        if not user_id:
            # Try alternative location
            user_id = meta.get("custom_data", {}).get("user_id")

        if not user_id:
            raise ValueError("Missing user_id in webhook metadata")

        # Parse renewal date
        renewal_date = None
        if renewal_date_str:
            try:
                renewal_date = datetime.fromisoformat(renewal_date_str.replace("Z", "+00:00"))
            except Exception:
                pass

        # Log webhook event
        self.supabase.table("lemon_webhook_events").insert({
            "event_id": event_id,
            "event_type": event_name,
            "payload": event_data,
            "user_id": user_id,
            "subscription_id": subscription_id,
            "created_at": datetime.now().isoformat()
        }).execute()

        # Process based on event type
        if event_name in ["subscription_created", "subscription_updated"]:
            return self._handle_subscription_active(
                user_id=user_id,
                subscription_id=subscription_id,
                customer_id=customer_id,
                status=status,
                renewal_date=renewal_date
            )

        elif event_name in ["subscription_cancelled", "subscription_expired"]:
            return self._handle_subscription_inactive(
                user_id=user_id,
                subscription_id=subscription_id,
                status=status
            )

        else:
            # Unknown event type, log but don't fail
            return {"status": "ignored", "event_type": event_name}

    def _handle_subscription_active(
        self,
        user_id: str,
        subscription_id: str,
        customer_id: str,
        status: str,
        renewal_date: Optional[datetime]
    ) -> Dict[str, Any]:
        """Handle subscription activation or update."""

        # Check if subscription exists
        existing = self.supabase.table("subscriptions").select("*").eq(
            "user_id", user_id
        ).execute()

        update_data = {
            "plan": "pro",
            "lemon_subscription_id": subscription_id,
            "lemon_customer_id": str(customer_id),
            "status": status if status in ["active", "past_due", "unpaid"] else "active",
            "renewal_date": renewal_date.isoformat() if renewal_date else None
        }

        if existing.data:
            # Update existing subscription
            self.supabase.table("subscriptions").update(update_data).eq(
                "user_id", user_id
            ).execute()
        else:
            # Create new subscription
            update_data["user_id"] = user_id
            update_data["started_at"] = datetime.now().isoformat()
            self.supabase.table("subscriptions").insert(update_data).execute()

        return {
            "status": "subscription_activated",
            "user_id": user_id,
            "plan": "pro"
        }

    def _handle_subscription_inactive(
        self,
        user_id: str,
        subscription_id: str,
        status: str
    ) -> Dict[str, Any]:
        """Handle subscription cancellation or expiration."""

        # Downgrade to free plan
        self.supabase.table("subscriptions").update({
            "plan": "free",
            "status": status if status in ["cancelled", "expired"] else "cancelled",
            "renewal_date": None
        }).eq("user_id", user_id).execute()

        return {
            "status": "subscription_deactivated",
            "user_id": user_id,
            "plan": "free"
        }

    def get_user_subscription(self, user_id: str) -> Optional[Dict[str, Any]]:
        """
        Get user's current subscription details.

        Args:
            user_id: User ID

        Returns:
            Subscription data or None
        """
        response = self.supabase.table("subscriptions").select("*").eq(
            "user_id", user_id
        ).execute()

        if response.data:
            return response.data[0]
        return None

    def is_pro_user(self, user_id: str) -> bool:
        """
        Check if user has active Pro subscription.

        Args:
            user_id: User ID

        Returns:
            True if user is Pro
        """
        subscription = self.get_user_subscription(user_id)

        if not subscription:
            return False

        return subscription.get("plan") == "pro" and subscription.get("status") == "active"


# Singleton instance (initialized in main.py)
billing_service: Optional[BillingService] = None

"""
Brandmint CLI — System notifications for long-running operations.

Provides desktop notifications when pipelines complete, useful for
multi-minute operations where user may switch context.

Usage:
    from brandmint.cli.notifications import notify_completion, notify_error

    # After pipeline completes
    notify_completion("Tryambakam Noesis", success=True, assets_generated=19)
    
    # On error
    notify_error("Tryambakam Noesis", "API rate limit exceeded")
"""

import platform
import subprocess
import logging
from typing import Optional

logger = logging.getLogger(__name__)


def _macos_notify(title: str, message: str, sound: bool = True) -> bool:
    """Send notification on macOS using osascript.
    
    Args:
        title: Notification title
        message: Notification body text
        sound: Play notification sound
        
    Returns:
        True if notification was sent successfully
    """
    try:
        script = f'display notification "{message}" with title "{title}"'
        if sound:
            script += ' sound name "Glass"'
        
        subprocess.run(
            ["osascript", "-e", script],
            capture_output=True,
            timeout=5,
        )
        return True
    except (subprocess.TimeoutExpired, FileNotFoundError) as e:
        logger.debug(f"macOS notification failed: {e}")
        return False


def _linux_notify(title: str, message: str) -> bool:
    """Send notification on Linux using notify-send.
    
    Args:
        title: Notification title
        message: Notification body text
        
    Returns:
        True if notification was sent successfully
    """
    try:
        subprocess.run(
            ["notify-send", title, message],
            capture_output=True,
            timeout=5,
        )
        return True
    except (subprocess.TimeoutExpired, FileNotFoundError) as e:
        logger.debug(f"Linux notification failed: {e}")
        return False


def send_notification(title: str, message: str, sound: bool = True) -> bool:
    """Send a system notification (cross-platform).
    
    Automatically detects the platform and uses the appropriate
    notification mechanism.
    
    Args:
        title: Notification title
        message: Notification body text
        sound: Play notification sound (macOS only)
        
    Returns:
        True if notification was sent successfully
    """
    system = platform.system()
    
    if system == "Darwin":
        return _macos_notify(title, message, sound)
    elif system == "Linux":
        return _linux_notify(title, message)
    else:
        # Windows or unknown - skip notification
        logger.debug(f"Notifications not supported on {system}")
        return False


def notify_completion(
    brand_name: str,
    success: bool = True,
    assets_generated: int = 0,
    duration_seconds: Optional[float] = None,
) -> bool:
    """Send notification when pipeline completes.
    
    Args:
        brand_name: Name of the brand that was processed
        success: Whether the pipeline completed successfully
        assets_generated: Number of assets generated
        duration_seconds: Total duration in seconds
        
    Returns:
        True if notification was sent
        
    Example:
        notify_completion("Tryambakam Noesis", success=True, assets_generated=19)
    """
    if success:
        title = "✓ Brandmint Complete"
        parts = [f"{brand_name} finished"]
        if assets_generated > 0:
            parts.append(f"{assets_generated} assets generated")
        if duration_seconds:
            minutes = int(duration_seconds // 60)
            secs = int(duration_seconds % 60)
            parts.append(f"in {minutes}m {secs}s" if minutes else f"in {secs}s")
        message = " • ".join(parts)
    else:
        title = "✗ Brandmint Failed"
        message = f"{brand_name} pipeline failed"
    
    return send_notification(title, message, sound=success)


def notify_error(brand_name: str, error_message: str) -> bool:
    """Send notification when an error occurs.
    
    Args:
        brand_name: Name of the brand being processed
        error_message: Short description of the error
        
    Returns:
        True if notification was sent
    """
    title = "⚠ Brandmint Error"
    message = f"{brand_name}: {error_message[:100]}"
    return send_notification(title, message, sound=True)


def notify_wave_complete(brand_name: str, wave_number: int, wave_name: str) -> bool:
    """Send notification when a wave completes (optional, for long runs).
    
    Args:
        brand_name: Name of the brand
        wave_number: Completed wave number
        wave_name: Name of the wave
        
    Returns:
        True if notification was sent
    """
    title = f"Wave {wave_number} Complete"
    message = f"{brand_name}: {wave_name}"
    return send_notification(title, message, sound=False)


def notify_waiting_for_input(brand_name: str, skill_id: str) -> bool:
    """Send notification when waiting for user input.
    
    Useful when a text skill needs manual execution.
    
    Args:
        brand_name: Name of the brand
        skill_id: Skill waiting for input
        
    Returns:
        True if notification was sent
    """
    title = "⏸ Input Needed"
    message = f"{brand_name}: {skill_id} waiting for output"
    return send_notification(title, message, sound=True)


# =============================================================================
# Webhook Notifications
# =============================================================================

def send_webhook_notification(
    webhook_url: str,
    brand_name: str,
    success: bool,
    waves_completed: int,
    message: Optional[str] = None,
) -> bool:
    """Send completion notification to a webhook URL (Slack, Discord, etc).
    
    Supports Slack and Discord webhook formats automatically.
    
    Args:
        webhook_url: URL to POST to
        brand_name: Name of the brand
        success: Whether the pipeline completed successfully
        waves_completed: Number of waves completed
        message: Optional custom message
        
    Returns:
        True if webhook was sent successfully
    """
    import json
    import urllib.request
    import urllib.error
    
    status_emoji = "✅" if success else "❌"
    status_text = "completed successfully" if success else "failed"
    
    # Detect webhook type from URL
    if "slack.com" in webhook_url or "hooks.slack.com" in webhook_url:
        # Slack format
        payload = {
            "text": f"{status_emoji} *Brandmint Pipeline {status_text}*",
            "blocks": [
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"{status_emoji} *{brand_name}* pipeline {status_text}\n"
                                f"• Waves completed: {waves_completed}\n"
                                + (f"• {message}" if message else "")
                    }
                }
            ]
        }
    elif "discord.com" in webhook_url or "discordapp.com" in webhook_url:
        # Discord format
        color = 0x00FF00 if success else 0xFF0000
        payload = {
            "embeds": [{
                "title": f"Brandmint Pipeline {status_text.title()}",
                "description": f"{brand_name}",
                "color": color,
                "fields": [
                    {"name": "Status", "value": status_emoji + " " + status_text, "inline": True},
                    {"name": "Waves", "value": str(waves_completed), "inline": True},
                ],
            }]
        }
        if message:
            payload["embeds"][0]["fields"].append({"name": "Note", "value": message})
    else:
        # Generic JSON format
        payload = {
            "event": "brandmint.pipeline.complete",
            "brand": brand_name,
            "success": success,
            "waves_completed": waves_completed,
            "message": message,
        }
    
    try:
        data = json.dumps(payload).encode("utf-8")
        request = urllib.request.Request(
            webhook_url,
            data=data,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(request, timeout=10) as response:
            return response.status == 200 or response.status == 204
    except (urllib.error.URLError, urllib.error.HTTPError) as e:
        logger.warning(f"Webhook notification failed: {e}")
        return False
    except Exception as e:
        logger.debug(f"Webhook error: {e}")
        return False

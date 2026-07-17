#!/usr/bin/env python3
"""Alert notification channels for GEO brand audit monitoring."""

from __future__ import annotations

import json
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Any, Dict, List, Optional

try:
    import httpx
    HAS_HTTPX = True
except ImportError:
    HAS_HTTPX = False


class AlertChannel:
    """Base class for alert notification channels."""
    
    def send(self, alert: Dict[str, Any]) -> bool:
        """Send alert notification. Returns True if successful."""
        raise NotImplementedError


class EmailChannel(AlertChannel):
    """Email notification channel via SMTP."""
    
    def __init__(self):
        self.smtp_host = os.getenv("ALERT_EMAIL_SMTP", "smtp.gmail.com")
        self.smtp_port = int(os.getenv("ALERT_EMAIL_PORT", "587"))
        self.username = os.getenv("ALERT_EMAIL_USER", "")
        self.password = os.getenv("ALERT_EMAIL_PASSWORD", "")
        self.recipients = os.getenv("ALERT_EMAIL_RECIPIENTS", "").split(",")
    
    def send(self, alert: Dict[str, Any]) -> bool:
        """Send alert via email."""
        if not all([self.username, self.password, self.recipients]):
            return False
        
        try:
            msg = MIMEMultipart()
            msg["From"] = self.username
            msg["To"] = ", ".join(self.recipients)
            msg["Subject"] = f"[GEO Alert] {alert['severity'].upper()}: {alert['metric']}"
            
            body = f"""
GEO Brand Audit Alert

Brand: {alert['brand_name']}
Severity: {alert['severity'].upper()}
Metric: {alert['metric']}
Current Value: {alert['current_value']:.2f}
Threshold: {alert['threshold']:.2f}
Message: {alert['message']}
Triggered At: {alert['triggered_at']}

---
This is an automated alert from GEO Brand Audit.
"""
            msg.attach(MIMEText(body, "plain"))
            
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                server.starttls()
                server.login(self.username, self.password)
                server.send_message(msg)
            
            return True
        except Exception as e:
            print(f"Email alert failed: {e}")
            return False


class SlackChannel(AlertChannel):
    """Slack notification channel via Webhook."""
    
    def __init__(self):
        self.webhook_url = os.getenv("ALERT_SLACK_WEBHOOK", "")
    
    def send(self, alert: Dict[str, Any]) -> bool:
        """Send alert via Slack webhook."""
        if not self.webhook_url:
            return False
        
        try:
            severity_emoji = {
                "critical": ":rotating_light:",
                "warning": ":warning:",
                "info": ":information_source:"
            }
            
            payload = {
                "text": f"{severity_emoji.get(alert['severity'], ':bell:')} *GEO Alert: {alert['metric']}*",
                "blocks": [
                    {
                        "type": "header",
                        "text": {
                            "type": "plain_text",
                            "text": f"GEO Alert: {alert['severity'].upper()}"
                        }
                    },
                    {
                        "type": "section",
                        "fields": [
                            {"type": "mrkdwn", "text": f"*Brand:*\n{alert['brand_name']}"},
                            {"type": "mrkdwn", "text": f"*Metric:*\n{alert['metric']}"},
                            {"type": "mrkdwn", "text": f"*Current Value:*\n{alert['current_value']:.2f}"},
                            {"type": "mrkdwn", "text": f"*Threshold:*\n{alert['threshold']:.2f}"}
                        ]
                    },
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": f"*Message:* {alert['message']}"
                        }
                    }
                ]
            }
            
            if HAS_HTTPX:
                response = httpx.post(self.webhook_url, json=payload, timeout=10)
                response.raise_for_status()
            else:
                import urllib.request
                data = json.dumps(payload).encode('utf-8')
                req = urllib.request.Request(self.webhook_url, data=data, headers={'Content-Type': 'application/json'})
                urllib.request.urlopen(req, timeout=10)
            return True
        except Exception as e:
            print(f"Slack alert failed: {e}")
            return False


class WeChatChannel(AlertChannel):
    """WeChat Work notification channel via Webhook."""
    
    def __init__(self):
        self.webhook_url = os.getenv("ALERT_WECHAT_WEBHOOK", "")
    
    def send(self, alert: Dict[str, Any]) -> bool:
        """Send alert via WeChat Work webhook."""
        if not self.webhook_url:
            return False
        
        try:
            severity_emoji = {
                "critical": "🚨",
                "warning": "⚠️",
                "info": "ℹ️"
            }
            
            content = f"""
{severity_emoji.get(alert['severity'], '🔔')} GEO品牌审计告警

品牌: {alert['brand_name']}
严重程度: {alert['severity'].upper()}
指标: {alert['metric']}
当前值: {alert['current_value']:.2f}
阈值: {alert['threshold']:.2f}
消息: {alert['message']}
触发时间: {alert['triggered_at']}
"""
            
            payload = {
                "msgtype": "text",
                "text": {
                    "content": content
                }
            }
            
            if HAS_HTTPX:
                response = httpx.post(self.webhook_url, json=payload, timeout=10)
                response.raise_for_status()
            else:
                import urllib.request
                data = json.dumps(payload).encode('utf-8')
                req = urllib.request.Request(self.webhook_url, data=data, headers={'Content-Type': 'application/json'})
                urllib.request.urlopen(req, timeout=10)
            return True
        except Exception as e:
            print(f"WeChat alert failed: {e}")
            return False


class DingTalkChannel(AlertChannel):
    """DingTalk notification channel via Webhook."""
    
    def __init__(self):
        self.webhook_url = os.getenv("ALERT_DINGTALK_WEBHOOK", "")
    
    def send(self, alert: Dict[str, Any]) -> bool:
        """Send alert via DingTalk webhook."""
        if not self.webhook_url:
            return False
        
        try:
            severity_emoji = {
                "critical": "🚨",
                "warning": "⚠️",
                "info": "ℹ️"
            }
            
            content = f"""
{severity_emoji.get(alert['severity'], '🔔')} GEO品牌审计告警

**品牌**: {alert['brand_name']}
**严重程度**: {alert['severity'].upper()}
**指标**: {alert['metric']}
**当前值**: {alert['current_value']:.2f}
**阈值**: {alert['threshold']:.2f}
**消息**: {alert['message']}
**触发时间**: {alert['triggered_at']}
"""
            
            payload = {
                "msgtype": "markdown",
                "markdown": {
                    "title": f"GEO Alert: {alert['metric']}",
                    "text": content
                }
            }
            
            if HAS_HTTPX:
                response = httpx.post(self.webhook_url, json=payload, timeout=10)
                response.raise_for_status()
            else:
                import urllib.request
                data = json.dumps(payload).encode('utf-8')
                req = urllib.request.Request(self.webhook_url, data=data, headers={'Content-Type': 'application/json'})
                urllib.request.urlopen(req, timeout=10)
            return True
        except Exception as e:
            print(f"DingTalk alert failed: {e}")
            return False


class AlertManager:
    """Manage alert notifications across multiple channels."""
    
    def __init__(self):
        self.channels: List[AlertChannel] = []
        self._load_channels()
    
    def _load_channels(self):
        """Load configured alert channels."""
        if os.getenv("ALERT_EMAIL_USER"):
            self.channels.append(EmailChannel())
        if os.getenv("ALERT_SLACK_WEBHOOK"):
            self.channels.append(SlackChannel())
        if os.getenv("ALERT_WECHAT_WEBHOOK"):
            self.channels.append(WeChatChannel())
        if os.getenv("ALERT_DINGTALK_WEBHOOK"):
            self.channels.append(DingTalkChannel())
    
    def notify(self, alert: Dict[str, Any]) -> Dict[str, bool]:
        """Send alert to all configured channels."""
        results = {}
        
        for i, channel in enumerate(self.channels):
            channel_name = channel.__class__.__name__
            try:
                success = channel.send(alert)
                results[channel_name] = success
            except Exception as e:
                results[channel_name] = False
                print(f"Alert notification failed for {channel_name}: {e}")
        
        return results
    
    def notify_batch(self, alerts: List[Dict[str, Any]]) -> List[Dict[str, bool]]:
        """Send multiple alerts to all channels."""
        return [self.notify(alert) for alert in alerts]


if __name__ == "__main__":
    # Test alert
    test_alert = {
        "brand_name": "TestBrand",
        "severity": "warning",
        "metric": "geo_score",
        "current_value": 35.0,
        "threshold": 40.0,
        "message": "GEO Score dropped below 40",
        "triggered_at": "2026-07-18T10:00:00"
    }
    
    manager = AlertManager()
    print(f"Loaded {len(manager.channels)} alert channels")
    
    if manager.channels:
        results = manager.notify(test_alert)
        print(f"Notification results: {results}")
    else:
        print("No alert channels configured. Set environment variables to enable.")
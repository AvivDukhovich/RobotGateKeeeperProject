"""
NotificationManager - Remote Alerting System
This module facilitates real-time mobile push notifications using the ntfy.sh 
protocol. It enables the RobotGateKeeper to provide instant out-of-band 
security alerts to the operator's mobile device.
"""

import requests


class NotificationManager:
    def __init__(self, topic_name):
        """
        Initializes the notification manager with a specific ntfy topic.

        Args:
            topic_name (str): The unique ntfy.sh channel name for the alerts.
        """
        self.url = f"https://ntfy.sh/{topic_name}"
        self.topic = topic_name  # You can customize this as needed

    def send_alert(self, title, message):
        try:
            requests.post(f"https://ntfy.sh/{self.topic}",
                data=message.encode('utf-8'),
                headers={
                    "Title": title,
                    "Priority": "urgent",
                    "Tags": "warning,rotating_light"
                },
                timeout=5
            )
            print(f"[NOTIFY] Alert pushed to phone for {title}")
        except Exception as e:
            print(f"[ERROR] ntfy push failed: {e}")

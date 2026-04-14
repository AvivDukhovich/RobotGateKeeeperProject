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

    def send_alert(self, ip_address, source_name="Robot-01"):
        """
        Transmits a high-priority push notification.
        Added 'source_name' to identify which sensor reported the threat.
        """
        try:
            # Better messaging for a distributed system
            message = f"[{source_name}] ALERT: Unauthorized device {ip_address} detected!"

            response = requests.post(
                self.url,
                data=message.encode('utf-8'),
                headers={
                    "Title": "Robot Gatekeeper: Intrusion Detected",
                    "Priority": "high",
                    "Tags": "warning,shield,robot"
                }
            )

            if response.status_code == 200:
                print(f"[NOTIFY] Alert successfully pushed for {source_name}")
            else:
                print(
                    f"[NOTIFY] ntfy.sh returned error: {response.status_code}")

        except Exception as e:
            print(f"[NOTIFY] Remote Alerting Failed: {e}")

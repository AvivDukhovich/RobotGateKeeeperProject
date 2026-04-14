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

    def send_alert(self, ip_address):
        """
        Transmits a high-priority push notification via a POST request to ntfy.sh.
        Includes custom headers for priority, titling, and visual tagging.

        Args:
            ip_address (str): The unauthorized IP address that triggered the alert.
        """
        try:
            # Formulate the alert message with clear urgency
            message = f"SECURITY ALERT: Unauthorized device {ip_address} detected on the Robot Network!"

            # Execute the HTTP POST request to the ntfy webhook
            response = requests.post(
                self.url,
                data=message.encode('utf-8'),  # Ensure UTF-8 for emoji support
                headers={
                    "Title": "Robot Gatekeeper Alert",
                    "Priority": "high",           # Triggers override on some mobile Do Not Disturb settings
                    "Tags": "warning,robot"       # Adds visual icons to the notification
                }
            )

            # Verify successful transmission
            if response.status_code == 200:
                print(f"[NOTIFY] Alert sent to phone for {ip_address}")
            else:
                print(f"[NOTIFY] Failed to send: {response.status_code}")

        except Exception as e:
            # Catch network/connection issues to prevent the main monitor from crashing
            print(f"[NOTIFY] Connection Error: {e}")

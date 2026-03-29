import requests

class NotificationManager:
    def __init__(self, topic_name):
        self.url = f"https://ntfy.sh/{topic_name}"

    def send_alert(self, ip_address):
        """Sends a high-priority push notification to your phone"""
        try:
            message = f"🚨 SECURITY ALERT: Unauthorized device {ip_address} detected on the Robot Network!"
            
            # Using requests to hit the ntfy webhook
            response = requests.post(
                self.url,
                data=message.encode('utf-8'),
                headers={
                    "Title": "Robot Gatekeeper Alert",
                    "Priority": "high",
                    "Tags": "warning,robot"
                }
            )
            if response.status_code == 200:
                print(f"[NOTIFY] Alert sent to phone for {ip_address}")
            else:
                print(f"[NOTIFY] Failed to send: {response.status_code}")
        except Exception as e:
            print(f"[NOTIFY] Connection Error: {e}")
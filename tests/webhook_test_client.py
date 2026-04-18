"""Test script to simulate Resend webhook POST request."""

import json
import urllib.request
import sys
sys.stdout.reconfigure(encoding='utf-8')


def send_test_webhook():
    payload = {
        'type': 'email.received',
        'created_at': '2026-04-18T01:15:00Z',
        'data': {
            'email_id': 'test-reply-abc123',
            'from': {'address': 'test-user@example.com'},
            'to': [{'address': 'asyncdev@test-domain.example.com'}],
            'subject': 'Re: [async-dev] Decision needed [dr-20260418-001]',
            'text': 'DECISION A - approve the plan',
            'html': '<p>DECISION A - approve the plan</p>',
            'headers': [
                {'name': 'X-Decision-Request-Id', 'value': 'dr-20260418-001'}
            ]
        }
    }
    
    url = 'http://localhost:8080/webhooks/resend'
    data = json.dumps(payload).encode('utf-8')
    
    try:
        req = urllib.request.Request(
            url,
            data=data,
            headers={'Content-Type': 'application/json'},
            method='POST'
        )
        
        with urllib.request.urlopen(req, timeout=5) as response:
            result = response.read().decode('utf-8')
            print(f"Webhook sent successfully!")
            print(f"Server response: {result}")
            return True
    except Exception as e:
        print(f"Failed to send webhook: {e}")
        return False


if __name__ == '__main__':
    print("Sending test webhook to localhost:8080...")
    send_test_webhook()
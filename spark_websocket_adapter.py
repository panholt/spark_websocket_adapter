import websocket
import requests
import sparkpy
import json
import logging
import sys
import os

log = logging.getLogger()
spark = sparkpy.Spark()


def message_callback(ws, message):
    try:
        event = json.loads(message)
    except ValueError:
        log.error('Invalid json received from websocket: %s', event)
        return
    if event.get('url'):
        # First event received, should be our webhook url
        webhook_url = event.get('url').replace('12345', '8443')
        webhook_secret = event.get('secret')
        sparkpy.Spark().create_webhook('Python Websocket Proxy',
                                       webhook_url,
                                       'all', 'all',
                                       secret=webhook_secret)
    elif event.get('data'):
        data = event.get('data')
        log.debug('Received event: %s', data)
        requests.post(inside_url, json=data)
    else:
        log.debug('Unknown event received over websocket: %s', event)
    return


def disconnect_callback(ws):
    log.debug('Disconnecting... cleaning up Cisco Spark webhooks')
    for hook in spark.webhooks.filtered(lambda x: x.name == 'Python Websocket Proxy'):
        log.debug('Deleting webhook: %s', hook.id)
        hook.delete()


if __name__ == '__main__':
    if os.environ.get('WEBSOCKET_PROXY'):
        proxy_url = os.environ.get('WEBSOCKET_PROXY')
        inside_url = os.environ.get('WEBHOOK_URL')
        log.debug('Starting up with OS environment proxy variable: %s', proxy_url)
        log.debug('Starting up with OS environment url variable: %s', inside_url)
    elif len(sys.argv) > 2:
        proxy_url = sys.argv[1]
        inside_url = sys.argv[2]
        log.debug('Starting up with proxy arg: %s', proxy_url)
        log.debug('Starting up with inside url arg: %s', inside_url)
    ws = websocket.WebSocketApp(proxy_url,
                                on_message=message_callback,
                                on_close=disconnect_callback)
    ws.run_forever()

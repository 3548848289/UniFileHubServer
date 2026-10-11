import json
import queue
import threading


_subscriber_lock = threading.Lock()
_subscribers = {}


def subscribe(username):
    subscriber = queue.Queue(maxsize=10)
    with _subscriber_lock:
        _subscribers.setdefault(username, set()).add(subscriber)
    return subscriber


def unsubscribe(username, subscriber):
    with _subscriber_lock:
        subscribers = _subscribers.get(username)
        if not subscribers:
            return
        subscribers.discard(subscriber)
        if not subscribers:
            _subscribers.pop(username, None)


def broadcast_clipboard_changed(username, action):
    payload = {
        'action': action,
    }
    with _subscriber_lock:
        subscribers = list(_subscribers.get(username, set()))

    for subscriber in subscribers:
        try:
            subscriber.put_nowait(payload)
        except queue.Full:
            try:
                subscriber.get_nowait()
            except queue.Empty:
                pass
            try:
                subscriber.put_nowait(payload)
            except queue.Full:
                pass


def sse_event(event_name, payload):
    return f"event: {event_name}\ndata: {json.dumps(payload, ensure_ascii=False)}\n\n"

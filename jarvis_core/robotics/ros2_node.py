from __future__ import annotations

try:
    import roslibpy  # type: ignore
except Exception:  # pragma: no cover
    roslibpy = None  # type: ignore


def publish_example(host: str = "localhost", port: int = 9090) -> bool:
    if roslibpy is None:
        return False
    client = roslibpy.Ros(host=host, port=port)
    topic = roslibpy.Topic(client, '/chatter', 'std_msgs/String')
    client.run()
    topic.publish(roslibpy.Message({'data': 'hello'}))
    topic.unadvertise()
    client.terminate()
    return True

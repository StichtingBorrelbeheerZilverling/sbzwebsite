from flask import Flask
from flask_socketio import SocketIO
import settings

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")


@socketio.on('evnt')
def handle_json(json):
    print("Received: {}".format(json))


@socketio.on('update_flow', namespace=settings.SOCKETIO_NAMESPACE)
def update_flow(json):
    if json.get('secret', '') != settings.UPDATE_FLOW_SECRET:
        # Ignore request
        return

    socketio.emit('flow', json['data'], namespace=settings.SOCKETIO_NAMESPACE)


if __name__ == "__main__":
    socketio.run(app, host="0.0.0.0", port="21338")

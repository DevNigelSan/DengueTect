"""
Start DengueTect.

  python run.py            Your laptop only (http://127.0.0.1:5000), auto-reload on, for development
  python run.py --network  Other devices on the same Wi-Fi can open it (phones, panelists' laptops),
                           using the Waitress server with debug mode OFF
  Hosting platforms set PORT and get the same safe server automatically.
"""
import os
import socket
import sys

from app import create_app

app = create_app()


def lan_address():
    """This computer's address on the Wi-Fi, for typing into a phone's browser."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(('8.8.8.8', 80))          # picks the Wi-Fi network card; no data is sent
        ip = s.getsockname()[0]
        s.close()
        return ip
    except OSError:
        return socket.gethostbyname(socket.gethostname())


def serve(port):
    """Production-style server: debug off, many users at once."""
    try:
        from waitress import serve as waitress_serve
    except ImportError:
        print('Waitress is not installed. Run:  pip install waitress')
        print('Starting Flask without debug mode for now.\n')
        app.run(debug=False, host='0.0.0.0', port=port)
        return
    waitress_serve(app, host='0.0.0.0', port=port, threads=8)


if __name__ == '__main__':
    hosted  = 'PORT' in os.environ          # hosting platforms set PORT; your laptop doesn't
    network = '--network' in sys.argv
    port    = int(os.environ.get('PORT', 5000))

    if hosted:
        serve(port)
    elif network:
        print('\n  DengueTect is running for this Wi-Fi network (debug mode OFF)')
        print(f'  On this laptop:          http://127.0.0.1:{port}')
        print(f'  On phones / other PCs:   http://{lan_address()}:{port}')
        print('  Devices must be on the same Wi-Fi. Press Ctrl+C to stop.\n')
        serve(port)
    else:
        app.run(debug=True, host='127.0.0.1', port=port)   # auto-reload while you edit code
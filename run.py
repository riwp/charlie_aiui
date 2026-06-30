import os
from apps import create_app

app = create_app()

if __name__ == '__main__':
    host_ip = os.getenv("HOST", "0.0.0.0")
    port_num = int(os.getenv("PORT", 5072))
    debug_state = os.getenv("FLASK_DEBUG") == "1" or True
    app.run(host=host_ip, port=port_num, debug=debug_state)
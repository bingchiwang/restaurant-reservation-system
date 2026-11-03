import os
import sys

# Ensure root workspace directory is on sys.path
root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

from backend.app import create_app
from backend.seed import seed_data

# Ensure initial data exists
seed_data()

app = create_app()

if __name__ == "__main__":
    print("[*] Restaurant Backend API running at http://127.0.0.1:5000")
    app.run(host="127.0.0.1", port=5000, debug=False)

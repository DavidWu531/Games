from flask import Flask

app = Flask(__name__)

from app import routes  # noqa: F401, E402

app.run(debug=True)  # convert to False on finish

# app.py
from flask import Flask
from routes.event_routes import event_routes
from routes.api_routes import api_routes

app = Flask(__name__)
app.register_blueprint(event_routes)
app.register_blueprint(api_routes)

@app.route('/')
def index():
    return "BAC.Events running. Visit /events and /api"

if __name__ == '__main__':
    app.run(debug=True)
from flask import Flask
import os

def create_app():
    app = Flask(__name__)
    app.secret_key = 'secret123'
    app.config['UPLOAD_FOLDER'] = os.path.join(os.getcwd(), 'uploads')
    app.config['ALLOWED_EXTENSIONS'] = {'xlsx'}

    from .routes import main_routes, upload_routes, summary_routes, detail_routes, samanvayak_routes
    app.register_blueprint(main_routes.bp)
    app.register_blueprint(upload_routes.bp)
    app.register_blueprint(summary_routes.bp)
    app.register_blueprint(detail_routes.bp)
    app.register_blueprint(samanvayak_routes.bp)

    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

    return app

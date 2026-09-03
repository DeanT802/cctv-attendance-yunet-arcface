from flask import Flask
from dotenv import load_dotenv
import os
import datetime

# Load environment variables
load_dotenv()

def format_time(value):
    """Custom filter to format time objects, including timedelta"""
    if value is None:
        return '-'
    
    if isinstance(value, datetime.timedelta):
        # Convert timedelta to hours and minutes
        total_seconds = int(value.total_seconds())
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        return f"{hours:02d}:{minutes:02d}"
    
    if hasattr(value, 'strftime'):
        return value.strftime('%H:%M')
    
    return str(value)

def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key')
    
    # Register custom filters
    app.jinja_env.filters['format_time'] = format_time
    
    # Import and register blueprints
    from app.routes import main
    app.register_blueprint(main)
    
    # Register face recognition blueprint
    try:
        from app.face_recognition_routes import face_recognition_bp
        app.register_blueprint(face_recognition_bp)
    except ImportError as e:
        print(f"Warning: Face recognition module not available: {e}")
    
    return app

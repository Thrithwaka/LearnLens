from app import app, db, initialize_database
import os

with app.app_context():
    print("Creating database tables...")
    db.create_all()
    
    print("Initializing database with default data...")
    initialize_database()
    
    print("Database setup complete!")
from flask_migrate import upgrade, init, migrate, stamp
from app import app, db

def run_migrations():
    """Run the database migrations"""
    with app.app_context():
        try:
            # Initialize migrations directory if it doesn't exist
            init()
        except:
            # Directory might already exist
            pass

        try:
            # Create a migration script
            migrate()
            
            # Apply the migration
            upgrade()
            
            # Stamp the database with the current migration
            stamp()
            
            print("Database migrations completed successfully!")
        except Exception as e:
            print(f"Error during migration: {e}")

if __name__ == '__main__':
    run_migrations()
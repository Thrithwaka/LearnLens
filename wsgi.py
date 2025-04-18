from app import app, initialize_database

# Initialize the database on startup
initialize_database()

if __name__ == "__main__":
    app.run()
from server import app

# This is the main entry point for the application
if __name__ == "__main__":
    import uvicorn
    # Address for hosting UI
    host = "127.0.0.1"
    port = 8001

    # Run the app on the specified host and port
    uvicorn.run(app, host=host, port=port)

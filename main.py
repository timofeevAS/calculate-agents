from server import app

if __name__ == "__main__":
    import uvicorn
    # Address for hosting UI
    host = "127.0.0.1"
    port = 8001

    uvicorn.run(app, host=host, port=port)

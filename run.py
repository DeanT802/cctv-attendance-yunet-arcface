from app import create_app

app = create_app()

if __name__ == '__main__':
    # CRITICAL FIX: Enable threaded=True untuk handle multiple requests simultaneously
    # Ini memungkinkan video stream tetap berjalan saat face recognition process
    # Without this, Flask is single-threaded and blocks all other requests!
    app.run(
        debug=True, 
        host='0.0.0.0', 
        port=5000,
        threaded=True,  # ← CRITICAL: Allows multiple concurrent requests
        use_reloader=True
    )

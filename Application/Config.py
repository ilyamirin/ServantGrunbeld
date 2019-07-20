class Config:
    DEVICE_ID = "464a"
    MANAGER_HOST = "127.0.0.1"
    MANAGER_PORT = 10020
    MGR_WS_URI = f"ws://{MANAGER_HOST}:{MANAGER_PORT}"
    RECONNECT_TIMEOUT = 0.3  # секунд
    WINDOW_NAME = "Ты"
    FPS = 30

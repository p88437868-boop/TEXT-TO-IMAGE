from __future__ import annotations

import getpass
import hashlib

from PySide6.QtCore import QLockFile, QObject, Signal
from PySide6.QtNetwork import QLocalServer, QLocalSocket

from textpic.paths import app_data_dir


class SingleInstance(QObject):
    activate_requested = Signal()

    def __init__(self, parent: QObject | None = None):
        super().__init__(parent)
        user_token = hashlib.sha1(
            getpass.getuser().encode("utf-8", errors="replace")
        ).hexdigest()[:10]
        self.server_name = f"TextPicStudio-{user_token}"
        self._lock = QLockFile(str(app_data_dir() / "app.lock"))
        self._lock.setStaleLockTime(30000)
        self._server: QLocalServer | None = None
        self.is_primary = False

    def acquire(self) -> bool:
        if not self._lock.tryLock(150):
            self._notify_primary()
            return False
        QLocalServer.removeServer(self.server_name)
        self._server = QLocalServer(self)
        if self._server.listen(self.server_name):
            self._server.newConnection.connect(self._on_new_connection)
        self.is_primary = True
        return True

    def _notify_primary(self) -> None:
        socket = QLocalSocket()
        socket.connectToServer(self.server_name)
        if socket.waitForConnected(600):
            socket.write(b"show")
            socket.waitForBytesWritten(300)
            socket.disconnectFromServer()

    def _on_new_connection(self) -> None:
        if self._server is None:
            return
        while self._server.hasPendingConnections():
            connection = self._server.nextPendingConnection()
            connection.readyRead.connect(
                lambda conn=connection: self._handle_connection(conn)
            )
            connection.disconnected.connect(connection.deleteLater)

    def _handle_connection(self, connection: QLocalSocket) -> None:
        payload = bytes(connection.readAll())
        if payload == b"show":
            self.activate_requested.emit()
        connection.disconnectFromServer()

    def close(self) -> None:
        if self._server is not None:
            self._server.close()
            self._server = None
        if self._lock.isLocked():
            self._lock.unlock()

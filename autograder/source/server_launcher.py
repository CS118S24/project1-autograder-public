from enum import Enum
from subprocess import Popen, TimeoutExpired


class LauncherCmd(Enum):
    STATUS_CHECK = 1
    KILL = 2


class LauncherResp:
    def __init__(self, cmd, value):
        self.cmd = cmd
        self.value = value


class ServerLauncher:
    def __init__(self, pipe):
        self.pipe = pipe
        self.server_process = None
    
    def dummy_server(self):
        cmd = self.pipe.recv()
        while cmd != LauncherCmd.KILL:
            if cmd == LauncherCmd.STATUS_CHECK:
                resp = LauncherResp(LauncherCmd.STATUS_CHECK, None)
                self.pipe.send(resp)

    # Should run in a separate multiprocess
    def start_server(self):
        try:
            self.server_process = Popen(['./server'])
        except Exception:
            self.dummy_server()
            return

        cmd = self.pipe.recv()
        while cmd != LauncherCmd.KILL:
            if cmd == LauncherCmd.STATUS_CHECK:
                result = self.server_process.poll()
                if result != None:
                    self.server_process = Popen(['./server'])
                resp = LauncherResp(LauncherCmd.STATUS_CHECK, result)
                self.pipe.send(resp)

            cmd = self.pipe.recv()

        self.server_process.terminate()
        try:
            self.server_process.wait(3)
        except TimeoutExpired:
            self.server_process.kill()
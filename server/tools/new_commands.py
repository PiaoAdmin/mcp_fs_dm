from asyncio import subprocess
import os
import pty
import select
import time
from typing import List, Optional, Tuple


class VirtualTerminal:
    def __init__(self, shell: List[str] = None):
        self.shell = shell or ["/bin/bash"]
        self.master_fd = None
        self.slave_fd = None
        self.process = None
        self.history = []
        self._create_terminal()

    def _create_terminal(self):
        self.process = subprocess.Popen(
            self.shell_cmd,
            stdin=self.slave_fd,
            stdout=self.slave_fd,
            stderr=self.slave_fd,
            close_fds=True
        )
        print(self.master_fd,self.slave_fd,self.process.pid)
        os.close(self.slave_fd)
        self.slave_fd = None
    
    def _ensure_terminal(self):
        if self.process is None or self.process.poll() is not None:
              self._create_terminal()
    
    def execute(self, command: str, timeout: Optional[int]) -> Tuple[int,str]:
        self._ensure_terminal()

        marker = f"__CMD_END__{time.time()}"
        wrapped_command = f"{command}\necho {marker}\n"
        os.write(self.master_fd, wrapped_command.encode())

        output_bytes = b""
        end_time = time.time() + timeout if timeout else None
        while True:
            if end_time and time.time() > end_time:
                os.write(self.master_fd, b'\x03') # Send Ctrl+C to interrupt
                raise TimeoutError("Command execution timed out")
            
            rlist, _, _ = select.select([self.master_fd], [], [], 0.1)
            if self.master_fd in rlist:
                chunk = os.read(self.master_fd, 1024)
                if not chunk:
                    break
                output_bytes += chunk
                if marker.encode() in output_bytes:
                    break
        output = output_bytes.decode(errors='ignore')
        output = output.split(marker)[0].strip()

        self.history.append((command, output))
        return self.process.pid, output
    
    def get_history(self) -> List[Tuple[str, str]]:
        return list(self.history)

    def close(self):
        if self.process:
            self.process.terminate()
            try:
                self.process.wait(timeout=2)
            except subprocess.TimeoutExpired:
                self.process.kill()
            self.process = None
        if self.master_fd:
            os.close(self.master_fd)
            self.master_fd = None

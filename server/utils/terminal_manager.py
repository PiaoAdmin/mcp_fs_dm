import os
import pty
import select
import signal
import subprocess
import threading
import time
from typing import Any, Optional, Dict, List, TypedDict

from server.config import get_config_manager


class CompletedSession:
    def __init__(self, pid: int, output: str, exit_code: Optional[int], start_time: float, end_time: float):
        self.pid = pid
        self.output = output
        self.exit_code = exit_code
        self.start_time = start_time
        self.end_time = end_time


class ActiveSession:
    def __init__(self, pid: int, process: subprocess.Popen, start_time: float):
        self.pid = pid
        self.process = process
        self.start_time = start_time
        self.last_output = ''
        self.all_output = ''
        self.is_blocked = False


class CommandResult(TypedDict):
    pid: int
    output: str
    isBlocked: bool    

class PersistentSession:
    def __init__(self, session_id:str, shell:str):
        self.session_id = session_id
        self.shell = shell
        self.shell = shell
        self.master_fd = None
        self.slave_fd = None
        self.process = None
        self.start_time = time.time()
        self.last_output = ''
        self.all_output = ''
        self.is_active = False
        self.output_lock = threading.Lock()
        self.reader_thread = None

    def start(self):
        try:
            self.master_fd, self.slave_fd = pty.openpty()

            self.process = subprocess.Popen(
                [self.shell],
                stdin=self.slave_fd,
                stdout=self.slave_fd,
                stderr=self.slave_fd,
                start_new_session=True,
                preexec_fn=os.setsid
            )
            self.is_active = True
            self.reader_thread = threading.Thread(target=self._read_output_loop, daemon=True)
            self.reader_thread.start()

            return True
        except Exception as e:
            self.cleanup()
            return False

    def _read_output_loop(self):
        while self.is_active and self.master_fd:
            try:
                # 使用select检查是否有数据可读
                ready, _, _ = select.select([self.master_fd], [], [], 0.1)
                if ready:
                    try:
                        data = os.read(self.master_fd, 1024).decode('utf-8', errors='ignore')
                        if data:
                            with self.output_lock:
                                self.last_output += data
                                self.all_output += data
                    except OSError:
                        break
            except Exception:
                break

    def execute_command(self, command: str):
        if not self.is_active or not self.master_fd:
            return False
        try:
            os.write(self.master_fd, (command + '\n').encode('utf-8'))
            return True
        except OSError:
            return False

    def get_output(self, is_full: bool = False) -> str:
        with self.output_lock:
            output = self.all_output if is_full else self.last_output
            self.last_output = ''
        return output

    def cleanup(self):
        self.is_active = False
        if self.process:
            try:
                self.process.terminate()
                self.process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.process.kill()
        if self.master_fd:
            os.close(self.master_fd)
        if self.slave_fd:
            os.close(self.slave_fd)


class TerminalManager:
    def __init__(self):
        self.active_sessions: Dict[int, ActiveSession] = {}
        self.completed_sessions: Dict[int, CompletedSession] = {}
        self._lock = threading.Lock()

    def _read_output_loop(self, session: ActiveSession):
        proc = session.process
        if proc.stdout:
            with proc.stdout:
                for line in iter(proc.stdout.readline, ''):
                    session.last_output += line
                    session.all_output += line

    def execute_command(self, command: str, timeout: float = 5.0, shell: Optional[str] = None) -> CommandResult:
        config = get_config_manager()
        shell_to_use = shell or config.config.get("shell", "/bin/bash")
        proc = subprocess.Popen(
            command,
            shell=True,
            executable=shell_to_use,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            start_new_session=True,
            text=True,
            bufsize=1
        )
        pid = proc.pid
        session = ActiveSession(pid, proc, time.time())
        with self._lock:
            self.active_sessions[pid] = session

        reader = threading.Thread(target=self._read_output_loop, args=(session,),daemon=True)
        reader.start()

        is_blocked = False
        try:
            proc.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            is_blocked = True
            with self._lock:
                session.is_blocked = True
        
        end_time = time.time()
        out = session.all_output
        exit_code = proc.returncode if proc.poll() is not None else None
        if exit_code is not None:
            completed = CompletedSession(pid, out, exit_code, session.start_time, end_time)
            with self._lock:
                self.completed_sessions[pid] = completed
                self.active_sessions.pop(pid, None)
                while len(self.completed_sessions) > 100:
                    oldest_pid = min(self.completed_sessions.items(), key=lambda x: x[1].end_time)[0]
                    del self.completed_sessions[oldest_pid]
        return CommandResult(
            pid=pid,
            output=out,
            isBlocked=is_blocked
        )

    def get_new_output(self, pid: int, is_full: bool) -> Optional[Dict]:
        with self._lock:
            session = self.active_sessions.get(pid)

        if session:
            out = session.last_output
            session.last_output = ''
            if session.process.poll() is not None:
                exit_code = session.process.returncode
                end_time = time.time()
                completed = CompletedSession(pid, session.all_output, exit_code, session.start_time, end_time)
                with self._lock:
                    self.completed_sessions[pid] = completed
                    self.active_sessions.pop(pid, None)
                    while len(self.completed_sessions) > 100:
                        oldest_pid = min(self.completed_sessions.items(), key=lambda x: x[1].end_time)[0]
                        del self.completed_sessions[oldest_pid]
                runtime = end_time - completed.start_time
                return {
                    "pid": pid,
                    "is_full": is_full,
                    "output": session.all_output if is_full else out,
                    "type": "completed",
                    "exit_code": exit_code,
                    "runtime": runtime
                }
            return {
                "pid": pid,
                "is_full": is_full,
                "output": session.all_output if is_full else out,
                "type": "active"
            }

        with self._lock:
            completed = self.completed_sessions.get(pid)
        if completed:
            runtime = completed.end_time - completed.start_time
            return {
                "pid": pid,
                "is_full": True,
                "output": completed.output,
                "type": "completed",
                "exit_code": completed.exit_code,
                "runtime": runtime
            }
        return None

    def get_session(self, pid: int) -> Optional[ActiveSession]:
        with self._lock:
            return self.active_sessions.get(pid)

    def force_terminate(self, pid: int) -> bool:
        with self._lock:
            session = self.active_sessions.get(pid)
        if not session:
            return False
        try:
            session.process.send_signal(signal.SIGINT)
            time.sleep(1)
            if session.process.poll() is None:
                session.process.kill()
            return True
        except Exception:
            return False
        
    def list_active_sessions(self) -> List[Dict[str,Any]]:
        with self._lock:
            return [
                {
                    "pid": session.pid,
                    "start_time": session.start_time,
                    "last_output": session.last_output,
                    "is_blocked": session.is_blocked
                }
                for session in self.active_sessions.values()
            ]
        
    def list_completed_sessions(self) -> List[Dict[str,Any]]:
        with self._lock:
            return [
                {
                    "pid": session.pid,
                    "output": session.output,
                    "exit_code": session.exit_code,
                    "start_time": session.start_time,
                    "end_time": session.end_time
                }
                for session in self.completed_sessions.values()
            ]
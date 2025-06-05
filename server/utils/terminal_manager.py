import subprocess
import threading
import time
from typing import Optional, Dict, List

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
        self.is_blocked = False


class TerminalManager:
    def __init__(self):
        self.active_sessions: Dict[int, ActiveSession] = {}
        self.completed_sessions: Dict[int, CompletedSession] = {}
        self._lock = threading.Lock()

    def _watch_timeout(self, pid: int, timeout: float):
        start = self.active_sessions[pid].start_time
        proc = self.active_sessions[pid].process
        while True:
            if proc.poll() is not None:
                return
            if time.time() - start > timeout:
                with self._lock:
                    if pid in self.active_sessions:
                        self.active_sessions[pid].is_blocked = True
                return
            time.sleep(0.1)

    def execute_command(self, command: str, timeout: float = 5.0, shell: Optional[str] = None) -> Dict:
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

        if timeout and timeout > 0:
            watcher = threading.Thread(target=self._watch_timeout, args=(pid, timeout), daemon=True)
            watcher.start()

        return {"pid": pid, "output": "", "isBlocked": False}


    def get_new_output(self, pid: int) -> Optional[str]:
        """
        获取指定 pid 的最新输出。若进程已结束，返回带有退出码、运行时长和最终输出的摘要。
        返回 None 表示该 pid 不存在。
        """
        with self._lock:
            session = self.active_sessions.get(pid)

        if session:
            out = session.last_output
            session.last_output = ''
            # 如果进程刚结束，将其移至 completed_sessions
            if session.process.poll() is not None:
                exit_code = session.process.returncode
                end_time = time.time()
                completed = CompletedSession(pid, out, exit_code, session.start_time, end_time)
                with self._lock:
                    self.completed_sessions[pid] = completed
                    self.active_sessions.pop(pid, None)
                runtime = end_time - completed.start_time
                return f"Process {pid} completed with exit code {exit_code}\nRuntime: {runtime:.2f}s\nFinal output:\n{completed.output}"
            return out

        # 不在 active_sessions，则检查 completed_sessions
        with self._lock:
            completed = self.completed_sessions.get(pid)
        if completed:
            runtime = completed.end_time - completed.start_time
            return f"Process {pid} completed with exit code {completed.exit_code}\nRuntime: {runtime:.2f}s\nFinal output:\n{completed.output}"

        return None

    def get_session(self, pid: int) -> Optional[ActiveSession]:
        """根据 pid 返回活动会话或 None。"""
        with self._lock:
            return self.active_sessions.get(pid)

    def force_terminate(self, pid: int) -> bool:
        """
        强制结束指定 pid 的进程。先发送 SIGINT，1 秒后若仍然存在则 SIGKILL。
        返回 True 表示找到了会话并发送了信号，False 表示无此 pid。
        """
        with self._lock:
            session = self.active_sessions.get(pid)
        if not session:
            return False
        try:
            session.process.kill()
            time.sleep(1)
            if session.process.poll() is None:
                session.process.kill()
            return True
        except Exception:
            return False

    def list_active_sessions(self) -> List[Dict]:
        now = time.time()
        with self._lock:
            return [
                {"pid": s.pid, "isBlocked": s.is_blocked, "runtime": now - s.start_time}
                for s in self.active_sessions.values()
            ]

    def list_completed_sessions(self) -> List[CompletedSession]:
        with self._lock:
            return list(self.completed_sessions.values())
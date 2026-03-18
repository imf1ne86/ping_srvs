import shutil
import subprocess
import sys
from typing import Tuple


class Networking:
    @staticmethod
    def _ping_command(host: str, count: int = 1, timeout_sec: int = 2) -> Tuple[list, dict]:
        """
        Возвращает (cmd, kwargs) для subprocess.run в зависимости от платформы.
        """
        if sys.platform.startswith("win"):
            # Windows: -n count, -w timeout(ms)
            cmd = ["ping", "-n", str(count), "-w", str(timeout_sec * 1000), host]
            kwargs = {"stdout": subprocess.DEVNULL, "stderr": subprocess.DEVNULL}
        else:
            # Unix (Linux, macOS): -c count, -W timeout(seconds) для Linux;
            # на macOS -W принимает миллисекунды, поэтому используем timeout вокруг ping if available.
            if shutil.which("ping"):
                # Попробуем классический вариант для Linux (most common)
                cmd = ["ping", "-c", str(count), "-W", str(timeout_sec), host]
                kwargs = {"stdout": subprocess.DEVNULL, "stderr": subprocess.DEVNULL}
            else:
                # fallback: use system timeout if ping exists but weird; still call ping without -W
                cmd = ["ping", "-c", str(count), host]
                kwargs = {"stdout": subprocess.DEVNULL, "stderr": subprocess.DEVNULL}
        return cmd, kwargs

    @staticmethod
    def is_server_available(host: str) -> bool:
        """
        Возвращает True, если хост отвечает на ping (ICMP), иначе False.

        Замечания:
        - Требуется доступ к утилите `ping` в системе.
        - На некоторых системах для отправки ICMP-пакетов требуются привилегии; в таком случае
          `ping` обычно имеет setuid или иные механизмы, и этот вызов всё равно работает.
        - Функция молчит (не выводит ничего), возвращает только булево значение.
        """
        try:
            cmd, kwargs = Networking._ping_command(host)
            # На случай отсутствия ping - считаем недоступным
            if shutil.which(cmd[0]) is None:
                return False
            # Безопасно выполнить с общим таймаутом (в секундах)
            completed = subprocess.run(cmd, timeout=5, **kwargs)
            return completed.returncode == 0
        except (subprocess.TimeoutExpired, OSError, ValueError):
            return False

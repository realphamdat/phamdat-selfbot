import os
import sys
import threading
import importlib

from modules.utils.logger import get_logger

logger = get_logger('extension_manager')

class ExtensionManager:
    def __init__(self, extensions_dir: str = "modules/extensions"):
        self.extensions_dir = extensions_dir
        self.modules = []
        self.running = False
        self._lock = threading.RLock()

    def discover_and_load(self):
        with self._lock:
            if self.running:
                logger.warning("Cannot load while running")
                return
            self.modules.clear()

        if not os.path.isdir(self.extensions_dir):
            logger.warning(f"Extensions directory '{self.extensions_dir}' not found")
            return

        abs_path = os.path.abspath(self.extensions_dir)
        if abs_path not in sys.path:
            sys.path.insert(0, abs_path)

        for filename in os.listdir(self.extensions_dir):
            if not filename.endswith(".py") or filename == "__init__.py":
                continue
            module_name = filename[:-3]
            try:
                mod = importlib.import_module(module_name)
                if hasattr(mod, 'running') and hasattr(mod, 'main'):
                    with self._lock:
                        self.modules.append((mod, None))
                    logger.info(f"Loaded: {module_name}")
                else:
                    logger.warning(f"Missing 'running' or 'main' in {module_name}")
            except Exception as e:
                logger.exception(f"Load failed {module_name}: {e}")

    def start_all(self):
        with self._lock:
            if self.running:
                return
            self.running = True
            modules_snapshot = list(self.modules)

        for mod, _ in modules_snapshot:
            try:
                mod.running = True
                t = threading.Thread(target=mod.main, name=f"ext_{mod.__name__}", daemon=True)
                t.start()
                with self._lock:
                    for i, (m, _) in enumerate(self.modules):
                        if m is mod:
                            self.modules[i] = (mod, t)
                            break
                logger.info(f"Started: {mod.__name__}")
            except Exception as e:
                logger.exception(f"Start failed {mod.__name__}: {e}")

    def stop_all(self, timeout: int = 5):
        with self._lock:
            if not self.running:
                return
            self.running = False
            modules_snapshot = list(self.modules)

        for mod, _ in modules_snapshot:
            try:
                if hasattr(mod, 'stop'):
                    mod.stop()
                else:
                    mod.running = False
                logger.info(f"Stopping: {mod.__name__}")
            except Exception as e:
                logger.exception(f"Stop signal failed {mod.__name__}: {e}")

        for mod, thread in modules_snapshot:
            if thread and thread.is_alive():
                thread.join(timeout)
                if thread.is_alive():
                    logger.warning(f"{mod.__name__} did not stop within {timeout}s")
                else:
                    logger.info(f"Stopped: {mod.__name__}")

        with self._lock:
            self.modules = [(mod, None) for mod, _ in self.modules]
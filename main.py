from __future__ import annotations

import sys
import traceback
from datetime import datetime

from gui import App, APP_DIR


def _write_crash_log(exc_type, exc_value, exc_tb) -> None:
    try:
        APP_DIR.mkdir(parents=True, exist_ok=True)
        with open(APP_DIR / "crash.log", "a", encoding="utf-8") as f:
            f.write(f"\n=== {datetime.now().isoformat(timespec='seconds')} ===\n")
            traceback.print_exception(exc_type, exc_value, exc_tb, file=f)
    except Exception:
        pass


def _handle_callback_exception(exc_type, exc_value, exc_tb) -> None:
    """Substitui o tratamento padrao do Tkinter pra erros que acontecem
    depois que a janela ja abriu (sem console, o padrao so sumiria em
    silencio)."""
    _write_crash_log(exc_type, exc_value, exc_tb)
    try:
        from tkinter import messagebox
        messagebox.showerror(
            "Erro inesperado",
            "Ocorreu um erro inesperado. Detalhes salvos em:\n"
            f"{APP_DIR / 'crash.log'}"
        )
    except Exception:
        pass


if __name__ == "__main__":
    try:
        app = App()
        app.report_callback_exception = _handle_callback_exception
        app.mainloop()
    except Exception:
        _write_crash_log(*sys.exc_info())
        try:
            import tkinter as tk
            from tkinter import messagebox
            root = tk.Tk()
            root.withdraw()
            messagebox.showerror(
                "Erro ao iniciar",
                "O programa encontrou um erro ao iniciar. Detalhes salvos em:\n"
                f"{APP_DIR / 'crash.log'}"
            )
            root.destroy()
        except Exception:
            pass
        sys.exit(1)

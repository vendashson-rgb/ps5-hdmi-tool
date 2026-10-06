"""Animacao de GIF para Tkinter.

Se Pillow estiver disponivel e um `size` for passado, usa Pillow para
redimensionar cada frame e respeita a duracao original de cada frame do GIF.
Caso contrario, usa o suporte nativo do Tcl/Tk a GIF (sem redimensionar,
duracao fixa) -- suficiente para GIFs pequenos como o loading.gif.
"""

from __future__ import annotations

import tkinter as tk

try:
    from PIL import Image, ImageTk
    _HAS_PIL = True
except ImportError:
    _HAS_PIL = False


class GifAnimation(tk.Label):
    def __init__(self, master, path: str, delay_ms: int | None = None,
                 size: tuple[int, int] | None = None, **kwargs):
        # tk.Label nao herda o tema ttk -- sem isso sobra uma borda clara
        # (cor padrao do Tk) ao redor do gif quando o resto do app esta escuro.
        kwargs.setdefault("bg", "#000000")
        kwargs.setdefault("bd", 0)
        kwargs.setdefault("highlightthickness", 0)
        super().__init__(master, **kwargs)
        self._path = path
        self._size = size
        self._frames: list = []
        self._delays: list[int] = []
        self._default_delay = delay_ms or 100
        self._loaded = False

        self._idx = 0
        self._running = False
        self._after_id = None

    def _ensure_loaded(self):
        """Decodifica (e redimensiona via Pillow) os frames do GIF so na
        primeira vez que essa animacao realmente vai aparecer na tela, em
        vez de todas as ~11 animacoes de estagio serem decodificadas de
        uma vez no arranque do programa -- so a "idle" (a primeira
        mostrada) carrega de cara; o resto carrega sob demanda, uma vez
        cada, e fica em cache depois (`self._loaded`). Medido: decodificar
        as ~922 frames de todos os GIFs de estagio de uma vez levava ~6.3s
        sozinho -- a maior parte do tempo de abertura do programa (ver
        NOTES.md)."""
        if self._loaded:
            return
        self._loaded = True
        if self._size and _HAS_PIL:
            self._load_with_pil(self._path, self._size)
        else:
            self._load_native(self._path)
        if self._frames:
            self.configure(image=self._frames[0])

    def _load_with_pil(self, path: str, size: tuple[int, int]):
        im = Image.open(path)
        try:
            while True:
                frame = im.convert("RGBA").resize(size, Image.LANCZOS)
                self._frames.append(ImageTk.PhotoImage(frame))
                self._delays.append(im.info.get("duration", self._default_delay))
                im.seek(im.tell() + 1)
        except EOFError:
            pass

    def _load_native(self, path: str):
        i = 0
        while True:
            try:
                frame = tk.PhotoImage(file=path, format=f"gif -index {i}")
            except tk.TclError:
                break
            self._frames.append(frame)
            self._delays.append(self._default_delay)
            i += 1

    def start(self):
        if self._running:
            return
        self._ensure_loaded()
        if not self._frames:
            return
        self._running = True
        self._animate()

    def stop(self):
        self._running = False
        if self._after_id is not None:
            self.after_cancel(self._after_id)
            self._after_id = None
        if self._frames:
            self._idx = 0
            self.configure(image=self._frames[0])

    def _animate(self):
        if not self._running:
            return
        self._idx = (self._idx + 1) % len(self._frames)
        self.configure(image=self._frames[self._idx])
        delay = self._delays[self._idx] or self._default_delay
        self._after_id = self.after(delay, self._animate)

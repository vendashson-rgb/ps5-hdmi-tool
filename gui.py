"""
Interface grafica.

Fluxo:
  1. Detectar leitor CH341A
  2. Ler a NOR DUAS VEZES e comparar (garante que a leitura foi confiavel)
     -> salva backup automatico em database/backups/<identificador>/<data-hora>.bin
     -> mostra: chip HDMI detectado, MAC, tamanho, dados brutos (id/CFI)
  3. Pre-visualizar patch (escolhe o chip alvo, mostra exatamente o que vai mudar,
     SEM gravar nada ainda)
  4. Gravar na NOR (so habilita depois de ter backup + preview feitos)

  + Restaurar backup de arquivo (independente do fluxo acima, so precisa do
    leitor detectado)

*** AVISO IMPORTANTE ***
O campo 0x1C41FE-0x1C41FF e resolvido via tabela fixa (chip + REV Wi-Fi) --
ver NOTES.md e nor_patcher.py.KNOWN_CHECKSUMS. Resolvido apenas para 3
combinacoes ja vistas em amostras reais; pra qualquer outra combinacao o
patch mantem o valor antigo e avisa (result.checksum_left_stale). Use a
gravacao em placa de cliente SOMENTE quando o checksum foi resolvido.
"""

from __future__ import annotations

import os
import pathlib
import re
import sys
import threading
import time
import tkinter as tk
import webbrowser
from datetime import datetime
from tkinter import filedialog, messagebox, scrolledtext, simpledialog, ttk

from PIL import Image, ImageTk

from ch341_spi import CH341Error, CH341SPI
from gif_anim import GifAnimation
from nor_parser import CHIP_SLUG, EXPECTED_SIZE, NorInfo, compare_dumps, parse_nor
from nor_patcher import PatchResult, TARGET_BYTE, TARGET_LABEL, TARGET_NUVOTON, TARGET_REALTEK, apply_patch
from uart_reader import COMMON_BAUDRATES, DEFAULT_BAUDRATE, UartError, UartReader, list_ports
import dualsense
from dualsense import DualSenseController, DualSenseError

def _bundle_dir() -> pathlib.Path:
    """Pasta de onde ler recursos empacotados (imagens, driver). Quando
    rodando como .exe gerado pelo PyInstaller (--onefile), isso e uma pasta
    temporaria criada na hora (sys._MEIPASS) -- so leitura, nunca grava nada
    aqui."""
    if getattr(sys, "frozen", False):
        return pathlib.Path(sys._MEIPASS)  # type: ignore[attr-defined]
    return pathlib.Path(__file__).parent


def _app_dir() -> pathlib.Path:
    """Pasta onde gravar dados do usuario (backups). Quando rodando como
    .exe, usa %LOCALAPPDATA%\\PS5 HDMI Tool -- sempre gravavel pelo usuario
    atual, sem precisar de admin, mesmo se o .exe estiver instalado em
    Program Files (onde escrever direto do lado do .exe falharia em
    silencio pra usuario comum)."""
    if getattr(sys, "frozen", False):
        local_appdata = os.environ.get("LOCALAPPDATA")
        if local_appdata:
            return pathlib.Path(local_appdata) / "PS5 HDMI Tool"
        return pathlib.Path(sys.executable).parent
    return pathlib.Path(__file__).parent


BUNDLE_DIR = _bundle_dir()
APP_DIR = _app_dir()

CONTROLLER_DIAGRAM_DIR = BUNDLE_DIR / "images" / "controller"
sys.path.insert(0, str(CONTROLLER_DIAGRAM_DIR))
import bboxes as CONTROLLER_BBOXES  # noqa: E402

BG = "#000000"
BG_ALT = "#0a0a0a"
BG_ACTIVE = "#1c1c1c"
FG = "#e6e6e6"
FG_MUTED = "#8a8a8a"
BORDER = "#2a2a2a"
SELECT_BG = "#333333"

# Cores de destaque usadas na caixa de log (texto colorido por tipo de linha)
# e na barra de progresso -- mantidas do teste de redesign anterior, que o
# usuario gostou e pediu pra manter mesmo revertendo o layout dos botoes.
LOG_OK = "#4edea3"       # verde-menta -- sucesso
LOG_ERROR = "#ff6b6b"    # vermelho -- erro
LOG_WARN = "#ffd166"     # amarelo -- aviso
LOG_PATCH = "#b7b8ff"    # lilas -- linhas de patch
LOG_INFO = "#47d6ff"     # ciano -- informativo
LOG_MUTED = FG_MUTED

PROGRESS_COLOR = "#4edea3"  # mesma cor verde-menta da barra de progresso

IMAGES_DIR = BUNDLE_DIR / "images"
ICON_ICO = IMAGES_DIR / "icon.ico"
LOGO_PNG = IMAGES_DIR / "logo.png"
IDLE_GIF = IMAGES_DIR / "idle.gif"
IDLE_SIZE = (260, 260)
DETECTING_GIF = IMAGES_DIR / "detecting.gif"
DETECTING_SIZE = (260, 260)
READING_GIF = IMAGES_DIR / "reading.gif"
READING_SIZE = (260, 260)
READ_SUCCESS_GIF = IMAGES_DIR / "read_success.gif"
READ_SUCCESS_SIZE = (260, 260)
PREVIEW_GIF = IMAGES_DIR / "preview.gif"
PREVIEW_SIZE = (260, 260)
WRITE_CANCELLED_GIF = IMAGES_DIR / "write_cancelled.gif"
WRITE_CANCELLED_SIZE = (260, 260)
WRITING_GIF = IMAGES_DIR / "writing.gif"
WRITING_SIZE = (260, 260)
WRITING_ACTIVE_GIF = IMAGES_DIR / "writing_active.gif"
WRITING_ACTIVE_SIZE = (260, 260)
WRITE_SUCCESS_GIF = IMAGES_DIR / "write_success.gif"
WRITE_SUCCESS_SIZE = (260, 260)
DETECT_FAILED_GIF = IMAGES_DIR / "detect_failed.gif"
DETECT_FAILED_SIZE = (260, 260)

BACKUP_DIR = APP_DIR / "database" / "backups"

CONFIRM_PHRASE = "GRAVAR"
MIN_DETECT_DISPLAY_S = 1.2  # tempo minimo pra animacao de "detectando" aparecer na tela

# Catalogos de codigo de erro UART mantidos por terceiros -- nao temos (nem
# copiamos) o banco de dados deles aqui, so linkamos pra consulta rapida.
UART_REFERENCE_LINKS = [
    ("psdevwiki.com (Southbridge Error Codes)", "https://www.psdevwiki.com/ps5/Southbridge_Error_Codes"),
    ("uartcodes.com", "https://uartcodes.com/"),
    ("GBAtemp (PS5 UART commands)", "https://gbatemp.net/threads/ps5-uart-commands.642741/"),
    ("forterfix.com (PS5 UART)", "https://forterfix.com/ps5_uart"),
]


def safe_filename_part(text: str | None, fallback: str) -> str:
    if not text:
        return fallback
    cleaned = re.sub(r"[^A-Za-z0-9_-]", "", text)
    return cleaned[:40] if cleaned else fallback


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("PS5 HDMI Tool")
        self.geometry("1020x760")

        self.spi: CH341SPI | None = None
        self.last_info: NorInfo | None = None
        self.last_dump: bytes | None = None
        self.last_backup_path: pathlib.Path | None = None
        self.last_patch: PatchResult | None = None

        self.file_dump: bytes | None = None
        self.file_info: NorInfo | None = None
        self.file_patch: PatchResult | None = None

        self.uart: UartReader | None = None
        self.uart_connected = False

        self.controller: DualSenseController | None = None
        self._controller_devices: list[dict] = []
        self._controller_poll_job: str | None = None
        self._controller_has_pending_changes = False

        self._set_icon()
        self._apply_dark_theme()
        self._build_widgets()
        self.protocol("WM_DELETE_WINDOW", self.on_close)

    def on_close(self):
        if self.uart_connected:
            self._uart_disconnect()
        if self.controller is not None:
            self.on_controller_disconnect()
        self.destroy()

    def _set_icon(self):
        try:
            if ICON_ICO.exists():
                self.iconbitmap(default=str(ICON_ICO))
        except tk.TclError:
            pass

    def _apply_dark_theme(self):
        self.configure(bg=BG)

        style = ttk.Style(self)
        style.theme_use("clam")

        style.configure(".", background=BG, foreground=FG, bordercolor=BORDER,
                         darkcolor=BG, lightcolor=BG, troughcolor=BG_ALT)
        style.configure("TFrame", background=BG)
        style.configure("TLabel", background=BG, foreground=FG)
        style.configure("TLabelframe", background=BG, foreground=FG, bordercolor=BORDER)
        style.configure("TLabelframe.Label", background=BG, foreground=FG)

        style.configure("TButton", background=BG_ALT, foreground=FG, bordercolor=BORDER,
                         focuscolor=BORDER, padding=6)
        style.map("TButton",
                  background=[("active", BG_ACTIVE), ("disabled", BG)],
                  foreground=[("disabled", FG_MUTED)])

        style.configure("TCombobox", fieldbackground=BG_ALT, background=BG_ALT,
                         foreground=FG, arrowcolor=FG, bordercolor=BORDER)
        style.map("TCombobox",
                  fieldbackground=[("readonly", BG_ALT)],
                  foreground=[("readonly", FG)],
                  selectbackground=[("readonly", BG_ALT)],
                  selectforeground=[("readonly", FG)])
        self.option_add("*TCombobox*Listbox.background", BG_ALT)
        self.option_add("*TCombobox*Listbox.foreground", FG)
        self.option_add("*TCombobox*Listbox.selectBackground", SELECT_BG)
        self.option_add("*TCombobox*Listbox.selectForeground", FG)

        style.configure("TProgressbar", troughcolor=BG_ALT, background=PROGRESS_COLOR,
                         bordercolor=BORDER)

    def _build_widgets(self):
        header = ttk.Frame(self, padding=(10, 10, 10, 0))
        header.pack(fill="x")
        try:
            if LOGO_PNG.exists():
                self._logo_img = tk.PhotoImage(file=str(LOGO_PNG))
                # reduz o logo se vier grande demais (subsample so aceita inteiros)
                w = self._logo_img.width()
                factor = max(1, w // 48)
                if factor > 1:
                    self._logo_img = self._logo_img.subsample(factor, factor)
                ttk.Label(header, image=self._logo_img).pack(side="left", padx=(0, 10))
        except tk.TclError:
            pass
        ttk.Label(header, text="PS5 HDMI Tool", font=("Segoe UI", 14, "bold")).pack(side="left")

        style = ttk.Style(self)
        style.configure("TNotebook", background=BG, bordercolor=BORDER)
        style.configure("TNotebook.Tab", background=BG_ALT, foreground=FG, padding=(14, 8))
        style.map("TNotebook.Tab",
                  background=[("selected", BG_ACTIVE)],
                  foreground=[("selected", FG)])

        notebook = ttk.Notebook(self)
        notebook.pack(fill="both", expand=True, padx=10, pady=10)

        hw_tab = ttk.Frame(notebook)
        file_tab = ttk.Frame(notebook)
        uart_tab = ttk.Frame(notebook)
        controller_tab = ttk.Frame(notebook)
        notebook.add(hw_tab, text="Leitor CH341A (hardware)")
        notebook.add(file_tab, text="Analisar arquivo (.bin)")
        notebook.add(uart_tab, text="Leitor UART")
        notebook.add(controller_tab, text="Teste de Controle")

        self._build_hardware_tab(hw_tab)
        self._build_file_tab(file_tab)
        self._build_uart_tab(uart_tab)
        self._build_controller_tab(controller_tab)

    def _build_hardware_tab(self, parent):
        top = ttk.Frame(parent, padding=10)
        top.pack(fill="x")

        self.btn_detect = ttk.Button(top, text="1. Detectar leitor CH341A", command=self.on_detect)
        self.btn_detect.pack(side="left", padx=5)

        self.btn_read = ttk.Button(top, text="2. Ler NOR (2x + comparar + backup)",
                                    command=self.on_read, state="disabled")
        self.btn_read.pack(side="left", padx=5)

        status_row = ttk.Frame(parent, padding=(10, 0))
        status_row.pack(fill="x")
        self.lbl_status = ttk.Label(status_row, text="Status: aguardando")
        self.lbl_status.pack(side="left")

        self.lbl_backup_badge = tk.Label(
            status_row, text="  Backup: nenhum ainda  ",
            bg="#999999", fg="white", font=("Segoe UI", 9, "bold")
        )
        self.lbl_backup_badge.pack(side="right")

        self.progress = ttk.Progressbar(parent, mode="determinate")
        self.progress.pack(fill="x", padx=10, pady=5)

        patch_frame = ttk.LabelFrame(parent, text="3. Aplicar patch (chip HDMI)", padding=10)
        patch_frame.pack(fill="x", padx=10, pady=(5, 0))

        ttk.Label(patch_frame, text="Gravar NOR configurada para:").pack(side="left")
        self.target_var = tk.StringVar(value=TARGET_NUVOTON)
        self.combo_target = ttk.Combobox(
            patch_frame, textvariable=self.target_var, state="readonly", width=28,
            values=[TARGET_REALTEK, TARGET_NUVOTON]
        )
        self.combo_target.set(TARGET_NUVOTON)
        self.combo_target.pack(side="left", padx=8)

        self.btn_preview = ttk.Button(patch_frame, text="Pre-visualizar alteracoes",
                                       command=self.on_preview, state="disabled")
        self.btn_preview.pack(side="left", padx=5)

        write_frame = ttk.Frame(parent, padding=(10, 5))
        write_frame.pack(fill="x")
        self.btn_write = tk.Button(
            write_frame, text="4. GRAVAR NA NOR (irreversivel)",
            command=self.on_write, state="disabled",
            bg="#b30000", fg="white", font=("Segoe UI", 10, "bold")
        )
        self.btn_write.pack(side="left", padx=5, fill="x", expand=True)

        self.btn_restore = tk.Button(
            write_frame, text="Restaurar backup de arquivo...",
            command=self.on_restore_backup, state="disabled",
            bg=BG_ALT, fg=FG, font=("Segoe UI", 10, "bold"),
            activebackground=BG_ACTIVE, activeforeground=FG,
            relief="flat", highlightthickness=1, highlightbackground=BORDER,
        )
        self.btn_restore.pack(side="left", padx=5, fill="x", expand=True)

        write_progress_frame = ttk.LabelFrame(parent, text="Progresso da gravacao", padding=(10, 5))
        write_progress_frame.pack(fill="x", padx=10, pady=(0, 5))

        write_step_defs = [
            ("verify_before", "1. Conferindo se a NOR ainda e a mesma do backup..."),
            ("erase", "2. Apagando NOR..."),
            ("write", "3. Gravando NOR com o patch..."),
            ("verify_after", "4. Lendo e verificando a gravacao..."),
        ]
        self.write_steps = {}
        for key, base_text in write_step_defs:
            row = ttk.Frame(write_progress_frame)
            row.pack(fill="x", pady=1)
            lbl = ttk.Label(row, text=base_text, width=46, anchor="w")
            lbl.pack(side="left")
            bar = ttk.Progressbar(row, mode="determinate")
            bar.pack(side="left", padx=8, fill="x", expand=True)
            check = tk.Label(row, text="  ", bg=BG, fg=LOG_OK, font=("Segoe UI", 11, "bold"), width=2)
            check.pack(side="left")
            self.write_steps[key] = {"label": lbl, "bar": bar, "check": check, "base_text": base_text}

        body = ttk.Frame(parent)
        body.pack(fill="both", expand=True, padx=10, pady=10)

        body_left = ttk.Frame(body)
        body_left.pack(side="left", fill="both", expand=True)

        body_right = ttk.Frame(body, width=280)
        body_right.pack(side="right", fill="y", padx=(10, 0))
        body_right.pack_propagate(False)

        self.txt = scrolledtext.ScrolledText(body_left, wrap="word", font=("Consolas", 10))
        self.txt.configure(
            state="disabled", bg="#000000", fg=FG, insertbackground=FG,
            selectbackground=SELECT_BG, selectforeground=FG,
            relief="flat", borderwidth=0, highlightthickness=0,
        )
        self.txt.pack(fill="both", expand=True)
        self.txt.tag_configure("ok", foreground=LOG_OK)
        self.txt.tag_configure("error", foreground=LOG_ERROR)
        self.txt.tag_configure("warn", foreground=LOG_WARN)
        self.txt.tag_configure("patch", foreground=LOG_PATCH)
        self.txt.tag_configure("info", foreground=LOG_INFO)
        self.txt.tag_configure("muted", foreground=LOG_MUTED)

        self.idle_frame = ttk.Frame(body_right)
        self.idle_anim = GifAnimation(self.idle_frame, str(IDLE_GIF), size=IDLE_SIZE) if IDLE_GIF.exists() else None
        if self.idle_anim is not None:
            ttk.Label(self.idle_frame, text="Aguardando... conecte o leitor e clique em \"1. Detectar leitor\"",
                      font=("Segoe UI", 9), wraplength=260, justify="center").pack(pady=(0, 10))
            self.idle_anim.pack()

        self.detecting_frame = ttk.Frame(body_right)
        self.detecting_anim = (
            GifAnimation(self.detecting_frame, str(DETECTING_GIF), size=DETECTING_SIZE)
            if DETECTING_GIF.exists() else None
        )
        if self.detecting_anim is not None:
            ttk.Label(self.detecting_frame, text="Detectando leitor CH341A...",
                      font=("Segoe UI", 9), wraplength=260, justify="center").pack(pady=(0, 10))
            self.detecting_anim.pack()

        self.reading_frame = ttk.Frame(body_right)
        self.reading_anim = (
            GifAnimation(self.reading_frame, str(READING_GIF), size=READING_SIZE)
            if READING_GIF.exists() else None
        )
        if self.reading_anim is not None:
            ttk.Label(self.reading_frame, text="Lendo NOR...",
                      font=("Segoe UI", 9), wraplength=260, justify="center").pack(pady=(0, 10))
            self.reading_anim.pack()

        self.read_success_frame = ttk.Frame(body_right)
        self.read_success_anim = (
            GifAnimation(self.read_success_frame, str(READ_SUCCESS_GIF), size=READ_SUCCESS_SIZE)
            if READ_SUCCESS_GIF.exists() else None
        )
        if self.read_success_anim is not None:
            ttk.Label(self.read_success_frame, text="Leitura concluida com sucesso!",
                      font=("Segoe UI", 9), wraplength=260, justify="center").pack(pady=(0, 10))
            self.read_success_anim.pack()

        self.preview_frame = ttk.Frame(body_right)
        self.preview_anim = (
            GifAnimation(self.preview_frame, str(PREVIEW_GIF), size=PREVIEW_SIZE)
            if PREVIEW_GIF.exists() else None
        )
        if self.preview_anim is not None:
            ttk.Label(self.preview_frame, text="Preparando pre-visualizacao do patch...",
                      font=("Segoe UI", 9), wraplength=260, justify="center").pack(pady=(0, 10))
            self.preview_anim.pack()

        self.write_cancelled_frame = ttk.Frame(body_right)
        self.write_cancelled_anim = (
            GifAnimation(self.write_cancelled_frame, str(WRITE_CANCELLED_GIF), size=WRITE_CANCELLED_SIZE)
            if WRITE_CANCELLED_GIF.exists() else None
        )
        if self.write_cancelled_anim is not None:
            ttk.Label(self.write_cancelled_frame, text="Gravacao cancelada.",
                      font=("Segoe UI", 9), wraplength=260, justify="center").pack(pady=(0, 10))
            self.write_cancelled_anim.pack()

        self.writing_frame = ttk.Frame(body_right)
        self.writing_anim = (
            GifAnimation(self.writing_frame, str(WRITING_GIF), size=WRITING_SIZE)
            if WRITING_GIF.exists() else None
        )
        if self.writing_anim is not None:
            ttk.Label(self.writing_frame, text="Aguardando confirmacao...",
                      font=("Segoe UI", 9), wraplength=260, justify="center").pack(pady=(0, 10))
            self.writing_anim.pack()

        self.writing_active_frame = ttk.Frame(body_right)
        self.writing_active_anim = (
            GifAnimation(self.writing_active_frame, str(WRITING_ACTIVE_GIF), size=WRITING_ACTIVE_SIZE)
            if WRITING_ACTIVE_GIF.exists() else None
        )
        if self.writing_active_anim is not None:
            ttk.Label(self.writing_active_frame, text="Gravando NOR...",
                      font=("Segoe UI", 9), wraplength=260, justify="center").pack(pady=(0, 10))
            self.writing_active_anim.pack()

        self.write_success_frame = ttk.Frame(body_right)
        self.write_success_anim = (
            GifAnimation(self.write_success_frame, str(WRITE_SUCCESS_GIF), size=WRITE_SUCCESS_SIZE)
            if WRITE_SUCCESS_GIF.exists() else None
        )
        if self.write_success_anim is not None:
            ttk.Label(self.write_success_frame, text="Gravacao concluida com sucesso!",
                      font=("Segoe UI", 9), wraplength=260, justify="center").pack(pady=(0, 10))
            self.write_success_anim.pack()

        self.detect_failed_frame = ttk.Frame(body_right)
        self.detect_failed_anim = (
            GifAnimation(self.detect_failed_frame, str(DETECT_FAILED_GIF), size=DETECT_FAILED_SIZE)
            if DETECT_FAILED_GIF.exists() else None
        )
        if self.detect_failed_anim is not None:
            ttk.Label(self.detect_failed_frame, text="Leitor CH341A nao encontrado.",
                      font=("Segoe UI", 9), wraplength=260, justify="center").pack(pady=(0, 10))
            self.detect_failed_anim.pack()

        self._stages = {
            "idle": (self.idle_frame, self.idle_anim, {"expand": True}),
            "detecting": (self.detecting_frame, self.detecting_anim, {"expand": True}),
            "detect_failed": (self.detect_failed_frame, self.detect_failed_anim, {"expand": True}),
            "reading": (self.reading_frame, self.reading_anim, {"expand": True}),
            "read_success": (self.read_success_frame, self.read_success_anim, {"expand": True}),
            "preview": (self.preview_frame, self.preview_anim, {"expand": True}),
            "write_cancelled": (self.write_cancelled_frame, self.write_cancelled_anim, {"expand": True}),
            "writing": (self.writing_frame, self.writing_anim, {"expand": True}),
            "writing_active": (self.writing_active_frame, self.writing_active_anim, {"expand": True}),
            "write_success": (self.write_success_frame, self.write_success_anim, {"expand": True}),
        }
        self._show_stage("idle")

    # -- Aba "Analisar arquivo (.bin)" ---------------------------------------
    def _build_file_tab(self, parent):
        top = ttk.Frame(parent, padding=10)
        top.pack(fill="x")
        ttk.Label(top, text="Arquivo NOR (.bin):").pack(side="left")
        self.file_path_var = tk.StringVar(value="")
        entry = ttk.Entry(top, textvariable=self.file_path_var, state="readonly")
        entry.pack(side="left", padx=8, fill="x", expand=True)
        ttk.Button(top, text="Procurar...", command=self.on_file_browse).pack(side="left")

        info_frame = ttk.LabelFrame(parent, text="Informacoes do arquivo", padding=10)
        info_frame.pack(fill="x", padx=10, pady=(0, 10))

        file_info_fields = [
            ("size", "Tamanho do arquivo:"),
            ("sha256", "SHA-256:"),
            ("chip", "Chip HDMI detectado:"),
            ("mac", "Endereco MAC:"),
            ("raw_id", "Identificador bruto (serie/area adjacente):"),
            ("cfi", "Codigo CFI encontrado:"),
            ("wifi_rev", "Revisao Wi-Fi/Bluetooth (EXPERIMENTAL):"),
        ]
        self.file_info_labels = {}
        for i, (key, label_text) in enumerate(file_info_fields):
            ttk.Label(info_frame, text=label_text, font=("Segoe UI", 9, "bold")).grid(
                row=i, column=0, sticky="w", padx=(0, 10), pady=2)
            val_lbl = ttk.Label(info_frame, text="--", font=("Consolas", 9))
            val_lbl.grid(row=i, column=1, sticky="w", pady=2)
            self.file_info_labels[key] = val_lbl

        patch_frame = ttk.LabelFrame(parent, text="Aplicar patch (chip HDMI)", padding=10)
        patch_frame.pack(fill="x", padx=10, pady=(0, 10))

        ttk.Label(patch_frame, text="Gravar arquivo configurado para:").pack(side="left")
        self.file_target_var = tk.StringVar(value=TARGET_NUVOTON)
        combo = ttk.Combobox(
            patch_frame, textvariable=self.file_target_var, state="readonly", width=28,
            values=[TARGET_REALTEK, TARGET_NUVOTON]
        )
        combo.set(TARGET_NUVOTON)
        combo.pack(side="left", padx=8)

        self.btn_file_preview = ttk.Button(patch_frame, text="Pre-visualizar alteracoes",
                                            command=self.on_file_preview, state="disabled")
        self.btn_file_preview.pack(side="left", padx=5)

        self.btn_file_save = tk.Button(
            patch_frame, text="Salvar NOR com patch...",
            command=self.on_file_save, state="disabled",
            bg=BG_ALT, fg=FG, font=("Segoe UI", 9, "bold"),
            activebackground=BG_ACTIVE, activeforeground=FG,
            relief="flat", highlightthickness=1, highlightbackground=BORDER,
        )
        self.btn_file_save.pack(side="left", padx=5)

        log_frame = ttk.Frame(parent, padding=(10, 0, 10, 10))
        log_frame.pack(fill="both", expand=True)
        self.file_txt = scrolledtext.ScrolledText(log_frame, wrap="word", font=("Consolas", 10))
        self.file_txt.configure(
            state="disabled", bg="#000000", fg=FG, insertbackground=FG,
            selectbackground=SELECT_BG, selectforeground=FG,
            relief="flat", borderwidth=0, highlightthickness=0,
        )
        self.file_txt.pack(fill="both", expand=True)
        self.file_txt.tag_configure("ok", foreground=LOG_OK)
        self.file_txt.tag_configure("error", foreground=LOG_ERROR)
        self.file_txt.tag_configure("warn", foreground=LOG_WARN)
        self.file_txt.tag_configure("patch", foreground=LOG_PATCH)
        self.file_txt.tag_configure("info", foreground=LOG_INFO)
        self.file_txt.tag_configure("muted", foreground=LOG_MUTED)

    def file_log(self, msg: str, kind: str = "muted"):
        self.file_txt.configure(state="normal")
        self.file_txt.insert("end", msg + "\n", (kind,))
        self.file_txt.configure(state="disabled")
        self.file_txt.see("end")

    def on_file_browse(self):
        path_str = filedialog.askopenfilename(
            title="Selecione o arquivo NOR (.bin) para analisar",
            filetypes=[("Arquivo NOR", "*.bin"), ("Todos os arquivos", "*.*")],
        )
        if not path_str:
            return
        self.file_path_var.set(path_str)
        self._analyze_file(pathlib.Path(path_str))

    def _analyze_file(self, path: pathlib.Path):
        try:
            data = path.read_bytes()
        except OSError as e:
            messagebox.showerror("Erro ao abrir arquivo", str(e))
            return

        info = parse_nor(data)
        self.file_dump = data
        self.file_info = info
        self.file_patch = None
        self.btn_file_save.configure(state="disabled")

        self.file_info_labels["size"].configure(
            text=f"{info.size} bytes" + (" (OK)" if info.size_ok else " *** TAMANHO INESPERADO ***"))
        self.file_info_labels["sha256"].configure(text=info.sha256)
        chip_text = info.chip_name if info.chip_raw < 0 else f"{info.chip_name} (byte bruto 0x{info.chip_raw:02X})"
        self.file_info_labels["chip"].configure(text=chip_text)
        self.file_info_labels["mac"].configure(text=info.mac or "--")
        self.file_info_labels["raw_id"].configure(text=info.raw_id_block or "--")
        self.file_info_labels["cfi"].configure(text=info.cfi_code or "--")
        self.file_info_labels["wifi_rev"].configure(text=info.wifi_rev_hint or "--")

        self.file_txt.configure(state="normal")
        self.file_txt.delete("1.0", "end")
        self.file_txt.configure(state="disabled")
        self.file_log(f"Arquivo carregado: {path}", "info")
        self.file_log(
            f"Tamanho: {info.size} bytes" + (" (OK)" if info.size_ok else " *** TAMANHO INESPERADO ***"),
            "ok" if info.size_ok else "error",
        )
        if info.warnings:
            self.file_log("")
            self.file_log("AVISOS:", "warn")
            for w in info.warnings:
                self.file_log(f"  - {w}", "warn")

        if info.size_ok:
            self.btn_file_preview.configure(state="normal")
        else:
            self.btn_file_preview.configure(state="disabled")
            messagebox.showwarning(
                "Tamanho inesperado",
                f"O arquivo tem {info.size} bytes, mas o esperado e {EXPECTED_SIZE} "
                "bytes (2 MB). Pre-visualizacao de patch desabilitada."
            )

    def on_file_preview(self):
        if self.file_dump is None:
            return
        target = self.file_target_var.get()
        result = apply_patch(self.file_dump, target)
        self.file_patch = result

        self.file_log("=" * 60, "muted")
        self.file_log(f"PRE-VISUALIZACAO DO PATCH -- alvo: {TARGET_LABEL[target]}", "patch")
        for ch in result.changes:
            self.file_log(
                f"  offset 0x{ch.offset:06X}: {ch.old.hex(' ').upper()} -> "
                f"{ch.new.hex(' ').upper()}   [{ch.description}]", "patch"
            )
        self.file_log("")
        if result.checksum_left_stale:
            self.file_log(
                "*** ATENCAO: o checksum em 0x1C41FE-0x1C41FF NAO foi resolvido "
                "pra essa combinacao de chip + REV Wi-Fi (ainda nao vista). "
                "Ficou com o valor antigo. So use esse arquivo em placa de "
                "bancada/teste. ***", "warn"
            )
        else:
            self.file_log(
                "Checksum em 0x1C41FE-0x1C41FF resolvido com valor confirmado "
                "(ver NOTES.md) -- combinacao de chip + REV Wi-Fi ja vista em "
                "amostras reais.", "ok"
            )
        self.file_log("=" * 60, "muted")
        self.btn_file_save.configure(state="normal")

    def on_file_save(self):
        if self.file_patch is None:
            return
        current_path = pathlib.Path(self.file_path_var.get())
        default_name = f"{current_path.stem}_patched.bin"
        out_path_str = filedialog.asksaveasfilename(
            title="Salvar NOR com patch aplicado",
            defaultextension=".bin",
            initialfile=default_name,
            initialdir=str(current_path.parent),
            filetypes=[("Arquivo NOR", "*.bin"), ("Todos os arquivos", "*.*")],
        )
        if not out_path_str:
            return
        out_path = pathlib.Path(out_path_str)
        out_path.write_bytes(self.file_patch.data)
        self.file_log(f"Arquivo salvo com patch aplicado em: {out_path}", "ok")
        if self.file_patch.checksum_left_stale:
            messagebox.showinfo(
                "Arquivo salvo",
                f"NOR com patch salva em:\n{out_path}\n\n"
                "Lembrete: o checksum em 0x1C41FE-0x1C41FF NAO foi resolvido "
                "pra essa combinacao de chip + REV Wi-Fi -- use so em placa "
                "de bancada/teste."
            )
        else:
            messagebox.showinfo(
                "Arquivo salvo",
                f"NOR com patch salva em:\n{out_path}\n\n"
                "Checksum em 0x1C41FE-0x1C41FF resolvido com valor confirmado "
                "(ver NOTES.md)."
            )

    # -- Aba "Leitor UART" ----------------------------------------------------
    def _build_uart_tab(self, parent):
        top = ttk.Frame(parent, padding=10)
        top.pack(fill="x")

        ttk.Label(top, text="Porta:").pack(side="left")
        self.uart_port_var = tk.StringVar(value="")
        self.combo_uart_port = ttk.Combobox(top, textvariable=self.uart_port_var,
                                             state="readonly", width=14, values=list_ports())
        self.combo_uart_port.pack(side="left", padx=(4, 8))

        ttk.Button(top, text="Atualizar portas", command=self.on_uart_refresh_ports).pack(side="left")

        ttk.Label(top, text="  Baud:").pack(side="left")
        self.uart_baud_var = tk.StringVar(value=str(DEFAULT_BAUDRATE))
        self.combo_uart_baud = ttk.Combobox(top, textvariable=self.uart_baud_var, width=10,
                                             values=[str(b) for b in COMMON_BAUDRATES])
        self.combo_uart_baud.pack(side="left", padx=(4, 8))

        self.btn_uart_connect = ttk.Button(top, text="Conectar", command=self.on_uart_toggle)
        self.btn_uart_connect.pack(side="left", padx=(8, 0))

        status_row = ttk.Frame(parent, padding=(10, 0))
        status_row.pack(fill="x")
        self.lbl_uart_status = ttk.Label(status_row, text="Status: desconectado")
        self.lbl_uart_status.pack(side="left")

        warn_row = ttk.Frame(parent, padding=(10, 4))
        warn_row.pack(fill="x")
        ttk.Label(
            warn_row,
            text=("Captura bruta do log serial -- nao interpreta codigos de erro. "
                  "115200 e o baud mais comum em debug UART, mas confirme se nao vier "
                  "nada legivel. Confirme a tensao do adaptador (muitas placas usam "
                  "3.3V TTL) antes de conectar."),
            font=("Segoe UI", 8), foreground=FG_MUTED, wraplength=960, justify="left",
        ).pack(side="left")

        ref_row = ttk.Frame(parent, padding=(10, 0, 10, 4))
        ref_row.pack(fill="x")
        ttk.Label(ref_row, text="Catalogo de codigos (abre no navegador):").pack(side="left")
        for label, url in UART_REFERENCE_LINKS:
            ttk.Button(ref_row, text=label, command=lambda u=url: webbrowser.open(u)).pack(side="left", padx=4)

        actions_row = ttk.Frame(parent, padding=(10, 0, 10, 5))
        actions_row.pack(fill="x")
        ttk.Button(actions_row, text="Limpar log", command=self.on_uart_clear).pack(side="left")
        ttk.Button(actions_row, text="Salvar log em arquivo...", command=self.on_uart_save).pack(side="left", padx=8)

        send_row = ttk.Frame(parent, padding=(10, 0, 10, 10))
        send_row.pack(fill="x")
        ttk.Label(send_row, text="Enviar (opcional):").pack(side="left")
        self.uart_send_var = tk.StringVar(value="")
        send_entry = ttk.Entry(send_row, textvariable=self.uart_send_var)
        send_entry.pack(side="left", padx=8, fill="x", expand=True)
        send_entry.bind("<Return>", lambda _evt: self.on_uart_send())
        ttk.Button(send_row, text="Enviar", command=self.on_uart_send).pack(side="left")

        log_frame = ttk.Frame(parent, padding=(10, 0, 10, 10))
        log_frame.pack(fill="both", expand=True)
        self.uart_txt = scrolledtext.ScrolledText(log_frame, wrap="word", font=("Consolas", 10))
        self.uart_txt.configure(
            state="disabled", bg="#000000", fg=FG, insertbackground=FG,
            selectbackground=SELECT_BG, selectforeground=FG,
            relief="flat", borderwidth=0, highlightthickness=0,
        )
        self.uart_txt.pack(fill="both", expand=True)
        self.uart_txt.tag_configure("ok", foreground=LOG_OK)
        self.uart_txt.tag_configure("error", foreground=LOG_ERROR)
        self.uart_txt.tag_configure("warn", foreground=LOG_WARN)
        self.uart_txt.tag_configure("patch", foreground=LOG_PATCH)
        self.uart_txt.tag_configure("info", foreground=LOG_INFO)
        self.uart_txt.tag_configure("muted", foreground=LOG_MUTED)

    def uart_log(self, msg: str, kind: str = "muted"):
        self.uart_txt.configure(state="normal")
        self.uart_txt.insert("end", msg + "\n", (kind,))
        self.uart_txt.configure(state="disabled")
        self.uart_txt.see("end")

    def on_uart_refresh_ports(self):
        ports = list_ports()
        self.combo_uart_port.configure(values=ports)
        self.uart_log(f"Portas encontradas: {', '.join(ports) if ports else '(nenhuma)'}", "muted")

    def on_uart_toggle(self):
        if self.uart_connected:
            self._uart_disconnect()
        else:
            self._uart_connect()

    def _uart_connect(self):
        port = self.uart_port_var.get().strip()
        if not port:
            messagebox.showinfo("Selecione a porta", "Escolha uma porta COM antes de conectar.")
            return
        try:
            baud = int(self.uart_baud_var.get().strip())
        except ValueError:
            messagebox.showerror("Baud invalido", "O baud rate precisa ser um numero inteiro.")
            return

        reader = UartReader(port, baud)
        try:
            reader.open()
        except UartError as e:
            self.uart_log(f"ERRO: {e}", "error")
            messagebox.showerror("Erro ao conectar", str(e))
            return

        self.uart = reader
        self.uart_connected = True
        self.uart.start(self._on_uart_line, self._on_uart_error)

        self.lbl_uart_status.configure(text=f"Status: conectado em {port} @ {baud} bps")
        self.btn_uart_connect.configure(text="Desconectar")
        self.combo_uart_port.configure(state="disabled")
        self.combo_uart_baud.configure(state="disabled")
        self.uart_log("=" * 60, "muted")
        self.uart_log(f"Conectado em {port} @ {baud} bps. Capturando log...", "ok")
        self.uart_log("=" * 60, "muted")

    def _uart_disconnect(self):
        if self.uart is not None:
            self.uart.close()
            self.uart = None
        self.uart_connected = False
        self.lbl_uart_status.configure(text="Status: desconectado")
        self.btn_uart_connect.configure(text="Conectar")
        self.combo_uart_port.configure(state="readonly")
        self.combo_uart_baud.configure(state="normal")
        self.uart_log("Desconectado.", "muted")

    def _on_uart_line(self, text: str):
        self.after(0, lambda: self._append_uart_line(text))

    def _append_uart_line(self, text: str):
        lowered = text.lower()
        if any(k in lowered for k in ("error", "fail", "fatal", "panic")):
            kind = "error"
        elif "warn" in lowered:
            kind = "warn"
        elif any(k in lowered for k in ("ok", "boot", "success", "ready")):
            kind = "ok"
        else:
            kind = "muted"
        self.uart_log(text, kind)

    def _on_uart_error(self, msg: str):
        self.after(0, lambda: self._uart_error(msg))

    def _uart_error(self, msg: str):
        self.uart_log(f"ERRO na porta serial: {msg}", "error")
        self._uart_disconnect()

    def on_uart_clear(self):
        self.uart_txt.configure(state="normal")
        self.uart_txt.delete("1.0", "end")
        self.uart_txt.configure(state="disabled")

    def on_uart_save(self):
        content = self.uart_txt.get("1.0", "end")
        if not content.strip():
            messagebox.showinfo("Log vazio", "Nao ha nada capturado ainda pra salvar.")
            return
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        out_path_str = filedialog.asksaveasfilename(
            title="Salvar log UART",
            defaultextension=".txt",
            initialfile=f"uart_log_{timestamp}.txt",
            filetypes=[("Arquivo de texto", "*.txt"), ("Todos os arquivos", "*.*")],
        )
        if not out_path_str:
            return
        pathlib.Path(out_path_str).write_text(content, encoding="utf-8")
        self.uart_log(f"Log salvo em: {out_path_str}", "ok")

    def on_uart_send(self):
        if not self.uart_connected or self.uart is None:
            messagebox.showinfo("Nao conectado", "Conecte a porta UART antes de enviar.")
            return
        text = self.uart_send_var.get()
        if not text:
            return
        self.uart.write((text + "\n").encode("utf-8", errors="replace"))
        self.uart_log(f">> {text}", "patch")
        self.uart_send_var.set("")

    # -- Aba "Teste de Controle" (DualSense) ---------------------------------
    def _build_controller_tab(self, parent):
        top = ttk.Frame(parent, padding=10)
        top.pack(fill="x")
        ttk.Button(top, text="Detectar controle", command=self.on_controller_detect).pack(side="left")
        self.lbl_controller_status = ttk.Label(top, text="  Nenhum controle detectado ainda")
        self.lbl_controller_status.pack(side="left", padx=8)
        self.btn_controller_connect = ttk.Button(top, text="Conectar", command=self.on_controller_connect,
                                                  state="disabled")
        self.btn_controller_connect.pack(side="left", padx=4)
        self.btn_controller_disconnect = ttk.Button(top, text="Desconectar", command=self.on_controller_disconnect,
                                                     state="disabled")
        self.btn_controller_disconnect.pack(side="left", padx=4)

        warn_row = ttk.Frame(parent, padding=(10, 0, 10, 6))
        warn_row.pack(fill="x")
        ttk.Label(
            warn_row,
            text=("Leitura via HID bruto, nativo, sem precisar de internet/navegador. Conecte o "
                  "controle por CABO USB. Analogicos, gatilhos, botoes e D-pad sao de alta confianca; "
                  "touchpad, bateria, vibracao e barra de luz sao EXPERIMENTAIS (ainda nao validados "
                  "com hardware real) -- teste e me avise se algo vier errado."),
            font=("Segoe UI", 8), foreground=FG_MUTED, wraplength=960, justify="left",
        ).pack(side="left")

        body = ttk.Frame(parent, padding=10)
        body.pack(fill="both", expand=True)

        left_col = ttk.Frame(body)
        left_col.pack(side="left", fill="y", padx=(0, 24))

        ttk.Label(left_col, text="Analogico esquerdo", font=("Segoe UI", 9, "bold")).pack()
        self.canvas_ls = tk.Canvas(left_col, width=120, height=120, bg=BG, highlightthickness=0)
        self.canvas_ls.pack(pady=(4, 4))
        self._draw_stick_gauge(self.canvas_ls)
        self.lbl_ls_val = ttk.Label(left_col, text="X: 128  Y: 128")
        self.lbl_ls_val.pack()

        ttk.Label(left_col, text="Analogico direito", font=("Segoe UI", 9, "bold")).pack(pady=(14, 0))
        self.canvas_rs = tk.Canvas(left_col, width=120, height=120, bg=BG, highlightthickness=0)
        self.canvas_rs.pack(pady=(4, 4))
        self._draw_stick_gauge(self.canvas_rs)
        self.lbl_rs_val = ttk.Label(left_col, text="X: 128  Y: 128")
        self.lbl_rs_val.pack()

        ttk.Label(left_col, text="Gatilhos", font=("Segoe UI", 9, "bold")).pack(pady=(16, 2))
        ttk.Label(left_col, text="L2").pack(anchor="w")
        self.bar_l2 = ttk.Progressbar(left_col, mode="determinate", maximum=255, length=150)
        self.bar_l2.pack()
        ttk.Label(left_col, text="R2").pack(anchor="w", pady=(8, 0))
        self.bar_r2 = ttk.Progressbar(left_col, mode="determinate", maximum=255, length=150)
        self.bar_r2.pack()

        mid_col = ttk.Frame(body)
        mid_col.pack(side="left", padx=(0, 24))
        ttk.Label(mid_col, text="Diagrama (clique nos botoes do controle)", font=("Segoe UI", 9, "bold")).pack()
        self._build_controller_diagram(mid_col)

        right_col = ttk.Frame(body)
        right_col.pack(side="left", fill="both", expand=True)

        self.lbl_battery = ttk.Label(right_col, text="Bateria (experimental): --")
        self.lbl_battery.pack(anchor="w")

        vib_frame = ttk.LabelFrame(right_col, text="Teste de vibracao (experimental)", padding=8)
        vib_frame.pack(fill="x", pady=(16, 8))
        ttk.Button(vib_frame, text="Motor esquerdo (forte)",
                   command=lambda: self.on_controller_rumble("left")).pack(side="left", padx=4)
        ttk.Button(vib_frame, text="Motor direito (fraco)",
                   command=lambda: self.on_controller_rumble("right")).pack(side="left", padx=4)
        ttk.Button(vib_frame, text="Parar",
                   command=lambda: self.on_controller_rumble("stop")).pack(side="left", padx=4)

        light_frame = ttk.LabelFrame(right_col, text="Teste da barra de luz", padding=8)
        light_frame.pack(fill="x")
        for name, rgb in [("Vermelho", (255, 0, 0)), ("Verde", (0, 255, 0)), ("Azul", (0, 0, 255)),
                           ("Branco", (255, 255, 255)), ("Apagar", (0, 0, 0))]:
            ttk.Button(light_frame, text=name, command=lambda c=rgb: self.on_controller_light(c)).pack(
                side="left", padx=3)

        calib_frame = ttk.LabelFrame(right_col, text="Calibracao do analogico (grava no controle)", padding=8)
        calib_frame.pack(fill="x", pady=(16, 0))
        ttk.Label(
            calib_frame,
            text=("Mesmo recurso do dualshock-tools.github.io, feito nativamente aqui. So fica "
                  "permanente se voce clicar em 'Salvar alteracoes permanentemente' depois -- "
                  "ate la da pra testar e desistir sem risco."),
            font=("Segoe UI", 8), foreground=FG_MUTED, wraplength=260, justify="left",
        ).pack(anchor="w", pady=(0, 6))
        ttk.Button(calib_frame, text="Calibrar centro do analogico",
                   command=self.on_controller_calibrate_center).pack(fill="x", pady=2)
        ttk.Button(calib_frame, text="Calibrar alcance do analogico...",
                   command=self.on_controller_calibrate_range).pack(fill="x", pady=2)
        self.btn_controller_flash = ttk.Button(
            calib_frame, text="Salvar alteracoes permanentemente",
            command=self.on_controller_flash, state="disabled")
        self.btn_controller_flash.pack(fill="x", pady=(6, 2))
        self.lbl_controller_calib_status = ttk.Label(
            calib_frame, text="Nenhuma alteracao de calibracao pendente nesta sessao.",
            font=("Segoe UI", 8), foreground=FG_MUTED, wraplength=260, justify="left")
        self.lbl_controller_calib_status.pack(anchor="w", pady=(4, 0))

    def _build_controller_diagram(self, parent):
        """Diagrama do controle feito a partir do SVG real do DualSense usado
        pelo dualshock-tools.github.io (MIT, github.com/dualshock-tools) --
        pre-renderizado em images/controller/ por dev_tools/build_controller_diagram.py.
        Cada botao e uma imagem transparente (mesmo recorte/posicao do SVG
        original) que fica escondida e so aparece quando o botao e apertado."""
        w, h = CONTROLLER_BBOXES.DIAGRAM_SIZE
        c = tk.Canvas(parent, width=w, height=h, bg=BG, highlightthickness=0, bd=0)
        c.pack()

        self._diagram_photos = {}

        def load(name: str) -> tk.PhotoImage:
            img = tk.PhotoImage(file=str(CONTROLLER_DIAGRAM_DIR / f"{name}.png"))
            self._diagram_photos[name] = img
            return img

        c.create_image(0, 0, anchor="nw", image=load("idle"))

        d = {}
        for key in CONTROLLER_BBOXES.BBOXES:
            if key in ("l2", "r2"):
                continue  # esses dois usam intensidade variavel (ver abaixo), nao on/off
            img = load(key)
            d[key] = c.create_image(0, 0, anchor="nw", image=img, state="hidden")

        # L2/R2 crescem em intensidade (alpha) conforme a pressao, em vez de
        # simplesmente aparecer/sumir -- usa Pillow pra variar a transparencia
        # do mesmo recorte do gatilho.
        self._trigger_base = {
            "l2": Image.open(CONTROLLER_DIAGRAM_DIR / "l2.png").convert("RGBA"),
            "r2": Image.open(CONTROLLER_DIAGRAM_DIR / "r2.png").convert("RGBA"),
        }
        self._trigger_photo = {}
        self._trigger_level = {"l2": -1, "r2": -1}
        d["l2"] = c.create_image(0, 0, anchor="nw", image=self._make_trigger_photo("l2", 0))
        d["r2"] = c.create_image(0, 0, anchor="nw", image=self._make_trigger_photo("r2", 0))

        l2_box = CONTROLLER_BBOXES.BBOXES["l2"]
        r2_box = CONTROLLER_BBOXES.BBOXES["r2"]
        d["l2_text"] = c.create_text(
            (l2_box[0] + l2_box[2]) // 2, (l2_box[1] + l2_box[3]) // 2,
            text="L2 0%", fill=FG, font=("Segoe UI", 8, "bold"))
        d["r2_text"] = c.create_text(
            (r2_box[0] + r2_box[2]) // 2, (r2_box[1] + r2_box[3]) // 2,
            text="R2 0%", fill=FG, font=("Segoe UI", 8, "bold"))

        d["touch_dots"] = []
        self._diagram_canvas = c
        self._diagram = d

    def on_controller_detect(self):
        devices = dualsense.list_devices()
        self._controller_devices = devices
        if not devices:
            self.lbl_controller_status.configure(
                text="  Nenhum controle DualSense encontrado (conecte por cabo USB)")
            self.btn_controller_connect.configure(state="disabled")
            return
        first = devices[0]
        name = dualsense.KNOWN_PRODUCT_IDS.get(first["product_id"], "Controle Sony")
        extra = f" (+{len(devices) - 1} outro(s))" if len(devices) > 1 else ""
        self.lbl_controller_status.configure(text=f"  Encontrado: {name}{extra}")
        self.btn_controller_connect.configure(state="normal")

    def on_controller_connect(self):
        if not self._controller_devices:
            return
        dev_info = self._controller_devices[0]
        controller = DualSenseController(dev_info["path"])
        try:
            controller.open()
        except DualSenseError as e:
            messagebox.showerror("Erro ao conectar controle", str(e))
            return
        self.controller = controller
        self.controller.start()
        self.btn_controller_connect.configure(state="disabled")
        self.btn_controller_disconnect.configure(state="normal")
        self.lbl_controller_status.configure(text="  Conectado -- mexa nos sticks/botoes para testar")
        self._poll_controller()

    def _poll_controller(self):
        if self.controller is None:
            return
        s = self.controller.state
        self._update_stick(self.canvas_ls, s.left_stick_x, s.left_stick_y)
        self._update_stick(self.canvas_rs, s.right_stick_x, s.right_stick_y)
        self.lbl_ls_val.configure(text=f"X: {s.left_stick_x}  Y: {s.left_stick_y}")
        self.lbl_rs_val.configure(text=f"X: {s.right_stick_x}  Y: {s.right_stick_y}")

        self._update_diagram(s)

        if s.battery_percent is not None:
            charging = " (carregando)" if s.battery_charging else ""
            self.lbl_battery.configure(text=f"Bateria (experimental): {s.battery_percent}%{charging}")

        self._controller_poll_job = self.after(33, self._poll_controller)

    def _draw_stick_gauge(self, canvas: tk.Canvas):
        canvas.create_oval(8, 8, 112, 112, outline=FG_MUTED, width=1)
        canvas.create_line(60, 55, 60, 65, fill=FG_MUTED)
        canvas.create_line(55, 60, 65, 60, fill=FG_MUTED)

    def _update_stick(self, canvas: tk.Canvas, x: int, y: int):
        canvas.delete("dot")
        cx = 60 + (x - 128) / 128 * 50
        cy = 60 + (y - 128) / 128 * 50
        canvas.create_oval(cx - 6, cy - 6, cx + 6, cy + 6, fill=LOG_INFO, outline="", tags="dot")

    def _set_diagram_btn(self, key: str, visible: bool):
        c = self._diagram_canvas
        c.itemconfig(self._diagram[key], state=("normal" if visible else "hidden"))

    def _make_trigger_photo(self, key: str, level: int) -> ImageTk.PhotoImage:
        """level: 0-100 -- intensidade (alpha) do recorte verde do gatilho."""
        base = self._trigger_base[key]
        alpha = base.split()[-1].point(lambda a, lvl=level: a * lvl // 100)
        img = base.copy()
        img.putalpha(alpha)
        photo = ImageTk.PhotoImage(img)
        self._trigger_photo[key] = photo  # mantem referencia viva
        return photo

    def _update_trigger(self, key: str, analog_value: int):
        level = round(analog_value / 255 * 100 / 5) * 5  # quantiza de 5 em 5%
        if level == self._trigger_level[key]:
            return
        self._trigger_level[key] = level
        photo = self._make_trigger_photo(key, level)
        self._diagram_canvas.itemconfig(self._diagram[key], image=photo)

    def _update_diagram(self, s):
        c = self._diagram_canvas
        d = self._diagram

        for key in ("l1", "r1", "triangle", "circle", "cross", "square", "create", "options", "mute"):
            self._set_diagram_btn(key, s.buttons.get(key, False))
        self._set_diagram_btn("l3", s.buttons.get("l3", False))
        self._set_diagram_btn("r3", s.buttons.get("r3", False))
        self._set_diagram_btn("ps", s.buttons.get("ps", False))
        self._set_diagram_btn("touchpad", s.buttons.get("touchpad_click", False))

        for arm in ("dpad_up", "dpad_down", "dpad_left", "dpad_right"):
            self._set_diagram_btn(arm, False)
        dpad_map = {"cima": ["dpad_up"], "baixo": ["dpad_down"], "esquerda": ["dpad_left"],
                    "direita": ["dpad_right"], "cima-direita": ["dpad_up", "dpad_right"],
                    "baixo-direita": ["dpad_down", "dpad_right"], "baixo-esquerda": ["dpad_down", "dpad_left"],
                    "cima-esquerda": ["dpad_up", "dpad_left"]}
        for arm in dpad_map.get(s.dpad, []):
            self._set_diagram_btn(arm, True)

        l2_pct = int(s.l2_analog / 255 * 100)
        r2_pct = int(s.r2_analog / 255 * 100)
        self._update_trigger("l2", s.l2_analog)
        self._update_trigger("r2", s.r2_analog)
        c.itemconfig(d["l2_text"], text=f"L2 {l2_pct}%")
        c.itemconfig(d["r2_text"], text=f"R2 {r2_pct}%")
        self.bar_l2["value"] = s.l2_analog
        self.bar_r2["value"] = s.r2_analog

        for item in d["touch_dots"]:
            c.delete(item)
        dots = []
        if s.touch1_active:
            dots.append(self._draw_touch_dot(c, s.touch1_x, s.touch1_y))
        if s.touch2_active:
            dots.append(self._draw_touch_dot(c, s.touch2_x, s.touch2_y))
        d["touch_dots"] = dots

    def _draw_touch_dot(self, c: tk.Canvas, raw_x: int, raw_y: int):
        # resolucao aproximada do touchpad do DualSense: ~0-1919 x ~0-1079,
        # mapeada pra dentro da area real da tela do touchpad no diagrama
        x0, y0, x1, y1 = CONTROLLER_BBOXES.BBOXES["touchpad"]
        px = x0 + raw_x / 1920 * (x1 - x0)
        py = y0 + raw_y / 1080 * (y1 - y0)
        return c.create_oval(px - 4, py - 4, px + 4, py + 4, fill=LOG_PATCH, outline="")

    def on_controller_disconnect(self):
        if self._controller_poll_job is not None:
            self.after_cancel(self._controller_poll_job)
            self._controller_poll_job = None
        if self.controller is not None:
            self.controller.close()
            self.controller = None
        self.btn_controller_connect.configure(state="normal" if self._controller_devices else "disabled")
        self.btn_controller_disconnect.configure(state="disabled")
        self.lbl_controller_status.configure(text="  Desconectado")
        self._controller_has_pending_changes = False
        self.btn_controller_flash.configure(state="disabled")
        self.set_controller_calib_status("Nenhuma alteracao de calibracao pendente nesta sessao.")

    def on_controller_rumble(self, which: str):
        if self.controller is None:
            return
        try:
            if which == "left":
                self.controller.set_rumble_and_light(255, 0, 0, 0, 0)
            elif which == "right":
                self.controller.set_rumble_and_light(0, 255, 0, 0, 0)
            else:
                self.controller.set_rumble_and_light(0, 0, 0, 0, 0)
        except DualSenseError as e:
            messagebox.showerror("Erro ao testar vibracao", str(e))

    def on_controller_light(self, rgb: tuple[int, int, int]):
        if self.controller is None:
            return
        try:
            self.controller.set_rumble_and_light(0, 0, *rgb)
        except DualSenseError as e:
            messagebox.showerror("Erro ao testar barra de luz", str(e))

    # -- Calibracao do analogico (grava no controle) -------------------------
    def set_controller_calib_status(self, text: str):
        self.lbl_controller_calib_status.configure(text=text)

    def on_controller_calibrate_center(self):
        if self.controller is None:
            messagebox.showinfo("Nao conectado", "Conecte o controle antes de calibrar.")
            return
        proceed = messagebox.askyesno(
            "Calibrar centro do analogico",
            "Solte os dois analogicos (deixe-os parados, sem tocar) antes de continuar.\n\n"
            "Isto recalcula o ponto central dos dois sticks. A mudanca fica ativa na hora, "
            "mas so e gravada de forma permanente se voce clicar depois em "
            "'Salvar alteracoes permanentemente' -- ate la, da pra desistir sem risco.\n\n"
            "Continuar?",
        )
        if not proceed:
            return
        self.set_controller_calib_status("Calibrando centro do analogico...")
        threading.Thread(target=self._controller_calibrate_center_worker, daemon=True).start()

    def _controller_calibrate_center_worker(self):
        try:
            self.controller.calibrate_sticks_center()
            self.after(0, lambda: self._controller_calibrate_done(
                "Centro calibrado. Teste os sticks -- se estiver bom, clique em "
                "'Salvar alteracoes permanentemente'."))
        except DualSenseError as e:
            self.after(0, lambda: self._controller_calibrate_failed(str(e)))

    def _controller_calibrate_done(self, msg: str):
        self._controller_has_pending_changes = True
        self.btn_controller_flash.configure(state="normal")
        self.set_controller_calib_status(msg)

    def _controller_calibrate_failed(self, err: str):
        self.set_controller_calib_status(f"ERRO: {err}")
        messagebox.showerror("Erro na calibracao", err)

    def on_controller_calibrate_range(self):
        if self.controller is None:
            messagebox.showinfo("Nao conectado", "Conecte o controle antes de calibrar.")
            return
        proceed = messagebox.askyesno(
            "Calibrar alcance do analogico",
            "Na proxima tela, gire os dois analogicos em circulos completos e bem abertos "
            "varias vezes (uns 5 a 10 segundos) antes de clicar em Concluir.\n\n"
            "So fica permanente depois que voce clicar em 'Salvar alteracoes "
            "permanentemente'.\n\nContinuar?",
        )
        if not proceed:
            return
        try:
            self.controller.calibrate_range_begin()
        except DualSenseError as e:
            messagebox.showerror("Erro ao iniciar calibracao", str(e))
            return

        dlg = tk.Toplevel(self)
        dlg.title("Calibrando alcance dos analogicos")
        dlg.configure(bg=BG)
        dlg.transient(self)
        dlg.grab_set()
        tk.Label(
            dlg, bg=BG, fg=FG, font=("Segoe UI", 10), wraplength=360, justify="center",
            text=("Gire os dois analogicos em circulos completos e bem abertos, "
                  "varias vezes. Quando terminar, clique em Concluir."),
        ).pack(padx=20, pady=(20, 10))
        lbl_timer = tk.Label(dlg, text="0s", bg=BG, fg=LOG_INFO, font=("Consolas", 14, "bold"))
        lbl_timer.pack(pady=(0, 10))

        state = {"elapsed": 0, "ticking": True}

        def tick():
            if not state["ticking"] or not dlg.winfo_exists():
                return
            state["elapsed"] += 1
            lbl_timer.configure(text=f"{state['elapsed']}s")
            dlg.after(1000, tick)

        tick()

        btn_row = tk.Frame(dlg, bg=BG)
        btn_row.pack(pady=(0, 20))

        def finish(commit: bool):
            state["ticking"] = False
            dlg.destroy()
            if commit:
                self._controller_calibrate_range_finish()
            else:
                try:
                    self.controller.calibrate_range_end()
                except DualSenseError:
                    pass
                self.set_controller_calib_status("Calibracao de alcance cancelada.")

        ttk.Button(btn_row, text="Concluir", command=lambda: finish(True)).pack(side="left", padx=6)
        ttk.Button(btn_row, text="Cancelar", command=lambda: finish(False)).pack(side="left", padx=6)

    def _controller_calibrate_range_finish(self):
        try:
            self.controller.calibrate_range_end()
            self._controller_has_pending_changes = True
            self.btn_controller_flash.configure(state="normal")
            self.set_controller_calib_status(
                "Alcance calibrado. Teste os sticks -- se estiver bom, clique em "
                "'Salvar alteracoes permanentemente'."
            )
        except DualSenseError as e:
            self.set_controller_calib_status(f"ERRO: {e}")
            messagebox.showerror("Erro na calibracao", str(e))

    def on_controller_flash(self):
        if self.controller is None:
            return
        proceed = messagebox.askyesno(
            "Salvar alteracoes permanentemente",
            "Isto grava a calibracao atual de forma PERMANENTE na memoria do controle "
            "(vale ate a proxima calibracao, pode ser refeita quantas vezes precisar).\n\n"
            "Tem certeza?",
        )
        if not proceed:
            return
        try:
            self.controller.flash_changes()
            self._controller_has_pending_changes = False
            self.btn_controller_flash.configure(state="disabled")
            self.set_controller_calib_status("Alteracoes salvas permanentemente.")
            messagebox.showinfo("Salvo", "Calibracao salva permanentemente no controle.")
        except DualSenseError as e:
            messagebox.showerror("Erro ao salvar", str(e))

    def _show_stage(self, name: str):
        for key, (widget, anim, _) in self._stages.items():
            if key != name:
                if anim is not None:
                    anim.stop()
                widget.pack_forget()
        widget, anim, pack_opts = self._stages[name]
        widget.pack(**pack_opts)
        if anim is not None:
            anim.start()

    def log(self, msg: str, kind: str = "muted"):
        self.txt.configure(state="normal")
        self.txt.insert("end", msg + "\n", (kind,))
        self.txt.configure(state="disabled")
        self.txt.see("end")

    def set_status(self, msg: str):
        self.lbl_status.configure(text=f"Status: {msg}")

    def set_backup_badge(self, ok: bool, text: str):
        if ok:
            self.lbl_backup_badge.configure(bg="#1a8a1a", text=f"  ✓ {text}  ")
        else:
            self.lbl_backup_badge.configure(bg="#999999", text=f"  {text}  ")

    # -- Painel de progresso da gravacao (4 etapas) -------------------------
    def _reset_write_steps(self):
        for step in self.write_steps.values():
            step["bar"].stop()
            step["bar"].configure(mode="determinate", value=0, maximum=100)
            step["check"].configure(text="  ")
            step["label"].configure(text=step["base_text"])

    def _write_step_start(self, key: str, status_text: str):
        step = self.write_steps[key]
        step["check"].configure(text="  ")
        self.set_status(status_text)
        self.log(status_text, "info")
        if key == "erase":
            step["bar"].configure(mode="indeterminate", value=0)
            step["bar"].start(15)
        else:
            step["bar"].configure(mode="determinate", value=0, maximum=100)

    def _write_step_progress(self, key: str, done: int, total: int):
        step = self.write_steps[key]
        step["bar"].configure(mode="determinate", maximum=total, value=done)

    def _write_step_progress_cb(self, key: str, done: int, total: int):
        self.after(0, lambda: self._write_step_progress(key, done, total))

    def _write_step_done(self, key: str, ok: bool = True):
        step = self.write_steps[key]
        if key == "erase":
            step["bar"].stop()
            step["bar"].configure(mode="determinate", maximum=1, value=1)
        else:
            maximum = step["bar"]["maximum"]
            step["bar"].configure(value=maximum)
        step["check"].configure(text="✓" if ok else "✗",
                                 fg=LOG_OK if ok else LOG_ERROR)

    # -- Passo 1: detectar ------------------------------------------------
    def on_detect(self):
        self._show_stage("detecting")
        self.btn_detect.configure(state="disabled")
        self.set_status("detectando leitor...")
        threading.Thread(target=self._detect_worker, daemon=True).start()

    def _detect_worker(self):
        start = time.monotonic()
        try:
            spi = CH341SPI()
            spi.open()
            jedec = spi.read_jedec_id()
            spi.close()
            self.spi = spi
            self._wait_min_display(start)
            self.after(0, lambda: self._detect_done(jedec))
        except CH341Error as e:
            err_msg = str(e)
            self._wait_min_display(start)
            self.after(0, lambda: self._detect_failed(err_msg))

    def _wait_min_display(self, started_at: float):
        """Garante que uma animacao de etapa fique visivel por um tempo minimo,
        mesmo que a operacao real termine quase instantaneamente."""
        elapsed = time.monotonic() - started_at
        remaining = MIN_DETECT_DISPLAY_S - elapsed
        if remaining > 0:
            time.sleep(remaining)

    def _detect_done(self, jedec: bytes):
        self.set_status("leitor detectado")
        self.log(f"Leitor CH341A conectado. JEDEC ID do chip na NOR: {jedec.hex(' ').upper()}", "ok")
        self.btn_detect.configure(state="normal")
        self.btn_read.configure(state="normal")
        self.btn_restore.configure(state="normal")

    def _detect_failed(self, err: str):
        self._show_stage("detect_failed")
        self.set_status("falha ao detectar leitor")
        self.log(f"ERRO: {err}", "error")
        messagebox.showerror("Erro ao detectar leitor", err)
        self.btn_detect.configure(state="normal")

    # -- Passo 2: ler, comparar, backup, parsear ---------------------------
    def on_read(self):
        self._show_stage("reading")
        self.btn_read.configure(state="disabled")
        self.btn_detect.configure(state="disabled")
        self.btn_preview.configure(state="disabled")
        self.btn_write.configure(state="disabled")
        self.set_backup_badge(False, "lendo NOR...")
        self.set_status("lendo NOR (1a leitura)...")
        self.progress.configure(value=0, maximum=EXPECTED_SIZE)
        threading.Thread(target=self._read_worker, daemon=True).start()

    def _progress_cb(self, done, total):
        self.after(0, lambda: self.progress.configure(value=done, maximum=total))

    def _read_worker(self):
        try:
            with CH341SPI() as spi:
                self.after(0, lambda: self.set_status("lendo NOR (1a leitura)..."))
                dump1 = spi.read_all(EXPECTED_SIZE, progress_cb=self._progress_cb)

                self.after(0, lambda: self.set_status("lendo NOR (2a leitura, para conferir)..."))
                dump2 = spi.read_all(EXPECTED_SIZE, progress_cb=self._progress_cb)

            equal, n_diff, first_offsets = compare_dumps(dump1, dump2)
            if not equal:
                self.after(0, lambda: self._read_mismatch(n_diff, first_offsets))
                return

            info = parse_nor(dump1)
            backup_path = self._save_backup(dump1, dump2, info)
            self.after(0, lambda: self._read_done(dump1, info, backup_path))
        except CH341Error as e:
            err_msg = str(e)
            self.after(0, lambda: self._read_failed(err_msg))

    def _save_backup(self, dump1: bytes, dump2: bytes, info: NorInfo) -> pathlib.Path:
        """Salva as duas leituras na pasta do console (uma pasta por
        identificador, nao por data/hora -- leituras novas do mesmo console
        sobrescrevem DUMP1.bin/DUMP2.bin). Retorna o caminho do DUMP1.bin,
        usado como referencia de backup pra restaurar em caso de erro."""
        ident = safe_filename_part(info.raw_id_block, "SEM_IDENTIFICADOR")
        console_dir = BACKUP_DIR / ident
        console_dir.mkdir(parents=True, exist_ok=True)
        dump1_path = console_dir / "DUMP1.bin"
        dump1_path.write_bytes(dump1)
        (console_dir / "DUMP2.bin").write_bytes(dump2)
        return dump1_path

    def _read_mismatch(self, n_diff: int, first_offsets: list[int]):
        self.set_status("ERRO: as duas leituras nao bateram")
        self.set_backup_badge(False, "leitura falhou -- sem backup")
        offs = ", ".join(f"0x{o:X}" for o in first_offsets)
        self.log(
            f"As duas leituras da NOR deram resultados DIFERENTES em {n_diff} "
            f"byte(s). Primeiros offsets divergentes: {offs}", "error"
        )
        self.log(
            "NAO prossiga com gravacao. Verifique o contato do soquete/clipe "
            "na NOR e leia novamente.", "warn"
        )
        messagebox.showwarning(
            "Leituras inconsistentes",
            "As duas leituras da NOR deram resultados diferentes.\n"
            "Verifique o contato do leitor e tente novamente. Nao prossiga "
            "com gravacao enquanto isso nao for resolvido."
        )
        self.btn_detect.configure(state="normal")
        self.btn_read.configure(state="normal")

    def _read_done(self, dump: bytes, info: NorInfo, backup_path: pathlib.Path):
        self._show_stage("read_success")
        self.last_info = info
        self.last_dump = dump
        self.last_backup_path = backup_path
        self.last_patch = None
        self.set_status("leitura concluida com sucesso")
        self.set_backup_badge(True, f"Backup salvo em: {backup_path.parent.name}")
        self.log("=" * 60, "muted")
        self.log("LEITURA CONCLUIDA -- as duas leituras bateram byte a byte.", "ok")
        self.log(f"DUMP1.bin e DUMP2.bin salvos em: {backup_path.parent}", "muted")
        self.log("")
        self.log(f"Tamanho do arquivo: {info.size} bytes" + (" (OK)" if info.size_ok else " *** TAMANHO INESPERADO ***"))
        self.log(f"SHA-256: {info.sha256}")
        self.log(f"Chip HDMI detectado: {info.chip_name} (byte bruto 0x{info.chip_raw:02X})")
        self.log(f"Endereco MAC: {info.mac}")
        self.log(f"Identificador bruto (serie/area adjacente): {info.raw_id_block}")
        self.log(f"Codigo CFI encontrado: {info.cfi_code}")
        self.log(f"Revisao do modulo Wi-Fi/Bluetooth (EXPERIMENTAL, nao confirmado): {info.wifi_rev_hint}")
        if info.warnings:
            self.log("")
            self.log("AVISOS:", "warn")
            for w in info.warnings:
                self.log(f"  - {w}", "warn")
        self.log("=" * 60, "muted")
        self.btn_detect.configure(state="normal")
        self.btn_read.configure(state="normal")
        self.btn_preview.configure(state="normal")
        self.btn_write.configure(state="disabled")

    def _read_failed(self, err: str):
        self.set_status("falha na leitura")
        self.set_backup_badge(False, "leitura falhou -- sem backup")
        self.log(f"ERRO: {err}", "error")
        messagebox.showerror("Erro na leitura", err)
        self.btn_detect.configure(state="normal")
        self.btn_read.configure(state="normal")

    # -- Passo 3: pre-visualizar patch --------------------------------------
    def on_preview(self):
        self._show_stage("preview")
        if self.last_dump is None:
            messagebox.showinfo("Leia a NOR primeiro", "Faca a leitura da NOR (passo 2) antes de pre-visualizar o patch.")
            return
        target = self.target_var.get()
        result = apply_patch(self.last_dump, target)
        self.last_patch = result

        converted_path = None
        if self.last_backup_path is not None:
            from_slug = CHIP_SLUG.get(self.last_info.chip_raw, f"CHIP0x{self.last_info.chip_raw:02X}")
            to_slug = CHIP_SLUG.get(TARGET_BYTE[target], target.upper())
            converted_path = self.last_backup_path.parent / f"{from_slug}_FOR_{to_slug}.bin"
            converted_path.write_bytes(result.data)

        self.log("=" * 60, "muted")
        self.log(f"PRE-VISUALIZACAO DO PATCH -- alvo: {TARGET_LABEL[target]}", "patch")
        for ch in result.changes:
            self.log(
                f"  offset 0x{ch.offset:06X}: {ch.old.hex(' ').upper()} -> "
                f"{ch.new.hex(' ').upper()}   [{ch.description}]", "patch"
            )
        self.log("")
        if result.checksum_left_stale:
            self.log(
                "*** ATENCAO: o checksum em 0x1C41FE-0x1C41FF NAO foi resolvido "
                "pra essa combinacao de chip + REV Wi-Fi (ainda nao vista). "
                "Isso pode fazer o console nao exibir video mesmo ligando. So "
                "grave em placa de bancada/teste. ***", "warn"
            )
        else:
            self.log(
                "Checksum em 0x1C41FE-0x1C41FF resolvido com valor confirmado "
                "(ver NOTES.md) -- combinacao de chip + REV Wi-Fi ja vista em "
                "amostras reais.", "ok"
            )
        if converted_path is not None:
            self.log(f"NOR convertida salva em: {converted_path}", "muted")
        self.log("=" * 60, "muted")
        self.btn_write.configure(state="normal")

    # -- Passo 4: gravar -----------------------------------------------------
    def on_write(self):
        self._show_stage("writing")
        if self.last_patch is None or self.last_dump is None:
            messagebox.showinfo("Pre-visualize primeiro", "Clique em 'Pre-visualizar alteracoes' antes de gravar.")
            return

        if self.last_patch.checksum_left_stale:
            checksum_msg = (
                "O checksum em 0x1C41FE-FF NAO foi resolvido pra essa "
                "combinacao de chip + REV Wi-Fi -- ainda nao sabemos se isso "
                "impede o video de funcionar.\n\nUse isto SOMENTE em placa de "
                "bancada/teste, nunca em placa de cliente."
            )
        else:
            checksum_msg = (
                "O checksum em 0x1C41FE-FF foi resolvido com um valor "
                "confirmado em amostras reais (ver NOTES.md)."
            )
        proceed = messagebox.askyesno(
            "Confirmar gravacao",
            "Isto vai APAGAR e REGRAVAR a NOR inteira com o patch mostrado no "
            f"log.\n\n{checksum_msg}\n\nTem certeza que quer continuar?",
            icon="warning",
        )
        if not proceed:
            self._show_stage("write_cancelled")
            self.log("Gravacao cancelada pelo usuario (respondeu Nao na confirmacao).", "warn")
            return

        typed = simpledialog.askstring(
            "Confirmacao final",
            f"Digite {CONFIRM_PHRASE} para confirmar a gravacao:"
        )
        if typed != CONFIRM_PHRASE:
            self._show_stage("write_cancelled")
            self.log("Gravacao cancelada (confirmacao nao digitada corretamente).", "warn")
            return

        self._show_stage("writing_active")
        self.btn_detect.configure(state="disabled")
        self.btn_read.configure(state="disabled")
        self.btn_preview.configure(state="disabled")
        self.btn_write.configure(state="disabled")
        self.btn_restore.configure(state="disabled")
        self._reset_write_steps()
        self.set_status("gravando NOR...")
        threading.Thread(target=self._write_worker, daemon=True).start()

    def _write_worker(self):
        self._flash_worker(
            self.last_patch.data,
            pre_check_against=self.last_dump,
            pre_check_label="Conferindo se a NOR ainda e a mesma do backup...",
            context="patch",
        )

    def _flash_worker(self, data: bytes, pre_check_against: bytes | None,
                       pre_check_label: str, context: str):
        """Rotina generica de apagar+gravar+verificar, usada tanto pelo patch
        (passo 4) quanto pela restauracao de backup."""
        try:
            with CH341SPI() as spi:
                self.after(0, lambda: self._write_step_start("verify_before", pre_check_label))
                if pre_check_against is not None:
                    current = spi.read_all(
                        EXPECTED_SIZE,
                        progress_cb=lambda d, t: self._write_step_progress_cb("verify_before", d, t),
                    )
                    if current != pre_check_against:
                        self.after(0, lambda: self._write_step_done("verify_before", ok=False))
                        self.after(0, self._write_aborted_changed)
                        return
                self.after(0, lambda: self._write_step_done("verify_before"))

                self.after(0, lambda: self._write_step_start(
                    "erase", "Apagando NOR (pode levar ate 1-2 minutos)..."))
                spi.erase_chip()
                self.after(0, lambda: self._write_step_done("erase"))

                self.after(0, lambda: self._write_step_start(
                    "write", "Gravando NOR..."))
                spi.write_all(
                    data,
                    progress_cb=lambda d, t: self._write_step_progress_cb("write", d, t),
                )
                self.after(0, lambda: self._write_step_done("write"))

                self.after(0, lambda: self._write_step_start(
                    "verify_after", "Lendo a NOR gravada e verificando se bate com o esperado..."))
                verify = spi.read_all(
                    EXPECTED_SIZE,
                    progress_cb=lambda d, t: self._write_step_progress_cb("verify_after", d, t),
                )

            equal, n_diff, first_offsets = compare_dumps(verify, data)
            self.after(0, lambda: self._write_step_done("verify_after", ok=equal))
            self.after(0, lambda: self._write_done(equal, n_diff, first_offsets, context=context))
        except CH341Error as e:
            err_msg = str(e)
            self.after(0, lambda: self._write_failed(err_msg))

    def _write_aborted_changed(self):
        self.set_status("gravacao cancelada -- NOR mudou desde a leitura")
        self.log(
            "ABORTADO: a NOR conectada agora e diferente da que foi lida no "
            "passo 2. Se voce trocou o chip no soquete, refaca a leitura "
            "(passo 2) antes de gravar.", "error"
        )
        messagebox.showerror(
            "Gravacao cancelada",
            "A NOR conectada mudou desde a ultima leitura. Refaca o passo 2 "
            "antes de gravar."
        )
        self._reset_buttons_after_write()

    def _write_done(self, equal: bool, n_diff: int, first_offsets: list[int], context: str = "patch"):
        is_restore = context == "restore"
        verb = "RESTAURACAO" if is_restore else "GRAVACAO"
        reference = "o backup selecionado" if is_restore else "o patch pretendido"
        if equal:
            self._show_stage("write_success")
            self.set_status(f"{verb} CONCLUIDA E VERIFICADA")
            self.log("=" * 60, "muted")
            self.log(f"{verb} CONCLUIDA -- a NOR gravada bate 100% com {reference}.", "ok")
            self.log("Teste a placa agora.", "ok")
            if self.last_backup_path is not None:
                self.log(f"Backup desta sessao, se precisar: {self.last_backup_path}", "muted")
            self.log("=" * 60, "muted")
            messagebox.showinfo(f"{verb.capitalize()} concluida",
                                 f"{verb.capitalize()} concluida e verificada com sucesso.\nTeste a placa agora.")
        else:
            self.set_status(f"ERRO: {verb.lower()} nao bateu na verificacao")
            offs = ", ".join(f"0x{o:X}" for o in first_offsets)
            self.log(
                f"ERRO: a NOR gravada NAO bate com {reference} em "
                f"{n_diff} byte(s). Primeiros offsets: {offs}", "error"
            )
            if self.last_backup_path is not None:
                self.log(f"RESTAURE O BACKUP imediatamente: {self.last_backup_path}", "error")
            messagebox.showerror(
                "Falha na verificacao",
                "A operacao nao bateu na verificacao. Restaure um backup valido "
                "imediatamente (botao \"Restaurar backup de arquivo...\")."
            )
        self._reset_buttons_after_write()

    def _write_failed(self, err: str):
        for step in self.write_steps.values():
            step["bar"].stop()
        self.set_status("falha na gravacao")
        self.log(f"ERRO DURANTE A GRAVACAO: {err}", "error")
        if self.last_backup_path is not None:
            self.log(f"Se a NOR ficou incompleta, restaure o backup: {self.last_backup_path}", "error")
        messagebox.showerror("Erro na gravacao", f"{err}\n\nRestaure um backup valido se necessario.")
        self._reset_buttons_after_write()

    def _reset_buttons_after_write(self):
        self.btn_detect.configure(state="normal")
        self.btn_read.configure(state="normal")
        self.btn_preview.configure(state="normal")
        self.btn_write.configure(state="normal")
        self.btn_restore.configure(state="normal")

    # -- Restaurar backup de arquivo -----------------------------------------
    def on_restore_backup(self):
        BACKUP_DIR.mkdir(parents=True, exist_ok=True)
        path_str = filedialog.askopenfilename(
            title="Selecione o arquivo de backup (.bin) para restaurar",
            initialdir=str(BACKUP_DIR),
            filetypes=[("Backup NOR", "*.bin"), ("Todos os arquivos", "*.*")],
        )
        if not path_str:
            return
        path = pathlib.Path(path_str)
        data = path.read_bytes()
        if len(data) != EXPECTED_SIZE:
            messagebox.showerror(
                "Arquivo invalido",
                f"O arquivo selecionado tem {len(data)} bytes, mas o esperado "
                f"e {EXPECTED_SIZE} bytes (2 MB). Escolha outro arquivo."
            )
            return

        self._show_stage("writing")
        proceed = messagebox.askyesno(
            "Confirmar restauracao",
            f"Isto vai APAGAR e REGRAVAR a NOR inteira com o conteudo de:\n\n"
            f"{path}\n\n"
            "Use isto SOMENTE em placa de bancada/teste, nunca em placa de "
            "cliente, a menos que tenha certeza de que esse backup pertence "
            "exatamente a essa placa.\n\nTem certeza que quer continuar?",
            icon="warning",
        )
        if not proceed:
            self._show_stage("write_cancelled")
            self.log("Restauracao cancelada pelo usuario (respondeu Nao na confirmacao).", "warn")
            return

        typed = simpledialog.askstring(
            "Confirmacao final",
            f"Digite {CONFIRM_PHRASE} para confirmar a restauracao:"
        )
        if typed != CONFIRM_PHRASE:
            self._show_stage("write_cancelled")
            self.log("Restauracao cancelada (confirmacao nao digitada corretamente).", "warn")
            return

        self._show_stage("writing_active")
        self.btn_detect.configure(state="disabled")
        self.btn_read.configure(state="disabled")
        self.btn_preview.configure(state="disabled")
        self.btn_write.configure(state="disabled")
        self.btn_restore.configure(state="disabled")
        self._reset_write_steps()
        self.set_status("restaurando backup...")
        self.log("=" * 60, "muted")
        self.log(f"RESTAURANDO BACKUP a partir de: {path}", "info")
        threading.Thread(target=self._restore_worker, args=(data,), daemon=True).start()

    def _restore_worker(self, data: bytes):
        self._flash_worker(
            data,
            pre_check_against=None,
            pre_check_label="Preparando restauracao do backup selecionado...",
            context="restore",
        )


if __name__ == "__main__":
    app = App()
    app.mainloop()

"""
Leitura UART (serial) de placas PS5 via adaptador USB-serial ligado nos
pinos de debug da placa.

*** IMPORTANTE ***
Este modulo so CAPTURA o texto bruto que sai da porta serial -- ele NAO
interpreta nem traduz codigos de erro. A ideia e salvar esse log e comparar
com tabelas de codigos de erro conhecidas (ou mandar pra quem manja) pra
chegar a um diagnostico. Nao inventamos significado de codigo nenhum aqui.

Baud rate: 115200 e o valor mais comum em portas de debug UART em geral,
usado como padrao, mas confirme o valor certo com quem ja mexeu nesse tipo
de leitura antes de descartar outros valores se nao vier nada legivel.

Nivel de tensao: a maioria dos adaptadores USB-serial baratos trabalha em
5V ou e selecionavel. Debug UART de eletronicos embarcados costuma ser
3.3V TTL -- confirme a tensao do adaptador antes de conectar, pra nao
arriscar danificar a placa.
"""

from __future__ import annotations

import threading
import time
from typing import Callable

import serial
import serial.tools.list_ports

from i18n import t

DEFAULT_BAUDRATE = 115200
COMMON_BAUDRATES = [9600, 19200, 38400, 57600, 115200, 230400, 460800, 921600]

# Quantidade de slots de log de erro consultados por "errlog N" (0 a 10,
# igual ao PS5 NOR Modifier do TheCod3r -- unica fonte aberta que achamos
# com esse protocolo implementado e funcionando de verdade).
ERRLOG_SLOT_COUNT = 11


def checksum_command(cmd: str) -> str:
    """Formata um comando UART com o checksum que o firmware de debug espera:
    soma dos codigos ASCII do comando & 0xFF, em hex maiusculo, no formato
    "comando:XX". Protocolo conferido contra o codigo-fonte do PS5 NOR
    Modifier (TheCod3r/PS5NorModifier) -- usado por "errlog N" (consulta o
    slot N do log de erros) e "errlog clear" (apaga o log). Ver NOTES.md:
    ainda nao testado com hardware real neste projeto.
    """
    total = sum(ord(c) for c in cmd) & 0xFF
    return f"{cmd}:{total:02X}"


class UartError(Exception):
    pass


def list_ports() -> list[str]:
    return [p.device for p in serial.tools.list_ports.comports()]


class UartReader:
    """Le uma porta serial em uma thread de fundo e entrega linhas de texto
    via callback, ate ser parado com close()."""

    def __init__(self, port: str, baudrate: int = DEFAULT_BAUDRATE):
        self.port = port
        self.baudrate = baudrate
        self._ser: serial.Serial | None = None
        self._thread: threading.Thread | None = None
        self._stop_flag = threading.Event()

    def open(self):
        try:
            self._ser = serial.Serial(self.port, self.baudrate, timeout=0.2)
        except serial.SerialException as e:
            raise UartError(t("backend.uart.open_fail", port=self.port, detail=e)) from e

    def start(self, on_line: Callable[[str], None], on_error: Callable[[str], None] | None = None):
        """Inicia a leitura em background.
        on_line(texto) e chamado pra cada linha recebida (sem o \\n final).
        on_error(msg) e chamado se a porta cair/der erro durante a leitura.
        """
        self._stop_flag.clear()
        self._thread = threading.Thread(target=self._run, args=(on_line, on_error), daemon=True)
        self._thread.start()

    def _run(self, on_line, on_error):
        buf = bytearray()
        try:
            while not self._stop_flag.is_set():
                chunk = self._ser.read(256)
                if chunk:
                    buf.extend(chunk)
                    while b"\n" in buf:
                        line, _, rest = buf.partition(b"\n")
                        buf = bytearray(rest)
                        text = line.decode("utf-8", errors="replace").rstrip("\r")
                        on_line(text)
                else:
                    time.sleep(0.01)
        except serial.SerialException as e:
            if on_error and not self._stop_flag.is_set():
                on_error(str(e))

    def write(self, data: bytes):
        if self._ser is not None and self._ser.is_open:
            self._ser.write(data)

    def close(self):
        self._stop_flag.set()
        if self._thread is not None:
            self._thread.join(timeout=2)
            self._thread = None
        if self._ser is not None:
            try:
                self._ser.close()
            except Exception:
                pass
            self._ser = None

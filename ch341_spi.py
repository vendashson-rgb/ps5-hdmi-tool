"""
Camada de comunicacao com o leitor CH341A via CH341DLL.DLL (flash SPI).

*** ATENCAO ***
Este modulo ainda NAO foi testado contra o hardware real. As assinaturas de
funcao usadas aqui (CH341OpenDevice, CH341CloseDevice, CH341SetStream,
CH341StreamSPI4) seguem a interface publica da CH341DLL.DLL tal como usada
por outras ferramentas de gravacao de EEPROM/NOR baseadas nesse mesmo chip
(ex.: AsProgrammer, open source). E a mesma DLL que ja vem junto do
NeoProgrammer (Neoprogrammer/CH341DLL.DLL).

Antes de usar em qualquer placa real:
  1. Rodar com o leitor conectado e SEM nenhuma NOR no soquete, so pra
     confirmar que open()/close() funcionam sem travar.
  2. Rodar read_jedec_id() com uma NOR conhecida (ex.: W25Q16JV) e conferir
     se o ID bate com o esperado (EF 40 15 para a W25Q16JV) antes de
     confiar em qualquer leitura/gravacao de dados.

Se alguma chamada falhar ou o ID vier errado, me mandar a mensagem de erro
exata -- provavelmente vou precisar ajustar os nomes/assinaturas das funcoes
pra essa versao especifica da DLL.
"""

from __future__ import annotations

import ctypes
import os
import sys
import time
from ctypes import wintypes

# Quando rodando como .exe gerado pelo PyInstaller (--onefile), os arquivos
# empacotados (como drives/CH341DLL.dll) ficam numa pasta temporaria
# (sys._MEIPASS), nao ao lado deste arquivo .py.
_BUNDLE_DIR = getattr(sys, "_MEIPASS", os.path.dirname(__file__))

DLL_CANDIDATES = [
    "CH341DLL.dll",
    os.path.join(_BUNDLE_DIR, "drives", "CH341DLL.dll"),
    os.path.join(_BUNDLE_DIR, "CH341DLL.dll"),  # compatibilidade com instalacoes antigas
]

# Comandos padrao de flash SPI (JEDEC) -- isso e universal, nao depende da DLL.
CMD_WRITE_ENABLE = 0x06
CMD_WRITE_DISABLE = 0x04
CMD_READ_STATUS = 0x05
CMD_WRITE_STATUS = 0x01
CMD_READ_DATA = 0x03
CMD_PAGE_PROGRAM = 0x02
CMD_SECTOR_ERASE_4K = 0x20
CMD_CHIP_ERASE = 0xC7
CMD_JEDEC_ID = 0x9F

PAGE_SIZE = 256
SECTOR_SIZE = 4096
READ_CHUNK = 2048  # confirmado com hardware real: 4096 falha, 2048 funciona de forma confiavel

STATUS_BUSY_BIT = 0x01


class CH341Error(Exception):
    pass


class CH341SPI:
    def __init__(self, device_index: int = 0):
        self._dll = None
        self._index = device_index
        self._open = False
        self._load_dll()

    def _load_dll(self):
        last_err = None
        for candidate in DLL_CANDIDATES:
            try:
                self._dll = ctypes.WinDLL(candidate)
                self._declare_signatures()
                return
            except OSError as e:
                last_err = e
                if getattr(e, "winerror", None) == 193:
                    raise CH341Error(
                        "CH341DLL.dll e de 32 bits, mas este Python e de 64 bits "
                        "(Windows nao deixa misturar). Rode este programa com um "
                        "Python de 32 bits -- veja o README.md, secao "
                        "'Problema de 32 bits x 64 bits'."
                    ) from e
        raise CH341Error(
            "Nao foi possivel carregar CH341DLL.dll. Verifique se o driver do "
            "CH341A esta instalado e se o arquivo CH341DLL.dll esta na mesma "
            f"pasta do programa. Detalhe: {last_err}"
        )

    def _declare_signatures(self):
        dll = self._dll
        # bool CH341OpenDevice(ULONG iIndex) -- retorna handle (>=0) ou -1
        dll.CH341OpenDevice.argtypes = [wintypes.ULONG]
        dll.CH341OpenDevice.restype = ctypes.c_long
        # void CH341CloseDevice(ULONG iIndex)
        dll.CH341CloseDevice.argtypes = [wintypes.ULONG]
        dll.CH341CloseDevice.restype = None
        # bool CH341SetStream(ULONG iIndex, ULONG iMode)
        dll.CH341SetStream.argtypes = [wintypes.ULONG, wintypes.ULONG]
        dll.CH341SetStream.restype = wintypes.BOOL
        # bool CH341StreamSPI4(ULONG iIndex, ULONG iChipSelect, ULONG iLength, PVOID ioBuffer)
        dll.CH341StreamSPI4.argtypes = [
            wintypes.ULONG, wintypes.ULONG, wintypes.ULONG, ctypes.c_void_p
        ]
        dll.CH341StreamSPI4.restype = wintypes.BOOL

    def open(self):
        handle = self._dll.CH341OpenDevice(self._index)
        if handle == -1 or handle is None:
            raise CH341Error(
                "Leitor CH341A nao encontrado. Confira se esta conectado na "
                "USB e se o driver aparece no Gerenciador de Dispositivos."
            )
        # iMode: 0x81 costuma ser "SPI modo 0, MSB first, clock alto" nas
        # ferramentas que usam essa DLL -- PRECISA confirmar com hardware real.
        ok = self._dll.CH341SetStream(self._index, 0x81)
        if not ok:
            raise CH341Error("Falha ao configurar o modo SPI no leitor CH341A.")
        self._open = True

    def close(self):
        if self._open:
            self._dll.CH341CloseDevice(self._index)
            self._open = False

    def __enter__(self):
        self.open()
        return self

    def __exit__(self, exc_type, exc, tb):
        self.close()

    def _transfer(self, out_bytes: bytes, chip_select: int = 0x80) -> bytes:
        """Transferencia SPI full-duplex: envia out_bytes, recebe mesma quantidade de bytes."""
        buf = ctypes.create_string_buffer(out_bytes, len(out_bytes))
        ok = self._dll.CH341StreamSPI4(self._index, chip_select, len(out_bytes), buf)
        if not ok:
            raise CH341Error("Falha na transferencia SPI com o leitor CH341A.")
        return buf.raw[:len(out_bytes)]

    def read_jedec_id(self) -> bytes:
        resp = self._transfer(bytes([CMD_JEDEC_ID, 0, 0, 0]))
        return resp[1:4]

    def read_status(self) -> int:
        resp = self._transfer(bytes([CMD_READ_STATUS, 0]))
        return resp[1]

    def wait_ready(self, timeout_s: float = 10.0):
        start = time.time()
        while time.time() - start < timeout_s:
            if (self.read_status() & STATUS_BUSY_BIT) == 0:
                return
            time.sleep(0.01)
        raise CH341Error("Timeout esperando a NOR ficar pronta (status BUSY nao caiu).")

    def read_all(self, size: int, progress_cb=None) -> bytes:
        out = bytearray()
        addr = 0
        while addr < size:
            chunk_len = min(READ_CHUNK, size - addr)
            cmd = bytes([
                CMD_READ_DATA,
                (addr >> 16) & 0xFF,
                (addr >> 8) & 0xFF,
                addr & 0xFF,
            ]) + bytes(chunk_len)
            resp = self._transfer(cmd)
            out.extend(resp[4:])
            addr += chunk_len
            if progress_cb:
                progress_cb(addr, size)
        return bytes(out)

    def write_enable(self):
        self._transfer(bytes([CMD_WRITE_ENABLE]))

    def erase_chip(self):
        self.write_enable()
        self._transfer(bytes([CMD_CHIP_ERASE]))
        self.wait_ready(timeout_s=120.0)

    def write_all(self, data: bytes, progress_cb=None):
        """Grava via Page Program (256 bytes por pagina). Chamador deve ter apagado antes."""
        addr = 0
        size = len(data)
        while addr < size:
            page_len = min(PAGE_SIZE, size - addr)
            self.write_enable()
            cmd = bytes([
                CMD_PAGE_PROGRAM,
                (addr >> 16) & 0xFF,
                (addr >> 8) & 0xFF,
                addr & 0xFF,
            ]) + data[addr:addr + page_len]
            self._transfer(cmd)
            self.wait_ready()
            addr += page_len
            if progress_cb:
                progress_cb(addr, size)

"""
Leitura e teste de controle DualSense (PS5) via HID bruto -- nativo, sem
precisar de internet nem de navegador (inspirado no dualshock-tools.github.io,
reimplementado aqui em Python puro com a biblioteca `hid`).

*** NIVEL DE CONFIANCA DOS CAMPOS ***
- Analogicos (sticks, L2/R2), botoes de face, D-pad, L1/R1/L3/R3,
  Create/Options/PS/touchpad-click/mute: layout do report USB (report ID
  0x01) documentado de forma consistente por varios projetos open-source
  (ex.: pydualsense) -- confianca ALTA, mas ainda assim NAO testado com um
  controle real neste projeto.
- Touchpad (posicao dos dedos) e bateria: offsets tambem vindos da mesma
  fonte, porem mais sensiveis a pequenas diferencas de firmware -- marcar
  como EXPERIMENTAL na interface.
- Vibracao e cor da barra de luz (output report 0x02, via cabo USB):
  offsets conferidos diretamente contra o codigo-fonte real do projeto
  open-source pydualsense (github.com/flok/pydualsense) em 2026-10 --
  confianca ALTA, mas ainda NAO testado com um controle real neste projeto.
  Por Bluetooth o output report usa offsets diferentes (nao implementado
  ainda, so a leitura de entrada funciona por BT).

Suporta cabo USB (report 0x01) e, de forma experimental, Bluetooth
(report 0x31, com 1 byte de deslocamento). USB e o modo recomendado pra
comecar a testar.
"""

from __future__ import annotations

import threading
import time
from dataclasses import dataclass, field

import hid

from i18n import t

SONY_VENDOR_ID = 0x054C
DUALSENSE_PRODUCT_ID = 0x0CE6
DUALSENSE_EDGE_PRODUCT_ID = 0x0DF2
KNOWN_PRODUCT_IDS = {
    DUALSENSE_PRODUCT_ID: "DualSense",
    DUALSENSE_EDGE_PRODUCT_ID: "DualSense Edge",
}

_BUTTONS_1 = {"square": 0x10, "cross": 0x20, "circle": 0x40, "triangle": 0x80}
_DPAD_MASK = 0x0F
_DPAD_DIRECTIONS = {
    0: "cima", 1: "cima-direita", 2: "direita", 3: "baixo-direita",
    4: "baixo", 5: "baixo-esquerda", 6: "esquerda", 7: "cima-esquerda",
    8: "solto",
}
_BUTTONS_2 = {
    "l1": 0x01, "r1": 0x02, "l2_digital": 0x04, "r2_digital": 0x08,
    "create": 0x10, "options": 0x20, "l3": 0x40, "r3": 0x80,
}
_BUTTONS_3 = {"ps": 0x01, "touchpad_click": 0x02, "mute": 0x04}


class DualSenseError(Exception):
    pass


@dataclass
class DualSenseState:
    connected: bool = False
    connection: str = "usb"  # "usb" ou "bluetooth"

    left_stick_x: int = 128
    left_stick_y: int = 128
    right_stick_x: int = 128
    right_stick_y: int = 128
    l2_analog: int = 0
    r2_analog: int = 0

    buttons: dict = field(default_factory=dict)
    dpad: str = "solto"

    # Campos experimentais -- ver aviso no topo do arquivo
    touch1_active: bool = False
    touch1_x: int = 0
    touch1_y: int = 0
    touch2_active: bool = False
    touch2_x: int = 0
    touch2_y: int = 0
    battery_percent: int | None = None
    battery_charging: bool | None = None


def list_devices() -> list[dict]:
    """Lista os dispositivos HID da Sony reconhecidos como DualSense/Edge."""
    return [d for d in hid.enumerate(SONY_VENDOR_ID, 0) if d["product_id"] in KNOWN_PRODUCT_IDS]


class DualSenseController:
    def __init__(self, path: bytes):
        self._path = path
        self._dev: hid.device | None = None
        self._thread: threading.Thread | None = None
        self._stop_flag = threading.Event()
        self.state = DualSenseState()

    def open(self):
        try:
            dev = hid.device()
            dev.open_path(self._path)
        except OSError as e:
            raise DualSenseError(t("backend.ds.open_fail", detail=e)) from e
        self._dev = dev

    def start(self):
        """Inicia a leitura continua em background, atualizando self.state.
        A interface deve ler self.state periodicamente (ex.: via self.after
        no Tkinter) -- esta thread NAO mexe em widgets."""
        self._stop_flag.clear()
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def _run(self):
        while not self._stop_flag.is_set():
            try:
                data = self._dev.read(128, timeout_ms=100)
            except OSError:
                break
            if data:
                self._parse_report(bytes(data))
            else:
                time.sleep(0.005)

    def _parse_report(self, data: bytes):
        if not data:
            return
        report_id = data[0]
        if report_id == 0x01 and len(data) >= 11:
            self.state.connection = "usb"
            self._parse_core(data, base=1)
        elif report_id == 0x31 and len(data) >= 12:
            self.state.connection = "bluetooth"
            self._parse_core(data, base=2)
        # outros report IDs (feature reports, etc.) sao ignorados

    def _parse_core(self, data: bytes, base: int):
        s = self.state
        try:
            s.left_stick_x = data[base + 0]
            s.left_stick_y = data[base + 1]
            s.right_stick_x = data[base + 2]
            s.right_stick_y = data[base + 3]
            s.l2_analog = data[base + 4]
            s.r2_analog = data[base + 5]

            b1 = data[base + 7]
            b2 = data[base + 8]
            b3 = data[base + 9]

            s.dpad = _DPAD_DIRECTIONS.get(b1 & _DPAD_MASK, "?")
            buttons = {}
            for name, mask in _BUTTONS_1.items():
                buttons[name] = bool(b1 & mask)
            for name, mask in _BUTTONS_2.items():
                buttons[name] = bool(b2 & mask)
            for name, mask in _BUTTONS_3.items():
                buttons[name] = bool(b3 & mask)
            s.buttons = buttons
            s.connected = True
        except IndexError:
            return

        # -- Campos experimentais, nao validados com hardware real ainda --
        try:
            touch_off = base + 32
            t1 = data[touch_off:touch_off + 4]
            t2 = data[touch_off + 4:touch_off + 8]
            if len(t1) == 4:
                s.touch1_active = not bool(t1[0] & 0x80)
                s.touch1_x = t1[1] | ((t1[2] & 0x0F) << 8)
                s.touch1_y = (t1[2] >> 4) | (t1[3] << 4)
            if len(t2) == 4:
                s.touch2_active = not bool(t2[0] & 0x80)
                s.touch2_x = t2[1] | ((t2[2] & 0x0F) << 8)
                s.touch2_y = (t2[2] >> 4) | (t2[3] << 4)

            battery_byte = data[base + 52]
            s.battery_percent = min(100, (battery_byte & 0x0F) * 10 + 5)
            s.battery_charging = bool(battery_byte & 0x10)
        except IndexError:
            pass

    def set_rumble_and_light(self, motor_left: int, motor_right: int,
                              led_r: int, led_g: int, led_b: int):
        """Layout confirmado contra o codigo-fonte real do projeto
        open-source pydualsense (github.com/flok/pydualsense) -- motores em
        [3]/[4] e cor da barra de luz em [45]/[46]/[47] (via cabo USB)."""
        if self._dev is None:
            return
        buf = bytearray(48)
        buf[0] = 0x02
        buf[1] = 0xFF  # valid_flag0 -- habilita controle de vibracao
        buf[2] = 0x01 | 0x02 | 0x04 | 0x10 | 0x40  # valid_flag1 -- habilita mic led/cor/etc
        buf[3] = max(0, min(255, motor_right))
        buf[4] = max(0, min(255, motor_left))
        buf[45] = max(0, min(255, led_r))
        buf[46] = max(0, min(255, led_g))
        buf[47] = max(0, min(255, led_b))
        try:
            self._dev.write(bytes(buf))
        except OSError as e:
            raise DualSenseError(t("backend.ds.send_fail", detail=e)) from e

    # -- Calibracao do analogico (feature reports) ---------------------------
    # Sequencia de comandos (report IDs 0x80/0x81 para NVS lock/unlock, 0x82
    # para pedir a calibracao, 0x83 para a resposta) conferida diretamente
    # contra o codigo-fonte real do projeto open-source dualshock-tools
    # (github.com/dualshock-tools/dualshock-tools.github.io, MIT) em
    # 2026-10. A calibracao em si (media das amostras de ADC) e calculada
    # inteiramente pelo firmware do controle -- nos so mandamos os comandos
    # de "comecar"/"amostrar"/"terminar", nunca valores numericos de
    # calibracao. So fica permanente apos chamar flash_changes().

    @staticmethod
    def _feature_contains(data, expected_u32: int, search_len: int = 8) -> bool:
        """Verifica se os 4 bytes esperados (big-endian) aparecem dentro dos
        primeiros `search_len` bytes da resposta. Feito assim (em vez de um
        indice fixo) porque a posicao exata do report ID dentro do buffer
        retornado pela hidapi pode variar um byte dependendo da plataforma --
        ver o bug corrigido no output report de luz/vibracao."""
        if not data:
            return False
        target = expected_u32.to_bytes(4, "big")
        return target in bytes(data[:search_len])

    def _require_dev(self):
        if self._dev is None:
            raise DualSenseError(t("backend.ds.not_connected"))

    def nvs_unlock(self):
        self._require_dev()
        try:
            self._dev.send_feature_report(bytes([0x80, 3, 2, 101, 50, 64, 12]))
            self._dev.get_feature_report(0x81, 64)
        except OSError as e:
            raise DualSenseError(t("backend.ds.unlock_fail", detail=e)) from e

    def nvs_lock(self):
        self._require_dev()
        try:
            self._dev.send_feature_report(bytes([0x80, 3, 1]))
            self._dev.get_feature_report(0x81, 64)
        except OSError as e:
            raise DualSenseError(t("backend.ds.lock_fail", detail=e)) from e

    def flash_changes(self):
        """Confirma (grava permanentemente) as mudancas de calibracao feitas
        nesta sessao -- equivalente ao botao 'Salvar alteracoes
        permanentemente' do dualshock-tools."""
        self.nvs_unlock()
        self.nvs_lock()

    def calibrate_sticks_center(self):
        """Recalcula o centro dos dois analogicos. O usuario deve soltar os
        sticks (deixa-los parados) antes de chamar isto."""
        self._require_dev()
        try:
            self._dev.send_feature_report(bytes([0x82, 1, 1, 1]))
            resp = self._dev.get_feature_report(0x83, 64)
            if not self._feature_contains(resp, 0x83010101):
                raise DualSenseError(t("backend.ds.center_start_unexpected"))

            for _ in range(5):
                time.sleep(0.1)
                self._dev.send_feature_report(bytes([0x82, 3, 1, 1]))
                resp = self._dev.get_feature_report(0x83, 64)
                if not self._feature_contains(resp, 0x83010101):
                    raise DualSenseError(t("backend.ds.center_sample_fail"))

            self._dev.send_feature_report(bytes([0x82, 2, 1, 1]))
            resp = self._dev.get_feature_report(0x83, 64)
            if not self._feature_contains(resp, 0x83010102):
                raise DualSenseError(t("backend.ds.center_finish_fail"))
        except OSError as e:
            raise DualSenseError(t("backend.ds.comm_error_calib", detail=e)) from e

    def calibrate_range_begin(self):
        """Inicia a calibracao de alcance -- o usuario deve girar os dois
        analogicos em circulos completos repetidas vezes logo em seguida."""
        self._require_dev()
        try:
            self._dev.send_feature_report(bytes([0x82, 1, 1, 2]))
            resp = self._dev.get_feature_report(0x83, 64)
            if not self._feature_contains(resp, 0x83010201):
                raise DualSenseError(t("backend.ds.range_start_unexpected"))
        except OSError as e:
            raise DualSenseError(t("backend.ds.comm_error_range_start", detail=e)) from e

    def calibrate_range_end(self):
        self._require_dev()
        try:
            self._dev.send_feature_report(bytes([0x82, 2, 1, 2]))
            resp = self._dev.get_feature_report(0x83, 64)
            if not self._feature_contains(resp, 0x83010202):
                raise DualSenseError(t("backend.ds.range_finish_fail"))
        except OSError as e:
            raise DualSenseError(t("backend.ds.comm_error_range_finish", detail=e)) from e

    def close(self):
        self._stop_flag.set()
        if self._thread is not None:
            self._thread.join(timeout=1)
            self._thread = None
        if self._dev is not None:
            try:
                self._dev.close()
            except Exception:
                pass
            self._dev = None

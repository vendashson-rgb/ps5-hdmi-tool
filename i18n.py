"""
Internacionalizacao (PT-BR / EN / ES) do PS5 HDMI Tool.

Uso:
    from i18n import t, set_language, get_language

    t("hw.btn_detect")                  # string simples
    t("file.log.loaded", path=path)     # string com placeholders ({path})
    set_language("en")                  # troca o idioma ativo (afeta t() dali pra frente)

Todas as strings do programa (gui.py e os modulos de backend que levantam
mensagens de erro mostradas ao usuario) devem passar por t(), nunca texto
fixo, para que o seletor de idioma (bandeiras) funcione em 100% da interface.
"""

from __future__ import annotations

DEFAULT_LANG = "pt"
LANGUAGES = ("pt", "en", "es")

_current_lang = DEFAULT_LANG
_listeners: list = []


def get_language() -> str:
    return _current_lang


def set_language(lang: str) -> None:
    global _current_lang
    if lang not in LANGUAGES:
        raise ValueError(f"Idioma nao suportado: {lang!r}")
    _current_lang = lang
    for cb in list(_listeners):
        cb()


def on_language_change(callback) -> None:
    """Registra uma funcao (sem argumentos) chamada toda vez que o idioma mudar."""
    _listeners.append(callback)


def t(key: str, **kwargs) -> str:
    entry = STRINGS.get(key)
    if entry is None:
        return key
    text = entry.get(_current_lang) or entry.get(DEFAULT_LANG) or key
    if kwargs:
        try:
            return text.format(**kwargs)
        except (KeyError, IndexError):
            return text
    return text


STRINGS: dict[str, dict[str, str]] = {
    # -- App / cabecalho -----------------------------------------------------
    "app.title": {"pt": "PS5 HDMI Tool", "en": "PS5 HDMI Tool", "es": "PS5 HDMI Tool"},
    "app.lang_tooltip": {"pt": "Idioma", "en": "Language", "es": "Idioma"},

    # -- Abas ------------------------------------------------------------------
    "tab.hardware": {"pt": "Leitor CH341A (hardware)", "en": "CH341A Reader (hardware)", "es": "Lector CH341A (hardware)"},
    "tab.file": {"pt": "Analisar arquivo (.bin)", "en": "Analyze file (.bin)", "es": "Analizar archivo (.bin)"},
    "tab.uart": {"pt": "Leitor UART", "en": "UART Reader", "es": "Lector UART"},
    "tab.controller": {"pt": "Teste de Controle", "en": "Controller Test", "es": "Prueba de Control"},

    # -- Textos/termos comuns ---------------------------------------------------
    "common.browse": {"pt": "Procurar...", "en": "Browse...", "es": "Buscar..."},
    "common.btn_preview": {"pt": "Pre-visualizar alteracoes", "en": "Preview changes", "es": "Previsualizar cambios"},
    "common.warnings_label": {"pt": "AVISOS:", "en": "WARNINGS:", "es": "AVISOS:"},
    "common.size_ok_suffix": {"pt": " (OK)", "en": " (OK)", "es": " (OK)"},
    "common.size_bad_suffix": {"pt": " *** TAMANHO INESPERADO ***", "en": " *** UNEXPECTED SIZE ***", "es": " *** TAMANO INESPERADO ***"},
    "common.verb_write": {"pt": "GRAVACAO", "en": "WRITE", "es": "GRABACION"},
    "common.verb_restore": {"pt": "RESTAURACAO", "en": "RESTORE", "es": "RESTAURACION"},
    "common.err_open_file_title": {"pt": "Erro ao abrir arquivo", "en": "Error opening file", "es": "Error al abrir archivo"},
    "common.file_nor_filter": {"pt": "Arquivo NOR", "en": "NOR file", "es": "Archivo NOR"},
    "common.file_all_filter": {"pt": "Todos os arquivos", "en": "All files", "es": "Todos los archivos"},

    # -- Aba hardware: topo/botoes ----------------------------------------------
    "hw.btn_detect": {"pt": "1. Detectar leitor CH341A", "en": "1. Detect CH341A reader", "es": "1. Detectar lector CH341A"},
    "hw.btn_read": {"pt": "2. Ler NOR (2x + comparar + backup)", "en": "2. Read NOR (2x + compare + backup)", "es": "2. Leer NOR (2x + comparar + backup)"},
    "hw.status_prefix": {"pt": "Status: {msg}", "en": "Status: {msg}", "es": "Estado: {msg}"},
    "hw.backup_badge_none": {"pt": "Backup: nenhum ainda", "en": "Backup: none yet", "es": "Backup: ninguno aun"},
    "hw.backup_badge_reading": {"pt": "lendo NOR...", "en": "reading NOR...", "es": "leyendo NOR..."},
    "hw.backup_badge_failed": {"pt": "leitura falhou -- sem backup", "en": "read failed -- no backup", "es": "lectura fallo -- sin backup"},
    "hw.backup_badge_saved": {"pt": "Backup salvo em: {name}", "en": "Backup saved in: {name}", "es": "Backup guardado en: {name}"},
    "hw.backup_badge_ok_prefix": {"pt": "✓ {text}", "en": "✓ {text}", "es": "✓ {text}"},
    "hw.patch_frame_title": {"pt": "3. Aplicar patch (chip HDMI)", "en": "3. Apply patch (HDMI chip)", "es": "3. Aplicar parche (chip HDMI)"},
    "hw.target_label": {"pt": "Gravar NOR configurada para:", "en": "Write NOR configured for:", "es": "Grabar NOR configurada para:"},
    "hw.btn_write": {"pt": "4. GRAVAR NA NOR", "en": "4. WRITE TO NOR", "es": "4. GRABAR EN LA NOR"},
    "hw.btn_restore": {"pt": "Carregar arquivo .bin para gravar...", "en": "Load .bin file to write...", "es": "Cargar archivo .bin para grabar..."},
    "hw.btn_restore_from_backup": {"pt": "Restaurar NOR a partir de Backup", "en": "Restore NOR from Backup", "es": "Restaurar NOR desde Backup"},
    "hw.progress_frame_title": {"pt": "Progresso da gravacao", "en": "Write progress", "es": "Progreso de la grabacion"},

    # -- Etapas do painel de progresso (texto base do rotulo) -------------------
    "step.verify_before.label": {"pt": "1. Conferindo se a NOR ainda e a mesma do backup...", "en": "1. Checking that the NOR still matches the backup...", "es": "1. Verificando que la NOR siga igual al backup..."},
    "step.erase.label": {"pt": "2. Apagando NOR...", "en": "2. Erasing NOR...", "es": "2. Borrando NOR..."},
    "step.write.label": {"pt": "3. Gravando NOR com o patch...", "en": "3. Writing NOR with patch...", "es": "3. Grabando NOR con el parche..."},
    "step.verify_after.label": {"pt": "4. Lendo e verificando a gravacao...", "en": "4. Reading and verifying the write...", "es": "4. Leyendo y verificando la grabacion..."},
    # -- Mensagens ao vivo durante cada etapa (status bar + log) -----------------
    "step.verify_before.status_patch": {"pt": "Conferindo se a NOR ainda e a mesma do backup...", "en": "Checking that the NOR still matches the backup...", "es": "Verificando que la NOR siga igual al backup..."},
    "step.verify_before.status_restore": {"pt": "Preparando gravacao do arquivo selecionado...", "en": "Preparing to write the selected file...", "es": "Preparando la grabacion del archivo seleccionado..."},
    "step.erase.status": {"pt": "Apagando NOR (pode levar ate 1-2 minutos)...", "en": "Erasing NOR (can take up to 1-2 minutes)...", "es": "Borrando NOR (puede tardar 1-2 minutos)..."},
    "step.write.status": {"pt": "Gravando NOR...", "en": "Writing NOR...", "es": "Grabando NOR..."},
    "step.verify_after.status": {"pt": "Lendo a NOR gravada e verificando se bate com o esperado...", "en": "Reading the written NOR and verifying it matches what's expected...", "es": "Leyendo la NOR grabada y verificando que coincida con lo esperado..."},

    # -- Legendas das animacoes (estagios) ---------------------------------------
    "stage.idle": {"pt": "Aguardando... conecte o leitor e clique em \"1. Detectar leitor\"", "en": "Waiting... connect the reader and click \"1. Detect reader\"", "es": "Esperando... conecte el lector y haga clic en \"1. Detectar lector\""},
    "stage.detecting": {"pt": "Detectando leitor CH341A...", "en": "Detecting CH341A reader...", "es": "Detectando lector CH341A..."},
    "stage.reading": {"pt": "Lendo NOR...", "en": "Reading NOR...", "es": "Leyendo NOR..."},
    "stage.read_success": {"pt": "Leitura concluida com sucesso!", "en": "Read completed successfully!", "es": "¡Lectura completada con exito!"},
    "stage.preview": {"pt": "Preparando pre-visualizacao do patch...", "en": "Preparing patch preview...", "es": "Preparando la previsualizacion del parche..."},
    "stage.write_cancelled": {"pt": "Gravacao cancelada.", "en": "Write cancelled.", "es": "Grabacion cancelada."},
    "stage.writing": {"pt": "Aguardando confirmacao...", "en": "Waiting for confirmation...", "es": "Esperando confirmacion..."},
    "stage.writing_active": {"pt": "Gravando NOR...", "en": "Writing NOR...", "es": "Grabando NOR..."},
    "stage.write_success": {"pt": "Gravacao concluida com sucesso!", "en": "Write completed successfully!", "es": "¡Grabacion completada con exito!"},
    "stage.detect_failed": {"pt": "Leitor CH341A nao encontrado.", "en": "CH341A reader not found.", "es": "Lector CH341A no encontrado."},
    "stage.verifying_file": {"pt": "Verificando se o arquivo e uma NOR de PS5 valida...", "en": "Checking if the file is a valid PS5 NOR...", "es": "Verificando si el archivo es una NOR de PS5 valida..."},

    # -- Status bar (valores passados pra set_status) ---------------------------
    "status.waiting": {"pt": "aguardando", "en": "waiting", "es": "esperando"},
    "status.verifying_file": {"pt": "verificando arquivo...", "en": "checking file...", "es": "verificando archivo..."},
    "status.detecting": {"pt": "detectando leitor...", "en": "detecting reader...", "es": "detectando lector..."},
    "status.reader_detected": {"pt": "leitor detectado", "en": "reader detected", "es": "lector detectado"},
    "status.detect_failed": {"pt": "falha ao detectar leitor", "en": "failed to detect reader", "es": "fallo al detectar el lector"},
    "status.reading_1": {"pt": "lendo NOR (1a leitura)...", "en": "reading NOR (1st read)...", "es": "leyendo NOR (1ra lectura)..."},
    "status.reading_2": {"pt": "lendo NOR (2a leitura, para conferir)...", "en": "reading NOR (2nd read, to verify)...", "es": "leyendo NOR (2da lectura, para verificar)..."},
    "status.read_mismatch": {"pt": "ERRO: as duas leituras nao bateram", "en": "ERROR: the two reads did not match", "es": "ERROR: las dos lecturas no coincidieron"},
    "status.read_success": {"pt": "leitura concluida com sucesso", "en": "read completed successfully", "es": "lectura completada con exito"},
    "status.read_failed": {"pt": "falha na leitura", "en": "read failed", "es": "fallo en la lectura"},
    "status.writing": {"pt": "gravando NOR...", "en": "writing NOR...", "es": "grabando NOR..."},
    "status.backup_before_write": {"pt": "fazendo backup antes de gravar...", "en": "making backup before writing...", "es": "haciendo backup antes de grabar..."},
    "status.file_loaded": {"pt": "arquivo carregado, pronto pra gravar", "en": "file loaded, ready to write", "es": "archivo cargado, listo para grabar"},
    "status.write_aborted_changed": {"pt": "gravacao cancelada -- NOR mudou desde a leitura", "en": "write cancelled -- NOR changed since the read", "es": "grabacion cancelada -- la NOR cambio desde la lectura"},
    "status.done_verified": {"pt": "{verb} CONCLUIDA E VERIFICADA", "en": "{verb} COMPLETED AND VERIFIED", "es": "{verb} COMPLETADA Y VERIFICADA"},
    "status.verify_mismatch": {"pt": "ERRO: {verb} nao bateu na verificacao", "en": "ERROR: {verb} did not match on verification", "es": "ERROR: {verb} no coincidio en la verificacion"},
    "status.write_failed": {"pt": "falha na gravacao", "en": "write failed", "es": "fallo en la grabacion"},
    "status.restoring": {"pt": "gravando arquivo...", "en": "writing file...", "es": "grabando archivo..."},

    # -- Aba hardware: logs -------------------------------------------------------
    "hw.log.reader_connected": {"pt": "Leitor CH341A conectado. JEDEC ID do chip na NOR: {jedec}", "en": "CH341A reader connected. JEDEC ID of the NOR chip: {jedec}", "es": "Lector CH341A conectado. JEDEC ID del chip en la NOR: {jedec}"},
    "hw.log.chip_identified_ok": {"pt": "Chip de flash identificado: {manuf} {model} ({size} bytes) -- e o chip esperado em placas de PS5, ja confirmado neste programa.", "en": "Flash chip identified: {manuf} {model} ({size} bytes) -- this is the expected chip on PS5 boards, already confirmed in this program.", "es": "Chip de flash identificado: {manuf} {model} ({size} bytes) -- es el chip esperado en placas de PS5, ya confirmado en este programa."},
    "hw.log.chip_identified_warn_model": {"pt": "Chip de flash: fabricante {manuf} reconhecido, mas esse modelo especifico ainda nao foi confirmado neste programa (o esperado e a Winbond W25Q16JV, 2 MB). Confira se e o chip certo antes de prosseguir.", "en": "Flash chip: {manuf} manufacturer recognized, but this specific model hasn't been confirmed in this program yet (the expected one is the Winbond W25Q16JV, 2 MB). Check that it's the right chip before proceeding.", "es": "Chip de flash: fabricante {manuf} reconocido, pero este modelo especifico aun no fue confirmado en este programa (el esperado es la Winbond W25Q16JV, 2 MB). Verifique que sea el chip correcto antes de continuar."},
    "hw.log.chip_identified_warn_unknown": {"pt": "Chip de flash NAO reconhecido (fabricante diferente da Winbond esperada nas placas de PS5). Confira se e o chip certo no soquete/clipe antes de prosseguir.", "en": "Flash chip NOT recognized (manufacturer different from the Winbond expected on PS5 boards). Check that it's the right chip in the socket/clip before proceeding.", "es": "Chip de flash NO reconocido (fabricante diferente de la Winbond esperada en placas de PS5). Verifique que sea el chip correcto en el zocalo/clip antes de continuar."},
    "hw.log.error_prefix": {"pt": "ERRO: {err}", "en": "ERROR: {err}", "es": "ERROR: {err}"},
    "hw.err_detect_title": {"pt": "Erro ao detectar leitor", "en": "Error detecting reader", "es": "Error al detectar el lector"},
    "hw.log.read_mismatch": {"pt": "As duas leituras da NOR deram resultados DIFERENTES em {n} byte(s). Primeiros offsets divergentes: {offs}", "en": "The two NOR reads gave DIFFERENT results in {n} byte(s). First diverging offsets: {offs}", "es": "Las dos lecturas de la NOR dieron resultados DIFERENTES en {n} byte(s). Primeros offsets divergentes: {offs}"},
    "hw.log.read_mismatch_warn": {"pt": "NAO prossiga com gravacao. Verifique o contato do soquete/clipe na NOR e leia novamente.", "en": "DO NOT proceed with writing. Check the socket/clip contact on the NOR and read again.", "es": "NO continue con la grabacion. Verifique el contacto del zocalo/clip en la NOR y lea de nuevo."},
    "hw.read_mismatch_title": {"pt": "Leituras inconsistentes", "en": "Inconsistent reads", "es": "Lecturas inconsistentes"},
    "hw.read_mismatch_body": {"pt": "As duas leituras da NOR deram resultados diferentes.\nVerifique o contato do leitor e tente novamente. Nao prossiga com gravacao enquanto isso nao for resolvido.", "en": "The two NOR reads gave different results.\nCheck the reader's contact and try again. Do not proceed with writing until this is resolved.", "es": "Las dos lecturas de la NOR dieron resultados diferentes.\nVerifique el contacto del lector e intente de nuevo. No continue con la grabacion hasta resolver esto."},
    "status.read_invalid": {"pt": "ERRO: NOR corrompida ou inexistente", "en": "ERROR: corrupted or missing NOR", "es": "ERROR: NOR corrupta o inexistente"},
    "hw.read_invalid_title": {"pt": "NOR corrompida ou inexistente", "en": "Corrupted or missing NOR", "es": "NOR corrupta o inexistente"},
    "hw.log.read_invalid_blank": {"pt": "LEITURA REJEITADA: as duas leituras bateram, mas o conteudo e 100% vazio (0xFF). Isso normalmente indica que nao ha NOR no soquete/clipe, ou mau contato -- um PS5 de verdade nao liga com a NOR vazia assim.", "en": "READ REJECTED: both reads matched, but the content is 100% blank (0xFF). This usually means there's no NOR in the socket/clip, or bad contact -- a real PS5 doesn't power on with the NOR blank like this.", "es": "LECTURA RECHAZADA: las dos lecturas coincidieron, pero el contenido es 100% vacio (0xFF). Esto normalmente indica que no hay NOR en el zocalo/clip, o mal contacto -- un PS5 real no enciende con la NOR vacia asi."},
    "hw.read_invalid_body_blank": {"pt": "As duas leituras bateram, mas vieram 100% vazias (0xFF).\n\nIsso normalmente significa que nao ha nenhuma NOR conectada no soquete/clipe, ou que o contato esta ruim -- nao que a placa tenha uma NOR vazia de verdade (um PS5 nao liga assim).\n\nVerifique a conexao do leitor na NOR e tente ler novamente. Se a placa realmente tiver uma NOR fisicamente presente e o problema persistir, pode ser uma falha real do chip.", "en": "Both reads matched, but came back 100% blank (0xFF).\n\nThis usually means there's no NOR actually connected to the socket/clip, or the contact is bad -- not that the board genuinely has a blank NOR (a PS5 doesn't power on like that).\n\nCheck the reader's connection to the NOR and try reading again. If the board really does have a NOR physically present and the problem persists, it may be a genuine chip failure.", "es": "Las dos lecturas coincidieron, pero volvieron 100% vacias (0xFF).\n\nEsto normalmente significa que no hay ninguna NOR conectada al zocalo/clip, o que el contacto esta mal -- no que la placa tenga realmente una NOR vacia (un PS5 no enciende asi).\n\nVerifique la conexion del lector en la NOR e intente leer de nuevo. Si la placa realmente tiene una NOR presente fisicamente y el problema persiste, puede ser una falla real del chip."},
    "hw.log.read_invalid_bad_magic": {"pt": "LEITURA REJEITADA: as duas leituras bateram e tem dado, mas nao tem a assinatura de uma NOR de PS5 no inicio. Pode ser uma NOR corrompida, o chip errado no soquete, ou nao ser uma NOR de PS5.", "en": "READ REJECTED: both reads matched and have data, but don't have a PS5 NOR signature at the start. It may be a corrupted NOR, the wrong chip in the socket, or not a PS5 NOR at all.", "es": "LECTURA RECHAZADA: las dos lecturas coincidieron y tienen datos, pero no tienen la firma de una NOR de PS5 al inicio. Puede ser una NOR corrupta, el chip equivocado en el zocalo, o no ser una NOR de PS5."},
    "hw.read_invalid_body_bad_magic": {"pt": "As duas leituras bateram e tem dado (nao esta vazia), mas nao tem a assinatura de uma NOR de PS5 no inicio do arquivo.\n\nIsso pode ser uma NOR corrompida, o chip errado no soquete, ou um chip que nao e de PS5.\n\nConfira se o chip certo esta no soquete e com bom contato, e tente ler novamente.", "en": "Both reads matched and have data (it's not blank), but don't have a PS5 NOR signature at the start of the file.\n\nThis could be a corrupted NOR, the wrong chip in the socket, or a chip that isn't from a PS5.\n\nCheck that the right chip is in the socket with good contact, and try reading again.", "es": "Las dos lecturas coincidieron y tienen datos (no esta vacia), pero no tienen la firma de una NOR de PS5 al inicio del archivo.\n\nEsto puede ser una NOR corrupta, el chip equivocado en el zocalo, o un chip que no es de PS5.\n\nVerifique que el chip correcto este en el zocalo con buen contacto, e intente leer de nuevo."},
    "hw.log.read_done": {"pt": "LEITURA CONCLUIDA -- as duas leituras bateram byte a byte.", "en": "READ COMPLETE -- both reads matched byte for byte.", "es": "LECTURA COMPLETADA -- las dos lecturas coincidieron byte a byte."},
    "hw.log.dumps_saved": {"pt": "DUMP1.bin e DUMP2.bin salvos em: {path}", "en": "DUMP1.bin and DUMP2.bin saved in: {path}", "es": "DUMP1.bin y DUMP2.bin guardados en: {path}"},
    "hw.log.size": {"pt": "Tamanho do arquivo: {size} bytes{suffix}", "en": "File size: {size} bytes{suffix}", "es": "Tamano del archivo: {size} bytes{suffix}"},
    "hw.log.sha256": {"pt": "SHA-256: {sha}", "en": "SHA-256: {sha}", "es": "SHA-256: {sha}"},
    "hw.log.chip": {"pt": "Chip HDMI detectado: {name} (byte bruto 0x{raw})", "en": "Detected HDMI chip: {name} (raw byte 0x{raw})", "es": "Chip HDMI detectado: {name} (byte bruto 0x{raw})"},
    "hw.log.mac": {"pt": "Endereco MAC: {mac}", "en": "MAC address: {mac}", "es": "Direccion MAC: {mac}"},
    "hw.log.mobo_serial": {"pt": "Identificador da placa-mae: {val}", "en": "Motherboard identifier: {val}", "es": "Identificador de la placa base: {val}"},
    "hw.log.board_serial": {"pt": "Numero de serie do console: {val}", "en": "Console serial number: {val}", "es": "Numero de serie de la consola: {val}"},
    "hw.log.raw_id": {"pt": "Identificador bruto (serie/area adjacente): {val}", "en": "Raw identifier (serial/adjacent area): {val}", "es": "Identificador bruto (serie/area adyacente): {val}"},
    "hw.log.cfi": {"pt": "SKU / modelo do console: {val}", "en": "SKU / console model: {val}", "es": "SKU / modelo de la consola: {val}"},
    "hw.log.wifi_rev": {"pt": "Revisao do modulo Wi-Fi/Bluetooth (EXPERIMENTAL, nao confirmado): {val}", "en": "Wi-Fi/Bluetooth module revision (EXPERIMENTAL, unconfirmed): {val}", "es": "Revision del modulo Wi-Fi/Bluetooth (EXPERIMENTAL, no confirmado): {val}"},
    "hw.log.board_family": {"pt": "Familia da placa: {family} -- leitor de disco: {disc}", "en": "Board family: {family} -- disc drive: {disc}", "es": "Familia de la placa: {family} -- lector de disco: {disc}"},
    "hw.log.region": {"pt": "Regiao: {val}", "en": "Region: {val}", "es": "Region: {val}"},
    "hw.log.wifi_mac": {"pt": "Endereco MAC Wi-Fi: {val}", "en": "Wi-Fi MAC address: {val}", "es": "Direccion MAC Wi-Fi: {val}"},
    "hw.log.fw_current": {"pt": "Firmware atual gravado na NOR: {val}", "en": "Current firmware stored in NOR: {val}", "es": "Firmware actual grabado en la NOR: {val}"},
    "hw.log.emc_version": {"pt": "Firmware do EMC -- ativo (slot {slot}): {active} / backup: {backup}", "en": "EMC firmware -- active (slot {slot}): {active} / backup: {backup}", "es": "Firmware del EMC -- activo (slot {slot}): {active} / backup: {backup}"},
    "hw.err_read_title": {"pt": "Erro na leitura", "en": "Read error", "es": "Error en la lectura"},

    "hw.no_nor_title": {"pt": "Leia a NOR primeiro", "en": "Read the NOR first", "es": "Lea la NOR primero"},
    "hw.no_nor_body": {"pt": "Faca a leitura da NOR (passo 2) antes de pre-visualizar o patch.", "en": "Read the NOR (step 2) before previewing the patch.", "es": "Lea la NOR (paso 2) antes de previsualizar el parche."},
    "hw.log.preview_title": {"pt": "PRE-VISUALIZACAO DO PATCH -- alvo: {target}", "en": "PATCH PREVIEW -- target: {target}", "es": "PREVISUALIZACION DEL PARCHE -- objetivo: {target}"},
    "hw.log.preview_change": {"pt": "  offset 0x{offset}: {old} -> {new}   [{desc}]", "en": "  offset 0x{offset}: {old} -> {new}   [{desc}]", "es": "  offset 0x{offset}: {old} -> {new}   [{desc}]"},
    "hw.log.checksum_stale": {"pt": "*** ATENCAO: o checksum em 0x1C41FE-0x1C41FF NAO foi resolvido pra essa combinacao de chip + REV Wi-Fi (ainda nao vista). Isso pode fazer o console nao exibir video mesmo ligando. So grave em placa de bancada/teste. ***", "en": "*** WARNING: the checksum at 0x1C41FE-0x1C41FF was NOT resolved for this chip + Wi-Fi REV combination (not seen yet). This may cause the console to power on without video. Only write to a bench/test board. ***", "es": "*** ATENCION: el checksum en 0x1C41FE-0x1C41FF NO fue resuelto para esta combinacion de chip + REV Wi-Fi (aun no vista). Esto puede hacer que la consola encienda sin video. Grabe solo en una placa de banco/prueba. ***"},
    "hw.log.checksum_resolved": {"pt": "Checksum em 0x1C41FE-0x1C41FF resolvido com valor confirmado (ver NOTES.md) -- combinacao de chip + REV Wi-Fi ja vista em amostras reais.", "en": "Checksum at 0x1C41FE-0x1C41FF resolved with a confirmed value (see NOTES.md) -- chip + Wi-Fi REV combination already seen in real samples.", "es": "Checksum en 0x1C41FE-0x1C41FF resuelto con un valor confirmado (ver NOTES.md) -- combinacion de chip + REV Wi-Fi ya vista en muestras reales."},
    "hw.log.converted_saved": {"pt": "NOR convertida salva em: {path}", "en": "Converted NOR saved in: {path}", "es": "NOR convertida guardada en: {path}"},

    "hw.donor_sep_label": {"pt": "-- ou --", "en": "-- or --", "es": "-- o --"},
    "hw.btn_donor": {"pt": "Usar arquivo-base...", "en": "Use donor file...", "es": "Usar archivo base..."},
    "hw.donor_pick_title": {"pt": "Selecionar arquivo-base (.bin)", "en": "Select donor file (.bin)", "es": "Seleccionar archivo base (.bin)"},
    "hw.donor_size_err_title": {"pt": "Arquivo-base invalido", "en": "Invalid donor file", "es": "Archivo base invalido"},
    "hw.donor_size_err_body": {"pt": "O arquivo-base tem {size} bytes, mas o esperado e {expected} bytes (2 MB). Nao e uma NOR completa valida -- escolha outro arquivo.", "en": "The donor file is {size} bytes, but {expected} bytes (2 MB) were expected. It's not a valid full NOR dump -- choose another file.", "es": "El archivo base tiene {size} bytes, pero se esperaban {expected} bytes (2 MB). No es un dump de NOR completo valido -- elija otro archivo."},
    "hw.donor_confirm_title": {"pt": "Confirmar arquivo-base", "en": "Confirm donor file", "es": "Confirmar archivo base"},
    "hw.donor_confirm_body": {"pt": "O arquivo-base selecionado foi detectado como:\n\nChip HDMI: {chip}\nFamilia da placa: {family}\n\nO programa vai gravar nele o numero de serie e o MAC (LAN + Wi-Fi) do console que voce acabou de ler, mantendo todo o resto do arquivo-base como esta. Confira se o chip e a familia batem com o que voce pretende instalar antes de continuar. Deseja prosseguir?", "en": "The selected donor file was detected as:\n\nHDMI chip: {chip}\nBoard family: {family}\n\nThe program will write the serial number and MAC (LAN + Wi-Fi) of the console you just read into it, keeping everything else in the donor file as-is. Check that the chip and board family match what you intend to install before continuing. Proceed?", "es": "El archivo base seleccionado fue detectado como:\n\nChip HDMI: {chip}\nFamilia de la placa: {family}\n\nEl programa va a grabar en el el numero de serie y el MAC (LAN + Wi-Fi) de la consola que acaba de leer, manteniendo todo lo demas del archivo base como esta. Confirme que el chip y la familia coinciden con lo que pretende instalar antes de continuar. Desea continuar?"},
    "hw.log.donor_title": {"pt": "USANDO ARQUIVO-BASE: {path}", "en": "USING DONOR FILE: {path}", "es": "USANDO ARCHIVO BASE: {path}"},
    "hw.log.donor_detected": {"pt": "Arquivo-base detectado como: {chip} -- familia {family}", "en": "Donor file detected as: {chip} -- family {family}", "es": "Archivo base detectado como: {chip} -- familia {family}"},

    "hw.preview_first_title": {"pt": "Pre-visualize primeiro", "en": "Preview first", "es": "Previsualice primero"},
    "hw.preview_first_body": {"pt": "Clique em 'Pre-visualizar alteracoes' antes de gravar.", "en": "Click 'Preview changes' before writing.", "es": "Haga clic en 'Previsualizar cambios' antes de grabar."},
    "hw.checksum_stale_confirm": {"pt": "O checksum em 0x1C41FE-FF NAO foi resolvido pra essa combinacao de chip + REV Wi-Fi -- ainda nao sabemos se isso impede o video de funcionar.\n\nUse isto SOMENTE em placa de bancada/teste, nunca em placa de cliente.", "en": "The checksum at 0x1C41FE-FF was NOT resolved for this chip + Wi-Fi REV combination -- we don't yet know if this prevents video from working.\n\nUse this ONLY on a bench/test board, never on a customer's board.", "es": "El checksum en 0x1C41FE-FF NO fue resuelto para esta combinacion de chip + REV Wi-Fi -- aun no sabemos si esto impide que el video funcione.\n\nUse esto SOLO en una placa de banco/prueba, nunca en la placa de un cliente."},
    "hw.checksum_resolved_confirm": {"pt": "O checksum em 0x1C41FE-FF foi resolvido com um valor confirmado em amostras reais (ver NOTES.md).", "en": "The checksum at 0x1C41FE-FF was resolved with a value confirmed in real samples (see NOTES.md).", "es": "El checksum en 0x1C41FE-FF fue resuelto con un valor confirmado en muestras reales (ver NOTES.md)."},
    "hw.no_backup_title": {"pt": "Nenhum backup feito ainda", "en": "No backup made yet", "es": "Aun no se hizo backup"},
    "hw.no_backup_body": {"pt": "Voce ainda nao fez backup desta NOR nesta sessao. Sem um backup, se algo der errado essa gravacao vai ser IRREVERSIVEL.\n\nQuer que o programa faca um backup automatico agora (2 leituras da NOR atual) antes de continuar?\n\nSim = fazer backup agora e depois continuar a gravacao.\nNao = continuar a gravacao sem fazer backup.", "en": "You haven't backed up this NOR in this session yet. Without a backup, if something goes wrong this write will be IRREVERSIBLE.\n\nDo you want the program to make an automatic backup now (2 reads of the current NOR) before continuing?\n\nYes = make the backup now and then continue with the write.\nNo = continue the write without making a backup.", "es": "Aun no hizo un backup de esta NOR en esta sesion. Sin un backup, si algo sale mal esta grabacion sera IRREVERSIBLE.\n\n¿Quiere que el programa haga un backup automatico ahora (2 lecturas de la NOR actual) antes de continuar?\n\nSi = hacer el backup ahora y luego continuar con la grabacion.\nNo = continuar la grabacion sin hacer backup."},
    "hw.log.backup_before_write_start": {"pt": "Fazendo backup automatico da NOR antes de gravar (2 leituras)...", "en": "Making an automatic backup of the NOR before writing (2 reads)...", "es": "Haciendo un backup automatico de la NOR antes de grabar (2 lecturas)..."},
    "hw.log.backup_before_write_done": {"pt": "Backup automatico salvo em: {path}", "en": "Automatic backup saved to: {path}", "es": "Backup automatico guardado en: {path}"},
    "hw.no_backup_warn_title": {"pt": "Nenhum backup encontrado", "en": "No backup found", "es": "No se encontro backup"},
    "hw.no_backup_warn_body": {"pt": "Voce ainda nao fez backup desta NOR nesta sessao (leia a NOR no passo 2, ou aceite o backup automatico oferecido ao gravar). Sem um backup salvo, nao ha nada pra restaurar.", "en": "You haven't backed up this NOR in this session yet (read the NOR in step 2, or accept the automatic backup offered when writing). Without a saved backup, there's nothing to restore.", "es": "Aun no hizo un backup de esta NOR en esta sesion (lea la NOR en el paso 2, o acepte el backup automatico ofrecido al grabar). Sin un backup guardado, no hay nada para restaurar."},
    "hw.log.file_loaded_title": {"pt": "ARQUIVO CARREGADO a partir de: {path} (clique em \"4. GRAVAR NA NOR\" pra gravar)", "en": "FILE LOADED from: {path} (click \"4. WRITE TO NOR\" to write it)", "es": "ARCHIVO CARGADO desde: {path} (haga clic en \"4. GRABAR EN LA NOR\" para grabarlo)"},
    "hw.confirm_write_title": {"pt": "Confirmar gravacao", "en": "Confirm write", "es": "Confirmar grabacion"},
    "hw.confirm_write_body": {"pt": "Isto vai APAGAR e REGRAVAR a NOR inteira com o patch mostrado no log.\n\n{checksum_msg}\n\nTem certeza que quer continuar?", "en": "This will ERASE and REWRITE the entire NOR with the patch shown in the log.\n\n{checksum_msg}\n\nAre you sure you want to continue?", "es": "Esto va a BORRAR y REGRABAR toda la NOR con el parche mostrado en el registro.\n\n{checksum_msg}\n\n¿Esta seguro de que quiere continuar?"},
    "hw.log.write_cancelled_user": {"pt": "Gravacao cancelada pelo usuario (respondeu Nao na confirmacao).", "en": "Write cancelled by the user (answered No at the confirmation).", "es": "Grabacion cancelada por el usuario (respondio No en la confirmacion)."},
    "hw.confirm_final_title": {"pt": "Confirmacao final", "en": "Final confirmation", "es": "Confirmacion final"},
    "hw.confirm_final_write_body": {"pt": "Digite {phrase} para confirmar a gravacao:", "en": "Type {phrase} to confirm the write:", "es": "Escriba {phrase} para confirmar la grabacion:"},
    "hw.log.write_cancelled_phrase": {"pt": "Gravacao cancelada (confirmacao nao digitada corretamente).", "en": "Write cancelled (confirmation not typed correctly).", "es": "Grabacion cancelada (confirmacion no escrita correctamente)."},

    "hw.log.aborted_changed": {"pt": "ABORTADO: a NOR conectada agora e diferente da que foi lida no passo 2. Se voce trocou o chip no soquete, refaca a leitura (passo 2) antes de gravar.", "en": "ABORTED: the connected NOR is now different from the one read in step 2. If you swapped the chip in the socket, redo the read (step 2) before writing.", "es": "ABORTADO: la NOR conectada ahora es diferente de la leida en el paso 2. Si cambio el chip en el zocalo, repita la lectura (paso 2) antes de grabar."},
    "hw.aborted_title": {"pt": "Gravacao cancelada", "en": "Write cancelled", "es": "Grabacion cancelada"},
    "hw.aborted_body": {"pt": "A NOR conectada mudou desde a ultima leitura. Refaca o passo 2 antes de gravar.", "en": "The connected NOR has changed since the last read. Redo step 2 before writing.", "es": "La NOR conectada cambio desde la ultima lectura. Repita el paso 2 antes de grabar."},

    "hw.log.op_done": {"pt": "{verb} CONCLUIDA -- a NOR gravada bate 100% com {reference}.", "en": "{verb} COMPLETE -- the written NOR matches {reference} 100%.", "es": "{verb} COMPLETADA -- la NOR grabada coincide 100% con {reference}."},
    "hw.log.test_board_now": {"pt": "Teste a placa agora.", "en": "Test the board now.", "es": "Pruebe la placa ahora."},
    "hw.log.session_backup": {"pt": "Backup desta sessao, se precisar: {path}", "en": "This session's backup, if needed: {path}", "es": "Backup de esta sesion, si lo necesita: {path}"},
    "hw.op_done_title": {"pt": "{verb} concluida", "en": "{verb} complete", "es": "{verb} completada"},
    "hw.op_done_body": {"pt": "{verb} concluida e verificada com sucesso.\nTeste a placa agora.", "en": "{verb} completed and verified successfully.\nTest the board now.", "es": "{verb} completada y verificada con exito.\nPruebe la placa ahora."},
    "hw.reference_backup": {"pt": "o backup selecionado", "en": "the selected backup", "es": "el backup seleccionado"},
    "hw.reference_patch": {"pt": "o patch pretendido", "en": "the intended patch", "es": "el parche previsto"},
    "hw.log.op_mismatch": {"pt": "ERRO: a NOR gravada NAO bate com {reference} em {n} byte(s). Primeiros offsets: {offs}", "en": "ERROR: the written NOR does NOT match {reference} in {n} byte(s). First offsets: {offs}", "es": "ERROR: la NOR grabada NO coincide con {reference} en {n} byte(s). Primeros offsets: {offs}"},
    "hw.log.restore_now": {"pt": "RESTAURE O BACKUP imediatamente: {path}", "en": "RESTORE THE BACKUP immediately: {path}", "es": "RESTAURE EL BACKUP de inmediato: {path}"},
    "hw.verify_fail_title": {"pt": "Falha na verificacao", "en": "Verification failed", "es": "Fallo en la verificacion"},
    "hw.verify_fail_body": {"pt": "A operacao nao bateu na verificacao. Restaure um backup valido imediatamente (botao \"Restaurar backup de arquivo...\").", "en": "The operation did not match on verification. Restore a valid backup immediately (\"Restore backup from file...\" button).", "es": "La operacion no coincidio en la verificacion. Restaure un backup valido de inmediato (boton \"Restaurar backup de archivo...\")."},
    "hw.log.write_error": {"pt": "ERRO DURANTE A GRAVACAO: {err}", "en": "ERROR DURING WRITE: {err}", "es": "ERROR DURANTE LA GRABACION: {err}"},
    "hw.log.restore_if_incomplete": {"pt": "Se a NOR ficou incompleta, restaure o backup: {path}", "en": "If the NOR was left incomplete, restore the backup: {path}", "es": "Si la NOR quedo incompleta, restaure el backup: {path}"},
    "hw.write_err_title": {"pt": "Erro na gravacao", "en": "Write error", "es": "Error en la grabacion"},
    "hw.write_err_body": {"pt": "{err}\n\nRestaure um backup valido se necessario.", "en": "{err}\n\nRestore a valid backup if necessary.", "es": "{err}\n\nRestaure un backup valido si es necesario."},

    "hw.restore_select_title": {"pt": "Selecione o arquivo .bin para gravar na NOR (backup antigo, ou arquivo convertido na aba 'Analisar arquivo')", "en": "Select the .bin file to write to the NOR (an old backup, or a file converted in the 'Analyze file' tab)", "es": "Seleccione el archivo .bin para grabar en la NOR (backup antiguo, o archivo convertido en la pestana 'Analizar archivo')"},
    "hw.restore_backup_filter": {"pt": "Arquivo NOR", "en": "NOR file", "es": "Archivo NOR"},
    "hw.restore_invalid_title": {"pt": "Arquivo invalido", "en": "Invalid file", "es": "Archivo invalido"},
    "hw.restore_invalid_body": {"pt": "O arquivo selecionado tem {size} bytes, mas o esperado e {expected} bytes (2 MB). Escolha outro arquivo.", "en": "The selected file has {size} bytes, but {expected} bytes (2 MB) were expected. Choose another file.", "es": "El archivo seleccionado tiene {size} bytes, pero se esperaban {expected} bytes (2 MB). Elija otro archivo."},
    "hw.restore_not_ps5_title": {"pt": "Arquivo nao e uma NOR de PS5", "en": "File is not a PS5 NOR", "es": "El archivo no es una NOR de PS5"},
    "hw.restore_not_ps5_body": {"pt": "O arquivo selecionado tem o tamanho certo (2 MB), mas nao tem a assinatura de uma NOR de PS5 valida no inicio do arquivo.\n\nUse apenas arquivos NOR correspondentes a um PS5 -- lidos por este programa, gerados a partir de um arquivo-base, ou de outra ferramenta compativel. Nao use um .bin de outro tipo de dispositivo.", "en": "The selected file has the right size (2 MB), but doesn't have a valid PS5 NOR signature at the start of the file.\n\nOnly use NOR files that correspond to a PS5 -- read by this program, generated from a donor file, or from another compatible tool. Don't use a .bin from a different kind of device.", "es": "El archivo seleccionado tiene el tamano correcto (2 MB), pero no tiene la firma de una NOR de PS5 valida al inicio del archivo.\n\nUse solo archivos NOR correspondientes a un PS5 -- leidos por este programa, generados a partir de un archivo base, o de otra herramienta compatible. No use un .bin de otro tipo de dispositivo."},
    "hw.log.restore_not_ps5": {"pt": "Arquivo rejeitado (nao e uma NOR de PS5 valida): {path}", "en": "File rejected (not a valid PS5 NOR): {path}", "es": "Archivo rechazado (no es una NOR de PS5 valida): {path}"},
    "hw.confirm_restore_title": {"pt": "Confirmar gravacao", "en": "Confirm write", "es": "Confirmar grabacion"},
    "hw.confirm_restore_body": {"pt": "Isto vai APAGAR e REGRAVAR a NOR inteira com o conteudo de:\n\n{path}\n\nUse isto SOMENTE em placa de bancada/teste, nunca em placa de cliente, a menos que tenha certeza de que esse arquivo pertence exatamente a essa placa (backup antigo dela, ou um arquivo que voce acabou de converter pra ela na aba 'Analisar arquivo').\n\nTem certeza que quer continuar?", "en": "This will ERASE and REWRITE the entire NOR with the contents of:\n\n{path}\n\nUse this ONLY on a bench/test board, never on a customer's board, unless you're certain this file belongs exactly to that board (an old backup of it, or a file you just converted for it in the 'Analyze file' tab).\n\nAre you sure you want to continue?", "es": "Esto va a BORRAR y REGRABAR toda la NOR con el contenido de:\n\n{path}\n\nUse esto SOLO en una placa de banco/prueba, nunca en la placa de un cliente, a menos que este seguro de que este archivo pertenece exactamente a esa placa (backup antiguo de ella, o un archivo que acaba de convertir para ella en la pestana 'Analizar archivo').\n\n¿Esta seguro de que quiere continuar?"},
    "hw.log.restore_cancelled_user": {"pt": "Gravacao cancelada pelo usuario (respondeu Nao na confirmacao).", "en": "Write cancelled by the user (answered No at the confirmation).", "es": "Grabacion cancelada por el usuario (respondio No en la confirmacion)."},
    "hw.confirm_final_restore_body": {"pt": "Digite {phrase} para confirmar a gravacao:", "en": "Type {phrase} to confirm the write:", "es": "Escriba {phrase} para confirmar la grabacion:"},
    "hw.log.restore_cancelled_phrase": {"pt": "Gravacao cancelada (confirmacao nao digitada corretamente).", "en": "Write cancelled (confirmation not typed correctly).", "es": "Grabacion cancelada (confirmacion no escrita correctamente)."},
    "hw.log.restoring_from": {"pt": "GRAVANDO ARQUIVO a partir de: {path}", "en": "WRITING FILE from: {path}", "es": "GRABANDO ARCHIVO desde: {path}"},

    # -- Aba "Analisar arquivo (.bin)" -------------------------------------------
    "file.label_path": {"pt": "Arquivo NOR (.bin):", "en": "NOR file (.bin):", "es": "Archivo NOR (.bin):"},
    "file.info_frame_title": {"pt": "Informacoes do arquivo", "en": "File information", "es": "Informacion del archivo"},
    "file.field.size": {"pt": "Tamanho do arquivo:", "en": "File size:", "es": "Tamano del archivo:"},
    "file.field.sha256": {"pt": "SHA-256:", "en": "SHA-256:", "es": "SHA-256:"},
    "file.field.chip": {"pt": "Chip HDMI detectado:", "en": "Detected HDMI chip:", "es": "Chip HDMI detectado:"},
    "file.field.mac": {"pt": "Endereco MAC:", "en": "MAC address:", "es": "Direccion MAC:"},
    "file.field.mobo_serial": {"pt": "Identificador da placa-mae:", "en": "Motherboard identifier:", "es": "Identificador de la placa base:"},
    "file.field.board_serial": {"pt": "Numero de serie do console:", "en": "Console serial number:", "es": "Numero de serie de la consola:"},
    "file.field.raw_id": {"pt": "Identificador bruto (serie/area adjacente):", "en": "Raw identifier (serial/adjacent area):", "es": "Identificador bruto (serie/area adyacente):"},
    "file.field.cfi": {"pt": "SKU / modelo do console:", "en": "SKU / console model:", "es": "SKU / modelo de la consola:"},
    "file.field.wifi_rev": {"pt": "Revisao Wi-Fi/Bluetooth (EXPERIMENTAL):", "en": "Wi-Fi/Bluetooth revision (EXPERIMENTAL):", "es": "Revision Wi-Fi/Bluetooth (EXPERIMENTAL):"},
    "file.field.board_family": {"pt": "Familia da placa (leitor de disco):", "en": "Board family (disc drive):", "es": "Familia de la placa (lector de disco):"},
    "file.field.region": {"pt": "Regiao:", "en": "Region:", "es": "Region:"},
    "file.field.wifi_mac": {"pt": "Endereco MAC Wi-Fi:", "en": "Wi-Fi MAC address:", "es": "Direccion MAC Wi-Fi:"},
    "file.field.fw_current": {"pt": "Firmware atual gravado na NOR:", "en": "Current firmware stored in NOR:", "es": "Firmware actual grabado en la NOR:"},
    "file.field.emc_version": {"pt": "Firmware do EMC (ativo / backup):", "en": "EMC firmware (active / backup):", "es": "Firmware del EMC (activo / backup):"},
    "file.field.console_type": {"pt": "Tipo de console:", "en": "Console type:", "es": "Tipo de consola:"},
    "file.field.idu_mode": {"pt": "Modo IDU (unidade de demonstracao):", "en": "IDU mode (demo unit):", "es": "Modo IDU (unidad de demostracion):"},
    "file.patch_frame_title": {"pt": "Aplicar patch (chip HDMI)", "en": "Apply patch (HDMI chip)", "es": "Aplicar parche (chip HDMI)"},
    "file.target_label": {"pt": "Gravar arquivo configurado para:", "en": "Save file configured for:", "es": "Guardar archivo configurado para:"},
    "file.btn_save": {"pt": "Salvar NOR com patch...", "en": "Save NOR with patch...", "es": "Guardar NOR con parche..."},

    "file.donor_sep_label": {"pt": "-- ou --", "en": "-- or --", "es": "-- o --"},
    "file.btn_donor": {"pt": "Usar arquivo-base automatico", "en": "Use automatic donor file", "es": "Usar archivo base automatico"},
    "file.btn_donor_manual": {"pt": "Regenerar com arquivo-base...", "en": "Regenerate with donor file...", "es": "Regenerar con archivo base..."},
    "file.log.donor_available": {"pt": "Arquivo-base disponivel para a familia {family}: {name}. Clique em 'Usar arquivo-base automatico' para gravar os dados deste console nele.", "en": "Donor file available for family {family}: {name}. Click 'Use automatic donor file' to write this console's data into it.", "es": "Archivo base disponible para la familia {family}: {name}. Haga clic en 'Usar archivo base automatico' para grabar los datos de esta consola en el."},
    "file.log.donor_manual_hint": {"pt": "Familia da placa nao identificada (arquivo em branco/corrompido ou revisao ainda nao mapeada). Se voce sabe o modelo da placa pela etiqueta fisica, clique em 'Regenerar com arquivo-base...' e escolha o arquivo-base certo manualmente.", "en": "Board family not identified (blank/corrupted file, or a revision not mapped yet). If you know the board model from its physical label, click 'Regenerate with donor file...' and pick the right donor file manually.", "es": "Familia de la placa no identificada (archivo en blanco/corrupto o revision aun no mapeada). Si conoce el modelo de la placa por la etiqueta fisica, haga clic en 'Regenerar con archivo base...' y elija el archivo base correcto manualmente."},
    "file.log.donor_title": {"pt": "USANDO ARQUIVO-BASE: {path}", "en": "USING DONOR FILE: {path}", "es": "USANDO ARCHIVO BASE: {path}"},

    "file.console_type_label": {"pt": "Converter tipo de console para:", "en": "Convert console type to:", "es": "Convertir tipo de consola a:"},
    "file.btn_console_type": {"pt": "Converter", "en": "Convert", "es": "Convertir"},
    "file.console_type_confirm_title": {"pt": "Confirmar conversao de tipo de console", "en": "Confirm console type conversion", "es": "Confirmar conversion de tipo de consola"},
    "file.console_type_confirm_body": {"pt": "Isto vai mudar o campo \"Tipo de console\" (0x1C7010) do arquivo carregado para: {target}.\n\nEsse campo e usado pelo sistema pra decidir se exige o leitor de disco fisico -- a conversao Disco -> Digital e o metodo conhecido pra permitir que um PS5 Fat com leitor de disco com defeito (sem substituto possivel, pois e pareado com a APU) volte a atualizar normalmente. Grave o resultado SOMENTE em placa de bancada/teste antes de confiar em cliente.\n\nDeseja continuar?", "en": "This will change the \"Console type\" field (0x1C7010) of the loaded file to: {target}.\n\nThis field is used by the system to decide whether it requires the physical disc drive -- the Disk -> Digital conversion is the known method to let a Fat PS5 with a broken disc drive (no replacement possible, since it's paired with the APU) go back to updating normally. Only write the result to a bench/test board before trusting it with a customer. \n\nProceed?", "es": "Esto va a cambiar el campo \"Tipo de consola\" (0x1C7010) del archivo cargado a: {target}.\n\nEste campo lo usa el sistema para decidir si exige el lector de disco fisico -- la conversion Disco -> Digital es el metodo conocido para que un PS5 Fat con lector de disco defectuoso (sin reemplazo posible, ya que esta emparejado con la APU) vuelva a actualizar normalmente. Grabe el resultado SOLO en una placa de banco/prueba antes de confiar en un cliente.\n\nDesea continuar?"},
    "file.log.console_type_title": {"pt": "CONVERSAO DE TIPO DE CONSOLE", "en": "CONSOLE TYPE CONVERSION", "es": "CONVERSION DE TIPO DE CONSOLA"},

    "file.browse_title": {"pt": "Selecione o arquivo NOR (.bin) para analisar", "en": "Select the NOR file (.bin) to analyze", "es": "Seleccione el archivo NOR (.bin) a analizar"},
    "file.size_warn_title": {"pt": "Tamanho inesperado", "en": "Unexpected size", "es": "Tamano inesperado"},
    "file.size_warn_body": {"pt": "O arquivo tem {size} bytes, mas o esperado e {expected} bytes (2 MB). Pre-visualizacao de patch desabilitada.", "en": "The file has {size} bytes, but {expected} bytes (2 MB) were expected. Patch preview disabled.", "es": "El archivo tiene {size} bytes, pero se esperaban {expected} bytes (2 MB). Previsualizacion de parche deshabilitada."},
    "file.log.loaded": {"pt": "Arquivo carregado: {path}", "en": "File loaded: {path}", "es": "Archivo cargado: {path}"},
    "file.log.size": {"pt": "Tamanho: {size} bytes{suffix}", "en": "Size: {size} bytes{suffix}", "es": "Tamano: {size} bytes{suffix}"},
    "file.log.preview_title": {"pt": "PRE-VISUALIZACAO DO PATCH -- alvo: {target}", "en": "PATCH PREVIEW -- target: {target}", "es": "PREVISUALIZACION DEL PARCHE -- objetivo: {target}"},
    "file.log.preview_change": {"pt": "  offset 0x{offset}: {old} -> {new}   [{desc}]", "en": "  offset 0x{offset}: {old} -> {new}   [{desc}]", "es": "  offset 0x{offset}: {old} -> {new}   [{desc}]"},
    "file.log.checksum_stale": {"pt": "*** ATENCAO: o checksum em 0x1C41FE-0x1C41FF NAO foi resolvido pra essa combinacao de chip + REV Wi-Fi (ainda nao vista). Ficou com o valor antigo. So use esse arquivo em placa de bancada/teste. ***", "en": "*** WARNING: the checksum at 0x1C41FE-0x1C41FF was NOT resolved for this chip + Wi-Fi REV combination (not seen yet). It kept the old value. Only use this file on a bench/test board. ***", "es": "*** ATENCION: el checksum en 0x1C41FE-0x1C41FF NO fue resuelto para esta combinacion de chip + REV Wi-Fi (aun no vista). Quedo con el valor anterior. Use este archivo solo en una placa de banco/prueba. ***"},
    "file.log.checksum_resolved": {"pt": "Checksum em 0x1C41FE-0x1C41FF resolvido com valor confirmado (ver NOTES.md) -- combinacao de chip + REV Wi-Fi ja vista em amostras reais.", "en": "Checksum at 0x1C41FE-0x1C41FF resolved with a confirmed value (see NOTES.md) -- chip + Wi-Fi REV combination already seen in real samples.", "es": "Checksum en 0x1C41FE-0x1C41FF resuelto con un valor confirmado (ver NOTES.md) -- combinacion de chip + REV Wi-Fi ya vista en muestras reales."},
    "file.save_title": {"pt": "Salvar NOR com patch aplicado", "en": "Save NOR with patch applied", "es": "Guardar NOR con el parche aplicado"},
    "file.log.saved": {"pt": "Arquivo salvo com patch aplicado em: {path}", "en": "File saved with patch applied in: {path}", "es": "Archivo guardado con el parche aplicado en: {path}"},
    "file.saved_title": {"pt": "Arquivo salvo", "en": "File saved", "es": "Archivo guardado"},
    "file.saved_body_stale": {"pt": "NOR com patch salva em:\n{path}\n\nLembrete: o checksum em 0x1C41FE-0x1C41FF NAO foi resolvido pra essa combinacao de chip + REV Wi-Fi -- use so em placa de bancada/teste.", "en": "NOR with patch saved in:\n{path}\n\nReminder: the checksum at 0x1C41FE-0x1C41FF was NOT resolved for this chip + Wi-Fi REV combination -- use only on a bench/test board.", "es": "NOR con parche guardada en:\n{path}\n\nRecordatorio: el checksum en 0x1C41FE-0x1C41FF NO fue resuelto para esta combinacion de chip + REV Wi-Fi -- use solo en una placa de banco/prueba."},
    "file.saved_body_ok": {"pt": "NOR com patch salva em:\n{path}\n\nChecksum em 0x1C41FE-0x1C41FF resolvido com valor confirmado (ver NOTES.md).", "en": "NOR with patch saved in:\n{path}\n\nChecksum at 0x1C41FE-0x1C41FF resolved with a confirmed value (see NOTES.md).", "es": "NOR con parche guardada en:\n{path}\n\nChecksum en 0x1C41FE-0x1C41FF resuelto con un valor confirmado (ver NOTES.md)."},

    # -- Aba "Leitor UART" --------------------------------------------------------
    "uart.port_label": {"pt": "Porta:", "en": "Port:", "es": "Puerto:"},
    "uart.btn_refresh": {"pt": "Atualizar portas", "en": "Refresh ports", "es": "Actualizar puertos"},
    "uart.baud_label": {"pt": "  Baud:", "en": "  Baud:", "es": "  Baudios:"},
    "uart.btn_connect": {"pt": "Conectar", "en": "Connect", "es": "Conectar"},
    "uart.btn_disconnect": {"pt": "Desconectar", "en": "Disconnect", "es": "Desconectar"},
    "uart.status_disconnected": {"pt": "Status: desconectado", "en": "Status: disconnected", "es": "Estado: desconectado"},
    "uart.status_connected": {"pt": "Status: conectado em {port} @ {baud} bps", "en": "Status: connected on {port} @ {baud} bps", "es": "Estado: conectado en {port} @ {baud} bps"},
    "uart.warning": {"pt": "Captura bruta do log serial -- nao interpreta codigos de erro. 115200 e o baud mais comum em debug UART, mas confirme se nao vier nada legivel. Confirme a tensao do adaptador (muitas placas usam 3.3V TTL) antes de conectar.", "en": "Raw capture of the serial log -- does not interpret error codes. 115200 is the most common baud rate for UART debug, but check it if nothing readable shows up. Confirm the adapter's voltage (many boards use 3.3V TTL) before connecting.", "es": "Captura cruda del log serial -- no interpreta codigos de error. 115200 es el baudrate mas comun en debug UART, pero verifiquelo si no aparece nada legible. Confirme el voltaje del adaptador (muchas placas usan 3.3V TTL) antes de conectar."},
    "uart.catalog_label": {"pt": "Catalogo de codigos (abre no navegador):", "en": "Code catalog (opens in browser):", "es": "Catalogo de codigos (abre en el navegador):"},
    "uart.btn_read_errors": {"pt": "Ler codigos de erro", "en": "Read error codes", "es": "Leer codigos de error"},
    "uart.btn_clear_errors": {"pt": "Limpar codigos de erro no console", "en": "Clear error codes on console", "es": "Borrar codigos de error en la consola"},
    "uart.errlog_warning": {"pt": "Envia o comando \"errlog N\" (protocolo conferido no PS5 NOR Modifier/TheCod3r) -- ainda NAO testado com hardware real neste projeto. Se nao vier resposta, confirme o baud e a pinagem antes de desconfiar do comando.", "en": "Sends the \"errlog N\" command (protocol verified against PS5 NOR Modifier/TheCod3r) -- NOT yet tested with real hardware in this project. If there's no response, check the baud rate and pinout before suspecting the command itself.", "es": "Envia el comando \"errlog N\" (protocolo verificado en PS5 NOR Modifier/TheCod3r) -- aun NO probado con hardware real en este proyecto. Si no hay respuesta, confirme el baudrate y el pinout antes de desconfiar del comando."},
    "uart.clear_errors_confirm_title": {"pt": "Limpar codigos de erro?", "en": "Clear error codes?", "es": "Borrar codigos de error?"},
    "uart.clear_errors_confirm_body": {"pt": "Isso envia \"errlog clear\" e apaga o historico de erros gravado no console. Nao pode ser desfeito. Deseja continuar?", "en": "This sends \"errlog clear\" and erases the error history stored on the console. This cannot be undone. Do you want to continue?", "es": "Esto envia \"errlog clear\" y borra el historial de errores guardado en la consola. No se puede deshacer. Desea continuar?"},
    "uart.log.read_errors_start": {"pt": "Consultando {n} slots de log de erro (errlog 0-{max})...", "en": "Querying {n} error log slots (errlog 0-{max})...", "es": "Consultando {n} slots de log de error (errlog 0-{max})..."},
    "uart.log.read_errors_done": {"pt": "Consulta de codigos de erro concluida.", "en": "Error code query finished.", "es": "Consulta de codigos de error finalizada."},
    "uart.log.clear_errors_sent": {"pt": "Comando de limpeza enviado.", "en": "Clear command sent.", "es": "Comando de limpieza enviado."},
    "uart.btn_clear": {"pt": "Limpar log", "en": "Clear log", "es": "Limpiar log"},
    "uart.btn_save_log": {"pt": "Salvar log em arquivo...", "en": "Save log to file...", "es": "Guardar log en archivo..."},
    "uart.send_label": {"pt": "Enviar (opcional):", "en": "Send (optional):", "es": "Enviar (opcional):"},
    "uart.btn_send": {"pt": "Enviar", "en": "Send", "es": "Enviar"},

    "uart.select_port_title": {"pt": "Selecione a porta", "en": "Select the port", "es": "Seleccione el puerto"},
    "uart.select_port_body": {"pt": "Escolha uma porta COM antes de conectar.", "en": "Choose a COM port before connecting.", "es": "Elija un puerto COM antes de conectar."},
    "uart.invalid_baud_title": {"pt": "Baud invalido", "en": "Invalid baud rate", "es": "Baudrate invalido"},
    "uart.invalid_baud_body": {"pt": "O baud rate precisa ser um numero inteiro.", "en": "The baud rate must be a whole number.", "es": "El baudrate debe ser un numero entero."},
    "uart.log.error": {"pt": "ERRO: {err}", "en": "ERROR: {err}", "es": "ERROR: {err}"},
    "uart.connect_err_title": {"pt": "Erro ao conectar", "en": "Connection error", "es": "Error al conectar"},
    "uart.log.connected": {"pt": "Conectado em {port} @ {baud} bps. Capturando log...", "en": "Connected on {port} @ {baud} bps. Capturing log...", "es": "Conectado en {port} @ {baud} bps. Capturando log..."},
    "uart.log.disconnected": {"pt": "Desconectado.", "en": "Disconnected.", "es": "Desconectado."},
    "uart.log.port_error": {"pt": "ERRO na porta serial: {msg}", "en": "ERROR on the serial port: {msg}", "es": "ERROR en el puerto serial: {msg}"},
    "uart.log_empty_title": {"pt": "Log vazio", "en": "Empty log", "es": "Log vacio"},
    "uart.log_empty_body": {"pt": "Nao ha nada capturado ainda pra salvar.", "en": "There's nothing captured yet to save.", "es": "Aun no hay nada capturado para guardar."},
    "uart.save_log_title": {"pt": "Salvar log UART", "en": "Save UART log", "es": "Guardar log UART"},
    "uart.text_file_filter": {"pt": "Arquivo de texto", "en": "Text file", "es": "Archivo de texto"},
    "uart.log.saved": {"pt": "Log salvo em: {path}", "en": "Log saved in: {path}", "es": "Log guardado en: {path}"},
    "uart.not_connected_title": {"pt": "Nao conectado", "en": "Not connected", "es": "No conectado"},
    "uart.not_connected_body": {"pt": "Conecte a porta UART antes de enviar.", "en": "Connect the UART port before sending.", "es": "Conecte el puerto UART antes de enviar."},
    "uart.log.ports_found": {"pt": "Portas encontradas: {ports}", "en": "Ports found: {ports}", "es": "Puertos encontrados: {ports}"},
    "uart.ports_none": {"pt": "(nenhuma)", "en": "(none)", "es": "(ninguno)"},

    # -- Aba "Teste de Controle" --------------------------------------------------
    "ctrl.btn_detect": {"pt": "Detectar controle", "en": "Detect controller", "es": "Detectar control"},
    "ctrl.status_none": {"pt": "  Nenhum controle detectado ainda", "en": "  No controller detected yet", "es": "  Ningun control detectado aun"},
    "ctrl.btn_connect": {"pt": "Conectar", "en": "Connect", "es": "Conectar"},
    "ctrl.btn_disconnect": {"pt": "Desconectar", "en": "Disconnect", "es": "Desconectar"},
    "ctrl.warning": {"pt": "Leitura via HID bruto, nativo, sem precisar de internet/navegador. Conecte o controle por CABO USB. Analogicos, gatilhos, botoes e D-pad sao de alta confianca; touchpad, bateria, vibracao e barra de luz sao EXPERIMENTAIS (ainda nao validados com hardware real) -- teste e me avise se algo vier errado.", "en": "Native raw HID reading, no internet/browser required. Connect the controller via USB CABLE. Sticks, triggers, buttons and D-pad are high-confidence; touchpad, battery, vibration and light bar are EXPERIMENTAL (not yet validated with real hardware) -- test it and let us know if anything comes out wrong.", "es": "Lectura via HID crudo, nativa, sin necesidad de internet/navegador. Conecte el control por CABLE USB. Analogicos, gatillos, botones y D-pad son de alta confianza; touchpad, bateria, vibracion y barra de luz son EXPERIMENTALES (aun no validados con hardware real) -- pruebelo y avisenos si algo sale mal."},
    "ctrl.left_stick": {"pt": "Analogico esquerdo", "en": "Left stick", "es": "Analogico izquierdo"},
    "ctrl.right_stick": {"pt": "Analogico direito", "en": "Right stick", "es": "Analogico derecho"},
    "ctrl.stick_xy": {"pt": "X: {x}  Y: {y}", "en": "X: {x}  Y: {y}", "es": "X: {x}  Y: {y}"},
    "ctrl.triggers": {"pt": "Gatilhos", "en": "Triggers", "es": "Gatillos"},
    "ctrl.diagram_label": {"pt": "Diagrama (clique nos botoes do controle)", "en": "Diagram (click the controller's buttons)", "es": "Diagrama (haga clic en los botones del control)"},
    "ctrl.battery": {"pt": "Bateria (experimental): --", "en": "Battery (experimental): --", "es": "Bateria (experimental): --"},
    "ctrl.battery_value": {"pt": "Bateria (experimental): {pct}%{charging}", "en": "Battery (experimental): {pct}%{charging}", "es": "Bateria (experimental): {pct}%{charging}"},
    "ctrl.charging_suffix": {"pt": " (carregando)", "en": " (charging)", "es": " (cargando)"},
    "ctrl.vib_frame_title": {"pt": "Teste de vibracao (experimental)", "en": "Vibration test (experimental)", "es": "Prueba de vibracion (experimental)"},
    "ctrl.motor_left": {"pt": "Motor esquerdo (forte)", "en": "Left motor (strong)", "es": "Motor izquierdo (fuerte)"},
    "ctrl.motor_right": {"pt": "Motor direito (fraco)", "en": "Right motor (weak)", "es": "Motor derecho (debil)"},
    "ctrl.stop": {"pt": "Parar", "en": "Stop", "es": "Detener"},
    "ctrl.light_frame_title": {"pt": "Teste da barra de luz", "en": "Light bar test", "es": "Prueba de la barra de luz"},
    "ctrl.color_red": {"pt": "Vermelho", "en": "Red", "es": "Rojo"},
    "ctrl.color_green": {"pt": "Verde", "en": "Green", "es": "Verde"},
    "ctrl.color_blue": {"pt": "Azul", "en": "Blue", "es": "Azul"},
    "ctrl.color_white": {"pt": "Branco", "en": "White", "es": "Blanco"},
    "ctrl.color_off": {"pt": "Apagar", "en": "Off", "es": "Apagar"},
    "ctrl.calib_frame_title": {"pt": "Calibracao do analogico (grava no controle)", "en": "Stick calibration (writes to the controller)", "es": "Calibracion del analogico (graba en el control)"},
    "ctrl.calib_note": {"pt": "Mesmo recurso do dualshock-tools.github.io, feito nativamente aqui. So fica permanente se voce clicar em 'Salvar alteracoes permanentemente' depois -- ate la da pra testar e desistir sem risco.", "en": "Same feature as dualshock-tools.github.io, done natively here. It only becomes permanent if you click 'Save changes permanently' afterwards -- until then you can test and back out without risk.", "es": "Misma funcion de dualshock-tools.github.io, hecha nativamente aqui. Solo queda permanente si hace clic en 'Guardar cambios permanentemente' despues -- hasta entonces puede probar y desistir sin riesgo."},
    "ctrl.btn_calib_center": {"pt": "Calibrar centro do analogico", "en": "Calibrate stick center", "es": "Calibrar centro del analogico"},
    "ctrl.btn_calib_range": {"pt": "Calibrar alcance do analogico...", "en": "Calibrate stick range...", "es": "Calibrar rango del analogico..."},
    "ctrl.btn_flash": {"pt": "Salvar alteracoes permanentemente", "en": "Save changes permanently", "es": "Guardar cambios permanentemente"},
    "ctrl.calib_status_idle": {"pt": "Nenhuma alteracao de calibracao pendente nesta sessao.", "en": "No pending calibration changes in this session.", "es": "Ninguna calibracion pendiente en esta sesion."},

    "ctrl.not_found_extra": {"pt": "  Nenhum controle DualSense encontrado (conecte por cabo USB)", "en": "  No DualSense controller found (connect via USB cable)", "es": "  Ningun control DualSense encontrado (conecte por cable USB)"},
    "ctrl.sony_controller": {"pt": "Controle Sony", "en": "Sony controller", "es": "Control Sony"},
    "ctrl.found_extra": {"pt": " (+{n} outro(s))", "en": " (+{n} more)", "es": " (+{n} mas)"},
    "ctrl.found_status": {"pt": "  Encontrado: {name}{extra}", "en": "  Found: {name}{extra}", "es": "  Encontrado: {name}{extra}"},
    "ctrl.connect_err_title": {"pt": "Erro ao conectar controle", "en": "Error connecting controller", "es": "Error al conectar el control"},
    "ctrl.connected_status": {"pt": "  Conectado -- mexa nos sticks/botoes para testar", "en": "  Connected -- move the sticks/buttons to test", "es": "  Conectado -- mueva los analogicos/botones para probar"},
    "ctrl.disconnected_status": {"pt": "  Desconectado", "en": "  Disconnected", "es": "  Desconectado"},
    "ctrl.rumble_err_title": {"pt": "Erro ao testar vibracao", "en": "Error testing vibration", "es": "Error al probar la vibracion"},
    "ctrl.light_err_title": {"pt": "Erro ao testar barra de luz", "en": "Error testing light bar", "es": "Error al probar la barra de luz"},

    "ctrl.not_connected_title": {"pt": "Nao conectado", "en": "Not connected", "es": "No conectado"},
    "ctrl.not_connected_body": {"pt": "Conecte o controle antes de calibrar.", "en": "Connect the controller before calibrating.", "es": "Conecte el control antes de calibrar."},
    "ctrl.calib_center_title": {"pt": "Calibrar centro do analogico", "en": "Calibrate stick center", "es": "Calibrar centro del analogico"},
    "ctrl.calib_center_body": {"pt": "Solte os dois analogicos (deixe-os parados, sem tocar) antes de continuar.\n\nIsto recalcula o ponto central dos dois sticks. A mudanca fica ativa na hora, mas so e gravada de forma permanente se voce clicar depois em 'Salvar alteracoes permanentemente' -- ate la, da pra desistir sem risco.\n\nContinuar?", "en": "Release both sticks (leave them untouched) before continuing.\n\nThis recalculates the center point of both sticks. The change is active immediately, but only becomes permanent if you later click 'Save changes permanently' -- until then, you can back out without risk.\n\nContinue?", "es": "Suelte los dos analogicos (dejelos quietos, sin tocar) antes de continuar.\n\nEsto recalcula el punto central de los dos analogicos. El cambio queda activo de inmediato, pero solo se graba de forma permanente si despues hace clic en 'Guardar cambios permanentemente' -- hasta entonces, puede desistir sin riesgo.\n\n¿Continuar?"},
    "ctrl.calib_center_status_progress": {"pt": "Calibrando centro do analogico...", "en": "Calibrating stick center...", "es": "Calibrando centro del analogico..."},
    "ctrl.calib_center_done": {"pt": "Centro calibrado. Teste os sticks -- se estiver bom, clique em 'Salvar alteracoes permanentemente'.", "en": "Center calibrated. Test the sticks -- if it's good, click 'Save changes permanently'.", "es": "Centro calibrado. Pruebe los analogicos -- si esta bien, haga clic en 'Guardar cambios permanentemente'."},
    "ctrl.calib_err_prefix": {"pt": "ERRO: {err}", "en": "ERROR: {err}", "es": "ERROR: {err}"},
    "ctrl.calib_err_title": {"pt": "Erro na calibracao", "en": "Calibration error", "es": "Error en la calibracion"},
    "ctrl.calib_range_title": {"pt": "Calibrar alcance do analogico", "en": "Calibrate stick range", "es": "Calibrar rango del analogico"},
    "ctrl.calib_range_body": {"pt": "Na proxima tela, gire os dois analogicos em circulos completos e bem abertos varias vezes (uns 5 a 10 segundos) antes de clicar em Concluir.\n\nSo fica permanente depois que voce clicar em 'Salvar alteracoes permanentemente'.\n\nContinuar?", "en": "On the next screen, rotate both sticks in wide, complete circles several times (about 5 to 10 seconds) before clicking Finish.\n\nIt only becomes permanent after you click 'Save changes permanently'.\n\nContinue?", "es": "En la siguiente pantalla, gire los dos analogicos en circulos completos y bien abiertos varias veces (unos 5 a 10 segundos) antes de hacer clic en Finalizar.\n\nSolo queda permanente despues de que haga clic en 'Guardar cambios permanentemente'.\n\n¿Continuar?"},
    "ctrl.calib_start_err_title": {"pt": "Erro ao iniciar calibracao", "en": "Error starting calibration", "es": "Error al iniciar la calibracion"},
    "ctrl.calib_range_dlg_title": {"pt": "Calibrando alcance dos analogicos", "en": "Calibrating stick range", "es": "Calibrando el rango de los analogicos"},
    "ctrl.calib_range_dlg_body": {"pt": "Gire os dois analogicos em circulos completos e bem abertos, varias vezes. Quando terminar, clique em Concluir.", "en": "Rotate both sticks in wide, complete circles, several times. When you're done, click Finish.", "es": "Gire los dos analogicos en circulos completos y bien abiertos, varias veces. Cuando termine, haga clic en Finalizar."},
    "ctrl.seconds_suffix": {"pt": "{n}s", "en": "{n}s", "es": "{n}s"},
    "ctrl.btn_finish": {"pt": "Concluir", "en": "Finish", "es": "Finalizar"},
    "ctrl.btn_cancel": {"pt": "Cancelar", "en": "Cancel", "es": "Cancelar"},
    "ctrl.calib_range_cancelled": {"pt": "Calibracao de alcance cancelada.", "en": "Range calibration cancelled.", "es": "Calibracion de rango cancelada."},
    "ctrl.calib_range_done": {"pt": "Alcance calibrado. Teste os sticks -- se estiver bom, clique em 'Salvar alteracoes permanentemente'.", "en": "Range calibrated. Test the sticks -- if it's good, click 'Save changes permanently'.", "es": "Rango calibrado. Pruebe los analogicos -- si esta bien, haga clic en 'Guardar cambios permanentemente'."},
    "ctrl.flash_confirm_title": {"pt": "Salvar alteracoes permanentemente", "en": "Save changes permanently", "es": "Guardar cambios permanentemente"},
    "ctrl.flash_confirm_body": {"pt": "Isto grava a calibracao atual de forma PERMANENTE na memoria do controle (vale ate a proxima calibracao, pode ser refeita quantas vezes precisar).\n\nTem certeza?", "en": "This writes the current calibration PERMANENTLY to the controller's memory (valid until the next calibration, which can be redone as many times as needed).\n\nAre you sure?", "es": "Esto graba la calibracion actual de forma PERMANENTE en la memoria del control (vale hasta la proxima calibracion, se puede rehacer cuantas veces sea necesario).\n\n¿Esta seguro?"},
    "ctrl.flash_saved_status": {"pt": "Alteracoes salvas permanentemente.", "en": "Changes saved permanently.", "es": "Cambios guardados permanentemente."},
    "ctrl.flash_saved_title": {"pt": "Salvo", "en": "Saved", "es": "Guardado"},
    "ctrl.flash_saved_body": {"pt": "Calibracao salva permanentemente no controle.", "en": "Calibration saved permanently to the controller.", "es": "Calibracion guardada permanentemente en el control."},
    "ctrl.flash_err_title": {"pt": "Erro ao salvar", "en": "Error saving", "es": "Error al guardar"},

    # -- ch341_spi.py (CH341Error) ------------------------------------------------
    "backend.ch341.wrong_bitness": {"pt": "CH341DLL.dll e de 32 bits, mas este Python e de 64 bits (Windows nao deixa misturar). Rode este programa com um Python de 32 bits -- veja o README.md, secao 'Problema de 32 bits x 64 bits'.", "en": "CH341DLL.dll is 32-bit, but this Python is 64-bit (Windows does not allow mixing them). Run this program with a 32-bit Python -- see README.md, section '32-bit x 64-bit issue'.", "es": "CH341DLL.dll es de 32 bits, pero este Python es de 64 bits (Windows no permite mezclarlos). Ejecute este programa con un Python de 32 bits -- vea el README.md, seccion 'Problema de 32 bits x 64 bits'."},
    "backend.ch341.dll_not_found": {"pt": "Nao foi possivel carregar CH341DLL.dll. Verifique se o driver do CH341A esta instalado e se o arquivo CH341DLL.dll esta na mesma pasta do programa. Detalhe: {detail}", "en": "Could not load CH341DLL.dll. Check that the CH341A driver is installed and that CH341DLL.dll is in the same folder as the program. Detail: {detail}", "es": "No se pudo cargar CH341DLL.dll. Verifique que el driver del CH341A este instalado y que el archivo CH341DLL.dll este en la misma carpeta del programa. Detalle: {detail}"},
    "backend.ch341.reader_not_found": {"pt": "Leitor CH341A nao encontrado. Confira se esta conectado na USB e se o driver aparece no Gerenciador de Dispositivos.", "en": "CH341A reader not found. Check that it's connected via USB and that the driver appears in Device Manager.", "es": "Lector CH341A no encontrado. Verifique que este conectado por USB y que el driver aparezca en el Administrador de dispositivos."},
    "backend.ch341.spi_mode_fail": {"pt": "Falha ao configurar o modo SPI no leitor CH341A.", "en": "Failed to configure SPI mode on the CH341A reader.", "es": "Fallo al configurar el modo SPI en el lector CH341A."},
    "backend.ch341.transfer_fail": {"pt": "Falha na transferencia SPI com o leitor CH341A.", "en": "SPI transfer with the CH341A reader failed.", "es": "Fallo en la transferencia SPI con el lector CH341A."},
    "backend.ch341.timeout_busy": {"pt": "Timeout esperando a NOR ficar pronta (status BUSY nao caiu).", "en": "Timeout waiting for the NOR to become ready (BUSY status did not clear).", "es": "Tiempo de espera agotado esperando que la NOR este lista (el estado BUSY no bajo)."},

    # -- uart_reader.py (UartError) ------------------------------------------------
    "backend.uart.open_fail": {"pt": "Nao foi possivel abrir a porta {port}: {detail}", "en": "Could not open port {port}: {detail}", "es": "No se pudo abrir el puerto {port}: {detail}"},

    # -- dualsense.py (DualSenseError) ---------------------------------------------
    "backend.ds.open_fail": {"pt": "Nao foi possivel abrir o controle: {detail}", "en": "Could not open the controller: {detail}", "es": "No se pudo abrir el control: {detail}"},
    "backend.ds.send_fail": {"pt": "Falha ao enviar comando para o controle: {detail}", "en": "Failed to send command to the controller: {detail}", "es": "Fallo al enviar el comando al control: {detail}"},
    "backend.ds.not_connected": {"pt": "Controle nao conectado.", "en": "Controller not connected.", "es": "Control no conectado."},
    "backend.ds.unlock_fail": {"pt": "Falha ao destravar a memoria do controle: {detail}", "en": "Failed to unlock the controller's memory: {detail}", "es": "Fallo al desbloquear la memoria del control: {detail}"},
    "backend.ds.lock_fail": {"pt": "Falha ao travar/salvar a memoria do controle: {detail}", "en": "Failed to lock/save the controller's memory: {detail}", "es": "Fallo al bloquear/guardar la memoria del control: {detail}"},
    "backend.ds.center_start_unexpected": {"pt": "O controle nao respondeu como esperado ao iniciar a calibracao de centro.", "en": "The controller did not respond as expected when starting center calibration.", "es": "El control no respondio como se esperaba al iniciar la calibracion de centro."},
    "backend.ds.center_sample_fail": {"pt": "Falha durante a amostragem da calibracao de centro.", "en": "Failed during center calibration sampling.", "es": "Fallo durante el muestreo de la calibracion de centro."},
    "backend.ds.center_finish_fail": {"pt": "Falha ao finalizar/gravar a calibracao de centro.", "en": "Failed to finish/write the center calibration.", "es": "Fallo al finalizar/grabar la calibracion de centro."},
    "backend.ds.comm_error_calib": {"pt": "Erro de comunicacao durante a calibracao: {detail}", "en": "Communication error during calibration: {detail}", "es": "Error de comunicacion durante la calibracion: {detail}"},
    "backend.ds.range_start_unexpected": {"pt": "O controle nao respondeu como esperado ao iniciar a calibracao de alcance.", "en": "The controller did not respond as expected when starting range calibration.", "es": "El control no respondio como se esperaba al iniciar la calibracion de rango."},
    "backend.ds.comm_error_range_start": {"pt": "Erro de comunicacao ao iniciar calibracao de alcance: {detail}", "en": "Communication error starting range calibration: {detail}", "es": "Error de comunicacion al iniciar la calibracion de rango: {detail}"},
    "backend.ds.range_finish_fail": {"pt": "Falha ao finalizar a calibracao de alcance.", "en": "Failed to finish range calibration.", "es": "Fallo al finalizar la calibracion de rango."},
    "backend.ds.comm_error_range_finish": {"pt": "Erro de comunicacao ao finalizar calibracao de alcance: {detail}", "en": "Communication error finishing range calibration: {detail}", "es": "Error de comunicacion al finalizar la calibracion de rango: {detail}"},

    # -- nor_parser.py --------------------------------------------------------------
    "backend.parser.chip_unknown": {"pt": "Desconhecido (byte 0x{raw} nao reconhecido -- NAO prosseguir sem confirmar manualmente)", "en": "Unknown (byte 0x{raw} not recognized -- do NOT proceed without manual confirmation)", "es": "Desconocido (byte 0x{raw} no reconocido -- NO continue sin confirmar manualmente)"},
    "backend.parser.truncated": {"pt": "Nao foi possivel ler (arquivo truncado)", "en": "Could not read (file truncated)", "es": "No se pudo leer (archivo truncado)"},
    "backend.parser.size_warning": {"pt": "Tamanho do arquivo ({size} bytes) diferente do esperado ({expected} bytes / 2 MB). NAO prossiga com gravacao.", "en": "File size ({size} bytes) differs from the expected ({expected} bytes / 2 MB). Do NOT proceed with writing.", "es": "El tamano del archivo ({size} bytes) difiere del esperado ({expected} bytes / 2 MB). NO continue con la grabacion."},
    "backend.parser.chip_byte_warning": {"pt": "Byte do seletor de CI HDMI (offset 0x1C4062) nao bate com nenhum valor conhecido. Pode ser uma revisao de placa ainda nao mapeada.", "en": "The HDMI chip selector byte (offset 0x1C4062) does not match any known value. It may be a board revision not yet mapped.", "es": "El byte selector del CI HDMI (offset 0x1C4062) no coincide con ningun valor conocido. Puede ser una revision de placa aun no mapeada."},
    "backend.parser.blank_warning": {"pt": "*** ARQUIVO TOTALMENTE EM BRANCO (todos os bytes 0xFF) -- nao e possivel identificar chip, familia, numero de serie nem MAC porque nao ha dado nenhum neste dump. Isso quase sempre indica FALHA NA LEITURA (mau contato do clipe/leitor, chip nao detectado direito), nao uma NOR realmente apagada -- um PS5 de verdade nao liga com a NOR totalmente vazia. Confira a conexao do leitor CH341A e leia a placa de novo antes de confiar neste arquivo. ***", "en": "*** FILE IS COMPLETELY BLANK (every byte is 0xFF) -- chip, board family, serial number and MAC cannot be identified because there is no data at all in this dump. This almost always means the READ FAILED (bad clip/reader contact, chip not detected properly), not a genuinely erased NOR -- a real PS5 does not power on with a fully blank NOR. Check the CH341A reader connection and read the board again before trusting this file. ***", "es": "*** EL ARCHIVO ESTA COMPLETAMENTE EN BLANCO (todos los bytes son 0xFF) -- no es posible identificar chip, familia de placa, numero de serie ni MAC porque no hay ningun dato en este dump. Esto casi siempre indica una FALLA DE LECTURA (mal contacto del clip/lector, chip no detectado correctamente), no una NOR realmente borrada -- un PS5 real no enciende con la NOR totalmente vacia. Verifique la conexion del lector CH341A y lea la placa de nuevo antes de confiar en este archivo. ***"},
    "backend.parser.blank_chip": {"pt": "Nao detectado (arquivo em branco)", "en": "Not detected (blank file)", "es": "No detectado (archivo en blanco)"},
    "backend.parser.console_type_slim": {"pt": "Edicao Slim", "en": "Slim Edition", "es": "Edicion Slim"},
    "backend.parser.console_type_disk": {"pt": "Disco", "en": "Disk", "es": "Disco"},
    "backend.parser.console_type_digital": {"pt": "Digital", "en": "Digital", "es": "Digital"},
    "backend.parser.idu_disabled": {"pt": "Desativado", "en": "Disabled", "es": "Desactivado"},
    "backend.parser.idu_enabled": {"pt": "Ativado", "en": "Enabled", "es": "Activado"},
    "backend.parser.wifi_rev_warning": {"pt": "Revisao do Wi-Fi (offset 0x1C4068) e EXPERIMENTAL, ainda nao 100% confirmada -- ver NOTES.md.", "en": "The Wi-Fi revision (offset 0x1C4068) is EXPERIMENTAL, not yet 100% confirmed -- see NOTES.md.", "es": "La revision de Wi-Fi (offset 0x1C4068) es EXPERIMENTAL, aun no confirmada al 100% -- ver NOTES.md."},
    "backend.parser.wifi_rev_ambiguous": {"pt": "1.4 (ambiguo com 1.1 -- confirmando)", "en": "1.4 (ambiguous with 1.1 -- confirming)", "es": "1.4 (ambiguo con 1.1 -- confirmando)"},
    "backend.parser.wifi_rev_unknown": {"pt": "desconhecido (byte 0x{raw})", "en": "unknown (byte 0x{raw})", "es": "desconocido (byte 0x{raw})"},
    "backend.parser.disc_yes": {"pt": "sim", "en": "yes", "es": "si"},
    "backend.parser.disc_no": {"pt": "nao", "en": "no", "es": "no"},

    # -- nor_patcher.py (descricoes de patch) ----------------------------------------
    "backend.patch.chip_selector": {"pt": "Seletor de CI HDMI -> {target}", "en": "HDMI chip selector -> {target}", "es": "Selector de CI HDMI -> {target}"},
    "backend.patch.zero_block": {"pt": "Zerar bloco de pareamento (20 bytes)", "en": "Clear pairing block (20 bytes)", "es": "Borrar bloque de emparejamiento (20 bytes)"},
    "backend.patch.zero_flag": {"pt": "Zerar flag de pareamento (1 byte)", "en": "Clear pairing flag (1 byte)", "es": "Borrar bandera de emparejamiento (1 byte)"},
    "backend.patch.counter": {"pt": "Incrementar contador de gravacao (+1)", "en": "Increment write counter (+1)", "es": "Incrementar contador de grabacion (+1)"},
    "backend.patch.checksum_known": {"pt": "Checksum -> valor conhecido pra {target} + REV Wi-Fi 0x{wifi_rev} (tabela confirmada, ver NOTES.md)", "en": "Checksum -> known value for {target} + Wi-Fi REV 0x{wifi_rev} (confirmed table, see NOTES.md)", "es": "Checksum -> valor conocido para {target} + REV Wi-Fi 0x{wifi_rev} (tabla confirmada, ver NOTES.md)"},
    "backend.patch.checksum_unknown": {"pt": "Checksum NAO resolvido pra REV Wi-Fi 0x{wifi_rev} (combinacao ainda nao vista) -- mantido valor antigo, RISCO", "en": "Checksum NOT resolved for Wi-Fi REV 0x{wifi_rev} (combination not seen yet) -- old value kept, RISK", "es": "Checksum NO resuelto para REV Wi-Fi 0x{wifi_rev} (combinacion aun no vista) -- se mantuvo el valor anterior, RIESGO"},
    "backend.patch.donor_mobo_serial": {"pt": "Identificador da placa-mae -> reaproveitado do console lido", "en": "Motherboard identifier -> reused from the read console", "es": "Identificador de la placa base -> reutilizado de la consola leida"},
    "backend.patch.donor_board_serial": {"pt": "Numero de serie do console -> reaproveitado do console lido", "en": "Console serial number -> reused from the read console", "es": "Numero de serie de la consola -> reutilizado de la consola leida"},
    "backend.patch.donor_mac": {"pt": "Endereco MAC -> reaproveitado do console lido", "en": "MAC address -> reused from the read console", "es": "Direccion MAC -> reutilizada de la consola leida"},
    "backend.patch.donor_wifi_mac": {"pt": "Endereco MAC Wi-Fi -> reaproveitado do console lido", "en": "Wi-Fi MAC address -> reused from the read console", "es": "Direccion MAC Wi-Fi -> reutilizada de la consola leida"},
    "backend.patch.donor_mobo_serial_kept": {"pt": "Identificador da placa-mae -> mantido do arquivo-base (console lido nao tinha esse dado -- bloco em branco)", "en": "Motherboard identifier -> kept from the donor file (read console had no data there -- blank block)", "es": "Identificador de la placa base -> mantenido del archivo base (la consola leida no tenia ese dato -- bloque en blanco)"},
    "backend.patch.donor_board_serial_kept": {"pt": "Numero de serie do console -> mantido do arquivo-base (console lido nao tinha esse dado -- bloco em branco)", "en": "Console serial number -> kept from the donor file (read console had no data there -- blank block)", "es": "Numero de serie de la consola -> mantenido del archivo base (la consola leida no tenia ese dato -- bloque en blanco)"},
    "backend.patch.donor_mac_kept": {"pt": "Endereco MAC -> mantido do arquivo-base (console lido nao tinha esse dado -- bloco em branco)", "en": "MAC address -> kept from the donor file (read console had no data there -- blank block)", "es": "Direccion MAC -> mantenida del archivo base (la consola leida no tenia ese dato -- bloque en blanco)"},
    "backend.patch.donor_wifi_mac_kept": {"pt": "Endereco MAC Wi-Fi -> mantido do arquivo-base (console lido nao tinha esse dado -- bloco em branco)", "en": "Wi-Fi MAC address -> kept from the donor file (read console had no data there -- blank block)", "es": "Direccion MAC Wi-Fi -> mantenida del archivo base (la consola leida no tenia ese dato -- bloque en blanco)"},
    "backend.patch.console_type": {"pt": "Tipo de console -> {target}", "en": "Console type -> {target}", "es": "Tipo de consola -> {target}"},

    # -- Atualizacao automatica (GitHub Releases) ------------------------------------
    "update.available_title": {"pt": "Atualizacao disponivel", "en": "Update available", "es": "Actualizacion disponible"},
    "update.available_body": {"pt": "Uma nova versao do PS5 HDMI Tool esta disponivel: {version} (voce esta usando a v{current}).\n\nDeseja baixar e instalar agora? O programa vai fechar sozinho e abrir o instalador no final.", "en": "A new version of PS5 HDMI Tool is available: {version} (you're using v{current}).\n\nDo you want to download and install it now? The program will close itself and open the installer at the end.", "es": "Hay una nueva version de PS5 HDMI Tool disponible: {version} (esta usando la v{current}).\n\n¿Quiere descargarla e instalarla ahora? El programa se cerrara solo y abrira el instalador al final."},
    "update.log.declined": {"pt": "Atualizacao {version} disponivel, mas o usuario optou por nao instalar agora.", "en": "Update {version} available, but the user chose not to install it now.", "es": "Actualizacion {version} disponible, pero el usuario opto por no instalarla ahora."},
    "update.downloading_title": {"pt": "Baixando atualizacao...", "en": "Downloading update...", "es": "Descargando actualizacion..."},
    "update.downloading_body": {"pt": "Baixando a versao {version}...", "en": "Downloading version {version}...", "es": "Descargando la version {version}..."},
    "update.progress_kb": {"pt": "{done} KB / {total} KB", "en": "{done} KB / {total} KB", "es": "{done} KB / {total} KB"},
    "update.ready_title": {"pt": "Atualizacao pronta", "en": "Update ready", "es": "Actualizacion lista"},
    "update.ready_body": {"pt": "O instalador da nova versao vai abrir agora. Este programa vai fechar -- so siga o instalador normalmente (ele substitui a instalacao atual).", "en": "The new version's installer will open now. This program will close -- just follow the installer as usual (it replaces the current install).", "es": "El instalador de la nueva version se abrira ahora. Este programa se cerrara -- solo siga el instalador normalmente (reemplaza la instalacion actual)."},
    "update.launch_err_title": {"pt": "Erro ao abrir o instalador", "en": "Error opening the installer", "es": "Error al abrir el instalador"},
    "update.launch_err_body": {"pt": "O instalador foi baixado, mas nao foi possivel abri-lo automaticamente:\n{err}\n\nBaixe e instale manualmente em:\n{url}", "en": "The installer was downloaded, but couldn't be opened automatically:\n{err}\n\nDownload and install it manually from:\n{url}", "es": "El instalador se descargo, pero no se pudo abrir automaticamente:\n{err}\n\nDescarguelo e instalelo manualmente desde:\n{url}"},
    "update.download_err_title": {"pt": "Erro ao baixar atualizacao", "en": "Error downloading update", "es": "Error al descargar la actualizacion"},
    "update.download_err_body": {"pt": "Nao foi possivel baixar a atualizacao:\n{err}\n\nVoce pode continuar usando a versao atual normalmente.", "en": "Couldn't download the update:\n{err}\n\nYou can keep using the current version normally.", "es": "No se pudo descargar la actualizacion:\n{err}\n\nPuede seguir usando la version actual normalmente."},
}

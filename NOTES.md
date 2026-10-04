# Mapa de offsets da NOR (EDM-xxx, PS5 Slim)

Registro do que já está confirmado e do que ainda falta, pra não perder o
histórico entre sessões. Tamanho de arquivo esperado: 2097152 bytes (2 MB).

## Confirmado (usado em `nor_parser.py`)

| Offset | Campo | Detalhe |
|---|---|---|
| 0x1C4062 | Seletor de CI HDMI | `0x01` = Realtek RTD2175P, `0xFF` = Nuvoton/Panasonic MN864739. Validado em 5 placas originais (rev 1.1, 1.3, 1.4, 1.5) + 1 conversão real. |
| 0x1C4020 (6 bytes) | Endereço MAC | Confirmado comparando placas — valor único por console. |
| 0x1C7200 (~33 bytes) | Bloco de identificação | Texto ASCII cru (contém o que parece ser o número de série no final da string, ex. `MZD1045691`, `NA410261047`). Ver quebra em dois subcampos confirmados logo abaixo. |
| 0x1C7200 (16 bytes) | Identificador da placa-mãe | Ex.: `BD062B1616300100`. Offset conferido contra o código-fonte do [PS5 NOR Modifier](https://github.com/TheCod3rYouTube/PS5NorModifier) (TheCod3r — projeto pro PS5 original, não o Slim) e validado batendo exatamente nas nossas 5 amostras de PS5 Slim. |
| 0x1C7210 (17 bytes) | Número de série do console | Ex.: `E44C01MZD10456917`. Mesma fonte/validação do campo acima — é exatamente o byte seguinte, sem gap. Ainda não confirmado fisicamente contra a etiqueta de um console real (é uma forte correspondência de offset/formato, não 100% confirmado visualmente). |
| 0x1C7230 (13 bytes) | **SKU / modelo do console** | `CFI-2014 B01X`, `CFI-2114 B01X`, `CFI-1214A 01X`. **Resolvido 2026-10-04**: é o SKU comercial impresso na etiqueta/caixa do console, não a revisão de placa EDM-xxx (são duas numerações diferentes — ver "Estudo PS5 Wee Tools" abaixo). Antes exibido como "código CFI não confirmado"; agora com offset fixo e rótulo correto. |
| 0x1C4000 (8 bytes) | Família da placa (EDM-0XX) + leitor de disco | `byte[2]` = número da família (ex. `0x04` → `EDM-04X`), `byte[5]` = tem leitor de disco (`0x01`=sim, `0x03`=não). **Confirmado 7/7** nas nossas amostras reais — bate exatamente com o prefixo EDM-xxx já usado nos nomes de arquivo, mas agora lido direto da NOR, não do nome do arquivo. |
| 0x1C7236 (2 bytes) | Região | Código de 2 dígitos (`14` = México/América Central/do Sul em todas as nossas amostras — bate com a região real dos consoles, todos brasileiros). |
| 0x1C73C0 (6 bytes) | Endereço MAC Wi-Fi | Distinto do MAC "LAN" em 0x1C4020 — mesmo padrão, mesmo offset confirmado em 2 fontes externas independentes. |
| 0x1C8C30 (8 bytes, ordem de bytes invertida) | Firmware atual gravado na NOR | Ex. `14.00.00.39`, `12.60.00.06`. **Corrige nota antiga** (ver "Não encontrados" abaixo) — a versão NÃO fica em texto ASCII (por isso buscas por "13.40" não achavam nada), fica em binário com bytes invertidos. Decodificado e consistente nas 7 amostras (ordem factory ≤ mínima ≤ atual faz sentido logicamente). |

## Campos da "receita de conversão" (Realtek ⇄ Nuvoton/Panasonic)

Baseado na comparação EDM-044 Realtek → EDM-044 Panasonic (mesmo console, conversão real feita por terceiro):

| Offset | Ação | Confiança |
|---|---|---|
| 0x1C4062 | Gravar valor do chip alvo | Alta |
| 0x1C4063–0x1C4069 | **Não tocar** — ligado à revisão do módulo Wi-Fi/Bluetooth, não ao HDMI. Copiar sempre do arquivo original do próprio cliente. Ver seção "Em investigação" abaixo — candidato a codificar o REV do Wi-Fi, ainda não confirmado 100%. | Alta (não tocar) / Média (o que representa) |
| 0x1C40C6–0x1C40D9 (20 bytes) | Zerar (`0xFF`) | Alta — idêntico em todas as placas originais testadas, independente de chip/revisão |
| 0x1C4923 (1 byte) | Zerar (`0xFF`) | Alta — mesmo padrão acima |
| 0x1C49BE–0x1C49BF (2 bytes) | Incrementar em +1 o valor já existente no arquivo do cliente (parece contador de gravação da flash, não precisa saber fórmula) | Média — só 1 exemplo confirmado de incremento |
| 0x1C41FE–0x1C41FF (2 bytes) | **Não é checksum do MAC/bloco variável.** Descoberto em 2026-10-02: é uma tabela fixa, função só de (chip 0x1C4062, byte REV Wi-Fi 0x1C4068) — ver abaixo | Alta confiança no comportamento (constante por combinação) — algoritmo exato ainda não encontrado, mas não precisa mais dele: basta a tabela |

### Descoberta 2026-10-02: 0x1C41FE-FF não depende do MAC

Comparando pares de consoles com o **mesmo** par (chip, REV Wi-Fi) mas MAC
diferente — `EDM-041` vs `EDM-44 convertido` (chip=0xFF, wifi=0x11) e
`EDM-O33` vs `EDM-030` (chip=0xFF, wifi=0x12) — o valor em 0x1C41FE-FF saiu
**byte a byte idêntico** nos dois casos, apesar do MAC ser totalmente
diferente. Comparando o bloco inteiro 0x1C4000-0x1C4200 desses pares, as
**únicas** diferenças são o MAC (0x1C4020-25) e um outro par de bytes em
0x1C403E-3F (provavelmente um checksum do MAC, ainda não resolvido, mas
irrelevante pra essa descoberta). Isso descarta de vez a hipótese antiga
("checksum do bloco que contém o MAC") — testar >25 CRC/Fletcher contra o
bloco com o MAC nunca ia bater porque o MAC não entra na conta.

Tabela confirmada até agora (todas as amostras que temos):

| chip (0x1C4062) | REV Wi-Fi (0x1C4068) | 0x1C41FE-FF | Confirmado em |
|---|---|---|---|
| 0x01 (Realtek) | 0x11 | `45 86` | EDM-044 |
| 0x01 (Realtek) | 0x21 | `32 90` | EDM-050 |
| 0xFF (Nuvoton/Panasonic) | 0x21 | `34 8f` | EDM-051 |
| 0xFF (Nuvoton/Panasonic) | 0x12 | `ad a0` | EDM-O33 **e** EDM-030 (2 amostras, MAC diferente, bateu igual) |
| 0xFF (Nuvoton/Panasonic) | 0x11 | `e7 0e` | EDM-041 **e** EDM-44 convertido (2 amostras, MAC diferente, bateu igual) |

Tentado sem sucesso achar o algoritmo exato (pra generalizar pra combinações
ainda não vistas): >20 variantes de CRC-16 (CCITT, ARC, MODBUS, USB, X-25,
Kermit, etc., nos dois byte-orders) e soma simples/Fletcher-16/XOR-fold,
sobre o MAC isolado, sobre os 8 bytes 0x1C4062-69, e sobre os dois
concatenados — nenhum bateu. Pode ser uma tabela de fato "cravada" na
fábrica (não calculada), não um checksum matemático.

**Desbloqueio prático:** pra converter um console Realtek→Panasonic/Nuvoton
(ou vice-versa) cujo byte de REV Wi-Fi já seja um dos 3 valores confirmados
acima (0x11, 0x12 ou 0x21), já sabemos o valor exato a gravar em 0x1C41FE-FF
sem precisar do algoritmo — é só consultar a tabela. Pra um console com um
byte de REV Wi-Fi novo (não listado), ainda não temos como prever o valor —
precisa de uma amostra real original com esse byte pra descobrir.

## Estudo 2026-10-04: PS5 NOR Modifier (TheCod3r/PS5NorModifier)

Repositório sugerido pelo usuário: https://github.com/TheCod3rYouTube/PS5NorModifier
— C# WinForms, projeto do mesmo autor do uartcodes.com. **O próprio README
diz "PS5 Slim not currently supported"** — é feito pro PS5 original (Phat),
não pro Slim. Por isso os offsets de lá não são assumidos como válidos aqui
sem confirmar contra nossas próprias amostras.

O que testamos e **confirmou bater** nos nossos dumps de PS5 Slim (mesmo
offset, campo limpo em todas as 5 amostras):
- `0x1C4020` (MAC) — já era o nosso próprio offset, confirma consistência.
- `0x1C7200` (16 bytes) e `0x1C7210` (17 bytes) — os dois subcampos novos
  da tabela acima (identificador da placa-mãe + número de série do console).

O que **não bateu** como esperado: o campo "variante/região da placa" deles
(`0x1c7226`, 19 bytes, sufixos tipo "01A"=EUA/Canadá, "02A"=Oceania etc.) —
nas nossas amostras de Slim esse offset cai bem em cima do início do nosso
já conhecido código `CFI-XXXX`, sem nenhum sufixo de região de 3 caracteres
antes. Ou o layout diverge um pouco aqui entre PS5 e PS5 Slim, ou o campo de
região fica em outro offset no Slim — não implementado, não confirmado.

Achado que vale testar depois (não implementado ainda): o programa deles
consulta códigos de erro **ativamente** via UART, enviando comandos de texto
tipo `errlog 0`, `errlog 1` ... `errlog 10` e `errlog clear` (com um checksum
simples — soma dos valores ASCII do comando & 0xFF, formato `comando:XX`),
em vez de só escutar o log cru como a nossa aba "Leitor UART" faz hoje. Se o
firmware de debug do PS5 Slim aceitar os mesmos comandos (provável, mesma
família de SoC), dava pra adicionar um botão "Consultar códigos de erro" que
manda esses comandos e já devolve a lista de erros gravados, sem precisar
esperar o usuário religar o console e capturar o boot inteiro. Fica registrado
aqui como ideia de melhoria futura, não testado ainda.

## Estudo 2026-10-04: PS5 Wee Tools (andy-man/ps5-wee-tools)

Repositório sugerido pelo usuário: https://github.com/andy-man/ps5-wee-tools
— Python, com suporte explícito a PS5 Slim desde a v0.1.5 do changelog
("Slim model support"). Muito mais completo que o PS5NorModifier: tem um
mapa inteiro de offsets em `utils/sflash.py` (`NOR_AREAS` e `NOR_PARTITIONS`).
Testamos TODOS os campos relevantes contra nossas 7 amostras reais.

**Confirmados e já implementados em `nor_parser.py`/`gui.py`** (ver tabela no
topo deste arquivo): SKU (0x1C7230), família da placa + leitor de disco
(0x1C4000), região (0x1C7236), MAC Wi-Fi (0x1C73C0), firmware atual
(0x1C8C30). `MB_SN`/`SN` (0x1C7200/0x1C7210) bateram de novo, terceira fonte
confirmando o mesmo que já tínhamos do PS5NorModifier.

**Confirmados mas NÃO implementados na interface ainda** (decodificam limpo
nas 7 amostras, mas não são essenciais pro fluxo de conversão de chip —
ficam aqui documentados pra caso sirvam depois):
- `KIBAN` (0x1C7250, 13 bytes) — número sequencial de produção (ex.
  `0000027419298`); EDM-044 e sua conversão real pro Nuvoton bateram igual
  (mesmo console), EDM-O33/EDM-030 vieram sequenciais (`...136`/`...137`,
  provavelmente mesmo lote de fabricação).
- `SOCUID` (0x1C7260, 16 bytes) — binário de alta entropia, provável
  ID único de chip/chave criptográfica. O próprio projeto de origem marca
  como "Social UID?" (incerto).
- `FW_M`/`FW_F` (0x1C8C10/0x1C8C20) — firmware mínimo e de fábrica, mesmo
  formato do firmware atual. Ordem bate logicamente (fábrica ≤ mínimo ≤
  atual) em todas as amostras.
- `MODEL`/`MODEL2` (0x1C7011/0x1C7038) — nas nossas 4 amostras "Slim"
  (EDM-044/050/051/041, todas sem leitor de disco) deu `0x01`/`0x8D`; nas 2
  amostras com leitor de disco (EDM-O33/EDM-030) deu `0x02`/`0x89`. O
  projeto de origem rotula isso como "Slim/Disc/Digital edition", mas pela
  nossa amostra a correlação mais consistente é com presença de leitor de
  disco (Digital vs Disc), não com geração Slim — rótulo exato ainda
  incerto, não implementado até confirmar com mais amostras (faltaria uma
  Slim COM leitor de disco pra desambiguar).

**Conexão com a investigação do I2C (ver seção abaixo):** o mapa de
partições (`NOR_PARTITIONS`) mostra que a região onde achamos ~490 mil bytes
diferentes entre EDM-050/EDM-051 (`emc_ipl_b`, 0x082000-0x100000) é a
partição de firmware do **EMC** (microcontrolador embarcado da própria
Southbridge) — faz sentido ter muita diferença binária entre consoles
distintos (versões/builds de firmware diferentes por lote de fábrica), e
reforça a conclusão de que isso não tem relação com o chip HDMI: a conversão
real do EDM-044 (mesmo console) não tocou nem um byte dessa partição.

## Confirmado 2026-10-04: não existe bloco de config I2C fora do que já patcheamos

Dúvida levantada: o CI HDMI (Realtek ou Nuvoton) se comunica com a Southbridge
(CXD90069GG) via I2C — será que existe, em algum outro lugar da NOR, um bloco
de configuração do barramento I2C (endereço de slave, etc.) que ainda não
identificamos e que precisaria ser ajustado na conversão?

**Teste:** diff byte a byte do arquivo **inteiro** (2.097.152 bytes, não só o
bloco 0x1C4000-0x1C4900) entre `EDM-044 REALTEK ... REV. 1.4.bin` (original) e
`EDM-44 REALTEK --- PANASONIC ... .bin` (mesmo console físico, convertido de
verdade por terceiro). Isolando a variável certa — só o chip HDMI mudou, nada
mais nesse console.

**Resultado:** exatamente **25 bytes diferentes em todo o arquivo**, e todos
caem dentro dos 5 blocos já catalogados acima (seletor 0x1C4062, zerar
0x1C40C6-D9, checksum 0x1C41FE-FF, zerar 0x1C4923, contador 0x1C49BF). Nenhuma
outra diferença em lugar nenhum do arquivo de 2 MB.

**Conclusão:** não existe, nesta NOR de 2 MB, nenhum bloco separado de
configuração do barramento I2C do CI HDMI. A explicação mais provável é que o
firmware da própria CXD90069GG (que não mora nesta flash — essa NOR funciona
como uma "EEPROM de configuração da placa", pequena demais pra conter o
firmware da Southbridge) já contém os dois drivers I2C embutidos (Realtek e
Nuvoton), com endereço/protocolo fixos no firmware; o byte seletor
(0x1C4062) só decide qual dos dois usar no boot. Se um console convertido
der erro de UART `C0810303` (falha I2C Southbridge↔CI HDMI, confirmado em
kasynparts.com/ps5-repair-wiki-hdmi-subsystem-mn864739) mesmo com o patch
certo, é indício de problema físico (trilha SDA/SCL, solda, chip defeituoso),
não de configuração faltando na NOR.

**Nota sobre falso-ruído:** um diff do arquivo inteiro entre EDM-050 (Realtek)
e EDM-051 (Nuvoton) — consoles **diferentes**, mesma REV 1.5 — deu ~490 mil
bytes diferentes espalhados pelo arquivo todo (dados únicos por aparelho). Não
serve como evidência pra essa pergunta porque não isola a variável do chip —
só o par "mesmo console, convertido de verdade" serve pra esse teste.

## Em investigação: REV do módulo Wi-Fi/Bluetooth

**Importante:** o "REV 1.x" nos nomes dos arquivos (REV 1.1, 1.3, 1.4, 1.5) é a
revisão do **módulo Wi-Fi/Bluetooth**, não da placa-mãe (confirmado pelo
usuário em 2026-10). Ainda **não implementado no programa** — aguardando mais
amostras pra confirmar antes de mostrar na interface.

Candidato encontrado em 2026-10-03: byte **0x1C4068**, cruzando as 5 amostras
originais conhecidas:

| REV (do nome do arquivo) | Valor em 0x1C4068 |
|---|---|
| 1.1 (EDM-041, Nuvoton) | `0x11` |
| 1.3 (EDM-O33, Panasonic) | `0x12` |
| 1.3 (EDM-030, Panasonic/Nuvoton — CFI-1214A igual ao EDM-O33) | `0x12` |
| 1.4 (EDM-044, Realtek) | `0x11` |
| 1.5 (EDM-050 Realtek **e** EDM-051 Nuvoton) | `0x21` |

EDM-030 reforça a confiança nesse byte: bateu `0x12` igual ao EDM-O33, e os
dois dumps têm o mesmo código CFI (`CFI-1214A 01X`) e o mesmo bloco inteiro
0x1C4062-69 — mesmo módulo Wi-Fi, consoles diferentes (MAC diferente). Essa
mesma comparação foi a base da descoberta do checksum acima.

Ponto forte: EDM-050 e EDM-051 são rev 1.5 com chips HDMI diferentes (Realtek
vs Nuvoton) e bateram exatamente igual — forte indício de que o grupo de
bytes 0x1C4063-0x1C4069 depende da revisão, não do chip HDMI nem do console
individual.

**Pendência:** REV 1.1 e REV 1.4 deram o mesmo valor (`0x11`). Com só 1
amostra de cada, não dá pra saber se isso é correto (as duas revisões de
placa realmente usam o mesmo módulo Wi-Fi fisicamente) ou se esse byte não é
exatamente o que pensamos. **Resolver com as novas NOR's que o amigo do
usuário vai mandar.** Idealmente conseguir uma 2ª amostra de REV 1.1 ou REV
1.4 pra confirmar se o valor se repete.

Não encontrado em lugar nenhum: o **modelo/part number** do módulo Wi-Fi
(tipo "AW-NB222NF") como texto. Só existe esse código numérico de revisão —
não achamos nada que identifique a peça em si.

## Não encontrados / não implementados ainda

- Revisão da placa-mãe (se for diferente do REV do Wi-Fi) — não aparece como string no dump.
- Modelo/part number do módulo Wi-Fi — não identificado (ver acima).
- ~~Versão de firmware do sistema — provavelmente não fica armazenada nesta NOR~~ **Errado, corrigido 2026-10-04**: fica sim, só que em binário (bytes invertidos), não em texto ASCII — por isso a busca por texto não achava nada. Ver tabela "Confirmado" acima (offset 0x1C8C30).

## Leitor UART (aba separada do programa)

Não temos (nem copiamos) um catálogo de códigos de erro UART dentro do
programa — o banco de dados é mantido por terceiros e fica desatualizado
rápido. A aba "Leitor UART" só captura o log bruto e tem botões que abrem
no navegador as referências usadas pela comunidade pra consultar o código
na hora:

- `psdevwiki.com/ps5/Southbridge_Error_Codes` — fonte "raiz" citada por
  praticamente todas as ferramentas de bancada (incluindo o Console Service
  Tool).
- `uartcodes.com` — banco de dados pesquisável mantido pelo TheCod3r.
- Tópico "PS5 UART commands" no GBAtemp — discussão da comunidade.
- `forterfix.com/ps5_uart` — ferramenta online que foi o ponto de partida
  dessa pesquisa.

Fluxo confirmado (do guia do Console Service Tool): módulo UART de **3.3V**
(nunca 5V), TX↔RX cruzados (TX da placa no RX do módulo e vice-versa) + GND
em comum. A leitura é feita em 4 estados do aparelho — standby, boot
inicial, ligado, e um segundo boot — salvando e limpando o log entre cada
estado pra não misturar os códigos.

Alguns códigos confirmados via busca (achados soltos, não é lista completa):
`80810001` (falha geral de energia), `80910002` (erro no PMIC do SSD),
`80871001` (erro de DDR4), `80891001` (erro no controlador SSD/DDR4),
`808F0001` (timeout do chip TPM 2.0).

## Arquivos de referência usados nesta análise

Pasta `NOR's/`:
- EDM-044 REALTEK HDMI E J20H104 REV. 1.4.bin (original)
- EDM-44 REALTEK --- PANASONIC HDMI E J20H104 REV .bin (mesmo console, convertido por terceiro)
- EDM-050 REALTK HDMI E J20H104 REV. 1.5.bin (original)
- EDM-051 NUVOTON HDMI E J20H104 REV. 1.5.BIN (original)
- EDM-O33 PANASONIC HDMI E J20H100 REV 1.3.bin (original)
- EDM-041 NUVOTON HDMI E J20H104 REV 1.1 .BIN (original)
- EDM-030 CFI-1214A 01X .bin (original, Panasonic/Nuvoton — confirmado pelo programa, mesmo grupo chip/REV Wi-Fi do EDM-O33)

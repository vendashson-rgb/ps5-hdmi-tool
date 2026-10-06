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

**Implementado em 2026-10-05 (v1.0.2+)**: o programa deles consulta códigos
de erro **ativamente** via UART, enviando comandos de texto tipo `errlog 0`,
`errlog 1` ... `errlog 10` e `errlog clear` (com um checksum simples — soma
dos valores ASCII do comando & 0xFF, formato `comando:XX`). Implementamos
isso na aba "Leitor UART": botão "Ler códigos de erro" (manda `errlog 0`
até `errlog 10` com um intervalo de 0.3s entre cada) e "Limpar códigos de
erro no console" (`errlog clear`, com confirmação — irreversível). Função
`checksum_command()` em `uart_reader.py`, conferida manualmente (`errlog 0`
→ `errlog 0:DB`). **Ainda não testado com hardware real neste projeto** —
não sabemos se o firmware de debug do PS5 Slim aceita exatamente os mesmos
comandos do PS5 original (mesma família de SoC, mas não confirmado). Ao
testar pela primeira vez: se não vier resposta nenhuma, confira baud/pinagem
antes de desconfiar do comando.

**Decisão consciente de escopo**: o usuário trouxe um print de uma ferramenta
de terceiros (não identificada, sem link) mostrando uma tabela muito mais
rica — com Slot/Data/Hora, Prioridade (Low/Medium/High/Severe) e descrição
completa do erro por linha. Não implementamos esse nível de interpretação
porque não temos o código-fonte dessa ferramenta pra confirmar o formato
exato da resposta nem a classificação de prioridade — inventar isso seria
arriscado (pode levar alguém a ignorar um erro sério achando que é "Low").
Por enquanto mostramos a resposta crua (igual ao resto da aba UART, com a
mesma coloração por palavra-chave) e deixamos a interpretação pro catálogo
externo (psdevwiki/uartcodes.com, já linkados na aba).

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

## Checagem cruzada 2026-10-04: tabela de blog (bank/block da sflash)

Usuário trouxe uma tabela (print de blog, sem URL) com offsets em termos de
"Bank/Block" da sflash do PS5. Testamos os offsets relevantes contra nossas
amostras reais -- resultado principal foi **confirmar** (não corrigir) o que
já tínhamos:

- `0x1C7230` ("hw_model" na tabela, 32 bytes) — mesmo campo que já
  implementamos como SKU (13 bytes). Confirma que o padding depois do texto
  é `0x00`, não `0xFF` — não muda nada na nossa extração (ela já corta no
  tamanho certo antes de chegar no padding).
- `0x1C8068` (4 bytes) — **mesmo valor** do nosso campo "firmware atual" em
  `0x1C8C30` (testado em 3 amostras, bateu 3/3). É um dado duplicado na NOR,
  não um campo novo.
- Região "backup" espelhada em `+0x3000` (os mesmos campos de firmware
  repetidos em outro bank) — bate com a constante `BACKUP_OFFSET = 0x3000`
  já vista no ps5-wee-tools.

**Divergência encontrada entre as duas fontes externas** (ps5-wee-tools vs
essa tabela), sem impacto pra gente porque não expomos nenhum dos dois campos
na interface: ps5-wee-tools chama `0x1C8C10` de "Minimum FW" e `0x1C8C20` de
"Factory FW"; a tabela do blog inverte os dois. Registrado aqui só pra não
confiar cegamente em nenhuma das duas fontes se um dia implementarmos esses
campos.

## Estudo 2026-10-04: fórum stetofix (post de jul/2023, pré-PS5 Slim)

Usuário trouxe um print de fórum (stetofix.com, tópico "NOR PS5 / Dumps
Flash", usuário "Calvin", jul/2023 — **anterior ao lançamento do PS5 Slim**,
o que explica por que ele não menciona o valor `0x01` em `0x1C7011` que a
gente já usa pra "sem leitor de disco"). Testamos os 3 offsets que ele cita
e a gente ainda não tinha, contra 4 amostras reais (2 sem leitor de disco:
EDM-044/EDM-050; 2 com leitor de disco: EDM-O33/EDM-030):

- **`0x1C7270` ("Chave BD?", só em dumps de BD) — confirmado 4/4.** Vazio
  (`0xFF`) nos 2 consoles sem leitor de disco, com dado real nos 2 consoles
  com leitor de disco. Correlação perfeita, reforça (de forma independente)
  a deteccao de leitor de disco que já temos via `0x1C4000` byte[5]. Não
  implementado na interface — serve como sinal extra de confirmação, não
  como campo novo necessário.
- **`0x1C6000` (MACs de controle Bluetooth pareado, a cada 8 bytes) —
  confirmado, informação nova.** É uma lista real de MACs (6 bytes + 2 bytes
  extra cada) até bater num run de `0xFF`. Quantidade variou bastante entre
  consoles (1 a 4+ entradas nas amostras testadas, um dos consoles veio tão
  cheio que passou da janela de 64 bytes testada). **Candidato forte a
  funcionalidade futura**: dá pra mostrar "quantos controles já foram
  pareados nesse console" — útil pra quem compra placa usada querer saber se
  ela já foi utilizada antes. Não implementado ainda.
- **`0x1C73C0` ("3 MACs") — confirmado, sem necessidade de mudar nada.** São
  3 MACs sequenciais (ex. terminando em `:33`/`:34`/`:35`) — o nosso campo já
  captura o primeiro (o relevante), os outros dois são sempre +1/+2 dele.
- **`0x1C8C34` ("FW Versionnr") — não é um campo novo nem diverge do
  nosso.** Refazendo a conta com o nosso algoritmo real (inverter os 8 bytes
  de `0x1C8C30` e pegar os 4 primeiros), `0x1C8C34` cai exatamente na metade
  de trás do mesmo campo de 8 bytes que já usamos — é a mesma informação,
  só descrita a partir de outro ponto inicial. Mais uma confirmação
  independente (4ª fonte agora) do nosso campo de firmware atual.

## Testado e implementado 2026-10-04: versão de firmware do EMC

Revisitando o `andy-man/ps5-wee-tools` (release v0.1.8, link direto que o
usuário trouxe) — já tínhamos estudado esse projeto a fundo antes; essa
release específica não trouxe offset novo de NOR, só recursos do app deles
(validação de MD5, 20 idiomas, etc.) e menciona uma versão PRO paga/fechada
com "patcher de SouthBridge (EMC)". O que valia testar: a forma como eles
leem a versão do **firmware do EMC** (coprocessador da própria Southbridge),
diferente da "versão do sistema" que já temos.

**Método**: as partições `emc_ipl_a` (offset 0x004000) e `emc_ipl_b` (offset
0x082000, cada uma 0x7E000 bytes) são containers no formato **SLB2** (magic
`"SLB2"`, header com lista de entradas nome+offset+tamanho — formato próprio
da Sony, não documentamos antes). Dentro de cada uma tem uma entrada chamada
`"C0008001"` cujos bytes 0x0A-0x10 decodificam a versão do EMC (3 campos
little-endian de 2 bytes cada, formatados como `major.minor.build`).

**Resultado — bateu nas 4 amostras testadas, com validação cruzada tripla**:
o MD5 de cada partição `emc_ipl_a`/`emc_ipl_b` (truncada no tamanho
declarado no próprio header SLB2) bate **exatamente** com a tabela
`EMC_IPL_MD5` do `data/data.py` do mesmo projeto (que mapeia MD5 → versão
do EMC → lista de firmwares de sistema compatíveis) — e a versão de sistema
que aparece nessa tabela pra cada MD5 bate com o nosso campo `fw_current`
(0x1C8C30) já implementado, sempre pro slot marcado como ativo
(`ACT_SLOT`, offset 0x001000):

| Amostra | emc_ipl ativo (slot) | Versão EMC decodificada | Nosso `fw_current` | Bate? |
|---|---|---|---|---|
| EDM-044 | B | 1.30.0 | 14.00.00.39 (FW 14.00) | Sim — MD5 da 1.30.0 na tabela lista fw:['14.00'] |
| EDM-050 | A | 1.26.0 | 12.20.00.05 (FW 12.20) | Sim — MD5 da 1.26.0 lista fw inclui '12.20' |
| EDM-051 | B | 1.26.0 | 12.60.00.06 (FW 12.60) | Sim — mesma versão EMC, fw inclui '12.60' |
| EDM-O33 | B | 1.28.1 | 13.60.00.07 (FW 13.60) | Sim — MD5 da 1.28.1 lista fw:['13.60'] |

Três fontes de dado completamente independentes (nosso offset NVS já
confirmado, o parser SLB2 novo, e a tabela MD5 do projeto externo)
concordando perfeitamente — confiança alta nisso.

**Atualização 2026-10-04 (v1.0.2)**: implementado. Novo módulo `slb2.py`
(parser genérico do container, ~40 linhas) + `extract_act_slot()` e
`extract_emc_version()` em `nor_parser.py`. Mostra a versão do slot **ativo**
e do **backup** (não embutimos a tabela MD5→firmware-de-sistema — ela muda a
cada firmware novo do PS5 e exigiria manutenção constante; mostramos só a
versão decodificada do EMC, que não depende de tabela nenhuma). Campo novo
"Firmware do EMC (ativo / backup)" na aba "Analisar arquivo" e no log da aba
de hardware, nos 3 idiomas.

## Implementado 2026-10-05/06: conversão via arquivo-base

Em vez de aplicar o patch pontual nos bytes conhecidos (seletor de chip,
bloco de pareamento, checksum, contador — método que já tínhamos), este
método alternativo usa um **arquivo-base** (.bin completo de 2 MB de outro
console, já configurado com o chip HDMI e a família de placa certos pra
aquele modelo — ex. `EDM-040-J100-PANASONIC.BIN` pra uma EDM-04X,
`EDM-051-PANASONIC-J104.BIN` pra uma EDM-05X) e só regrava nele o número de
série do console lido, descartando o resto do conteúdo original do cliente.

**Risco identificado antes de implementar**: a ideia original só reaproveita
o número de série, não o MAC. Isso significa que vários consoles diferentes
convertidos com o mesmo arquivo-base sairiam todos com o **mesmo endereço
MAC** (LAN e Wi-Fi) — o arquivo-base tem um MAC fixo gravado nele. Isso
gera conflito de rede real se dois desses consoles acabarem na mesma rede
Wi-Fi/roteador (endereço MAC duplicado é um problema de rede clássico, não
é exagero). Perguntado ao usuário — decisão: reaproveitar o MAC também, não
só o número de série.

**Implementado** (`nor_patcher.apply_donor_identity()`): recebe o
arquivo-base e o dump do console lido, copia o arquivo-base inteiro e
regrava por cima dele, nos offsets já confirmados:
- `0x1C7200` (16B) identificador da placa-mãe
- `0x1C7210` (17B) número de série do console
- `0x1C4020` (6B) MAC LAN
- `0x1C73C0` (6B) MAC Wi-Fi

Tudo o resto do arquivo-base (chip HDMI, SKU, região, firmware, checksum
0x1C41FE-FF, etc.) fica exatamente como veio — a responsabilidade de o
arquivo-base estar correto (chip e família certos) é de quem escolhe o
arquivo, não do programa. Por isso a interface mostra o chip e a família
detectados no arquivo-base (via `parse_nor()`) e pede confirmação explícita
antes de prosseguir, pra reduzir risco de usar o arquivo errado numa placa
de cliente.

Testado com `EDM-044` como arquivo-base e `EDM-051` como "console lido"
(pares reais que já tínhamos, só pra validar o mecanismo) — número de
série e MAC transplantados corretamente, chip do arquivo-base preservado.

Botão "Usar arquivo-base..." na aba de hardware, ao lado do fluxo de patch
já existente (os dois continuam disponíveis — esse é um método alternativo,
não substitui o patch pontual, que continua sendo a opção mais testada
quando não se tem um arquivo-base disponível).

## Implementado 2026-10-05: conversão via arquivo-base automática na aba "Analisar arquivo .bin"

Extensão do mecanismo acima (`apply_donor_identity()`) pra aba de análise de
arquivo, que trabalha em cima de um `.bin` já aberto em disco (não exige
leitura de hardware). Diferença em relação ao botão da aba de hardware: ali
o usuário escolhe manualmente o arquivo-base (diálogo de arquivo); aqui a
escolha é **automática**, baseada na família de placa detectada no arquivo
aberto (`NorInfo.board_family`, ex. `EDM-05X`).

Os arquivos-base ficam empacotados dentro do próprio programa, em
`donor_files/` (novo diretório de recurso, ao lado de `images/` e
`drives/` — adicionado ao `datas` do `.spec` do PyInstaller pra ir junto no
`.exe`). `gui._load_donor_files()` varre `donor_files/*.bin` na
inicialização, roda `parse_nor()` em cada um e monta o mapeamento
`família -> caminho do arquivo` (`{"EDM-04X": .../EDM-040-J100-PANASONIC.BIN,
"EDM-05X": .../EDM-051-PANASONIC-J104.BIN}` com os dois arquivos atuais).
Isso é deliberadamente genérico — qualquer arquivo-base novo colocado em
`donor_files/` entra automaticamente no mapeamento pela família que ele
mesmo reporta, sem precisar mexer no código pra cada família nova.

Ao analisar um arquivo (`_analyze_file`), se a família detectada tiver um
arquivo-base correspondente em `donor_files/`, o botão "Usar arquivo-base
automático" é habilitado e uma linha no log avisa qual arquivo seria usado.
Ao clicar, mostra a mesma confirmação da aba de hardware (chip + família
detectados no arquivo-base) antes de rodar `apply_donor_identity()` e
habilitar "Salvar NOR com patch..." (reaproveita o mesmo botão/fluxo de
salvar que o patch pontual já usava).

Testado (smoke test headless): abrindo o `EDM-051 NUVOTON ... REV. 1.5.BIN`
real como "arquivo do cliente", família detectada `EDM-05X` bate com
`EDM-051-PANASONIC-J104.BIN`, resultado confirmado com número de série,
MAC e MAC Wi-Fi do cliente transplantados e chip/SKU do arquivo-base
preservados.

**Importante sobre os arquivos em `donor_files/`**: como esses dois `.bin`
passam a ir junto no `.exe` publicado (empacotados via PyInstaller) e
também no histórico do repositório no GitHub (público), os campos de
número de série e MAC/MAC Wi-Fi **originais** dos dois arquivos-base foram
zerados antes de versionar (`0x1C7200`, `0x1C7210`, `0x1C4020`, `0x1C73C0`
-> tudo `0x00`). Isso não muda o comportamento em nada, porque
`apply_donor_identity()` sempre sobrescreve esses mesmos 4 campos com os
dados do console lido antes de usar o arquivo — os valores originais nunca
chegam a ser usados. A troca só existe pra não publicar número de
série/MAC reais de placas físicas ("database/" já é ignorado no git por
esse mesmo motivo, ver `.gitignore`).

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

## Diagnosticado e corrigido 2026-10-06: dumps "não identificados" eram leituras em branco, não gap de detecção

Usuário adicionou mais amostras na pasta `NOR's/` e reportou que, ao ler
essas placas, o programa mostrava como "não identificado". Três arquivos
novos (`EDM-010 OANASONIC HDMI J20H100 REV 1.0 DISCO.bin`, `EDM-020
PANASONIC HDMI J20H100 REV 1.2 DISCO.bin`, `EDM-050 REALTECK HDMI J20H104
REV 1.5.bin` — note a falta do "E" no nome, diferente do `EDM-050 REALTK
HDMI E J20H104 REV. 1.5.bin` que já funcionava).

**Diagnóstico** (`data.count(0xFF) == len(data)`): os 3 arquivos têm **os
2.097.152 bytes inteiros em `0xFF`** — não é um offset diferente pra essa
geração de placa, é um dump **100% vazio**, literalmente sem nenhum byte
de dado em lugar nenhum do arquivo (bloco de identidade, MAC, firmware,
tudo). Isso não é "família de placa ainda não mapeada" — é a **ausência
total** de dados.

Isso quase certamente **não é uma NOR realmente apagada**: um PS5 real
não liga com a NOR inteiramente vazia (o firmware de boot, dados do EMC
etc. também ficam lá). O padrão clássico de "tudo 0xFF" é o que aparece
quando a leitura falha por mau contato do clipe/leitor (barramento
flutuando em nível alto) ou o chip não foi detectado corretamente — ou
seja, é um **problema de leitura de hardware**, não algo que o parser
consiga "identificar melhor". Recomendado ao usuário: reler essas 3 placas
físicas com mais cuidado na conexão do CH341A antes de confiar nesses
arquivos.

**Dois bugs de software reais encontrados nesse processo, corrigidos**:
1. `extract_board_family()` montava a string da família direto com
   `f"EDM-0{chunk[2]}X"`, sem checar se `chunk[2]` é um dígito decimal
   plausível (0-9). Com o bloco em branco, `chunk[2] == 0xFF` (255 em
   decimal) virava a família sem sentido `"EDM-0255X"` em vez de "não
   identificado". Corrigido: só monta a string se `chunk[2] <= 9`, senão
   devolve `None` (mesmo tratamento que o flag de leitor de disco já tinha
   pra valor desconhecido).
2. Antes não existia nenhuma forma de distinguir "chip Nuvoton confirmado"
   de "bloco em branco" — os dois batem com o mesmo byte `0xFF` no seletor
   de chip (offset 0x1C4062), então um dump vazio aparecia como "Nuvoton
   detectado", o que é enganoso. Adicionada `nor_parser.is_blank()`
   (`True` se o arquivo inteiro é `0xFF`) — quando `True`, `parse_nor()`
   reporta o chip como "Não detectado (arquivo em branco)" em vez de
   "Nuvoton", e insere um aviso bem explícito no topo da lista de warnings
   explicando o diagnóstico acima (provável falha de leitura, não NOR
   vazia de verdade).

Testado contra todas as amostras da pasta `NOR's/` (via `parse_nor()`
direto e também pela aba "Analisar arquivo .bin" da interface): os 8
arquivos com dado real continuam identificando exatamente igual a antes
(nenhuma regressão); os 3 arquivos em branco agora mostram o aviso claro
em vez da família quebrada `"EDM-0255X"` com chip "Nuvoton" enganoso.

## Implementado 2026-10-06: "Regenerar com arquivo-base..." (manual) na aba "Analisar arquivo .bin" + correção no transplante de identidade

Consequência direta do diagnóstico acima: pra um arquivo totalmente em
branco (como os EDM-010/020 do usuário), a família da placa não dá pra
detectar automaticamente — não tem dado nenhum no arquivo pra isso. Então
o botão automático ("Usar arquivo-base automático") nunca vai habilitar
pra esses casos, por mais arquivos-base que a gente adicione em
`donor_files/`.

**Novo botão** `btn_file_donor_manual` ("Regenerar com arquivo-base..."),
na aba de análise de arquivo, ao lado do automático. Fica habilitado
sempre que o arquivo carregado tem o tamanho certo (2 MB), independente de
ter identificado a família ou não — é o mesmo diálogo manual de escolher
arquivo-base que já existia na aba de hardware (`on_use_donor_file`), só
que aplicado em cima de um arquivo já aberto em vez de uma leitura de
hardware. Pensado pro caso em que o técnico sabe o modelo da placa pela
etiqueta física (silkscreen) mesmo quando o dump não tem esse dado pra
extrair sozinho. Quando a família não é detectada, um aviso no log aponta
pra esse botão.

**Bug real encontrado e corrigido em `nor_patcher.apply_donor_identity()`**:
antes, os 4 campos de identidade (serial placa-mãe, serial console, MAC,
MAC Wi-Fi) eram sempre copiados do "console lido" pro arquivo-base, sem
checar se esse dado era válido. Com um console lido totalmente em branco
(`0xFF`), isso apagava os campos BONS que já vinham no arquivo-base,
substituindo por lixo `0xFF` — o oposto do que "regenerar" deveria fazer.
Corrigido: agora, se o campo correspondente no console lido está em branco
(`new.count(0xFF) == length`), o campo NÃO é sobrescrito — mantém o valor
que já estava no arquivo-base, e o log mostra isso explicitamente
("mantido do arquivo-base (console lido não tinha esse dado -- bloco em
branco)") em vez de fingir que fez um transplante que não aconteceu.

Testado: `EDM-010 ... DISCO.bin` (100% em branco, família `EDM-04X` nem
dá pra detectar) como "console lido" + `EDM-040-J100-PANASONIC.BIN` como
arquivo-base -> resultado final preserva exatamente o chip, família,
serial e MAC do arquivo-base (nada é apagado), e o log de mudanças mostra
os 4 campos como "mantidos", não como "reaproveitados". Fluxo de botões
também testado via instância real do `App` (estado automático
desabilitado, manual habilitado, botão de salvar habilita após aplicar).

## Implementado 2026-10-06: conversão de "Tipo de console" (Disco/Digital/Edição Slim)

Usuário trouxe um print do **Console Service Tool** (ferramenta de
terceiro que ele já tinha instalada em `ConsoleServiceTool/` nesta
máquina) mostrando um campo editável "Console Type:" com as opções
"Disk", "Digital", "Slim Edition" pro mesmo arquivo `EDM-O33 ... .bin`
que já tínhamos analisado. Pedido: implementar essa mesma conversão,
focada no caso de PS5 "Fat" (EDM-01X a EDM-03X, com leitor de disco fixo)
com leitor de disco com defeito — como o leitor é pareado com a APU e não
dá pra trocar por outro, a única forma de o aparelho voltar a atualizar é
o sistema parar de exigir o leitor, convertendo o console pra "Digital"
via software.

**Método usado pra achar o offset real** (sem adivinhar): o Console
Service Tool é um app .NET 8 (WinForms + WebView2, `ConsoleServiceTool.dll`).
Baixado o decompilador `ilspycmd` (pacote oficial do projeto ILSpy, via
NuGet, rodado com `dotnet ilspycmd.dll -p -o <pasta> ConsoleServiceTool.dll`
usando o runtime .NET 8 já instalado na máquina — não precisou de SDK) e
decompilado o `.dll` inteiro de volta pra C#. Achados nos arquivos
`ConsoleServiceTool.Console.Sony.Shared/ConsoleType.cs`,
`Nvs.cs` e `Nor.cs`:

- `ConsoleType` é um enum de 4 bytes **big-endian**: `SlimEdition =
  0x22010101`, `Disk = 0x22020101`, `Digitial = 0x22030101` (bytes no
  arquivo: `22 01 01 01` / `22 02 01 01` / `22 03 01 01` — só o segundo
  byte muda: 01/02/03).
- Essa struct `Nvs` é lida sequencialmente a partir de um offset fixo
  dentro do `Nor` inteiro (`Header` 0x1000 + `ActiveSlot` 0x1000 + `Mbr1` +
  `Mbr2` + `EmcIplA` + `EmcIplB` + `UsbPdcA` + `UsbPdcB` + `Unk[671744]`).
  Em vez de somar todos esses tamanhos um por um (risco de erro), a base
  da `Nvs` foi calculada **duas vezes de forma independente**, usando dois
  campos que já tínhamos validado (`MacAddressData`, offset relativo 32
  dentro da `Nvs`, e `MotherBoardSerialNumberData`, offset relativo
  12800) contra os offsets absolutos já confirmados nesse projeto
  (`OFFSET_MAC = 0x1C4020`, `OFFSET_MOBO_SERIAL = 0x1C7200`). As duas
  contas bateram exatamente na mesma base: `0x1C4000` (= o mesmo
  `OFFSET_BOARD_ID` que já usávamos) -- ou seja, a `Nvs` do Console
  Service Tool é literalmente o mesmo bloco que a gente já vinha lendo
  campo por campo, só que ele trata como uma struct única. A partir
  dessa base: `ConsoleType` fica em **0x1C7010** (4 bytes) e o campo
  `Idu` (modo "unidade de demonstração" de loja, não relacionado à
  conversão disco/digital) fica em **0x1C9600** (1 byte: `0xFF` =
  desativado, `0x01` = ativado).

**Confirmado empiricamente** contra as 11 amostras reais em `NOR's/`
(incluindo bater exatamente com o "Disk" mostrado pelo próprio Console
Service Tool no print do usuário pro arquivo EDM-O33): placas EDM-03X
(SKU `CFI-1xxx`, geração "Fat") mostram `Disk`; placas EDM-04X/05X (SKU
`CFI-2xxx`, geração "Slim") mostram `SlimEdition` uniformemente,
independente do chip HDMI (Realtek ou Nuvoton) ou se são "com"/"sem"
leitor de disco no nosso flag já conhecido (0x1C4005) — reforça a teoria
de que na geração Slim o leitor é modular/detectado em runtime, então não
existe uma distinção Disco/Digital fixa gravada na NOR pra esses modelos
(diferente da geração Fat, onde essa troca faz sentido real). Os 3
arquivos totalmente em branco (ver seção acima) mostram `0xFFFFFFFF`,
tratado como "não identificado" — consistente com o resto do programa.

Verificado também no código decompilado (`PS5NorView.cs`,
`ButtonSave_Click`/`UpdateChangedNorValues`) que o Console Service Tool
só regrava esse campo isolado — não recalcula nenhum checksum nem mexe em
mais nada quando convertendo tipo de console, diferente do patch de chip
HDMI (que depende da tabela de checksum em 0x1C41FE). Por isso
`apply_console_type()` ficou simples: troca só os 4 bytes, sem
`checksum_left_stale`.

**Implementado**: `nor_parser.extract_console_type()`/`extract_idu_mode()`
(novos campos em `NorInfo`, exibidos na aba "Analisar arquivo .bin"), e
`nor_patcher.apply_console_type(original, target)` com
`target in {"disk", "digital", "slim"}`. Nova seção na aba de análise de
arquivo: combo com os 3 tipos + botão "Converter", com confirmação
explicando o propósito (console Fat com leitor de disco com defeito) e
aviso pra só gravar em placa de bancada/teste antes de confiar em
cliente.

Testado: conversão Disco -> Digital no arquivo EDM-O33 real muda só 1
byte (offset 0x1C7011, só o byte discriminador — os outros 3 bytes fixos
`22 01 01` não mudam entre Disco e Digital), volta exatamente aos bytes
originais revertendo a conversão (round-trip bit-exato verificado). Fluxo
completo também testado via instância real do `App`, incluindo troca de
idioma com o combo re-populado corretamente.

Pasta de referência: `ConsoleServiceTool/` (não faz parte do nosso
repositório git, fica fora de `ps5-hdmi-tool/` -- só foi usada aqui como
material de pesquisa, como os outros projetos de terceiros já citados
neste arquivo).

## Renomeado 2026-10-06: botão "Restaurar backup de arquivo..." -> "Gravar arquivo .bin na NOR..."

Usuário pediu pra aba de hardware ter uma opção de carregar uma NOR
modificada (ex.: convertida na aba "Analisar arquivo") e gravar ela no
chip conectado. Essa função **já existia** -- o botão "Restaurar backup
de arquivo..." (`on_restore_backup`) sempre aceitou qualquer `.bin` de
2 MB válido, não só backups próprios, e já fica habilitado assim que o
leitor é detectado (não exige ter lido a placa antes). O problema era só
o nome e os textos ao redor (diálogo de seleção, confirmação, log), que
davam a entender que era exclusivo pra restaurar um backup antigo da
mesma placa -- por isso não ficou óbvio que servia também pra gravar um
arquivo recém-convertido.

Só renomeado (nenhuma mudança de lógica): botão, título do diálogo de
arquivo, filtro de tipo de arquivo, títulos/corpos de confirmação, frase
de confirmação final e linhas de log -- todos trocados de linguagem
"restaurar backup" pra linguagem genérica "gravar arquivo .bin", nos 3
idiomas. `on_restore_backup`/`_restore_worker` (nomes internos) e
`BACKUP_DIR` como pasta inicial do diálogo continuam iguais.

## Implementado 2026-10-06: validação real de NOR de PS5 + animação ao gravar arquivo .bin

Usuário pediu pra "Gravar arquivo .bin na NOR..." (aba de hardware) só
aceitar arquivos que sigam o padrão de uma NOR de PS5 -- hoje só
conferíamos o tamanho (2 MB), o que deixa passar qualquer binário de 2 MB,
não só NORs de PS5 de verdade. Pediu também uma animação ao clicar nessa
opção (imagem enviada, `images/verifying_file.gif`, 480x480, 76 frames) e
avisou que vai mandar uma segunda animação depois, pro caso de arquivo
inválido.

**Validação real**: achamos uma assinatura fixa de 32 bytes no offset 0
de toda NOR de PS5 -- `"SONY COMPUTER ENTERTAINMENT INC."` -- vista no
código-fonte decompilado do Console Service Tool (`NorHeader.Magic`, ver
seção acima) e **confirmada em todas as nossas 8 amostras reais com
dado** (as 3 em branco/corrompidas, como esperado, não têm -- ver seção
"Diagnosticado e corrigido 2026-10-06"). Nova função
`nor_parser.has_valid_nor_magic()`. Tamanho certo sozinho não bastava pra
provar que é uma NOR de PS5; agora a gravação exige os dois: tamanho
E assinatura.

**Fluxo em `on_restore_backup`** (reestruturado em 4 métodos, mesmo
padrão já usado em `on_detect`/`_detect_worker`/`_wait_min_display`):
1. `on_restore_backup`: escolhe o arquivo, mostra o novo estágio
   "verifying_file" (a animação) e dispara a verificação numa thread
   separada (pra animação não travar).
2. `_verify_file_worker` (thread): confere tamanho + assinatura, garante
   tempo mínimo de exibição da animação (`_wait_min_display`, mesmo
   mecanismo da detecção), volta pra thread principal via `self.after()`.
3. `_verify_file_done` (thread principal): se tamanho errado -> erro
   específico de tamanho (já existia); se assinatura errada -> **novo**
   erro "Arquivo não é uma NOR de PS5" explicando que só deve usar
   arquivos NOR de PS5; se os dois passam -> `_proceed_restore`.
4. `_proceed_restore`: fluxo de confirmação dupla + gravação que já
   existia antes, inalterado.

Testado: arquivo de 2 MB com bytes aleatórios (tamanho certo, assinatura
errada) rejeitado com a mensagem nova; arquivo de tamanho errado rejeitado
com a mensagem antiga; arquivo real (`EDM-O33 ... .bin`) passa nos dois
testes e chega até o diálogo de confirmação de gravação. Fluxo assíncrono
completo (thread + `self.after()` + `mainloop()`) testado de ponta a
ponta também.

**Pendente**: a segunda animação (pra quando o arquivo é rejeitado) ainda
não foi adicionada -- por enquanto, arquivo inválido só volta pro estágio
"idle" (ver `TODO` em `_verify_file_done`). Trocar por uma animação
dedicada assim que o usuário mandar.

## Implementado 2026-10-06: só mostrar .bin no diálogo de "Gravar arquivo .bin na NOR"

Filtro de arquivo (`on_restore_backup`) tinha duas opções no diálogo --
"Arquivo NOR (*.bin)" e "Todos os arquivos (*.*)" -- deixando o usuário
escolher qualquer tipo de arquivo por engano. Removida a opção "Todos os
arquivos"; agora o diálogo só lista `.bin`.

## Implementado 2026-10-06: carregar arquivo .bin exige clicar no passo 4 pra gravar + botão "Restaurar NOR a partir de Backup" + aviso de backup ausente

Usuário pediu 3 coisas relacionadas ao fluxo de gravação da aba de
hardware:

1. **"Carregar arquivo .bin para gravar..."** (renomeado de "Gravar
   arquivo .bin na NOR...") não deve gravar nada direto mais -- só deve
   carregar o arquivo, mostrar todas as informações parseadas dele (igual
   ao que já aparecia depois de ler a placa de verdade no passo 2) e
   habilitar o passo "4. GRAVAR NA NOR". A gravação em si só acontece
   quando o usuário clicar nesse botão do passo 4, igual ao fluxo normal
   de ler+pré-visualizar.
   - `_verify_file_done` agora chama `_load_file_for_write(path, data)`
     em vez de `_proceed_restore` direto. `_load_file_for_write` faz
     `parse_nor(data)`, guarda em `self.last_dump`/`self.last_info`, cria
     um `PatchResult` "vazio" (`changes=[]`, sem alterar nada -- só grava
     o arquivo como está), loga tudo via novo método compartilhado
     `_log_full_info(info)` (extraído do que já existia em `_read_done`,
     reusado nos dois lugares), e habilita `btn_write`.
   - Novo atributo `self._write_source` ("patch" ou "restore") -- marca
     se `self.last_dump`/`self.last_patch` vieram de uma leitura real do
     chip (deve conferir se a NOR não mudou antes de gravar, via
     `pre_check_against=self.last_dump`) ou de um arquivo externo
     carregado (não tem o que conferir contra o chip, já que o arquivo
     nunca veio dele -- `pre_check_against=None`, igual ao comportamento
     antigo de restaurar backup). `_write_worker` agora decide com base
     nisso.

2. **Removida a palavra "(irreversível)"** do texto do botão "4. GRAVAR
   NA NOR" -- o processo pode sim ser revertido depois, usando o novo
   botão "Restaurar NOR a partir de Backup" (ver item 3), então o rótulo
   do botão não devia mais afirmar que é irreversível.

3. **Novo botão "Restaurar NOR a partir de Backup"** (`btn_restore_from_backup`
   / `on_restore_from_backup`), ao lado dos outros dois botões de
   gravação. Grava de volta o último backup feito nesta sessão
   (`self.last_backup_path` -- seja o do passo 2, seja o automático do
   item 4 abaixo), reaproveitando o `_proceed_restore` que já existia
   (mesma dupla confirmação + frase de confirmação). Se não houver nenhum
   backup feito ainda (`self.last_backup_path is None`), mostra aviso
   "Nenhum backup encontrado" em vez de tentar gravar.

4. **Aviso de backup ausente ao clicar em "4. GRAVAR NA NOR"**: se
   `self.last_backup_path is None` nesse momento (típico do fluxo do
   item 1 -- carregou um arquivo externo sem nunca ter lido a placa no
   passo 2), mostra uma caixa de aviso explicando que, sem backup, a
   gravação será IRREVERSÍVEL, perguntando se quer fazer um backup
   automático agora. Se sim, lê a NOR atual duas vezes (mesma lógica de
   comparação de confiabilidade do passo 2, incluindo o aviso de leituras
   divergentes) e salva via `_save_backup` antes de prosseguir pro
   diálogo de confirmação normal de gravação; se não, segue direto pra
   confirmação. Implementado como `on_write` -> (opcional)
   `_backup_before_write_worker` (thread) -> `_write_confirm_and_go`
   (extraído do corpo antigo de `on_write`, agora reaproveitado nos dois
   caminhos).

Testado manualmente após build/instalação local (v1.0.12 em diante,
pendente de build final desta leva de mudanças).

## Implementado 2026-10-06: validar que existe uma NOR de verdade no passo 2 (leitura via hardware)

Usuário reportou uma falha de segurança: testando com a leitora CH341A sem
nenhuma NOR conectada no soquete/clipe, o passo 2 ("Ler NOR") terminava
como se tivesse lido com sucesso -- as duas leituras batiam entre si (já
que um soquete vazio devolve sempre o mesmo valor fixo, tipicamente 0xFF),
então `compare_dumps` não pegava isso, e o programa seguia como se fosse
uma NOR válida.

**Causa raiz**: `_read_worker` só conferia se as duas leituras batiam
entre si (`compare_dumps`), nunca se o *conteúdo* delas fazia sentido como
NOR de PS5. Já tínhamos as duas funções certas pra isso
(`nor_parser.is_blank()` e `nor_parser.has_valid_nor_magic()`, criadas em
sessões anteriores -- ver "Diagnosticado e corrigido 2026-10-06" e
"Implementado 2026-10-06: validação real de NOR de PS5" acima), só não
estavam sendo usadas nesse ponto do fluxo; só apareciam como aviso no log
(`parse_nor`) ou na validação de arquivo externo (`on_restore_backup`).

**Correção**: depois que as duas leituras baterem, `_read_worker` agora
confere, nessa ordem, antes de aceitar a leitura como válida:
1. `is_blank(dump1)` -- 100% 0xFF -- rejeita como "soquete vazio ou mau
   contato" (um PS5 de verdade não liga com a NOR vazia assim).
2. `has_valid_nor_magic(dump1)` -- se tiver dado mas não a assinatura
   `"SONY COMPUTER ENTERTAINMENT INC."` no offset 0 -- rejeita como "NOR
   corrompida, chip errado no soquete, ou não é NOR de PS5".

Nos dois casos: mostra erro bloqueante (`messagebox.showerror`, título
"NOR corrompida ou inexistente"), loga o motivo, reusa a animação de
"detect_failed" que já existia, e **não** salva backup nem habilita
pré-visualizar/doador/gravar -- a leitura é tratada como falha, não como
sucesso parcial. `self.last_dump`/`self.last_backup_path` continuam
`None`, então não há risco de alguém gravar algo em cima de uma leitura
inválida achando que é dado real.

Não mexe na aba "Analisar arquivo (.bin)" nem no fluxo de carregar `.bin`
externo pra gravar (`on_restore_backup`) -- aquele já tinha sua própria
validação de assinatura desde a sessão anterior, e a aba de análise de
arquivo continua permissiva de propósito (é o lugar certo pra abrir um
dump em branco/corrompido e tentar regenerar a partir de um
arquivo-base).

Testado com NOR falsa simulando 3 cenários: soquete vazio (0xFF puro) ->
rejeitado, não vira `last_dump`/backup; dado qualquer sem a assinatura
certa -> rejeitado; NOR real válida -> continua funcionando normalmente
(sem regressão).

## Implementado 2026-10-06: identificar o chip de flash (Winbond) no passo 1

Usuário mandou print de outra ferramenta de CH341A mostrando que ela
identifica o chip conectado como `Manuf: WINBOND`, `Name: W25Q16JV-xM`,
`Size: 2097152` a partir do JEDEC ID, e pediu pro nosso programa também
ser capaz de reconhecer a Winbond.

O passo 1 ("Detectar leitor CH341A") já lia o JEDEC ID (`read_jedec_id()`)
desde o início do projeto, mas só mostrava os 3 bytes brutos em hex no
log -- não traduzia isso pra fabricante/modelo. `0xEF` é o código de
fabricante padrão da JEDEC pra Winbond (constante oficial da indústria,
não é algo que estamos adivinhando); `EF 40 15` é o ID exato da
W25Q16JV, já confirmado nas nossas amostras reais (ver docstring de
`ch341_spi.py` e `NOTES.md`).

Nova função `ch341_spi.describe_jedec_id(jedec) -> (fabricante, modelo,
tamanho, confirmado)`:
- `EF 40 15` exato -> `("Winbond", "W25Q16JV", 2097152, True)`.
- Qualquer outro ID com primeiro byte `0xEF` -> `("Winbond", None, None,
  False)` -- reconhece o fabricante mas avisa que esse modelo específico
  ainda não foi confirmado neste programa.
- Qualquer outro fabricante -> `(None, None, None, False)`.

Retorna dado estruturado, não texto pronto -- seguindo a mesma regra já
estabelecida nesse projeto de nunca cravar string traduzida fora do
`i18n.py` (ver gotcha de `CONSOLE_TYPE_TARGET_LABEL` documentado acima).
`gui.py`/`_detect_done` monta a frase certa com `t()` a partir desses
campos, em 3 variações (chip confirmado / fabricante Winbond mas modelo
não confirmado / fabricante desconhecido).

Não bloqueia nada -- é só informativo no passo 1, igual o JEDEC ID bruto
já era. A validação que de fato impede prosseguir com uma NOR inválida
continua sendo a do passo 2 (ver seção anterior, "validar que existe uma
NOR de verdade").

Testado com 3 JEDEC IDs simulados: `EF 40 15` (Winbond W25Q16JV
confirmado), outro ID com `0xEF` (Winbond reconhecido, modelo não
confirmado) e um ID de outro fabricante (`0xC2`, Macronix, não
reconhecido).

## Implementado 2026-10-06: programa demorando pra abrir (duas causas, as duas corrigidas) + atualização automática via GitHub

Usuário reportou que o programa estava demorando pra abrir, e pediu duas
coisas: (1) otimizar a abertura; (2) o programa checar sozinho se tem uma
versão nova no GitHub, avisar o usuário, e se ele aceitar, baixar e
sobrescrever a instalação atual.

### Causa raiz da lentidão (medida, não só suposta)

Duas causas, medidas separadamente antes de mexer em qualquer coisa:

1. **`GifAnimation` carregava TODOS os frames de TODAS as ~11 animações de
   estágio no arranque**, mesmo só uma ficando visível por vez (a "idle").
   Cada frame passa por `Image.convert("RGBA").resize(..., LANCZOS)` do
   Pillow -- caro. Medido: decodificar os ~922 frames de todos os 11 GIFs
   (480x480 cada, resize pra 260x260) levava **6.3 segundos sozinho**, a
   maior fatia do tempo de abertura.
2. **Build em modo "onefile" do PyInstaller + UPX ligado.** Onefile
   descompacta tudo numa pasta temporária toda vez que o `.exe` abre (não
   só na instalação); UPX comprime o `.exe` no disco mas precisa
   descomprimir na memória a cada abertura -- as duas coisas somam um
   custo de processo que só existe em onefile/UPX, não em onedir puro.

### Correção 1: carregamento preguiçoso de GIF (`gif_anim.py`)

`GifAnimation.__init__` não decodifica mais nada -- só guarda o caminho e
o tamanho. Novo `_ensure_loaded()` decodifica (com cache via
`self._loaded`) na primeira vez que `start()` é chamado pra aquela
animação -- ou seja, na primeira vez que aquele estágio realmente aparece
na tela. Como `_show_stage()` já chama `anim.start()`/`anim.stop()` certo
pra cada estágio, nenhuma outra mudança foi necessária em `gui.py`.

Resultado medido (`App()` construído direto, sem passar pelo `.exe`
empacotado): de ~6.3s só nos GIFs (mais o resto do custo de construir a
janela) pra **1.53s no total** pra montar a janela inteira -- só a "idle"
(162 frames) carrega de cara agora, as outras 10 animações (760 frames)
carregam sob demanda, uma vez cada, na primeira vez que o usuário realmente
vir aquele estágio (durante uma leitura/gravação de verdade, por exemplo
-- onde o tempo de decodificar um GIF é imperceptível perto do tempo de
esperar o hardware).

### Correção 2: PyInstaller onedir (não onefile) + UPX desligado

`PS5_HDMI_Tool.spec`: `EXE(..., exclude_binaries=True, upx=False)` +
`COLLECT(exe, a.binaries, a.datas, upx=False, name='PS5_HDMI_Tool')`, em
vez de passar `a.binaries`/`a.datas` direto pro `EXE()` (que era o que
gerava o `.exe` único). Build agora sai em `dist/PS5_HDMI_Tool/` (pasta,
com `PS5_HDMI_Tool.exe` + `_internal/`), não mais `dist/PS5_HDMI_Tool.exe`.
`installer.iss` ajustado pra copiar a pasta inteira (`Source: "dist\
PS5_HDMI_Tool\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs`)
em vez de só o `.exe`. README.md/README.en.md atualizados (comandos de
build, caminho do `.exe` gerado, nota sobre não usar `--onefile`).

Medido com o build final (onedir + GIF preguiçoso): processo até a janela
aparecer na tela, **2.41s** (via `Start-Process` + polling de
`MainWindowHandle`) -- bateu com o esperado (overhead de processo/DLLs +
~1.5s de `App()`).

### Atualização automática (`version.py` + `updater.py`)

Novo `version.py`: `APP_VERSION = "1.0.16"` -- fonte única da versão em
tempo de execução, usada só pela checagem de atualização. **Precisa ser
atualizado junto com `version_info.txt` e `installer.iss` a cada bump de
versão daqui pra frente** (3 arquivos, nenhum lê o outro automaticamente
-- documentado no topo do próprio `version.py`).

Novo `updater.py`, só biblioteca padrão (`urllib`, sem dependência nova
pra empacotar):
- `check_for_update() -> UpdateInfo | None`: consulta
  `api.github.com/repos/vendashson-rgb/ps5-hdmi-tool/releases/latest`,
  compara a tag (`vX.Y.Z`) com `APP_VERSION`, acha o asset
  `PS5_HDMI_Tool_Setup.exe` na release. Timeout de 6s. Qualquer erro (sem
  internet, API fora do ar, repositório sem releases, asset não encontrado)
  -> retorna `None` **sem levantar exceção** -- essa checagem é um bônus,
  nunca deve incomodar ou travar o programa por falta de internet.
- `download_update(info, dest_path, progress_cb=None)`: baixa em chunks de
  256 KB, chama `progress_cb(baixado, total)` a cada chunk.

Fluxo em `gui.py`: `App.__init__` agenda `self.after(3000,
self._start_update_check)` -- 3s depois do programa abrir (não compete com
o arranque), roda `check_for_update()` numa thread (mesmo padrão
thread+`self.after(0, ...)` já usado em todo o resto do programa). Se
achar atualização: `messagebox.askyesno` perguntando se quer baixar e
instalar agora. Se sim: abre um `Toplevel` modal com barra de progresso
determinada, baixa numa thread, e ao terminar chama
`subprocess.Popen([instalador_baixado])` seguido de `self.destroy()` +
`sys.exit(0)` -- fecha o programa atual pra o instalador conseguir
sobrescrever o `.exe` sem o erro de "acesso negado" (DeleteFile falhou)
que o usuário bateu mais cedo nesta sessão tentando instalar manualmente
com o programa antigo ainda aberto. Download com erro -> mensagem de erro,
programa continua funcionando normalmente com a versão atual.

Testado: checagem contra o repositório real (`gh release list` confirmou
`v1.0.7` como última publicada) -- com `APP_VERSION` maior, retorna `None`
corretamente (não finge achar atualização); com `APP_VERSION` forçado pra
baixo, acha a `v1.0.7` certinha (versão, URL do asset, tamanho). Download
e fluxo completo (perguntar -> baixar com progresso -> salvar -> abrir
instalador -> fechar o programa) testado de ponta a ponta contra um
servidor HTTP local fake, com `subprocess.Popen`/`sys.exit`
mockados. Falha de rede (URL inválida) testada -> retorna `None` em
silêncio, sem exceção.

# Mapa de offsets da NOR (EDM-xxx, PS5 Slim)

Registro do que já está confirmado e do que ainda falta, pra não perder o
histórico entre sessões. Tamanho de arquivo esperado: 2097152 bytes (2 MB).

## Confirmado (usado em `nor_parser.py`)

| Offset | Campo | Detalhe |
|---|---|---|
| 0x1C4062 | Seletor de CI HDMI | `0x01` = Realtek RTD2175P, `0xFF` = Nuvoton/Panasonic MN864739. Validado em 5 placas originais (rev 1.1, 1.3, 1.4, 1.5) + 1 conversão real. |
| 0x1C4020 (6 bytes) | Endereço MAC | Confirmado comparando placas — valor único por console. |
| 0x1C7200 (~33 bytes) | Bloco de identificação | Texto ASCII cru (contém o que parece ser o número de série no final da string, ex. `MZD1045691`, `NA410261047`). Ainda não isolamos exatamente qual parte é "o" número de série oficial — mostramos o campo bruto inteiro. |
| ~0x1C7230 | Código "CFI-XXXX" | Texto ASCII real encontrado no dump (`CFI-2014 B01X`, `CFI-2114 B01X`, `CFI-1214A 01X`). **Não confirmado** o que exatamente representa — não bate 1:1 com os números EDM-xxx usados nos nomes de arquivo. Mostrar como informação extra, nunca como "revisão da placa" até confirmar. |

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
- Versão de firmware do sistema — provavelmente não fica armazenada nesta NOR (fica no SSD). Confirmado por busca: nenhum padrão tipo "13.40" aparece como texto em nenhuma das 6 amostras.

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

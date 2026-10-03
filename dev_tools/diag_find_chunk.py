"""
Diagnostico: descobre o maior tamanho de bloco que a CH341StreamSPI4 aceita
para leitura (comando 0x03 + endereco de 3 bytes + N bytes de dados).

Roda direto no terminal (nao precisa da interface grafica). Testa varios
tamanhos, do maior pro menor, e para no primeiro que funcionar de forma
CONFIAVEL (duas leituras da mesma area batendo).
"""
import sys

from ch341_spi import CH341SPI, CMD_READ_DATA

SIZES_TO_TRY = [4096, 2048, 1024, 512, 256, 128, 64, 32, 16, 8]


def try_read(spi: CH341SPI, addr: int, data_len: int) -> bytes | None:
    cmd = bytes([
        CMD_READ_DATA,
        (addr >> 16) & 0xFF,
        (addr >> 8) & 0xFF,
        addr & 0xFF,
    ]) + bytes(data_len)
    try:
        resp = spi._transfer(cmd)
        return resp[4:]
    except Exception as e:
        print(f"  tamanho {data_len}: FALHOU na chamada -- {e}")
        return None


def main():
    print("Conectando ao CH341A...")
    with CH341SPI() as spi:
        jedec = spi.read_jedec_id()
        print(f"JEDEC ID: {jedec.hex(' ').upper()}")
        print()
        print("Testando tamanhos de bloco (endereco 0x000000), do maior pro menor:")
        working_size = None
        for size in SIZES_TO_TRY:
            r1 = try_read(spi, 0, size)
            if r1 is None:
                continue
            r2 = try_read(spi, 0, size)
            if r2 is None:
                continue
            if r1 == r2:
                print(f"  tamanho {size}: OK -- duas leituras bateram. Primeiros bytes: {r1[:8].hex(' ').upper()}")
                working_size = size
                break
            else:
                print(f"  tamanho {size}: a chamada funcionou mas as duas leituras NAO bateram (dado instavel)")

        print()
        if working_size:
            print(f">>> Tamanho de bloco recomendado: {working_size} bytes de dados (+4 de comando/endereco)")
            print(">>> Me mande esse numero para eu ajustar o programa principal.")
        else:
            print(">>> Nenhum tamanho funcionou de forma confiavel. Precisamos investigar mais.")


if __name__ == "__main__":
    sys.exit(main())

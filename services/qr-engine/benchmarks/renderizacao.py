import argparse
import csv
import ctypes
import json
import platform
import subprocess
import sys
from ctypes import wintypes
from pathlib import Path
from statistics import median
from time import perf_counter

from src.schemas.pedido import PedidoRenderizacao
from src.servicos.renderizacao import renderizar

RESOLUCOES = (256, 512, 1024, 2048)
FORMATOS = ("png", "svg")

GRADIENTE_LINEAR = {
    "type": "linear",
    "angle": 45,
    "stops": [
        {
            "position": 0.0,
            "color": "#6D28D9",
        },
        {
            "position": 1.0,
            "color": "#172554",
        },
    ],
}

GRADIENTE_RADIAL = {
    "type": "radial",
    "stops": [
        {
            "position": 0.0,
            "color": "#FFFFFF",
        },
        {
            "position": 1.0,
            "color": "#E0E7FF",
        },
    ],
}

ESTILOS = {
    "convencional": {},
    "formas": {
        "modules": {
            "shape": "rounded",
            "color": "#6D28D9",
        },
    },
    "gradiente": {
        "modules": {
            "shape": "rounded",
            "gradient": GRADIENTE_LINEAR,
        },
    },
    "completa": {
        "modules": {
            "shape": "rounded",
            "gradient": GRADIENTE_LINEAR,
        },
        "eyes": {
            "outer": {
                "shape": "rounded",
                "gradient": GRADIENTE_LINEAR,
            },
            "inner": {
                "shape": "dots",
                "color": "#172554",
            },
        },
        "background": {
            "gradient": GRADIENTE_RADIAL,
        },
    },
}


class ContadoresMemoria(ctypes.Structure):
    _fields_ = [
        ("cb", wintypes.DWORD),
        ("PageFaultCount", wintypes.DWORD),
        ("PeakWorkingSetSize", ctypes.c_size_t),
        ("WorkingSetSize", ctypes.c_size_t),
        ("QuotaPeakPagedPoolUsage", ctypes.c_size_t),
        ("QuotaPagedPoolUsage", ctypes.c_size_t),
        ("QuotaPeakNonPagedPoolUsage", ctypes.c_size_t),
        ("QuotaNonPagedPoolUsage", ctypes.c_size_t),
        ("PagefileUsage", ctypes.c_size_t),
        ("PeakPagefileUsage", ctypes.c_size_t),
    ]


def obter_memoria():
    if platform.system() != "Windows":
        raise RuntimeError("A medicao de memoria requer Windows.")

    kernel32 = ctypes.WinDLL(
        "kernel32",
        use_last_error=True,
    )

    psapi = ctypes.WinDLL(
        "psapi",
        use_last_error=True,
    )

    kernel32.GetCurrentProcess.argtypes = []
    kernel32.GetCurrentProcess.restype = wintypes.HANDLE

    psapi.GetProcessMemoryInfo.argtypes = [
        wintypes.HANDLE,
        ctypes.POINTER(ContadoresMemoria),
        wintypes.DWORD,
    ]

    psapi.GetProcessMemoryInfo.restype = wintypes.BOOL

    contadores = ContadoresMemoria()
    contadores.cb = ctypes.sizeof(contadores)

    processo = kernel32.GetCurrentProcess()

    sucesso = psapi.GetProcessMemoryInfo(
        processo,
        ctypes.byref(contadores),
        contadores.cb,
    )

    if not sucesso:
        raise ctypes.WinError(ctypes.get_last_error())

    return {
        "working_set_bytes": contadores.WorkingSetSize,
        "peak_working_set_bytes": contadores.PeakWorkingSetSize,
        "pagefile_usage_bytes": contadores.PagefileUsage,
        "peak_pagefile_usage_bytes": contadores.PeakPagefileUsage,
    }


def criar_pedido(estilo, formato, tamanho):
    return PedidoRenderizacao.model_validate(
        {
            "content": "ntizoconnect",
            "output": {
                "format": formato,
                "size": tamanho,
                "margin": 4,
            },
            "options": {
                "errorCorrection": "H",
            },
            "style": ESTILOS[estilo],
        }
    )


def executar_processo_memoria(
    estilo,
    formato,
    tamanho,
):
    pedido = criar_pedido(
        estilo,
        formato,
        tamanho,
    )

    memoria_inicial = obter_memoria()

    resultado = renderizar(pedido)

    memoria_final = obter_memoria()

    dados = {
        "memoria_inicial_bytes": (memoria_inicial["working_set_bytes"]),
        "pico_inicial_bytes": (memoria_inicial["peak_working_set_bytes"]),
        "memoria_final_bytes": (memoria_final["working_set_bytes"]),
        "pico_memoria_bytes": (memoria_final["peak_working_set_bytes"]),
        "aumento_pico_bytes": max(
            0,
            memoria_final["peak_working_set_bytes"] - memoria_inicial["peak_working_set_bytes"],
        ),
        "pico_commit_bytes": (memoria_final["peak_pagefile_usage_bytes"]),
        "tamanho_resultado_bytes": len(resultado.dados),
    }

    print(json.dumps(dados))


def medir_memoria(
    estilo,
    formato,
    tamanho,
    repeticoes,
):
    medicoes = []

    for _ in range(repeticoes):
        processo = subprocess.run(
            [
                sys.executable,
                "-m",
                "benchmarks.renderizacao",
                "--worker",
                "--estilo",
                estilo,
                "--formato",
                formato,
                "--tamanho",
                str(tamanho),
            ],
            capture_output=True,
            text=True,
            check=True,
            timeout=120,
        )

        medicoes.append(json.loads(processo.stdout))

    mib = 1024**2

    return {
        "memoria_inicial_mediana_mib": round(
            median(m["memoria_inicial_bytes"] for m in medicoes) / mib,
            3,
        ),
        "pico_memoria_mediana_mib": round(
            median(m["pico_memoria_bytes"] for m in medicoes) / mib,
            3,
        ),
        "pico_memoria_maximo_mib": round(
            max(m["pico_memoria_bytes"] for m in medicoes) / mib,
            3,
        ),
        "aumento_pico_mediana_mib": round(
            median(m["aumento_pico_bytes"] for m in medicoes) / mib,
            3,
        ),
        "pico_commit_maximo_mib": round(
            max(m["pico_commit_bytes"] for m in medicoes) / mib,
            3,
        ),
    }


def guardar_csv(destino, registos):
    with destino.open(
        "w",
        newline="",
        encoding="utf-8",
    ) as ficheiro:
        escritor = csv.DictWriter(
            ficheiro,
            fieldnames=list(registos[0]),
        )

        escritor.writeheader()
        escritor.writerows(registos)


def carregar_baseline(caminho):
    with caminho.open(
        encoding="utf-8-sig",
        newline="",
    ) as ficheiro:
        return {
            (
                linha["estilo"],
                linha["formato"],
                int(linha["resolucao"]),
            ): linha
            for linha in csv.DictReader(ficheiro)
        }


def comparar_resultados(
    resultados,
    baseline,
):
    comparacao = []

    for actual in resultados:
        chave = (
            actual["estilo"],
            actual["formato"],
            actual["resolucao"],
        )

        anterior = baseline[chave]

        antes = float(anterior["mediana_ms"])

        depois = actual["mediana_ms"]

        comparacao.append(
            {
                "estilo": chave[0],
                "formato": chave[1],
                "resolucao": chave[2],
                "antes_ms": antes,
                "depois_ms": depois,
                "aceleracao": round(
                    antes / depois,
                    3,
                ),
                "reducao_percentual": round(
                    (1 - depois / antes) * 100,
                    3,
                ),
                "bytes_antes": int(anterior["bytes"]),
                "bytes_depois": actual["bytes"],
            }
        )

    return comparacao


def validar_imagem_anterior(
    resultado,
    caminho,
):
    if not caminho.is_file():
        return "nao_disponivel"

    if resultado.dados == caminho.read_bytes():
        return "bytes_identicos"

    if resultado.extensao.lstrip(".") == "png":
        from io import BytesIO

        from PIL import Image

        with (
            Image.open(BytesIO(resultado.dados)) as actual,
            Image.open(caminho) as anterior,
        ):
            if (
                actual.size == anterior.size
                and actual.mode == anterior.mode
                and actual.tobytes() == anterior.tobytes()
            ):
                return "pixels_identicos"

    return "diferente"


def executar_benchmark(args):
    destino = args.destino.resolve()

    destino.mkdir(
        parents=True,
        exist_ok=True,
    )

    imagens = destino / "imagens"

    imagens.mkdir(
        exist_ok=True,
    )

    resultados = []
    resultados_memoria = []

    for estilo in ESTILOS:
        for formato in FORMATOS:
            for tamanho in RESOLUCOES:
                pedido = criar_pedido(
                    estilo,
                    formato,
                    tamanho,
                )

                # Aquecimento.
                renderizar(pedido)

                tempos = []

                for _ in range(args.repeticoes):
                    inicio = perf_counter()

                    resultado = renderizar(pedido)

                    duracao = (perf_counter() - inicio) * 1000

                    tempos.append(duracao)

                nome = f"{estilo}-{tamanho}.{formato}"

                (imagens / nome).write_bytes(resultado.dados)

                equivalencia = "nao_disponivel"

                if args.imagens_anteriores:
                    equivalencia = validar_imagem_anterior(
                        resultado,
                        args.imagens_anteriores / nome,
                    )

                if equivalencia == "diferente":
                    raise RuntimeError(f"Resultado diferente: {nome}")

                registo = {
                    "estilo": estilo,
                    "formato": formato,
                    "resolucao": tamanho,
                    "mediana_ms": round(
                        median(tempos),
                        3,
                    ),
                    "minimo_ms": round(
                        min(tempos),
                        3,
                    ),
                    "maximo_ms": round(
                        max(tempos),
                        3,
                    ),
                    "bytes": len(resultado.dados),
                    "equivalencia": equivalencia,
                }

                resultados.append(registo)

                print(
                    f"{estilo:14} "
                    f"{formato:3} "
                    f"{tamanho:4}px | "
                    f"{registo['mediana_ms']:9.2f} ms | "
                    f"{equivalencia}"
                )

    guardar_csv(
        destino / "resultados-finais.csv",
        resultados,
    )

    if args.baseline:
        comparacao = comparar_resultados(
            resultados,
            carregar_baseline(args.baseline),
        )

        guardar_csv(
            destino / "comparacao-final.csv",
            comparacao,
        )

    if args.memoria:
        print("\nMedicao de memoria\n")

        for estilo in ESTILOS:
            for formato in FORMATOS:
                for tamanho in RESOLUCOES:
                    memoria = medir_memoria(
                        estilo,
                        formato,
                        tamanho,
                        args.repeticoes,
                    )

                    resultados_memoria.append(
                        {
                            "estilo": estilo,
                            "formato": formato,
                            "resolucao": tamanho,
                            **memoria,
                        }
                    )

                    print(
                        f"{estilo:14} "
                        f"{formato:3} "
                        f"{tamanho:4}px | "
                        f"{memoria['pico_memoria_maximo_mib']:8.2f} MiB"
                    )

        guardar_csv(
            destino / "resultados-memoria.csv",
            resultados_memoria,
        )

    ambiente = {
        "python": platform.python_version(),
        "sistema": platform.platform(),
        "arquitectura": platform.machine(),
        "processador": platform.processor(),
        "repeticoes": args.repeticoes,
        "configuracoes": len(resultados),
        "medicao_memoria": args.memoria,
    }

    (destino / "ambiente.json").write_text(
        json.dumps(
            ambiente,
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    print(f"\nResultados: {destino}")


def main():
    parser = argparse.ArgumentParser(
        description="Benchmark integral do motor QR.",
    )

    parser.add_argument(
        "--destino",
        type=Path,
    )

    parser.add_argument(
        "--baseline",
        type=Path,
    )

    parser.add_argument(
        "--imagens-anteriores",
        type=Path,
    )

    parser.add_argument(
        "--repeticoes",
        type=int,
        default=3,
    )

    parser.add_argument(
        "--memoria",
        action="store_true",
    )

    parser.add_argument(
        "--worker",
        action="store_true",
    )

    parser.add_argument(
        "--estilo",
        choices=tuple(ESTILOS),
    )

    parser.add_argument(
        "--formato",
        choices=FORMATOS,
    )

    parser.add_argument(
        "--tamanho",
        type=int,
        choices=RESOLUCOES,
    )

    args = parser.parse_args()

    if args.repeticoes < 1:
        parser.error("O numero de repeticoes deve ser positivo.")

    if args.worker:
        if not all(
            (
                args.estilo,
                args.formato,
                args.tamanho,
            )
        ):
            parser.error("O worker requer estilo, formato e tamanho.")

        executar_processo_memoria(
            args.estilo,
            args.formato,
            args.tamanho,
        )

        return

    if args.destino is None:
        parser.error("O argumento --destino e obrigatorio.")

    executar_benchmark(args)


if __name__ == "__main__":
    main()

import json
from datetime import datetime

import yfinance as yf

ARQUIVO = "carteira.json"

ATIVOS_VALIDOS = {
    "PETR4": "Petrobras",
    "VALE3": "Vale",
    "ITUB4": "Itaú Unibanco",
    "BBAS3": "Banco do Brasil",
    "ABEV3": "Ambev",
    "MGLU3": "Magazine Luiza",
    "WEGE3": "WEG",
    "BOVA11": "ETF Ibovespa",
}

COTACOES_OFFLINE = {
    "PETR4": 38.50, "VALE3": 61.20, "ITUB4": 34.80, "BBAS3": 26.40,
    "ABEV3": 12.90, "MGLU3": 9.15, "WEGE3": 52.30, "BOVA11": 128.70,
}


def carregar_carteira():
    try:
        with open(ARQUIVO, "r", encoding="utf-8") as arquivo:
            return json.load(arquivo)
    except FileNotFoundError:
        print("Nenhuma carteira salva — começando do zero.")
        return {}
    except json.JSONDecodeError:
        print("Arquivo de carteira corrompido — começando do zero.")
        return {}


def salvar_carteira(carteira):
    try:
        with open(ARQUIVO, "w", encoding="utf-8") as arquivo:
            json.dump(carteira, arquivo, indent=4, ensure_ascii=False)
        print(f"Carteira salva em {ARQUIVO}")
    except OSError as erro:
        print(f"Não foi possível salvar: {erro}")


def buscar_cotacao(ticker):
    try:
        acao = yf.Ticker(ticker + ".SA")
        historico = acao.history(period="1d")

        if historico.empty:
            raise ValueError("sem dados retornados")

        return float(historico["Close"].iloc[-1]), "online"

    except Exception as erro:
        print(f"  [{ticker}] falha na consulta ({type(erro).__name__}) — usando valor offline")
        return COTACOES_OFFLINE[ticker], "offline"


def ler_float(mensagem, minimo=0.01):
    while True:
        try:
            valor = float(input(mensagem).replace(",", "."))
        except ValueError:
            print("  Digite um número válido!")
            continue

        if valor < minimo:
            print(f"  O valor deve ser pelo menos {minimo}!")
            continue

        return valor


def ler_int(mensagem, minimo=1):
    while True:
        try:
            valor = int(input(mensagem))
        except ValueError:
            print("  Digite um número inteiro!")
            continue

        if valor < minimo:
            print(f"  O valor deve ser pelo menos {minimo}!")
            continue

        return valor


def comprar(carteira, ticker, quantidade, preco):
    if ticker in carteira:
        antigo = carteira[ticker]
        total_qtd = antigo["quantidade"] + quantidade
        total_valor = antigo["quantidade"] * antigo["preco_medio"] + quantidade * preco
        carteira[ticker] = {
            "quantidade": total_qtd,
            "preco_medio": total_valor / total_qtd,
        }
    else:
        carteira[ticker] = {"quantidade": quantidade, "preco_medio": preco}


def relatorio(carteira):
    if not carteira:
        print("\nCarteira vazia.")
        return

    print("\nConsultando cotações...")

    investido_total = 0.0
    atual_total = 0.0
    resultados = {}
    origens = set()

    for ticker, dados in carteira.items():
        preco_atual, origem = buscar_cotacao(ticker)
        origens.add(origem)

        investido = dados["quantidade"] * dados["preco_medio"]
        atual = dados["quantidade"] * preco_atual
        resultados[ticker] = atual - investido

        investido_total += investido
        atual_total += atual

    print("\n" + "=" * 62)
    print("CARTEIRA DE INVESTIMENTOS")
    print(datetime.now().strftime("Consulta em %d/%m/%Y às %H:%M"))
    print("=" * 62)

    for ticker in sorted(resultados, key=resultados.get, reverse=True):
        dados = carteira[ticker]
        investido = dados["quantidade"] * dados["preco_medio"]
        lucro = resultados[ticker]

        try:
            variacao = lucro / investido * 100
        except ZeroDivisionError:
            variacao = 0.0

        sinal = "+" if lucro >= 0 else "-"
        nome = ATIVOS_VALIDOS[ticker]
        print(f"{ticker} ({nome})")
        print(f"   {dados['quantidade']} un | PM R$ {dados['preco_medio']:.2f} "
              f"| investido R$ {investido:.2f}")
        print(f"   resultado: {sinal}R$ {abs(lucro):.2f} ({sinal}{abs(variacao):.1f}%)")

    print("-" * 62)

    lucro_total = atual_total - investido_total

    try:
        rentabilidade = lucro_total / investido_total * 100
    except ZeroDivisionError:
        rentabilidade = 0.0

    print(f"Total investido: R$ {investido_total:.2f}")
    print(f"Valor atual:     R$ {atual_total:.2f}")
    print(f"Resultado:       R$ {lucro_total:.2f} ({rentabilidade:+.1f}%)")

    melhor = max(resultados, key=resultados.get)
    pior = min(resultados, key=resultados.get)
    print(f"Melhor posição:  {melhor} (R$ {resultados[melhor]:.2f})")
    print(f"Pior posição:    {pior} (R$ {resultados[pior]:.2f})")

    if "offline" in origens:
        print("\n[!] Algumas cotações vieram do modo offline.")
    print("=" * 62)


carteira = carregar_carteira()

while True:
    print("\n=== MINHA CARTEIRA ===")
    print("1 - Comprar ativo")
    print("2 - Ver relatório")
    print("3 - Listar ativos disponíveis")
    print("4 - Salvar e sair")

    opcao = input("Opção: ").strip()

    if opcao == "1":
        ticker = input("Ticker: ").strip().upper()

        if ticker not in ATIVOS_VALIDOS:
            print(f"  '{ticker}' não está na lista de ativos permitidos.")
            continue

        quantidade = ler_int("Quantidade: ")
        preco = ler_float("Preço pago por unidade: R$ ")
        comprar(carteira, ticker, quantidade, preco)
        print(f"  {quantidade} de {ticker} registrado(s). "
              f"PM: R$ {carteira[ticker]['preco_medio']:.2f}")

    elif opcao == "2":
        relatorio(carteira)

    elif opcao == "3":
        print("\nAtivos disponíveis:")
        for ticker, nome in ATIVOS_VALIDOS.items():
            print(f"  {ticker} - {nome}")

    elif opcao == "4":
        salvar_carteira(carteira)
        print(f"Encerrando com {len(carteira)} ativo(s) na carteira.")
        break

    else:
        print("Opção inválida!")

"""
Script de análise de tráfego HTTP.
Executa o mesmo fluxo do app.py com captura de rede ativada via Chrome DevTools Protocol.
Salva todas as requisições em 'trafego_capturado.json' para análise.
"""

import json
import getpass
import sys
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


BASE_URL = "http://10.2.2.8:8080/pacientehrn"


def criar_driver():
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    # Ativa o log de performance para captura de rede via CDP
    options.set_capability("goog:loggingPrefs", {"performance": "ALL"})
    return webdriver.Chrome(options=options)


def coletar_requisicoes(driver):
    """Extrai requisições HTTP do log de performance do Chrome."""
    requisicoes = []
    for entry in driver.get_log("performance"):
        msg = json.loads(entry["message"])["message"]
        if msg["method"] == "Network.requestWillBeSent":
            req = msg["params"]["request"]
            url = req.get("url", "")
            if "pacientehrn" in url:
                requisicoes.append({
                    "url": url,
                    "method": req.get("method"),
                    "headers": req.get("headers", {}),
                    "postData": req.get("postData", ""),
                })
    return requisicoes


def aguardar(driver, xpath, timeout=10):
    return WebDriverWait(driver, timeout).until(
        EC.presence_of_element_located((By.XPATH, xpath))
    )


def main():
    print("=== Análise de Tráfego HTTP - Etiqueta AT ===\n")
    username = input("Login: ")
    password = getpass.getpass("Senha: ")
    prontuario = input("Número do Prontuário (para teste): ")

    driver = criar_driver()
    todas_requisicoes = []

    try:
        # ── PASSO 1: Página de login ──────────────────────────────────────────
        print("\n[1/5] Abrindo página de login...")
        driver.get(f"{BASE_URL}/login.jsf")
        aguardar(driver, '//*[@id="login"]')
        todas_requisicoes += coletar_requisicoes(driver)

        # ── PASSO 2: Submissão do login ───────────────────────────────────────
        print("[2/5] Submetendo credenciais...")
        driver.find_element(By.ID, "login").send_keys(username)
        driver.find_element(By.ID, "xyb-ac").send_keys(password)
        btn = driver.find_element(By.ID, "formulario:botaoLogin")
        driver.execute_script("arguments[0].click();", btn)

        WebDriverWait(driver, 15).until(
            lambda d: "paginaPrincipal.jsf" in d.current_url
        )
        todas_requisicoes += coletar_requisicoes(driver)
        print(f"    Login OK → {driver.current_url}")

        # ── PASSO 3: Fechar modais (se presentes) e abrir menu Assistência ──────
        print("[3/5] Navegando pelo menu...")

        # Tenta fechar qualquer modal visível via JavaScript (não depende de clicabilidade)
        for modal_id in ["formModalNotificacao:btnFechar", "pnlNotificacoesDiv"]:
            try:
                el = driver.find_element(By.ID, modal_id)
                driver.execute_script("arguments[0].style.display='none';", el)
                print(f"    Modal ocultado: {modal_id}")
            except Exception:
                pass

        # Usa execute_script em todos os cliques de navegação para evitar interceptação
        js_click = lambda xpath: driver.execute_script(
            "arguments[0].click();",
            driver.find_element(By.XPATH, xpath)
        )

        js_click("//a[@class='img' and text()='Assistência']")
        js_click("/html/body/div[2]/form/div[3]/div/ul/li[3]/ul/li[9]/a")
        todas_requisicoes += coletar_requisicoes(driver)

        # ── PASSO 4: Busca pelo prontuário ────────────────────────────────────
        print("[4/5] Buscando prontuário...")
        campo = aguardar(driver, "/html/body/div[4]/div/form/div/div[2]/div[3]/input")
        campo.send_keys(prontuario)
        js_click("/html/body/div[4]/div/form/div/div[2]/div[4]/input")
        aguardar(driver, "/html/body/div[4]/div/form/div/div[4]/table/tbody/tr[1]/td[7]/a[2]/img")
        js_click("/html/body/div[4]/div/form/div/div[4]/table/tbody/tr[1]/td[7]/a[2]/img")
        todas_requisicoes += coletar_requisicoes(driver)

        # ── PASSO 5: Tratar modal de obstetrícia (se existir) ─────────────────
        print("[5/5] Verificando modal de obstetrícia...")
        try:
            WebDriverWait(driver, 3).until(
                EC.presence_of_element_located((By.XPATH, '//*[@id="formObstetricia:btnProntMae"]'))
            )
            js_click('//*[@id="formObstetricia:btnProntMae"]')
            todas_requisicoes += coletar_requisicoes(driver)
        except Exception:
            print("    (modal não encontrado — paciente comum)")

        # ── Salvar resultado ──────────────────────────────────────────────────
        saida = "trafego_capturado.json"
        with open(saida, "w", encoding="utf-8") as f:
            json.dump(todas_requisicoes, f, indent=2, ensure_ascii=False)

        print(f"\n✓ {len(todas_requisicoes)} requisição(ões) capturada(s) → {saida}")

        # Resumo no terminal
        print("\n── Resumo ──────────────────────────────────────────────")
        for i, r in enumerate(todas_requisicoes, 1):
            post_info = f"  postData: {r['postData'][:120]}..." if r["postData"] else ""
            print(f"[{i}] {r['method']} {r['url']}{post_info}")

    except Exception as e:
        print(f"\n✗ Erro: {e}", file=sys.stderr)
        raise
    finally:
        driver.quit()


if __name__ == "__main__":
    main()

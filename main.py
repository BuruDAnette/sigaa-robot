import sys
import json
import os
import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from scraper import SigaaScraper

def main():
    if len(sys.argv) < 3:
        print("Uso: python main.py <usuario> <senha>")
        sys.exit(1)

    login = sys.argv[1]
    senha = sys.argv[2]

    chrome_options = Options()
    chrome_options.add_argument("--start-maximized")
    chrome_options.add_argument("--disable-extensions")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")

    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    wait = WebDriverWait(driver, 10)
    
    scraper = SigaaScraper(driver)
    
    dados_gerais = []

    try:
        print("[Python] Acedendo ao SIGAA...")
        driver.get("https://sig.cefetmg.br/sigaa/verTelaLogin.do")
        
        driver.find_element("name", "user.login").send_keys(login)
        driver.find_element("name", "user.senha").send_keys(senha)
        driver.find_element("css selector", "input[value='Entrar']").click()
        
        try:
            wait.until(EC.presence_of_element_located((By.ID, "painel-usuario")))
        except:
            print("[Python] Erro: Login falhou.")
            driver.quit()
            return

        print("[Python] Indo para lista de Turmas...")
        try:
            link = driver.find_element(By.LINK_TEXT, "Ver turmas anteriores")
            driver.execute_script("arguments[0].click();", link)
        except:
            pass

        indice_turma = 0
        
        while True:
            try:
                wait.until(EC.presence_of_element_located((By.CLASS_NAME, "listagem")) or EC.presence_of_element_located((By.CLASS_NAME, "subFormulario")))
            except:
                driver.get("https://sig.cefetmg.br/sigaa/portais/discente/turmas.jsf")
                time.sleep(1)

            botoes = driver.find_elements(By.XPATH, "//a[.//img[contains(@src, 'avancar.gif')]]")
            total = len(botoes)
            
            if total == 0 or indice_turma >= total:
                print(f"[Python] Processamento finalizado! {indice_turma} turmas processadas.")
                break

            print(f"\n--- Processando Turma {indice_turma + 1} de {total} ---")
            
            driver.execute_script("arguments[0].click();", botoes[indice_turma])
            time.sleep(1.5)

            try:
                nome_turma = scraper.get_nome_turma()
                print(f"[Python] Turma: {nome_turma}")

                if scraper.acessar_participantes():
                    prof = scraper.extrair_professor()
                    alunos = scraper.extrair_alunos()
                    
                    print(f"   -> {len(alunos)} alunos coletados.")

                    dados_gerais.append({
                        "disciplina": nome_turma,
                        "professor": prof,
                        "alunos": alunos
                    })
                
                driver.back()
                driver.back()
                
            except Exception as e:
                print(f"[Python] Erro nesta turma: {e}")
                driver.get("https://sig.cefetmg.br/sigaa/portais/discente/turmas.jsf")

            indice_turma += 1

        caminho_json = os.path.abspath("dados_sigaa.json")
        with open(caminho_json, "w", encoding="utf-8") as f:
            json.dump(dados_gerais, f, ensure_ascii=False, indent=4)

        print(f"JSON_GERADO:{caminho_json}")

    except Exception as e:
        print(f"[Python] Erro fatal: {e}")
    finally:
        driver.quit()

if __name__ == "__main__":
    main()
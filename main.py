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
        
        # Login
        driver.find_element("name", "user.login").send_keys(login)
        driver.find_element("name", "user.senha").send_keys(senha)
        driver.find_element("css selector", "input[value='Entrar']").click()
        
        try:
            wait.until(EC.presence_of_element_located((By.ID, "painel-usuario")))
        except:
            print("[Python] Erro: Login falhou.")
            return

        print("[Python] Indo para lista de Turmas Anteriores...")
        try:
            link_anteriores = driver.find_element(By.LINK_TEXT, "Ver turmas anteriores")
            driver.execute_script("arguments[0].click();", link_anteriores)
            wait.until(EC.presence_of_element_located((By.CLASS_NAME, "listagem")))
        except:
            print("[Python] Não achei o link de turmas anteriores. Tentando pegar a atual do dashboard.")

        botoes_turma = driver.find_elements(By.XPATH, "//table[@class='listagem']//a[.//img[contains(@src, 'avancar.gif')]]")
        total_turmas = len(botoes_turma)
        print(f"[Python] Encontradas {total_turmas} turmas para processar.")

        if total_turmas > 5:
            print("[Python] LIMITANDO A 5 TURMAS PARA TESTE RÁPIDO!")
            total_turmas = 5

        for i in range(total_turmas):
            print(f"\n--- Processando Turma {i+1}/{total_turmas} ---")
            
            botoes_turma = driver.find_elements(By.XPATH, "//table[@class='listagem']//a[.//img[contains(@src, 'avancar.gif')]]")
            
            if i >= len(botoes_turma): break # Segurança
            
            driver.execute_script("arguments[0].click();", botoes_turma[i])
            time.sleep(1.5)

            try:
                nome_turma = scraper.get_nome_turma()
                print(f"[Python] Turma: {nome_turma}")

                if scraper.acessar_participantes():
                    dados_professor = scraper.extrair_professor()
                    lista_alunos = scraper.extrair_alunos()
                    
                    print(f"[Python] -> {len(lista_alunos)} alunos coletados.")

                    dados_gerais.append({
                        "disciplina": nome_turma,
                        "professor": dados_professor,
                        "alunos": lista_alunos
                    })
                
            except Exception as e:
                print(f"[Python] Erro ao ler turma: {e}")

            print("[Python] Voltando para a lista...")
            driver.back()

            try:
                wait.until(EC.presence_of_element_located((By.CLASS_NAME, "listagem")))
            except:
                driver.get("https://sig.cefetmg.br/sigaa/portais/discente/turmas.jsf")
                wait.until(EC.presence_of_element_located((By.CLASS_NAME, "listagem")))

        
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
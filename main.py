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

def tentar_acessar_participantes(driver, wait):
    xpath_menus = [
        "//div[@class='itemMenu' and contains(text(),'Participantes')]",
        "//span[contains(@class, 'rich-menu-item-label') and contains(text(), 'Participantes')]",
        "//a[contains(text(),'Participantes')]"
    ]

    for xpath in xpath_menus:
        try:
            link = wait.until(EC.element_to_be_clickable((By.XPATH, xpath)))
            link.click()
            return True
        except:
            continue
    return False

def main():
    if len(sys.argv) < 3:
        print("Uso: python main.py <usuario> <senha>")
        # sys.argv = ["main.py", "LOGIN", "SENHA"]
        return

    usuario_sigaa = sys.argv[1]
    senha_sigaa = sys.argv[2]

    opts = Options()
    # opts.add_argument("--headless")
    opts.add_argument("--no-sandbox")
    opts.add_argument("--ignore-certificate-errors")
    opts.add_argument("--window-size=1920,1080")

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=opts)
    wait = WebDriverWait(driver, 10)
    todos_alunos = []

    try:
        print("=== [Python] Iniciando Robô (Modo Estagiário/Aluno) ===")
        driver.get("https://sig.cefetmg.br/sigaa/verTelaLogin.do")
        
        driver.find_element("name", "user.login").send_keys(usuario_sigaa)
        driver.find_element("name", "user.senha").send_keys(senha_sigaa)
        driver.find_element("css selector", "input[value='Entrar']").click()
        
        driver.get("https://sig.cefetmg.br/sigaa/portais/discente/discente.jsf")
        
        try:
            btn_anteriores = wait.until(EC.element_to_be_clickable((By.XPATH, "//a[contains(@href, 'turmas.jsf')]")))
            btn_anteriores.click()
            print("[Navegação] Acessou lista de turmas anteriores.")
        except:
            print("[ERRO] Não achou botão 'Ver turmas anteriores'.")
            return

        seletor_setinhas = "//table//img[contains(@src, 'avancar.gif')]/ancestor::a"
        
        try:
            wait.until(EC.presence_of_element_located((By.XPATH, seletor_setinhas)))
            elementos_setinhas = driver.find_elements(By.XPATH, seletor_setinhas)
            
            elementos_setinhas = [e for e in elementos_setinhas if e.is_displayed()]
            
            num_turmas = len(elementos_setinhas)
            print(f"[Python] Encontradas {num_turmas} matérias válidas.")
        except:
            print("[Python] Nenhuma matéria encontrada.")
            num_turmas = 0

        scraper = SigaaScraper(driver)

        for i in range(num_turmas):
            try:
                setinhas = driver.find_elements(By.XPATH, seletor_setinhas)
                setinhas = [e for e in setinhas if e.is_displayed()]
                
                if i >= len(setinhas): break
                
                botao_entrar = setinhas[i]
                
                try:
                    linha = botao_entrar.find_element(By.XPATH, "./ancestor::tr")
                    nome_materia = linha.text.split("\n")[0]
                except:
                    nome_materia = f"Matéria {i+1}"

                print(f"--- Acessando [{i+1}/{num_turmas}]: {nome_materia} ---")
                
                driver.execute_script("arguments[0].click();", botao_entrar)
                
                if tentar_acessar_participantes(driver, wait):
                    alunos = scraper.extract_student_data()
                    for a in alunos:
                        a['curso'] = nome_materia
                        todos_alunos.append(a)

                driver.get("https://sig.cefetmg.br/sigaa/portais/discente/turmas.jsf")
                wait.until(EC.presence_of_element_located((By.XPATH, seletor_setinhas)))

            except Exception as e:
                print(f"[ERRO] Falha na matéria {i+1}: {e}")
                driver.get("https://sig.cefetmg.br/sigaa/portais/discente/turmas.jsf")

        if todos_alunos:
            caminho_json = os.path.abspath("dados_integracao.json")
            with open(caminho_json, "w", encoding="utf-8") as f:
                json.dump(todos_alunos, f, ensure_ascii=False, indent=4)
            print(f"JSON_GERADO:{caminho_json}")
            print(f"[Python] Total coletado: {len(todos_alunos)} alunos.")
        else:
            print("[Python] Nenhum dado coletado.")

    except Exception as e:
        print(f"[ERRO FATAL] {e}")
    finally:
        driver.quit()

if __name__ == "__main__":
    main()
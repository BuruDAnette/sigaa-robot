import time
import json
import sys
import os
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from scraper import SigaaScraper

URL_LOGIN = "https://sig.cefetmg.br/sigaa/verTelaLogin.do"
URL_TURMAS_ANTERIORES = "https://sig.cefetmg.br/sigaa/portais/discente/turmas.jsf"

def salvar_dados(dados, nome_arquivo="alunos_coletados.json"):
    try:
        caminho = os.path.abspath(nome_arquivo)
        with open(caminho, 'w', encoding='utf-8') as f:
            json.dump(dados, f, ensure_ascii=False, indent=4)
        print(f"JSON_GERADO: {caminho}") 
    except Exception as e:
        print(f"Erro salvar: {e}")

def main():
    if len(sys.argv) < 3:
        print("Erro: Use python main.py <usuario> <senha>")
        # USERNAME = "seu_teste"
        # PASSWORD = "sua_senha"
        return
    else:
        USERNAME = sys.argv[1]
        PASSWORD = sys.argv[2]

    # --- CONFIGURAÇÃO ANTI-BLOQUEIO ---
    options = webdriver.ChromeOptions()
    options.add_argument("--start-maximized")
    options.add_argument("--disable-popup-blocking") # IMPORTANTE: Permite popups
    # options.add_argument("--headless") # Descomente para ocultar janela

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    wait = WebDriverWait(driver, 15)
    bot = SigaaScraper(driver)
    
    todos_alunos = []
    # SET PARA EVITAR DUPLICATAS (Armazena só as matrículas já vistas)
    matriculas_vistas = set()

    try:
        # 1. Login
        print("[1/5] Login...")
        driver.get(URL_LOGIN)
        driver.find_element(By.NAME, "user.login").send_keys(USERNAME)
        driver.find_element(By.NAME, "user.senha").send_keys(PASSWORD)
        driver.find_element(By.XPATH, "//input[@value='Entrar']").click()
        wait.until(EC.presence_of_element_located((By.ID, "conteudo")))

        # 2. Ir para Turmas
        print("[2/5] Indo para Turmas Anteriores...")
        driver.get(URL_TURMAS_ANTERIORES)
        wait.until(EC.presence_of_element_located((By.TAG_NAME, "table")))

        # 3. Loop Turmas
        idx = 0
        while True:
            # Pega as setinhas verdes (Botões de entrar)
            setinhas = driver.find_elements(By.XPATH, "//td//form[contains(@action, 'turmas.jsf')]//input[@type='image'] | //a[.//img[contains(@src, 'avancar') or contains(@src, 'seta')]]")
            
            if idx >= len(setinhas):
                print("--- Fim das turmas ---")
                break
                
            # Entra na turma
            try:
                linha = setinhas[idx].find_element(By.XPATH, "./ancestor::tr")
                nome_turma = linha.text.split("\n")[0]
            except: nome_turma = f"Turma {idx+1}"

            print(f"\n[3/5] Turma: {nome_turma}")
            
            # Clica (JS Force para garantir)
            driver.execute_script("arguments[0].click();", setinhas[idx])
            time.sleep(2)

            # 4. Extrai
            if bot.acessar_participantes():
                novos_alunos = bot.extrair_dados_perfil()
                
                # --- FILTRO DE DUPLICATAS ---
                count_adicionados = 0
                for aluno in novos_alunos:
                    mat = aluno.get('matricula')
                    
                    # Se tem matrícula e ela AINDA NÃO FOI VISTA
                    if mat and mat not in matriculas_vistas:
                        aluno['disciplina_origem'] = nome_turma
                        todos_alunos.append(aluno)
                        matriculas_vistas.add(mat) # Marca como visto
                        count_adicionados += 1
                    # Se não tem matrícula, adiciona mesmo assim por segurança (ou ignore)
                    elif not mat:
                        todos_alunos.append(aluno)
                
                print(f"   -> {len(novos_alunos)} lidos. {count_adicionados} novos adicionados (sem repetir).")
            else:
                print("   -> Erro ao acessar menu.")

            # 5. Volta
            print("   -> Voltando...")
            driver.get(URL_TURMAS_ANTERIORES)
            wait.until(EC.presence_of_element_located((By.TAG_NAME, "table")))
            idx += 1

        salvar_dados(todos_alunos)

    except Exception as e:
        print(f"ERRO FATAL: {e}")
        if todos_alunos: salvar_dados(todos_alunos)
    finally:
        driver.quit()

if __name__ == "__main__":
    main()
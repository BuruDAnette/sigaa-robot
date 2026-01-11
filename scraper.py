from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
import time
import re

def rodar_robo_sigaa(login, senha):
    print("Iniciando...")

    chrome_options = Options()
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--headless")

    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    
    dados_coletados = []

    try:
        print("Acessando login...")
        driver.get("https://sig.cefetmg.br/sigaa/verTelaLogin.do")
        driver.find_element(By.NAME, "user.login").send_keys(login)
        driver.find_element(By.NAME, "user.senha").send_keys(senha)
        driver.find_element(By.XPATH, "//input[@value='Entrar']").click()
        time.sleep(3) 

        print("Acessando lista de turmas...")
        url_lista = "https://sig.cefetmg.br/sigaa/portais/discente/turmas.jsf"
        driver.get(url_lista)
        time.sleep(2)

        try:
            banner = driver.find_element(By.ID, "sigaa-cookie-consent")
            driver.execute_script("arguments[0].click();", banner.find_element(By.TAG_NAME, "button"))
        except: pass

        setas = driver.find_elements(By.XPATH, "//img[contains(@src, 'avancar.gif')]/parent::a")
        total_materias = len(setas)
        print(f"Encontradas {total_materias} matérias.")

        for i in range(total_materias):
            try:
                driver.get(url_lista)
                time.sleep(2)
                setas_atualizadas = driver.find_elements(By.XPATH, "//img[contains(@src, 'avancar.gif')]/parent::a")
                
                if i >= len(setas_atualizadas): break
                
                setas_atualizadas[i].click()
                time.sleep(3)

                botao_participantes = None
                try:
                    menu_turma = driver.find_element(By.XPATH, "//td[contains(text(), 'Turma')]")
                    driver.execute_script("arguments[0].click();", menu_turma)
                    time.sleep(1)
                    botao_participantes = driver.find_element(By.XPATH, "//span[contains(@id, 'menuParticipantes')]")
                except:
                    try:
                        botao_participantes = driver.find_element(By.XPATH, "//div[@class='itemMenu' and contains(text(), 'Participantes')]")
                    except: pass

                if not botao_participantes:
                    frames = driver.find_elements(By.TAG_NAME, "iframe") + driver.find_elements(By.TAG_NAME, "frame")
                    for frame in frames:
                        try:
                            driver.switch_to.frame(frame)
                            botao_participantes = driver.find_element(By.XPATH, "//div[@class='itemMenu' and contains(text(), 'Participantes')]")
                            if botao_participantes: break
                        except: driver.switch_to.default_content()

                if botao_participantes:
                    driver.execute_script("arguments[0].click();", botao_participantes)
                    time.sleep(3)

                    linhas = driver.find_elements(By.CSS_SELECTOR, "table.participantes tbody tr")
                    if not linhas: linhas = driver.find_elements(By.CSS_SELECTOR, "table.listagem tbody tr")
                    
                    count = 0
                    for linha in linhas:
                        colunas = linha.find_elements(By.TAG_NAME, "td")
                        if len(colunas) >= 2:
                            texto_completo = colunas[1].text.strip()
                            
                            if "Departamento:" in texto_completo or "Formação:" in texto_completo or "Docente" in linha.text:
                                continue

                            if not texto_completo: continue

                            nome_real = texto_completo
                            matricula_real = ""
                            email_real = ""
                            curso_real = "SIGAA"

                            if "Matrícula:" in texto_completo:
                                try:
                                    partes = texto_completo.split("Curso:")
                                    nome_real = partes[0].strip()
                                    
                                    match_matr = re.search(r'Matrícula:\s*(\d+)', texto_completo)
                                    if match_matr:
                                        matricula_real = match_matr.group(1)
                                    
                                    match_email = re.search(r'E-mail:\s*([\w\.-]+@[\w\.-]+)', texto_completo)
                                    if match_email:
                                        email_real = match_email.group(1)

                                    match_curso = re.search(r'Curso:\s*(.*?)\n', texto_completo)
                                    if match_curso:
                                        curso_real = match_curso.group(1).strip()

                                except:
                                    pass
                            
                            if not matricula_real:
                                texto_col0 = colunas[0].text.strip()
                                if texto_col0.isdigit():
                                    matricula_real = texto_col0
                                else:
                                    matricula_real = str(hash(nome_real))

                            if not any(a['matricula'] == matricula_real for a in dados_coletados):
                                dados_coletados.append({
                                    "matricula": matricula_real,
                                    "nome": nome_real,
                                    "curso": curso_real,
                                    "email": email_real,
                                    "status": "ATIVO"
                                })
                                count += 1
                                
                    print(f"+{count} alunos processados na turma.")
                
                driver.switch_to.default_content()

            except Exception as e:
                print(f"Erro na matéria {i+1}: {str(e)[:50]}")
                driver.switch_to.default_content()
                continue

        return dados_coletados

    except Exception as e:
        return [{"erro": str(e)}]
    finally:
        driver.quit()
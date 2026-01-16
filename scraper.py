import time
import re
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

class SigaaScraper:
    def __init__(self, driver):
        self.driver = driver
        self.wait = WebDriverWait(driver, 5)

    def get_nome_turma(self):
        try:
            cod = self.driver.find_element(By.ID, "linkCodigoTurma").text.strip()
            nome = self.driver.find_element(By.ID, "linkNomeTurma").text.strip()
            return f"{cod.replace(' -', '')} - {nome}"
        except:
            return "Turma Desconhecida"

    def acessar_participantes(self):
        print("   -> [Navegação] Buscando menu Participantes...")
        try:
            btn = self.wait.until(EC.element_to_be_clickable(
                (By.XPATH, "//div[contains(@class, 'itemMenu') and contains(text(), 'Participantes')]")
            ))
            btn.click()
            return True
        except:
            try:
                self.driver.execute_script("document.querySelector('.itemMenuHeaderTurma').click()")
                time.sleep(0.5)
                self.driver.find_element(By.XPATH, "//div[contains(text(), 'Participantes')]").click()
                return True
            except:
                return False

    def extrair_professor(self):
        prof = {"nome": "N/A", "email": ""}
        try:
            self.wait.until(EC.presence_of_element_located((By.CLASS_NAME, "participantes")))
            tabelas = self.driver.find_elements(By.CLASS_NAME, "participantes")
            
            if tabelas:
                texto = tabelas[0].text
                match_email = re.search(r'E-Mail:\s*([\w\.-]+@[\w\.-]+)', texto, re.IGNORECASE)
                if match_email: prof['email'] = match_email.group(1).lower()

                linhas = texto.split('\n')
                for l in linhas:
                    l = l.strip()
                    if len(l) > 4 and "Departamento" not in l and "Formação" not in l and "E-Mail" not in l:
                        prof['nome'] = l
                        break
        except: pass
        return prof

    def extrair_alunos(self):
        lista = []
        try:
            linhas = self.driver.find_elements(By.XPATH, "//table[@class='participantes']//tr")
            print(f"   -> [Extração] Varrendo {len(linhas)} linhas por alunos (2 colunas)...")

            for tr in linhas:
                cols = tr.find_elements(By.TAG_NAME, "td")
                
                for i, col in enumerate(cols):
                    try:
                        texto = col.text
                        if "Matrícula" not in texto: continue

                        mat = re.search(r'Matr.cula:\s*(\d+)', texto).group(1)
                        
                        email_match = re.search(r'E-mail:\s*([\w\.-]+@[\w\.-]+)', texto)
                        email = email_match.group(1) if email_match else ""
                        
                        nome = texto.split('\n')[0].strip().replace("(Monitor)", "").strip()
                        
                        foto = ""
                        if i > 0:
                            try:
                                img = cols[i-1].find_element(By.TAG_NAME, "img")
                                src = img.get_attribute("src")
                                if src and "no_picture" not in src: foto = src
                            except: pass

                        lista.append({
                            "nome": nome,
                            "matricula": mat,
                            "email": email,
                            "foto": foto
                        })
                    except: continue

            return lista
        except: return []
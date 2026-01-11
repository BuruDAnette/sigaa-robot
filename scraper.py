import os
import time
import requests
import re
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

class SigaaScraper:
    def __init__(self, driver):
        self.driver = driver
        self.wait = WebDriverWait(self.driver, 5)

    def download_photo(self, url, matricula):
        if not url or "no_picture" in url or "offline" in url:
            return None
        try:
            if not os.path.exists("fotos"):
                os.makedirs("fotos")
            
            session = requests.Session()
            for cookie in self.driver.get_cookies():
                session.cookies.set(cookie['name'], cookie['value'])
            
            response = session.get(url, verify=False)
            if response.status_code == 200:
                ext = "jpg"
                if ".png" in url: ext = "png"
                filename = f"fotos/{matricula}.{ext}"
                with open(filename, 'wb') as f:
                    f.write(response.content)
                return filename
        except Exception as e:
            print(f"[AVISO] Erro ao baixar foto {matricula}: {e}")
        return None

    def extract_student_data(self):
        dados = []
        
        tabela = None
        selectors = [
            (By.ID, "participantes"),
            (By.XPATH, "//*[contains(text(),'Discentes')]/following::table[1]"),
            (By.XPATH, "//th[contains(text(),'Matrícula')]/ancestor::table"),
            (By.CSS_SELECTOR, "table.listagem")
        ]
        
        print("[Scraper] Buscando tabela de alunos...")
        for by, val in selectors:
            try:
                tabela = self.driver.find_element(by, val)
                if tabela.is_displayed():
                    print(f"[Scraper] Tabela encontrada via: {val}")
                    break
            except:
                continue
                
        if not tabela:
            print("[ERRO] Tabela de participantes não encontrada com nenhum método.")
            return []

        linhas = tabela.find_elements(By.TAG_NAME, "tr")
        print(f"[Scraper] Analisando {len(linhas)} linhas...")

        for i, linha in enumerate(linhas):
            try:
                texto = linha.text
                
                if "Matrícula" not in texto and "Curso" not in texto:
                    continue
                
                try:
                    btn_perfil = linha.find_element(By.CSS_SELECTOR, "img[title='Visualizar Perfil']")
                except:
                    continue

                matricula = "00000"
                nome = "Desconhecido"
                
                match_mat = re.search(r'Matrícula:\s*(\d+)', texto)
                if match_mat:
                    matricula = match_mat.group(1)
                
                try:
                    nome = texto.split("\n")[0].strip()
                    if "Visualizar Perfil" in nome: nome = nome.replace("Visualizar Perfil", "")
                except: pass

                self.driver.execute_script("arguments[0].click();", btn_perfil)
                
                modal = self.wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "div.ui-dialog")))
                time.sleep(0.3)
                
                email = "Não informado"
                caminho_foto = None
                
                try:
                    try:
                        lbl_email = modal.find_element(By.XPATH, ".//strong[contains(text(),'E-mail')]/following-sibling::em")
                        email = lbl_email.text.strip()
                    except:
                        match_email = re.search(r'[\w\.-]+@[\w\.-]+', modal.text)
                        if match_email: email = match_email.group(0)

                    img = modal.find_element(By.XPATH, ".//div[contains(@class,'ui-dialog-content')]//img[contains(@src,'foto') or contains(@src,'perfil') or contains(@src,'arquivo')]")
                    src = img.get_attribute("src")
                    caminho_foto = self.download_photo(src, matricula)

                except Exception as ex:
                    print(f"[Aviso] Falha ao ler detalhes do modal: {ex}")

                try:
                    fechar = modal.find_element(By.CSS_SELECTOR, "a.ui-dialog-titlebar-close")
                    self.driver.execute_script("arguments[0].click();", fechar)
                    self.wait.until(EC.invisibility_of_element_located((By.CSS_SELECTOR, "div.ui-dialog")))
                except: pass

                dados.append({
                    "matricula": matricula,
                    "nome": nome,
                    "email": email,
                    "foto_path": caminho_foto
                })
                print(f"[+]: {nome}")

            except Exception as e:
                continue
        
        return dados
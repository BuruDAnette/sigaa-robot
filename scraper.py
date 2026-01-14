import time
import re
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

class SigaaScraper:
    def __init__(self, driver):
        self.driver = driver
        self.wait = WebDriverWait(driver, 10)

    def get_nome_turma(self):

        try:
            codigo = self.driver.find_element(By.ID, "linkCodigoTurma").text.strip()
            nome = self.driver.find_element(By.ID, "linkNomeTurma").text.strip()
            codigo = codigo.replace(" -", "")
            return f"{codigo} - {nome}"
        except:
            return "Turma Desconhecida"

    def acessar_participantes(self):

        print("   -> [Navegação] Acedendo ao menu Participantes...")
        
        try:

            botao = self.wait.until(EC.element_to_be_clickable(
                (By.XPATH, "//div[contains(@class, 'itemMenu') and contains(text(), 'Participantes')]")
            ))
            botao.click()
            return True

        except Exception:
            try:
                print("   -> [Navegação] Tentando expandir menu lateral...")
                aba_turma = self.driver.find_element(By.CSS_SELECTOR, ".itemMenuHeaderTurma")
                self.driver.execute_script("arguments[0].click();", aba_turma)
                time.sleep(0.5)
                
                botao = self.driver.find_element(By.XPATH, "//div[contains(@class, 'itemMenu') and contains(text(), 'Participantes')]")
                botao.click()
                return True
            except:
                print("   -> [Erro] Não foi possível clicar no menu Participantes.")
                return False

    def extrair_professor(self):

        professor = {"nome": "Professor Não Identificado", "email": ""}
        
        try:
            self.wait.until(EC.presence_of_element_located((By.CLASS_NAME, "participantes")))
            
            tabelas = self.driver.find_elements(By.CLASS_NAME, "participantes")
            
            for tabela in tabelas:

                linhas = tabela.find_elements(By.TAG_NAME, "tr")
                for linha in linhas:
                    texto = linha.text
                    if "Departamento" in texto or "Formação" in texto:
                        linhas_texto = texto.split('\n')
                        
                        for l in linhas_texto:
                            l = l.strip()
                            if len(l) > 3 and "Departamento" not in l and "Formação" not in l and "E-Mail" not in l:
                                professor['nome'] = l
                                break
                        
                        match_email = re.search(r'E-Mail:\s*([\w\.-]+@[\w\.-]+)', texto, re.IGNORECASE)
                        if match_email:
                            professor['email'] = match_email.group(1).lower()
                        
                        return professor

        except Exception as e:
            print(f"   -> [Aviso] Erro ao ler professor: {e}")
        
        return professor

    def extrair_alunos(self):
        alunos_dados = []
        
        try:
            linhas = self.driver.find_elements(By.XPATH, "//table[@class='participantes']//tr")
            
            print(f"   -> [Extração] Analisando {len(linhas)} linhas na página...")

            for linha in linhas:
                try:
                    colunas = linha.find_elements(By.TAG_NAME, "td")
                    if len(colunas) < 2: continue

                    texto_celula = colunas[1].text
                    
                    match_mat = re.search(r'Matr.cula:\s*(\d+)', texto_celula)
                    
                    if match_mat:
                        matricula = match_mat.group(1)
                        
                        partes_texto = texto_celula.split('\n')
                        nome = partes_texto[0].strip().replace("(Monitor)", "").strip()
                        
                        if "Departamento" in texto_celula: continue

                        email = ""
                        match_email = re.search(r'E-mail:\s*([\w\.-]+@[\w\.-]+)', texto_celula)
                        if match_email: email = match_email.group(1)
                        
                        curso = ""
                        match_curso = re.search(r'Curso:\s*(.+)', texto_celula)
                        if match_curso: curso = match_curso.group(1).strip()

                        foto_url = ""
                        try:
                            img = colunas[0].find_element(By.TAG_NAME, "img")
                            src = img.get_attribute("src")
                            if src and "no_picture" not in src and "offline" not in src:
                                foto_url = src
                        except: pass

                        alunos_dados.append({
                            'nome': nome,
                            'matricula': matricula,
                            'email': email,
                            'curso': curso,
                            'foto': foto_url
                        })
                        print(f"      [Aluno] {nome}")
                
                except: continue

            return alunos_dados
        except Exception as e:
            print(f"   -> [Erro] Falha ao extrair alunos: {e}")
            return []
import time
import re
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys

class SigaaScraper:
    def __init__(self, driver):
        self.driver = driver
        self.wait = WebDriverWait(driver, 5)

    def acessar_participantes(self):
        print("   -> [Navegação] Procurando menu Participantes...")
        
        # 1. Tenta Menu Lateral (JS Force)
        try:
            self.driver.execute_script("document.querySelector('.itemMenuHeaderTurma').click()")
            time.sleep(0.5)
            # Tenta clicar no link dentro do div itemMenu
            self.driver.execute_script("""
                var itens = document.querySelectorAll('.itemMenu');
                for (var i = 0; i < itens.length; i++) {
                    if (itens[i].textContent.includes('Participantes')) {
                        itens[i].click();
                        break;
                    }
                }
            """)
            return True
        except: pass

        # 2. Tenta Menu Superior (Dropdown)
        try:
            aba_turma = self.driver.find_element(By.XPATH, "//td[normalize-space()='Turma']")
            ActionChains(self.driver).move_to_element(aba_turma).perform()
            time.sleep(1)
            self.driver.execute_script("document.getElementById('formMenuDrop:menuParticipantes:anchor').click();")
            return True
        except: pass
        
        # 3. Fallback Genérico
        try:
            links = self.driver.find_elements(By.XPATH, "//a[contains(text(), 'Participantes')]")
            for link in links:
                if link.is_displayed():
                    link.click()
                    return True
        except: pass

        return False

    def extrair_dados_perfil(self):
        alunos_dados = []
        
        # Espera carregar qualquer coisa na tela
        try:
            self.wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
        except:
            return []

        # Pega botões de perfil
        xpath_botoes = "//img[contains(@title, 'Visualizar Perfil')]/ancestor::a | //img[contains(@src, 'comprovante.png')]/ancestor::a"
        botoes = self.driver.find_elements(By.XPATH, xpath_botoes)
        
        print(f"   -> [Extração] Encontrados {len(botoes)} alunos.")
        
        janela_principal = self.driver.current_window_handle

        for i in range(len(botoes)):
            janela_aberta = False
            try:
                # Recarrega a lista de botões para evitar StaleElement
                botoes = self.driver.find_elements(By.XPATH, xpath_botoes)
                if i >= len(botoes): break
                
                # Abre perfil
                self.driver.execute_script("arguments[0].click();", botoes[i])
                
                # Verifica Janela vs Modal
                try:
                    WebDriverWait(self.driver, 3).until(lambda d: len(d.window_handles) > 1)
                    janelas = self.driver.window_handles
                    self.driver.switch_to.window(janelas[-1])
                    janela_aberta = True
                except TimeoutException:
                    pass # Modal na mesma tela

                # --- LEITURA DOS DADOS ---
                dados = self._ler_tags_especificas()
                
                if dados and dados.get('matricula'):
                    # Garante que temos um nome, senão coloca placeholder
                    if not dados.get('nome'):
                        dados['nome'] = "NOME_DESCONHECIDO"
                    alunos_dados.append(dados)
                else:
                    # Se falhar, tenta ler texto bruto
                    dados_brutos = self._ler_texto_bruto()
                    if dados_brutos and dados_brutos.get('matricula'):
                        alunos_dados.append(dados_brutos)
                    else:
                        print(f"      [AVISO] Não foi possível extrair matrícula do aluno {i+1}")

                # Fecha Janela ou Modal
                if janela_aberta:
                    self.driver.close()
                    self.driver.switch_to.window(janela_principal)
                else:
                    try:
                        ActionChains(self.driver).send_keys(Keys.ESCAPE).perform()
                        self.driver.execute_script("var x = document.querySelector('a.ui-dialog-titlebar-close'); if(x) x.click();")
                    except: pass
                
                time.sleep(0.2)

            except Exception as e:
                # print(f"Erro: {e}") # Silencioso
                if len(self.driver.window_handles) > 1:
                    self.driver.close()
                self.driver.switch_to.window(janela_principal)

        return alunos_dados

    def _ler_tags_especificas(self):
        """Lê baseando-se no HTML específico do SIGAA"""
        dados = {'nome': '', 'matricula': None, 'email': '', 'curso': '', 'foto': '', 'disciplina_origem': ''}
        
        try:
            # 1. NOME (CORREÇÃO APLICADA AQUI)
            try:
                # Procura pelo texto "Dados do Discente", sobe para o pai, e pega a tag <b>
                # Essa é a estratégia mais robusta baseada na sua imagem
                nome_el = self.driver.find_element(By.XPATH, "//*[contains(text(), 'Dados do Discente')]/../b")
                dados['nome'] = nome_el.text.strip()
            except:
                # Tenta fallback antigo se o primeiro falhar
                try:
                    nome_el = self.driver.find_element(By.XPATH, "//span[contains(@style, 'bold')] | //div[@id='perfil-discente']//b")
                    dados['nome'] = nome_el.text.strip()
                except: pass

            # 2. DADOS GERAIS (Matricula, Email, Curso)
            # O layout costuma ter Matricula: 12345 (texto solto ou dentro de tabelas)
            try:
                # Pega todo o texto do corpo do modal para regex rápidos ou busca direta
                corpo_texto = self.driver.find_element(By.TAG_NAME, "body").text
                
                # Matrícula via Regex (procura numero de 10 a 12 digitos)
                match_mat = re.search(r'Matrícula:\s*(\d+)', corpo_texto)
                if match_mat:
                    dados['matricula'] = match_mat.group(1)
                
                # Email
                match_email = re.search(r'E-mail:\s*([\w\.-]+@[\w\.-]+)', corpo_texto)
                if match_email:
                    dados['email'] = match_email.group(1)

                # Curso
                match_curso = re.search(r'Curso:\s*(.+)', corpo_texto)
                if match_curso:
                    dados['curso'] = match_curso.group(1).strip()
                    
            except: pass

            # 3. FOTO
            try:
                img = self.driver.find_element(By.XPATH, "//div[@id='foto-perfil']//img | //td//img[contains(@src, 'foto') or contains(@src, 'perfil') or contains(@src, 'WhatsApp')]")
                src = img.get_attribute("src")
                if "no_picture" not in src:
                    dados['foto'] = src
            except: pass
            
            # 4. Disciplina de Origem (Captura do título da janela se disponível ou passado externo)
            # Geralmente isso vem da iteração anterior, mas se estiver no modal:
            # dados['disciplina_origem'] = ... (Implementar se necessário)

            return dados
        except:
            return None

    def _ler_texto_bruto(self):
        """Fallback: Lê o texto da página inteira e usa Regex"""
        dados = {'nome': 'Desconhecido', 'matricula': None, 'email': '', 'curso': '', 'foto': ''}
        try:
            corpo = self.driver.find_element(By.TAG_NAME, "body").text
            
            # Matricula: Procura sequencia de 10 a 12 numeros solta
            match_mat = re.search(r'\b\d{10,12}\b', corpo)
            if match_mat: dados['matricula'] = match_mat.group(0)

            # Email
            match_email = re.search(r'[\w\.-]+@[\w\.-]+', corpo)
            if match_email: dados['email'] = match_email.group(0)
            
            return dados
        except: return None
import json
import sqlite3
import os

# 1. Configurações dos arquivos
ARQUIVO_JSON = r"C:\Users\Administrador\OneDrive\Documentos\sigaa-robot\alunos_coletados.json"
NOME_BANCO = "base_alunos.db"

def importar_dados():
    if not os.path.exists(ARQUIVO_JSON):
        print(f"Erro: O arquivo {ARQUIVO_JSON} não foi encontrado.")
        return

    print("--- Iniciando Importação ---")

    conexao = sqlite3.connect(NOME_BANCO)
    cursor = conexao.cursor()

    sql_create = """
    CREATE TABLE IF NOT EXISTS alunos (
        matricula TEXT PRIMARY KEY,
        nome TEXT,
        email TEXT,
        curso TEXT,
        foto TEXT,
        disciplina_origem TEXT
    );
    """
    cursor.execute(sql_create)

    try:
        with open(ARQUIVO_JSON, 'r', encoding='utf-8') as f:
            lista_alunos = json.load(f)
            print(f"Lidos {len(lista_alunos)} registros do JSON.")
    except Exception as e:
        print(f"Erro ao ler JSON: {e}")
        return

    novos = 0
    atualizados = 0

    for aluno in lista_alunos:

        dados = (
            aluno.get('nome', 'DESCONHECIDO'),
            aluno.get('email', ''),
            aluno.get('curso', ''),
            aluno.get('foto', ''),
            aluno.get('disciplina_origem', ''),
            aluno.get('matricula')
        )

        try:
            cursor.execute("""
                INSERT INTO alunos (nome, email, curso, foto, disciplina_origem, matricula)
                VALUES (?, ?, ?, ?, ?, ?)
            """, dados)
            novos += 1
            
        except sqlite3.IntegrityError:
            cursor.execute("""
                UPDATE alunos 
                SET nome = ?, email = ?, curso = ?, foto = ?, disciplina_origem = ?
                WHERE matricula = ?
            """, dados)
            atualizados += 1

    conexao.commit()
    conexao.close()

    print("-" * 30)
    print(f"Processo finalizado.")
    print(f"Novos alunos inseridos: {novos}")
    print(f"Alunos atualizados: {atualizados}")
    print(f"Banco de dados salvo em: {NOME_BANCO}")

# Executa o programa
if __name__ == "__main__":
    importar_dados()
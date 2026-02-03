from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from datetime import datetime, timedelta
import time
from unidecode import unidecode


# Configurações do ChromeDriver
chrome_options = Options()
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")

# Inicializa o navegador com o ChromeDriver
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
wait = WebDriverWait(driver, 50)

# Abre a página de login
driver.get("http://10.2.2.8:8080/pacientehrn/login.jsf")

# Insere o nome de usuário e senha
username = driver.find_element(By.ID, "login")
password = driver.find_element(By.ID, "xyb-ac")

username.send_keys("igorims")
password.send_keys("timao15@")

# Clica no botão de login
login_button = driver.find_element(By.ID, "formulario:botaoLogin")
login_button.click()

# Localiza a aba "Mapa" e simula passar o mouse sobre ela
aba_mapa = driver.find_element(By.XPATH, "/html/body/div[2]/form/div[3]/div/ul/li[3]")
ActionChains(driver).move_to_element(aba_mapa).perform()

# Espera a opção "Cirúrgico" estar clicável e clica
aba_cirurgico = driver.find_element(By.XPATH, "/html/body/div[2]/form/div[3]/div/ul/li[3]/ul/li[9]/a")
ActionChains(driver).move_to_element(aba_cirurgico).perform()
aba_cirurgico.click()

# Clica no botão de seleção de clínica
select = driver.find_element(By.ID, "formMedicos:selClinica")
select.click()

# Lista para armazenar os dados que serão salvos no HTML
dados_html = []

# Loop para percorrer as opções de 3 a 42
for i in range(2, 42):
    try:
        # Localiza a opção atual
        option_xpath = f'//*[@id="formMedicos:selClinica"]/option[{i}]'
        option = driver.find_element(By.XPATH, option_xpath)
        
        # Clica na opção
        option.click()
        
        # Espera um pouco para garantir que a tabela seja carregada
        time.sleep(0.5)
        
        # Localiza todas as linhas da tabela
        linhas = driver.find_elements(By.XPATH, '//*[@id="formMedicos:oTableNovo"]/tbody/tr')
        
        # Itera sobre as linhas da tabela
        for idx, linha in enumerate(linhas):
            try:
                # Localiza o valor da coluna 6 (j_id318)
                valor_coluna_xpath = f'//*[@id="formMedicos:oTableNovo:{idx}:j_id318"]'
                valor_coluna = linha.find_element(By.XPATH, valor_coluna_xpath).text
                
                # Converte o valor para inteiro
                valor_coluna = int(valor_coluna)
                
                # Verifica se o valor é maior ou igual a 15
                if valor_coluna >= 15:
                    # Extrai os dados das outras colunas
                    coluna1 = linha.find_element(By.XPATH, f'//*[@id="formMedicos:oTableNovo:{idx}:j_id304"]').text
                    coluna2 = linha.find_element(By.XPATH, f'//*[@id="formMedicos:oTableNovo:{idx}:j_id307"]').text
                    coluna3 = linha.find_element(By.XPATH, f'//*[@id="formMedicos:oTableNovo:{idx}:j_id312"]').text
                    coluna4 = linha.find_element(By.XPATH, f'//*[@id="formMedicos:oTableNovo:{idx}:j_id315"]').text
                    coluna5 = linha.find_element(By.XPATH, f'//*[@id="formMedicos:oTableNovo:{idx}:j_id318"]').text
                    
                    # Separa o conteúdo da coluna 3 (após o ponto ".")
                    if "." in coluna3:
                        parte1, parte2 = coluna3.split(".", 1)  # Divide no primeiro ponto
                        coluna3 = parte1.strip()  # Mantém apenas a parte antes do ponto
                        numero_leito = parte2.strip()  # Parte após o ponto
                    else:
                        numero_leito = ""  # Se não houver ponto, deixa vazio
                    
                    # Remove a informação após o hífen "-" da coluna 3
                    if "-" in coluna3:
                        coluna3 = coluna3.split("-", 1)[0].strip()  # Mantém apenas a parte antes do hífen
                    
                    # Remove acentos da coluna 3 para evitar problemas com "Clínica" e "Clinica"
                    coluna3_normalizada = unidecode(coluna3).lower()  # Normaliza para minúsculas e remove acentos

                    # Define o prazo máximo para limpeza
                    if any(word in coluna3_normalizada for word in ["clinica", "uce"]):
                        dias_adicionais = 30
                    else:
                        dias_adicionais = 15
                    
                    # Calcula a data de início no leito (data atual - coluna 5)
                    try:
                        dias_no_leito = int(coluna5)
                        data_atual = datetime.now()
                        inicio_no_leito = data_atual - timedelta(days=dias_no_leito)
                        inicio_no_leito_str = inicio_no_leito.strftime("%d/%m/%Y")
                    except Exception as e:
                        print(f"Erro ao calcular a data de início no leito: {e}")
                        inicio_no_leito_str = "N/A"
                    
                    # Calcula o prazo máximo para limpeza
                    prazo_maximo_limpeza = inicio_no_leito + timedelta(days=dias_adicionais)
                    prazo_maximo_limpeza_str = prazo_maximo_limpeza.strftime("%d/%m/%Y")
                    
                    # Adiciona os dados à lista
                    dados_html.append({
                        "coluna1": coluna1,
                        "coluna2": coluna2,
                        "coluna3": coluna3,
                        "coluna4": coluna4,
                        "coluna5": coluna5,
                        "numero_leito": numero_leito,
                        "inicio_no_leito": inicio_no_leito_str,
                        "prazo_maximo_limpeza": prazo_maximo_limpeza_str
                    })
            except Exception as e:
                print(f"Erro ao processar a linha {idx + 1}: {e}")
    except Exception as e:
        print(f"Erro ao processar a opção {i}: {e}")

driver.quit()

# Salva os dados em um arquivo HTML estilizado
with open("dados.html", "w", encoding="utf-8") as file:
    file.write("""
    <html>
    <head>
        <meta charset="utf-8">
        <title>Dados Capturados</title>
        <style>
            body {
                font-family: Arial, sans-serif;
                background-color: #f4f4f4;
                margin: 20px;
                padding: 20px;
                text-align: center;
            }
            h1 {
                color: #333;
            }
            table {
                width: 90%;
                margin: 20px auto;
                border-collapse: collapse;
                background: #fff;
                box-shadow: 0px 0px 10px rgba(0, 0, 0, 0.1);
                border-radius: 8px;
                overflow: hidden;
            }
            th, td {
                padding: 12px;
                border: 1px solid #ddd;
                text-align: center;
            }
            th {
                background: #007BFF;
                color: white;
            }
            tr:nth-child(even) {
                background: #f9f9f9;
            }
            tr:hover {
                background: #f1f1f1;
            }
        </style>
    </head>
    <body>
        <h1>Dados Capturados</h1>
        <table>
            <tr>
                <th>Prontuário</th>
                <th>Paciente</th>
                <th>Setor</th>
                <th>Dias no Leito</th>
                <th>Dias no Hospital</th>
                <th>Número do Leito</th>
                <th>Início no Leito</th>
                <th>Prazo Máximo para Limpeza</th>
            </tr>
    """)
    
    for dado in dados_html:
        file.write(f"""
            <tr>
                <td>{dado['coluna1']}</td>
                <td>{dado['coluna2']}</td>
                <td>{dado['coluna3']}</td>
                <td>{dado['coluna4']}</td>
                <td>{dado['coluna5']}</td>
                <td>{dado['numero_leito']}</td>
                <td>{dado['inicio_no_leito']}</td>
                <td>{dado['prazo_maximo_limpeza']}</td>
            </tr>
        """)

    file.write("""
        </table>
    </body>
    </html>
    """)

print("Dados salvos em dados.html")

import os
from flask import Flask, render_template, request, redirect, url_for, session, jsonify
import logging
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from datetime import datetime, timedelta, date
from unidecode import unidecode
from dist.conexao import get_db_connection
from relatorios.pdf import exportar_pdf
from relatorios.xlsx import exportar_xlsx
from relatorios.csv import exportar_csv
import pymysql
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from threading import Event
from threading import Timer
from flask import Response
import json
import threading
from threading import Thread
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import requests
from bs4 import BeautifulSoup
import re
import html
import time
from typing import List, Dict
from collections import Counter

app = Flask(__name__)
app.secret_key = "chave_secreta_para_sessao"
logging.basicConfig(level=logging.INFO)

EMAIL_HOST = "smtp.gmail.com"
EMAIL_PORT = 587

EMAIL_USER = "cleanleito@gmail.com"
EMAIL_PASSWORD = "ogtknovurmjxbqlh"

LEITOS_CACHE_FILE = "data\leitos_por_ip.json"
INTERVALO_ATUALIZACAO = 60 # 1 minutos 

timers_limpeza = {}


# 🔔 Evento global que sinaliza atualização de limpeza
atualizacao_evento = Event()

driver = None

def get_driver():
    options = webdriver.ChromeOptions()
    options.add_argument("--headless=new")  # headless opcional
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--disable-software-rasterizer")

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    return driver


@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()

        if not username or not password:
            return render_template(
                "index.html",
                error="Usuário e Senha são obrigatórios."
            )

        if login_if_needed(username, password):
            session.clear()
            session["usuario_logado"] = username.upper()
            session["logado"] = True
            return redirect(url_for("pagina_principal"))


        return render_template(
            "index.html",
            error="Usuário ou Senha incorretos."
        )

    return render_template("index.html")


@app.route("/pagina_principal")
def pagina_principal():
    if not session.get("logado"):
        return redirect(url_for("index"))
    return render_template("paginaPrincipal.html")


@app.context_processor
def inject_user():
    return dict(usuario_logado=session.get("usuario_logado"))



# Função para login e navegação até a página de prontuário (Principal)
def login_if_needed(username, password):
    BASE_URL = "http://10.2.2.8:8080"
    #BASE_URL = "https://sistemasnti.isgh.org.br"
    LOGIN_URL = f"{BASE_URL}/pacientehrn/login.jsf"
    PAGINA_PRINCIPAL = f"{BASE_URL}/pacientehrn/paginaPrincipal.jsf"

    session_http = requests.Session()

    try:
        # =========================
        # 1️⃣ GET login.jsf (captura ViewState + cookie)
        # =========================
        resp_get = session_http.get(LOGIN_URL, timeout=5)

        if resp_get.status_code != 200:
            logging.error("Falha ao acessar login.jsf")
            return False

        soup = BeautifulSoup(resp_get.text, "html.parser")
        viewstate_input = soup.find("input", {"name": "javax.faces.ViewState"})

        if not viewstate_input:
            logging.error("ViewState não encontrado")
            return False

        viewstate = viewstate_input["value"]

        # =========================
        # 2️⃣ POST login
        # =========================
        payload = {
            "formulario": "formulario",
            "login": username,
            "xyb-ac": password,
            "formulario:botaoLogin": "confirmar",
            "formulario:host": "10.2.2.8:8080",
            "javax.faces.ViewState": viewstate
        }

        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "User-Agent": "Mozilla/5.0"
        }

        resp_post = session_http.post(
            LOGIN_URL,
            data=payload,
            headers=headers,
            timeout=5,
            allow_redirects=True
        )

        # =========================
        # 3️⃣ Teste REAL de autenticação
        # =========================
        resp_check = session_http.get(
            PAGINA_PRINCIPAL,
            timeout=5,
            allow_redirects=True
        )

        # Se foi redirecionado para login → falhou
        if "login.jsf" in resp_check.url.lower():
            return False

        # Acesso permitido → login válido
        return True

    except Exception as e:
        logging.error(f"Erro no login HTTP: {e}")
        return False









# Função para buscar informações dos leitos de todos os setores (Usar depois para os cronogramas)
def get_cronograma_info(username, password):
    driver = get_driver()
    try:
        if "paginaPrincipal.jsf" not in driver.get_current_url():
            if not login_if_needed(username, password):
                return None

        aba_mapa = driver.find_element(By.XPATH, "/html/body/div[2]/form/div[3]/div/ul/li[3]")
        ActionChains(driver).move_to_element(aba_mapa).perform()

        aba_cirurgico = driver.find_element(By.XPATH, "/html/body/div[2]/form/div[3]/div/ul/li[3]/ul/li[9]/a")
        ActionChains(driver).move_to_element(aba_cirurgico).perform()
        aba_cirurgico.click()

        select = driver.find_element(By.ID, "formMedicos:selClinica")
        select.click()

        dados_html = []



        for i in range(2, 50):
            try:
                option_xpath = f'//*[@id="formMedicos:selClinica"]/option[{i}]'
                option = driver.find_element(By.XPATH, option_xpath)
                option.click()
                time.sleep(0.5)

                total_linhas = len(driver.find_elements(By.XPATH, '//*[@id="formMedicos:oTableNovo"]/tbody/tr'))

                for idx in range(total_linhas):
                    try:
                        linhas = driver.find_elements(By.XPATH, '//*[@id="formMedicos:oTableNovo"]/tbody/tr')

                        valor_coluna_xpath = f'//*[@id="formMedicos:oTableNovo:{idx}:j_id317"]'
                        valor_coluna = driver.find_element(By.XPATH, valor_coluna_xpath).text
                        valor_coluna = int(valor_coluna)

                        if valor_coluna >= 10:
                            prontuario = driver.find_element(By.XPATH, f'//*[@id="formMedicos:oTableNovo:{idx}:j_id308"]').text
                            paciente = driver.find_element(By.XPATH, f'//*[@id="formMedicos:oTableNovo:{idx}:j_id311"]').text
                            setor = driver.find_element(By.XPATH, f'//*[@id="formMedicos:oTableNovo:{idx}:j_id319"]').text
                            dias_no_leito = driver.find_element(By.XPATH, f'//*[@id="formMedicos:oTableNovo:{idx}:j_id322"]').text
                            dias_no_hospital = driver.find_element(By.XPATH, f'//*[@id="formMedicos:oTableNovo:{idx}:j_id325"]').text

                            # Tenta clicar no botão de prontuário (linkProntuario ou j_id330)
                            clicou = False
                            try:
                                xpath_link_prontuario = f'//*[@id="formMedicos:oTableNovo:{idx}:linkProntuario"]/img'
                                driver.find_element(By.XPATH, xpath_link_prontuario).click()
                                clicou = True
                            except NoSuchElementException:
                                try:
                                    xpath_jid330 = f'//*[@id="formMedicos:oTableNovo:{idx}:j_id330"]/img'
                                    driver.find_element(By.XPATH, xpath_jid330).click()
                                    time.sleep(1)
                                    try:
                                        # Aguarda até o botão "Prontuário da Mãe" estar clicável (visível e habilitado)
                                        btn_pront_mae = WebDriverWait(driver, 10).until(
                                            EC.element_to_be_clickable((By.XPATH, '//*[@id="formObstetricia:btnProntMae"]'))
                                        )
                                        btn_pront_mae.click()
                                        clicou = True
                                    except NoSuchElementException:
                                        print("Botão 'Prontuário da Mãe' não encontrado.")
                                except NoSuchElementException:
                                    print(f"Nenhum botão de prontuário encontrado para a linha {idx + 1}.")

                            time.sleep(1)

                            texto_diagnostico = "N/A"
                            if clicou:
                                try:
                                    elemento_diagnostico = driver.find_element(By.XPATH, '//*[@id="previAlta"]/strong[2]/span')
                                    texto_diagnostico = elemento_diagnostico.text.strip() or "N/A"
                                except:
                                    pass

                                try:
                                    driver.find_element(By.XPATH, '//*[@id="formCabecalho:btnPaginaPrincipal"]/img').click()
                                    time.sleep(1)
                                except Exception as e:
                                    print(f"Erro ao voltar para a página principal: {e}")
                                    continue

                            if "." in setor:
                                parte1, parte2 = setor.split(".", 1)
                                setor = parte1.strip()
                                numero_leito = parte2.strip()
                            else:
                                numero_leito = ""

                            if "-" in setor:
                                setor = setor.split("-", 1)[0].strip()

                            setor_normalizada = unidecode(setor).lower()
                            dias_adicionais = 30 if any(word in setor_normalizada for word in ["clinica", "uce"]) else 15

                            try:
                                dias_no_leito = int(dias_no_leito)
                                data_atual = datetime.now()
                                inicio_no_leito = data_atual - timedelta(days=dias_no_leito)
                                inicio_no_leito_str = inicio_no_leito.strftime("%d/%m/%Y")
                            except Exception as e:
                                print(f"Erro ao calcular a data de início no leito: {e}")
                                inicio_no_leito_str = "N/A"

                            prazo_maximo_limpeza = inicio_no_leito + timedelta(days=dias_adicionais)
                            prazo_maximo_limpeza_str = prazo_maximo_limpeza.strftime("%d/%m/%Y")

                            dados_html.append({
                                "prontuario": prontuario,
                                "paciente": paciente,
                                "setor": setor,
                                "dias_no_leito": dias_no_leito,
                                "dias_no_hospital": dias_no_hospital,
                                "numero_leito": numero_leito,
                                "inicio_no_leito": inicio_no_leito_str,
                                "prazo_maximo_limpeza": prazo_maximo_limpeza_str,
                                "diagnostico": texto_diagnostico
                            })

                    except Exception as e:
                        print(f"Erro ao processar a linha {idx + 1}: {e}")
            except Exception as e:
                print(f"Erro ao processar a opção {i}: {e}")

        return dados_html


    except Exception as e:
        logging.error(f"Erro ao buscar informações: {str(e)}")
        return None





def login_e_buscar_leitos(setores_desejados: List[str]) -> List[Dict]:
     
    # Configurações
    #BASE_URL = "https://sistemasnti.isgh.org.br"
    BASE_URL = "http://10.2.2.8:8080"
    LOGIN_URL = f"{BASE_URL}/pacientehrn/login.jsf"
    PEP_URL = f"{BASE_URL}/pacientehrn/cs_pep_sem_status.jsf"
    
    # Credenciais (fixas do seu sistema)
    USERNAME = "MAPACCG"
    PASSWORD = "@isgh#nti2"
    
    print(f"🏥 BUSCA VIA HTTP OTIMIZADA - {len(setores_desejados)} setores")
    print("=" * 60)
    
    inicio_total = time.time()
    
    # Criar sessão HTTP
    session = requests.Session()
    session.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Accept": "*/*",
        "Accept-Language": "pt-BR,pt;q=0.9,en;q=0.8",
    })
    
    try:
        # ============================================================
        # 1. LOGIN VIA HTTP (Rápido - ~2 segundos)
        # ============================================================
        print("🔸 Etapa 1/3: Login...")
        
        # 1.1 Obter página de login
        resp_login = session.get(LOGIN_URL, timeout=15)
        resp_login.raise_for_status()
        soup_login = BeautifulSoup(resp_login.text, 'html.parser')
        
        # 1.2 Extrair ViewState
        viewstate_input = soup_login.find("input", {"name": "javax.faces.ViewState"})
        if not viewstate_input:
            logging.error("❌ ViewState não encontrado")
            return []
        
        viewstate = viewstate_input["value"]
        
        # 1.3 Fazer login
        payload_login = {
            "formulario": "formulario",
            "login": USERNAME,
            "xyb-ac": PASSWORD,
            "formulario:botaoLogin": "confirmar",
            "formulario:host": "10.2.2.8:8080",
            "javax.faces.ViewState": viewstate
        }
        
        headers_login = {
            "Content-Type": "application/x-www-form-urlencoded",
            "Origin": BASE_URL,
            "Referer": LOGIN_URL,
        }
        
        resp_pos_login = session.post(LOGIN_URL, data=payload_login, headers=headers_login, timeout=15)
        
        # Verificar se login foi bem-sucedido
        if "login.jsf" in resp_pos_login.url:
            logging.error("❌ Login falhou - redirecionado para login")
            return []
        
        print("✅ Login realizado")
        
        # ============================================================
        # 2. PREPARAR SESSÃO - OBTER VIEWSTATE ATUAL
        # ============================================================
        print("🔸 Etapa 2/3: Preparando sessão...")
        
        # 2.1 Acessar página PEP
        resp_pep = session.get(PEP_URL, timeout=15)
        resp_pep.raise_for_status()
        soup_pep = BeautifulSoup(resp_pep.text, 'html.parser')
        
        # 2.2 Verificar se ainda está logado
        if "login.jsf" in resp_pep.url:
            logging.error("❌ Sessão expirada após login")
            return []
        
        # 2.3 Extrair ViewState atual
        viewstate_atual_input = soup_pep.find("input", {"name": "javax.faces.ViewState"})
        if not viewstate_atual_input:
            logging.error("❌ ViewState não encontrado na PEP")
            return []
        
        viewstate_atual = viewstate_atual_input["value"]
        
        # 2.4 Mapear setores disponíveis
        select_clinica = soup_pep.find("select", {"id": "formMedicos:selClinica"})
        if not select_clinica:
            logging.error("❌ Select de clínicas não encontrado")
            return []
        
        options = select_clinica.find_all("option")
        mapa_setores = {}
        
        for option in options:
            nome = option.text.strip()
            valor = option.get("value")
            if nome and valor and valor != "0":  # Ignorar "Selecione a Clínica"
                mapa_setores[nome] = valor
        
        print(f"✅ {len(mapa_setores)} setores disponíveis no sistema")
        
        # Filtrar setores que existem
        setores_validos = []
        setores_nao_encontrados = []
        for setor in setores_desejados:
            if setor in mapa_setores:
                setores_validos.append(setor)
            else:
                setores_nao_encontrados.append(setor)
                print(f"⚠️ Setor não disponível: '{setor}'")
        
        if not setores_validos:
            print("❌ Nenhum setor válido para buscar")
            return []
        
        # ============================================================
        # 3. BUSCAR DADOS DOS SETORES (OTIMIZADO)
        # ============================================================
        print(f"🔸 Etapa 3/3: Buscando {len(setores_validos)} setores...")
        
        dados_totais = []
        pacientes_vistos = set()  # Para evitar duplicatas
        setores_com_dados = []
        
        for setor_nome in setores_validos:
            valor_setor = mapa_setores[setor_nome]
            
            print(f"\n🔹 {setor_nome}...")
            inicio_setor = time.time()
            
            try:
                # 3.1 Preparar requisição AJAX
                headers_ajax = {
                    "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
                    "Origin": BASE_URL,
                    "Referer": PEP_URL,
                    "X-Requested-With": "XMLHttpRequest",
                    "Faces-Request": "partial/ajax",
                }
                
                payload_ajax = {
                    "AJAXREQUEST": "_viewRoot",
                    "formMedicos": "formMedicos",
                    "formMedicos:selClinica": valor_setor,
                    "formMedicos:selEnfermaria": "0",
                    "formMedicos:iptProntuario": "",
                    "javax.faces.ViewState": viewstate_atual,
                    "formMedicos:j_id264": "formMedicos:j_id264",
                }
                
                # 3.2 Fazer requisição
                resp = session.post(PEP_URL, data=payload_ajax, headers=headers_ajax, timeout=15)

                if resp.status_code == 200:
                    # 🔥 ATUALIZAR VIEWSTATE SE O JSF GERAR UM NOVO
                    novo_viewstate = _extrair_viewstate(resp.text)
                    if novo_viewstate:
                        viewstate_atual = novo_viewstate

                    dados_setor = _processar_resposta_setor_otimizada(resp.text, setor_nome)
                    
                    if dados_setor:
                        # Filtrar duplicatas dentro do mesmo setor
                        dados_filtrados = []
                        vistos_no_setor = set()
                        
                        for item in dados_setor:
                            chave = f"{item['prontuario']}_{setor_nome}"
                            if chave not in vistos_no_setor:
                                vistos_no_setor.add(chave)
                                dados_filtrados.append(item)
                        
                        # Filtrar pacientes já vistos em outros setores
                        dados_novos = []
                        for item in dados_filtrados:
                            if item['prontuario'] not in pacientes_vistos:
                                pacientes_vistos.add(item['prontuario'])
                                dados_novos.append(item)
                            else:
                                logging.debug(f"Paciente duplicado ignorado: {item['paciente']}")
                        
                        if dados_novos:
                            dados_totais.extend(dados_novos)
                            setores_com_dados.append(setor_nome)
                            fim_setor = time.time()
                            tempo_setor = fim_setor - inicio_setor
                            
                            # Mostrar amostra rápida
                            if len(dados_novos) <= 3:
                                for item in dados_novos[:2]:
                                    print(f"   • {item['paciente'][:25]:25} | Leito: {item['numero_leito']}")
                            else:
                                primeiro = dados_novos[0]
                                print(f"   • {primeiro['paciente'][:20]}... | Leito: {primeiro['numero_leito']}")
                            
                            print(f"✅ {len(dados_novos)} leito(s) em {tempo_setor:.1f}s")
                        else:
                            print(f"ℹ️ Todos os pacientes já foram capturados")
                    else:
                        print(f"ℹ️ Nenhum leito encontrado")
                else:
                    print(f"⚠️ HTTP {resp.status_code}")
                
                # Pequena pausa entre setores
                time.sleep(0.3)
                
            except requests.exceptions.Timeout:
                print(f"⏱️ Timeout ao buscar {setor_nome}")
                continue
            except Exception as e:
                print(f"❌ Erro: {str(e)[:50]}...")
                continue
        
        # ============================================================
        # 4. RESULTADO FINAL OTIMIZADO
        # ============================================================
        fim_total = time.time()
        tempo_total = fim_total - inicio_total
        
        print(f"\n" + "=" * 60)
        print("📊 RELATÓRIO FINAL")
        print("=" * 60)
        
        print(f"⏱️  Tempo total: {tempo_total:.2f} segundos")
        print(f"📊 Setores processados: {len(setores_validos)}")
        print(f"🛏️  Total de leitos: {len(dados_totais)}")
        print(f"🏥 Setores com dados: {len(setores_com_dados)}")
        
        if setores_nao_encontrados:
            print(f"⚠️  Setores não disponíveis: {', '.join(setores_nao_encontrados)}")
        
        if dados_totais:
            # Estatísticas por setor
            contagem = Counter([item['setor'] for item in dados_totais])
            
            print(f"\n📋 DISTRIBUIÇÃO POR SETOR:")
            for setor, count in sorted(contagem.items()):
                print(f"  • {setor}: {count} leito(s)")
            
            # Amostra dos resultados
            print(f"\n🎯 AMOSTRA DOS DADOS (5 primeiros):")
            for i, item in enumerate(dados_totais[:5], 1):
                paciente = item['paciente']
                if len(paciente) > 25:
                    paciente = paciente[:22] + "..."
                print(f"{i}. {paciente}")
                print(f"   Pront: {item['prontuario']:8} | Leito: {item['numero_leito']:3} | Setor: {item['setor']}")
        
        print("=" * 60)
        
        return dados_totais
        
    except requests.exceptions.RequestException as e:
        logging.error(f"❌ Erro de conexão: {str(e)}")
        return []
    except Exception as e:
        logging.error(f"❌ Erro geral: {str(e)}")
        return []


def _processar_resposta_setor_otimizada(resposta_texto: str, setor_nome: str) -> List[Dict]:
    """
    Processa resposta do servidor - VERSÃO OTIMIZADA
    """
    dados = []
    
    try:
        # Verificar se é resposta XML
        if '<update id="formMedicos:oTableNovo">' in resposta_texto:
            # Extrair HTML da resposta XML
            inicio = resposta_texto.find('<update id="formMedicos:oTableNovo">')
            fim = resposta_texto.find('</update>', inicio)
            
            if inicio != -1 and fim != -1:
                html_tabela = resposta_texto[inicio + len('<update id="formMedicos:oTableNovo">'):fim]
                html_tabela = html.unescape(html_tabela)
                soup = BeautifulSoup(html_tabela, 'html.parser')
            else:
                return []
        else:
            # É HTML normal - verificar se contém a tabela
            if '<table class="rich-table" id="formMedicos:oTableNovo"' not in resposta_texto:
                return []
            
            # Extrair tabela
            inicio = resposta_texto.find('<table class="rich-table" id="formMedicos:oTableNovo"')
            if inicio == -1:
                return []
            
            fim = resposta_texto.find('</table>', inicio)
            if fim == -1:
                fim = len(resposta_texto)
            
            html_tabela = resposta_texto[inicio:fim + 8]
            html_tabela = html.unescape(html_tabela)
            soup = BeautifulSoup(html_tabela, 'html.parser')
        
        # Buscar tabela
        tabela = soup.find("table", {"id": "formMedicos:oTableNovo"})
        if not tabela:
            return []
        
        # Encontrar linhas (detectar cabeçalho automaticamente)
        linhas = tabela.find_all("tr")
        
        # Verificar se a primeira linha é cabeçalho
        primeira_linha_texto = linhas[0].get_text().upper() if linhas else ""
        if "PRONTUÁRIO" in primeira_linha_texto or "PACIENTE" in primeira_linha_texto:
            linhas = linhas[1:]  # Pular cabeçalho
        
        # Processar cada linha
        for linha in linhas:
            try:
                celulas = linha.find_all("td")
                
                # Precisamos de pelo menos 3 células: Prontuário, Paciente, Clínica-Leito
                if len(celulas) < 3:
                    continue
                
                # Extrair dados básicos
                prontuario = celulas[0].get_text(strip=True)
                paciente = celulas[1].get_text(strip=True)
                
                # Coluna IMPORTANTE: Clínica - Enf.Leito (índice 2)
                texto_setor = celulas[2].get_text(strip=True)
                
                # Processar setor e leito COM PARSER OTIMIZADO
                setor, numero_leito = _parse_setor_leito_otimizado(texto_setor, setor_nome)
                
                # Validar dados mínimos
                if not prontuario or not paciente:
                    continue
                
                # Criar item
                item = {
                    "prontuario": prontuario,
                    "paciente": paciente,
                    "setor": setor,
                    "numero_leito": numero_leito,
                    "setor_original": setor_nome
                }
                
                # Adicionar campos extras se disponíveis
                campos_extras = [
                    ("dias_leito", 3),
                    ("dias_hospital", 4),
                    ("escala_braden", 5)
                ]
                
                for campo, indice in campos_extras:
                    if len(celulas) > indice:
                        item[campo] = celulas[indice].get_text(strip=True)
                
                dados.append(item)
                
            except Exception as e:
                logging.debug(f"Erro processando linha: {e}")
                continue
        
        return dados
        
    except Exception as e:
        logging.error(f"Erro processamento resposta: {e}")
        return []


def _parse_setor_leito_otimizado(texto_setor: str, setor_original: str) -> tuple:
    """
    Analisa o texto do campo setor/leito - VERSÃO OTIMIZADA
    
    Formato: "UTI ADULTO II - UTI ADULTO II-01"
    Retorna: ("UTI ADULTO II", "01")
    """
    
    if not texto_setor:
        return setor_original, ""
    
    texto = texto_setor.strip()
    
    # 1. Extrair número do leito
    numero_leito = ""
    
    # Padrões otimizados para número do leito
    padroes_leito = [
        r'[-\.](\d{1,2})$',           # "-01" ou ".01" no final
        r'[-\.](\d{1,2})\b',          # "-01" ou ".01" em qualquer lugar
        r'\b(\d{1,2})$',              # "01" no final
        r'leito[:\s]*(\d{1,2})\b',    # "leito: 01"
        r'[:\.]\s*(\d{1,2})\b',       # ": 01" ou ". 01"
    ]
    
    for padrao in padroes_leito:
        match = re.search(padrao, texto, re.IGNORECASE)
        if match:
            numero_leito = match.group(1).zfill(2)
            break
    
    # Se não encontrou com padrões específicos, pegar último número de 1-2 dígitos
    if not numero_leito:
        numeros = re.findall(r'\b(\d{1,2})\b', texto)
        if numeros:
            numero_leito = numeros[-1].zfill(2)
    
    # 2. Extrair setor
    setor = texto
    
    # Remover número do leito se encontrado
    if numero_leito:
        # Remover padrões como "-01", ".01", etc.
        numero_sem_zero = numero_leito.lstrip('0')
        padroes_remover = [
            r'[-\.]\s*' + numero_leito + r'\b',
            r'[-\.]\s*' + numero_sem_zero + r'\b',
            r'\s+' + numero_leito + r'$',
            r'\s+' + numero_sem_zero + r'$',
            r'leito[:\s]*' + numero_leito + r'\b',
            r'leito[:\s]*' + numero_sem_zero + r'\b',
        ]
        
        for padrao in padroes_remover:
            setor = re.sub(padrao, '', setor, flags=re.IGNORECASE)
    
    # Remover duplicatas "UTI ADULTO II - UTI ADULTO II"
    if " - " in setor:
        partes = [p.strip() for p in setor.split(" - ")]
        if len(partes) >= 2:
            # Se as partes forem similares, usar a primeira
            if partes[0] == partes[1] or partes[1].startswith(partes[0]):
                setor = partes[0]
            else:
                # Usar a primeira parte (normalmente é o setor)
                setor = partes[0]
    
    # Limpar espaços e caracteres especiais
    setor = setor.strip()
    setor = re.sub(r'\s+', ' ', setor)  # Remover múltiplos espaços
    setor = setor.rstrip(' -.:')
    
    # Se o setor ficou vazio, usar o setor original
    if not setor:
        setor = setor_original
    
    return setor, numero_leito


def _extrair_dados_xml_corrigida(xml_text: str, setor_nome: str) -> List[Dict]:
    """Extrai dados de resposta XML AJAX - Compatibilidade"""
    try:
        if '<update id="formMedicos:oTableNovo">' not in xml_text:
            return []
        
        inicio = xml_text.find('<update id="formMedicos:oTableNovo">') + len('<update id="formMedicos:oTableNovo">')
        fim = xml_text.find('</update>', inicio)
        
        if inicio <= 0 or fim <= inicio:
            return []
        
        html_tabela = xml_text[inicio:fim]
        html_tabela = html.unescape(html_tabela)
        
        soup = BeautifulSoup(html_tabela, 'html.parser')
        return _extrair_dados_da_tabela_soup_otimizada(soup, setor_nome)
        
    except Exception:
        return []


def _extrair_dados_da_tabela_soup_otimizada(soup, setor_nome: str) -> List[Dict]:
    """Extrai dados de um objeto BeautifulSoup da tabela - VERSÃO OTIMIZADA"""
    dados = []
    
    try:
        # Método 1: Buscar por IDs específicos
        for i in range(100):
            try:
                prontuario_elem = soup.find(id=f"formMedicos:oTableNovo:{i}:j_id308")
                paciente_elem = soup.find(id=f"formMedicos:oTableNovo:{i}:j_id311")
                setor_elem = soup.find(id=f"formMedicos:oTableNovo:{i}:j_id314")
                
                if not (prontuario_elem and paciente_elem and setor_elem):
                    break
                
                prontuario = prontuario_elem.get_text(strip=True)
                paciente = paciente_elem.get_text(strip=True)
                texto_setor = setor_elem.get_text(strip=True)
                
                setor, numero_leito = _parse_setor_leito_otimizado(texto_setor, setor_nome)
                
                if prontuario and paciente:
                    dados.append({
                        "prontuario": prontuario,
                        "paciente": paciente,
                        "setor": setor,
                        "numero_leito": numero_leito,
                        "setor_original": setor_nome
                    })
                    
            except Exception:
                continue
        
        # Se não encontrou pelos IDs, tentar método genérico
        if not dados:
            tabela = soup.find("table")
            if tabela:
                linhas = tabela.find_all("tr")
                for linha in linhas:
                    celulas = linha.find_all("td")
                    if len(celulas) >= 3:
                        prontuario = celulas[0].get_text(strip=True)
                        paciente = celulas[1].get_text(strip=True)
                        texto_setor = celulas[2].get_text(strip=True)
                        
                        setor, numero_leito = _parse_setor_leito_otimizado(texto_setor, setor_nome)
                        
                        if prontuario and paciente:
                            dados.append({
                                "prontuario": prontuario,
                                "paciente": paciente,
                                "setor": setor,
                                "numero_leito": numero_leito,
                                "setor_original": setor_nome
                            })
        
        return dados
        
    except Exception:
        return []


def _extrair_viewstate(texto: str) -> str:
    """
    Extrai o javax.faces.ViewState de uma resposta JSF
    """
    try:
        soup = BeautifulSoup(texto, 'html.parser')
        vs = soup.find("input", {"name": "javax.faces.ViewState"})
        if vs and vs.get("value"):
            return vs["value"]
    except Exception:
        pass
    return ""


# Funções de compatibilidade (mantém comportamento original)
def _processar_resposta_setor(resposta_texto: str, setor_nome: str) -> List[Dict]:
    """Alias para manter compatibilidade - usa versão otimizada"""
    return _processar_resposta_setor_otimizada(resposta_texto, setor_nome)

def _parse_setor_leito(texto_setor: str, setor_original: str) -> tuple:
    """Alias para manter compatibilidade - usa versão otimizada"""
    return _parse_setor_leito_otimizado(texto_setor, setor_original)

def _extrair_dados_da_tabela_soup_corrigida(soup, setor_nome: str) -> List[Dict]:
    """Alias para manter compatibilidade"""
    return _extrair_dados_da_tabela_soup_otimizada(soup, setor_nome)


    
def converter_data(data_str):
    """Converte uma data no formato DD/MM/YYYY para YYYY-MM-DD."""
    try:
        return datetime.strptime(data_str, "%d/%m/%Y").strftime("%Y-%m-%d")
    except ValueError:
        return None  # Retorna None se a data estiver inválida

def salvar_dados_no_banco(dados):
    conexao = get_db_connection()
    cursor = conexao.cursor()

    try:
        # Passo 1: Inserir um novo registro no histórico
        sql_historico = "INSERT INTO historico_cronogramas (data_criacao) VALUES (NOW())"
        cursor.execute(sql_historico)
        
        # Obtém o ID gerado automaticamente
        id_historico = cursor.lastrowid  

        # Passo 2: Inserir os dados no cronograma vinculados ao histórico
        sql_cronograma = """
        INSERT INTO cronograma (historico_id, paciente, prontuario, setor, dias_no_leito, dias_no_hospital, numero_leito, inicio_no_leito, prazo_maximo_limpeza,diagnostico)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """

        for dado in dados:
            inicio_no_leito = converter_data(dado["inicio_no_leito"])
            prazo_maximo_limpeza = converter_data(dado["prazo_maximo_limpeza"])

            cursor.execute(sql_cronograma, (
                id_historico,  # Relaciona com o ID do histórico
                dado["paciente"],
                dado["prontuario"],
                dado["setor"],
                dado["dias_no_leito"],
                dado["dias_no_hospital"],
                dado["numero_leito"],
                inicio_no_leito,
                prazo_maximo_limpeza,
                dado["diagnostico"]
            ))

        conexao.commit()
    
    except Exception as e:
        conexao.rollback()  # Evita inconsistências no banco
        print(f"Erro ao salvar dados: {e}")
    
    finally:
        cursor.close()
        conexao.close()






@app.route('/consultar_cronogramas')
def consultar_cronogramas():
    conexao = get_db_connection()
    cursor = conexao.cursor(pymysql.cursors.DictCursor)

    try:
        # Manter ordenação por data DESC (mais recente primeiro)
        cursor.execute("SELECT id, data_criacao FROM historico_cronogramas ORDER BY data_criacao DESC")
        historico = cursor.fetchall()

        # Numeração INVERTIDA (mais antigo = maior número)
        total = len(historico)
        for i, item in enumerate(historico):
            item['numero_sequencial'] = total - i  # Inverte a numeração
            if isinstance(item['data_criacao'], date):
                item['data_criacao'] = item['data_criacao'].strftime('%d/%m/%Y')
            
    except pymysql.MySQLError as e:
        print(f"Erro ao buscar histórico: {e}")
        historico = []
    finally:
        cursor.close()
        conexao.close()

    return render_template("paginaConsulta.html", historico=historico)


@app.route('/cronograma/<int:historico_id>')
def detalhes_cronograma(historico_id):
    conexao = get_db_connection()
    cursor = conexao.cursor(pymysql.cursors.DictCursor)  # 🔹 Retorna resultados como dicionários

    try:
        # Busca os dados da tabela cronograma filtrados pelo historico_id
        cursor.execute("""
            SELECT id, prontuario, paciente, setor, dias_no_leito, dias_no_hospital, numero_leito, inicio_no_leito, prazo_maximo_limpeza, diagnostico
            FROM cronograma
            WHERE historico_id = %s
        """, (historico_id,))
        cronograma = cursor.fetchall()

        # Busca a data de criação do histórico
        cursor.execute("""
            SELECT data_criacao
            FROM historico_cronogramas
            WHERE id = %s
        """, (historico_id,))
        data_criacao = cursor.fetchone()['data_criacao']

        for item in cronograma:
            if isinstance(item['inicio_no_leito'], date):
                item['inicio_no_leito'] = item['inicio_no_leito'].strftime('%d/%m/%Y')
            if isinstance(item['prazo_maximo_limpeza'], date):
                item['prazo_maximo_limpeza'] = item['prazo_maximo_limpeza'].strftime('%d/%m/%Y')

    except pymysql.MySQLError as e:
        print(f"Erro ao buscar cronograma: {e}")
        cronograma = []
        data_criacao = None

    finally:
        cursor.close()
        conexao.close()

    return render_template("cronograma.html", cronograma=cronograma, historico_id=historico_id, data_criacao=data_criacao)



# 👉 Rota para exibir a página de cadastro
@app.route('/gerenciar_funcionarios')
def gerenciar_funcionarios():
    return render_template('paginaFuncionarios.html')



@app.route('/cadastrar_funcionarios', methods=['POST'])
def cadastrar_funcionarios():
    dados = request.json
    nome = dados.get("nome")
    cpf = dados.get("cpf")
    id_cartao = dados.get("id_cartao", "").strip()
    tipo = dados.get("tipo")

    if not (nome and cpf and id_cartao and tipo):
        return jsonify({"erro": "⚠️ Preencha todos os campos obrigatórios."}), 400

    # Validação: 9 a 10 dígitos, apenas números
    if not (9 <= len(id_cartao) <= 10) or not id_cartao.isdigit():
        return jsonify({"erro": "⚠️ O ID do cartão deve conter entre 8 e 10 números."}), 400

    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute("""
                INSERT INTO funcionarios (nome, cpf, id_cartao, tipo, situacao)
                VALUES (%s, %s, %s, %s, %s)
            """, (nome, cpf, id_cartao, tipo, 1))
            conn.commit()
        conn.close()

        return jsonify({"mensagem": "Funcionário cadastrado com sucesso!"})

    except Exception as e:
        erro = str(e)

        if "Duplicate entry" in erro and "cpf" in erro:
            return jsonify({"erro": "⚠️ Este CPF já está cadastrado."}), 400

        if "Duplicate entry" in erro and "id_cartao" in erro:
            return jsonify({"erro": "⚠️ Este ID de cartão já está em uso."}), 400

        return jsonify({"erro": "❌ Erro interno ao cadastrar funcionário."}), 500




@app.route('/consultar_funcionarios', methods=['POST'])
def consultar_funcionarios():
    dados = request.get_json(silent=True) or {}

    # 🔹 Captura segura dos filtros
    nome = dados.get("nome", "").strip()
    id_cartao = dados.get("id_cartao", "").strip()
    tipo = dados.get("tipo", "").strip()

    # 🔹 Conexão com o banco
    conn = get_db_connection()
    funcionarios = []

    try:
        with conn.cursor(pymysql.cursors.DictCursor) as cursor:
            query = """
                SELECT 
                    id,
                    nome,
                    cpf,
                    id_cartao,
                    tipo,
                    situacao
                FROM funcionarios
                WHERE 1=1
            """
            params = []

            # 🔹 Aplica filtros dinamicamente
            if nome:
                query += " AND nome LIKE %s"
                params.append(f"%{nome}%")

            if id_cartao:
                query += " AND id_cartao = %s"
                params.append(id_cartao)

            if tipo:
                query += " AND tipo = %s"
                params.append(tipo)

            cursor.execute(query, params)
            funcionarios = cursor.fetchall()

            print("FILTROS RECEBIDOS:", dados)
            print("ID CARTAO FILTRADO:", id_cartao)

            # 🔹 Normaliza os tipos (evita problemas no JS)
            for u in funcionarios:
                u["situacao"] = int(u["situacao"]) if u["situacao"] is not None else 0
                u["id_cartao"] = str(u["id_cartao"]) if u["id_cartao"] is not None else ""
                u["cpf"] = u["cpf"] or ""
                u["tipo"] = u["tipo"] or ""

    except Exception as e:
        print("❌ ERRO AO CONSULTAR FUNCIONÁRIOS:", e)
        return jsonify({"erro": str(e)}), 500

    finally:
        conn.close()

    # 🔹 Retorna JSON bem formatado
    return jsonify({"funcionarios": funcionarios})
    






@app.route('/editar_funcionarios', methods=['POST'])
def editar_funcionarios():
    dados = request.json
    id = dados.get("id")
    nome = dados.get("nome")
    cpf = dados.get("cpf")
    id_cartao = dados.get("id_cartao")
    tipo = dados.get("tipo")
    situacao = dados.get("situacao")
    
    if not (nome and cpf and id_cartao and tipo):
        return jsonify({"erro": "⚠️ Preencha todos os campos obrigatórios."}), 400

    if not id:
        return jsonify({"erro": "ID do funcionário não informado"}), 400

    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute("""
                UPDATE funcionarios
                SET nome=%s, cpf=%s, id_cartao=%s ,tipo=%s, situacao=%s
                WHERE id=%s
            """, (nome, cpf, id_cartao, tipo, situacao, id))
            conn.commit()
        conn.close()
        return jsonify({"mensagem": "Funcionário atualizado com sucesso!"})
    except Exception as e:
            erro = str(e)

            if "Duplicate entry" in erro and "cpf" in erro:
                return jsonify({"erro": "⚠️ Este CPF já está cadastrado."}), 400

            if "Duplicate entry" in erro and "id_cartao" in erro:
                return jsonify({"erro": "⚠️ Este ID de cartão já está em uso."}), 400

            return jsonify({"erro": "❌ Erro interno ao cadastrar funcionário."}), 500



@app.route("/tablet")
def tablet_inicio():
    return render_template("tabletInicio.html")


@app.route("/carregar_leitos")
def carregar_leitos():
    try:
        ip = get_client_ip()

        # 🔹 Abre o JSON gerado pela thread
        with open(LEITOS_CACHE_FILE, "r", encoding="utf-8") as f:
            cache = json.load(f)

        if ip not in cache:
            return jsonify({
                "status": "erro",
                "mensagem": f"Nenhum dado disponível para o IP {ip}"
            }), 404

        dados_ip = cache[ip]["leitos"]

        # 🔹 Extrai setores únicos
        setores = sorted({item["setor"] for item in dados_ip})

        return jsonify({
            "status": "ok",
            "setores": setores,
            "ultima_atualizacao": cache[ip]["ultima_atualizacao"]
        })

    except FileNotFoundError:
        return jsonify({
            "status": "erro",
            "mensagem": "Cache ainda não foi gerado"
        }), 503

    except Exception as e:
        logging.error(f"Erro em /carregar_leitos: {e}")
        return jsonify({
            "status": "erro",
            "mensagem": str(e)
        }), 500





@app.route("/tablet_leitos")
def tablet_leitos():
    return render_template("tabletLeitos.html")



@app.route("/tablet_setores")
def tablet_setores():
    return render_template("tabletSetores.html")

@app.route("/get_leitos_por_setor")
def get_leitos_por_setor():
    setor = request.args.get("setor")
    ip_cliente = get_client_ip()

    logging.info(f"➡️ IP do cliente: {ip_cliente}")
    logging.info(f"➡️ Setor solicitado: {setor}")

    if not setor:
        return jsonify({
            "status": "erro",
            "mensagem": "Setor não informado"
        }), 400

    # ===============================
    # 🔹 BUSCA QTD_LEITOS NO BANCO
    # ===============================
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT qtd_leitos
                FROM dispositivos
                WHERE ip = %s
                  AND setor = %s
                  AND situacao = 1
                LIMIT 1
            """, (ip_cliente, setor))

            row = cursor.fetchone()

        conn.close()

        if not row or row["qtd_leitos"] is None:
            return jsonify({
                "status": "erro",
                "mensagem": "Quantidade de leitos não configurada para este setor"
            }), 404

        total_fixos = int(row["qtd_leitos"])

    except Exception:
        logging.exception("Erro ao buscar qtd_leitos em dispositivos")
        return jsonify({
            "status": "erro",
            "mensagem": "Erro ao consultar configuração de leitos"
        }), 500

    # ===============================
    # 🔹 CARREGA CACHE DE LEITOS
    # ===============================
    caminho_json = LEITOS_CACHE_FILE

    if not os.path.exists(caminho_json):
        logging.error(f"❌ JSON não encontrado: {caminho_json}")
        return jsonify({
            "status": "erro",
            "mensagem": "Dados não disponíveis"
        }), 404

    try:
        with open(caminho_json, "r", encoding="utf-8") as f:
            dados = json.load(f)
    except json.JSONDecodeError as e:
        logging.error(f"JSON inválido: {e}")
        return jsonify({
            "status": "erro",
            "mensagem": "Formato de dados inválido"
        }), 500
    except Exception:
        logging.exception("Erro ao ler JSON de cache")
        return jsonify({
            "status": "erro",
            "mensagem": "Erro ao ler dados"
        }), 500

    dados_ip = dados.get(ip_cliente)

    if not dados_ip:
        return jsonify({
            "status": "erro",
            "mensagem": "Nenhum dado encontrado para este dispositivo"
        }), 404

    leitos_setor = [
        l for l in dados_ip.get("leitos", [])
        if l.get("setor") == setor
    ]

    logging.info(f"📦 Registros no setor '{setor}': {len(leitos_setor)}")

    # ===============================
    # 🔹 PROCESSAMENTO DOS LEITOS
    # ===============================
    leitos_fixos_ocupados = set()
    mapa_pacientes_fixos = {}
    leitos_extras = []

    for l in leitos_setor:
        numero_leito = (l.get("numero_leito") or "").strip()
        paciente = l.get("paciente")

        if numero_leito.isdigit():
            leito_int = int(numero_leito)
            leitos_fixos_ocupados.add(leito_int)
            mapa_pacientes_fixos[leito_int] = paciente
        else:
            leitos_extras.append({
                "numero_leito": numero_leito,
                "paciente": paciente
            })

    # ===============================
    # 🔹 MONTA RESPOSTA
    # ===============================
    resultado = []

    for leito in range(1, total_fixos + 1):
        ocupado = leito in leitos_fixos_ocupados

        resultado.append({
            "numero_leito": str(leito),
            "setor": setor,
            "tipo": "fixo",
            "status": "ocupado" if ocupado else "livre",
            "icone": "amarelo" if ocupado else "verde",
            "paciente": mapa_pacientes_fixos.get(leito)
        })

    for extra in leitos_extras:
        resultado.append({
            "numero_leito": extra["numero_leito"],
            "setor": setor,
            "tipo": "extra",
            "status": "ocupado",
            "icone": "amarelo",
            "paciente": extra["paciente"]
        })

    return jsonify({
        "status": "ok",
        "leitos": resultado
    })






@app.route("/tablet_limpeza")
def tablet_limpeza():
    return render_template("tabletLimpeza.html")


@app.route('/verificar_funcionarios', methods=['POST'])
def verificar_funcionarios():
    dados = request.json
    id_cartao = dados.get("id_cartao")
    tipo = dados.get("tipo")

    if not id_cartao or not tipo:
        return jsonify({"erro": "id_cartao ou tipo não informados"}), 400

    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT nome FROM funcionarios
                WHERE id_cartao = %s AND tipo = %s AND situacao = 1
            """, (id_cartao, tipo))
            funcionarios = cursor.fetchone()

        conn.close()

        if funcionarios:
            return jsonify({"sucesso": True, "nome": funcionarios['nome']})
        else:
            return jsonify({"sucesso": False, "erro": "Funcionário não encontrado ou inativo"})
    except Exception as e:
        return jsonify({"erro": str(e)}), 500



@app.route("/limpeza/aguardando_validacao", methods=["POST"])
def limpeza_aguardando_validacao():
    data = request.json
    id_limpeza = data.get("id_limpeza")

    if not id_limpeza:
        return jsonify({"erro": "ID da limpeza obrigatório"}), 400

    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                UPDATE registro_limpeza
                SET status = 'AGUARDANDO_VALIDACAO'
                WHERE id = %s
                  AND status = 'EM_ANDAMENTO'
            """, (id_limpeza,))

            if cursor.rowcount == 0:
                return jsonify({"erro": "Limpeza não encontrada ou status inválido"}), 404

            conn.commit()

            # ←←← ADICIONE AQUI A NOTIFICAÇÃO
            atualizacao_evento.set()

            return jsonify({"sucesso": True, "mensagem": "Status atualizado para AGUARDANDO_VALIDACAO"})

    except Exception as e:
        conn.rollback()
        print("Erro ao atualizar para AGUARDANDO_VALIDACAO:", e)
        return jsonify({"erro": str(e)}), 500
    finally:
        conn.close()


@app.route('/registrar_limpeza', methods=['POST'])
def registrar_limpeza():
    dados = request.json
    print("📩 Dados recebidos:", dados)

    ip_dispositivo = get_client_ip()
    print("📡 IP do dispositivo:", ip_dispositivo)

    id_limpeza = dados.get("id_limpeza")

    # Início
    id_cartao_asg = dados.get("id_cartao_asg")
    funcionario_asg = dados.get("funcionario_asg")

    # Finalização
    id_cartao_enf = dados.get("id_cartao_enf")
    funcionario_enf = dados.get("funcionario_enf")

    leito = dados.get("leito", {})
    numero_leito = leito.get("numero_leito")
    setor = leito.get("setor")
    paciente = leito.get("paciente")

    tipo_limpeza = dados.get("tipo_limpeza")
    tempo_total_seconds = dados.get("tempo_total_seconds")
    tempo_total_text = dados.get("tempo_total_text")

    conn = get_db_connection()

    try:
        with conn.cursor() as cursor:

            # =============================
            # 🔹 INÍCIO DA LIMPEZA
            # =============================
            if not id_cartao_enf:

                if not numero_leito or not tipo_limpeza:
                    return jsonify({
                        "erro": "Número do leito e tipo de limpeza são obrigatórios"
                    }), 400

                cursor.execute("""
                    SELECT COUNT(*) AS total
                    FROM registro_limpeza
                    WHERE ip_dispositivo = %s
                      AND status = 'EM_ANDAMENTO'
                """, (ip_dispositivo,))

                total = cursor.fetchone()["total"]

                if total >= 2:
                    return jsonify({
                        "erro": "LIMITE_ATINGIDO",
                        "mensagem": "Este tablet já possui 2 limpezas em andamento."
                    }), 400

                cursor.execute("""
                    INSERT INTO registro_limpeza (
                        id_cartao_asg,
                        funcionario_asg,
                        ip_dispositivo,
                        numero_leito,
                        paciente,
                        setor,
                        tipo_limpeza,
                        status
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, 'EM_ANDAMENTO')
                """, (
                    id_cartao_asg,
                    funcionario_asg,
                    ip_dispositivo,
                    numero_leito,
                    paciente,
                    setor,
                    tipo_limpeza
                ))

                id_gerado = cursor.lastrowid
                conn.commit()

                # 🔔 Notifica o painel imediatamente
                atualizacao_evento.set()

                return jsonify({
                    "mensagem": "Limpeza iniciada com sucesso!",
                    "id_limpeza": id_gerado
                })

            # =============================
            # 🔹 FINALIZAÇÃO DA LIMPEZA
            # =============================
            else:
                if not id_limpeza:
                    return jsonify({
                        "erro": "ID da limpeza é obrigatório para finalizar"
                    }), 400

                data_fim = datetime.now()

                # 🔎 Busca o tipo direto do banco (fonte oficial)
                cursor.execute("""
                    SELECT tipo_limpeza
                    FROM registro_limpeza
                    WHERE id = %s
                """, (id_limpeza,))
                row = cursor.fetchone()

                if not row:
                    return jsonify({"erro": "Limpeza não encontrada"}), 404

                # 🔐 Normalização segura
                tipo_limpeza_db = row["tipo_limpeza"] or ""
                tipo_norm = tipo_limpeza_db.strip().upper()

                print("🧪 tipo_limpeza banco:", repr(tipo_limpeza_db))
                print("🧪 tipo_limpeza normalizado:", repr(tipo_norm))

                # ⏳ Define vencimento APENAS baseado no banco
                vencimento = None

                if tipo_norm == "ALTA / ÓBITO / TRANSFERÊNCIA":
                    vencimento = data_fim + timedelta(seconds=30)

                elif tipo_norm in ("LONGA PERMANÊNCIA", "LONGA PERMANENCIA"):
                    vencimento = data_fim + timedelta(days=7)

                cursor.execute("""
                    UPDATE registro_limpeza
                    SET id_cartao_enf = %s,
                        funcionario_enf = %s,
                        data_fim = %s,
                        tempo_total_seconds = %s,
                        tempo_total_text = %s,
                        status = 'CONCLUIDA',
                        vencimento = %s
                    WHERE id = %s
                    AND status IN ('EM_ANDAMENTO', 'AGUARDANDO_VALIDACAO')
                """, (
                    id_cartao_enf,
                    funcionario_enf,
                    data_fim,
                    tempo_total_seconds,
                    tempo_total_text,
                    vencimento,
                    id_limpeza
                ))

                if cursor.rowcount == 0:
                    return jsonify({
                        "erro": "Nenhuma limpeza em andamento encontrada com esse ID"
                    }), 404

                conn.commit()

                # 🔔 Notifica SSE imediatamente
                atualizacao_evento.set()

                return jsonify({"mensagem": "Limpeza finalizada com sucesso!"})


    except Exception as e:
        conn.rollback()
        print("❌ ERRO:", e)
        return jsonify({"erro": str(e)}), 500

    finally:
        conn.close()



@app.route("/verificar_limpeza_ativa", methods=["POST"])
def verificar_limpeza_ativa():
    data = request.get_json()
    leito = data.get("leito")
    ip = get_client_ip()

    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:

            # 1️⃣ Verifica limpeza ativa no MESMO leito
            cursor.execute("""
                SELECT 1
                FROM registro_limpeza
                WHERE setor = %s
                  AND numero_leito = %s
                 AND status IN ('EM_ANDAMENTO', 'AGUARDANDO_VALIDACAO')
                LIMIT 1
            """, (leito["setor"], leito["numero_leito"]))

            if cursor.fetchone():
                return jsonify({
                    "limpeza_ativa": True,
                    "motivo": "LEITO_OCUPADO",
                    "mensagem": "Este leito já possui uma limpeza em andamento."
                })

            # 2️⃣ Verifica limite de 2 limpezas no tablet
            cursor.execute("""
                SELECT COUNT(*) AS total
                FROM registro_limpeza
                WHERE ip_dispositivo = %s
                  AND status IN ('EM_ANDAMENTO', 'AGUARDANDO_VALIDACAO')
            """, (ip,))

            total = cursor.fetchone()["total"]

            if total >= 2:
                return jsonify({
                    "limpeza_ativa": True,
                    "motivo": "LIMITE_TABLET",
                    "mensagem": "Este dispositivo já possui 2 limpezas em andamento."
                })

            # ✅ Tudo liberado
            return jsonify({
                "limpeza_ativa": False,
                "mensagem": "Limpeza liberada para início."
            })

    finally:
        conn.close()


@app.route("/verificar_limpeza_funcionario", methods=["POST"])
def verificar_limpeza_funcionario():
    data = request.get_json()
    funcionario = data.get("funcionario_asg")

    if not funcionario:
        return jsonify({"erro": "Funcionário não informado"}), 400

    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT setor, numero_leito, data_inicio
                FROM registro_limpeza
                WHERE funcionario_asg = %s
                  AND status IN ('EM_ANDAMENTO', 'AGUARDANDO_VALIDACAO')
                LIMIT 1
            """, (funcionario,))

            limpeza = cursor.fetchone()

            if limpeza:
                return jsonify({
                    "existe": True,
                    "mensagem": "Este funcionário já possui uma limpeza em andamento.",
                    "limpeza": limpeza
                })

            return jsonify({"existe": False})

    finally:
        conn.close()



@app.route('/status_limpezas')
def status_limpezas():
    
    conn = get_db_connection()
    try:
        with conn.cursor(pymysql.cursors.DictCursor) as cursor:
            cursor.execute("""
                SELECT id, numero_leito, setor, funcionario_asg, funcionario_enf,
                       tipo_limpeza, data_inicio, data_fim, tempo_total_text, status
                FROM registro_limpeza
                ORDER BY data_inicio DESC
            """)
            registros = cursor.fetchall()
        return jsonify(registros)
    except Exception as e:
        print("❌ Erro ao buscar status:", e)
        return jsonify({"erro": str(e)}), 500
    finally:
        conn.close()



@app.route('/stream')
def stream():
    def event_stream():
        while True:
            atualizacao_evento.wait()
            atualizacao_evento.clear()  # 👈 LIMPA ANTES
            yield "data: atualizacao\n\n"
            print("🔔 SSE disparado")

    return Response(event_stream(), mimetype='text/event-stream')




@app.route('/listar_limpezas')
def listar_limpezas():
    
    setor = request.args.get("setor")
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            if setor:
                cursor.execute("""
                    SELECT rl.numero_leito, rl.setor, rl.paciente, rl.status, rl.tipo_limpeza,
                           rl.funcionario_asg, rl.funcionario_enf, rl.tempo_total_text
                    FROM registro_limpeza rl
                    INNER JOIN (
                        SELECT MAX(id) AS ultimo_id
                        FROM registro_limpeza
                        WHERE setor = %s
                        GROUP BY numero_leito
                    ) ult ON rl.id = ult.ultimo_id
                    ORDER BY rl.numero_leito ASC
                """, (setor,))
            else:
                cursor.execute("""
                    SELECT rl.numero_leito, rl.setor, rl.paciente, rl.status, rl.tipo_limpeza,
                           rl.funcionario_asg, rl.funcionario_enf, rl.tempo_total_text
                    FROM registro_limpeza rl
                    INNER JOIN (
                        SELECT MAX(id) AS ultimo_id
                        FROM registro_limpeza
                        GROUP BY numero_leito, setor
                    ) ult ON rl.id = ult.ultimo_id
                    ORDER BY rl.setor ASC, rl.numero_leito ASC
                """)
            
            dados = cursor.fetchall()
        return jsonify(dados)
    finally:
        conn.close()




@app.route("/listar_setores")
def listar_setores():
    
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT DISTINCT setor FROM registro_limpeza ORDER BY setor ASC")
            setores = [row["setor"] for row in cursor.fetchall() if row["setor"]]
        return jsonify(setores)
    except Exception as e:
        print("❌ Erro ao listar setores:", e)
        return jsonify([]), 500
    finally:
        conn.close()



def atualiza_pendentes():
    while True:
        try:
            conn = get_db_connection()
            with conn.cursor() as cursor:

                cursor.execute("""
                    SELECT id, numero_leito, setor, data_fim, vencimento
                    FROM registro_limpeza
                    WHERE status = 'CONCLUIDA'
                      AND vencimento IS NOT NULL
                      AND vencimento <= NOW()
                      AND email_enviado = 0;
                """)
                pendentes = cursor.fetchall()

                if not pendentes:
                    time.sleep(60)
                    continue

                cursor.execute("""
                    UPDATE registro_limpeza
                    SET status = 'PENDENTE'
                    WHERE status = 'CONCLUIDA'
                      AND vencimento IS NOT NULL
                      AND vencimento <= NOW();
                """)
                conn.commit()

                for p in pendentes:
                    emails = buscar_emails_por_setor(p["setor"])

                    enviado = enviar_email_pendente(
                        destinatarios=emails,
                        leito=p["numero_leito"],
                        setor=p["setor"],
                        ultima_limpeza=p["data_fim"],
                        vencimento=p["vencimento"]
                    )


                    if enviado:
                        cursor.execute(
                            "UPDATE registro_limpeza SET email_enviado = 1 WHERE id = %s",
                            (p["id"],)
                        )
                        conn.commit()

            atualizacao_evento.set()
            print(f"🔔 {len(pendentes)} leito(s) ficaram PENDENTE")

        except Exception as e:
            print("❌ Erro na atualização:", e)

        time.sleep(60)

  
def buscar_emails_por_setor(setor):
    conn = get_db_connection()
    with conn.cursor() as cursor:
        cursor.execute("""
            SELECT DISTINCT email
            FROM emails_notificacao
            WHERE situacao = 1
              AND (setor = %s OR setor = 'TODOS')
        """, (setor,))
        rows = cursor.fetchall()
    conn.close()

    return [r["email"] for r in rows]


@app.route("/relatorios")
def pagina_relatorios():
    return render_template("paginaRelatorios.html")


@app.route("/relatorios/leitos_registrados")
def leitos_registrados_por_setor():
    setor = request.args.get("setor")
    data_inicio = request.args.get("data_inicio")
    data_fim = request.args.get("data_fim")

    if not setor:
        return jsonify([])

    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:

            sql = """
                SELECT DISTINCT numero_leito
                FROM registro_limpeza
                WHERE setor = %s
                  AND numero_leito REGEXP '^[0-9]+$'
            """
            params = [setor]

            # 🔹 Aplica período se informado
            if data_inicio and data_fim:
                sql += " AND data_inicio BETWEEN %s AND %s"
                params.extend([data_inicio, data_fim])

            elif data_inicio:
                sql += " AND data_inicio >= %s"
                params.append(data_inicio)

            elif data_fim:
                sql += " AND data_inicio <= %s"
                params.append(data_fim)

            sql += " ORDER BY CAST(numero_leito AS UNSIGNED)"

            cursor.execute(sql, params)

            leitos = [row["numero_leito"] for row in cursor.fetchall()]

        return jsonify(leitos)

    except Exception as e:
        print("❌ Erro ao listar leitos com período:", e)
        return jsonify([]), 500

    finally:
        conn.close()





@app.route("/relatorios/previa")
def previa_relatorio():
    return render_template("previaRelatorio.html")




@app.route("/relatorios/dados")
def dados_relatorio():
    setor = request.args.get("setor")
    leito = request.args.get("leito")
    tipo_limpeza = request.args.get("tipo_limpeza")
    status = request.args.get("status")
    inicio = request.args.get("inicio")
    fim = request.args.get("fim")

    conn = get_db_connection()
    try:
        with conn.cursor(pymysql.cursors.DictCursor) as cursor:
            sql = """
                SELECT
                    setor,
                    numero_leito,
                    paciente,
                    tipo_limpeza,
                    data_inicio,
                    data_fim,
                    funcionario_asg,
                    funcionario_enf,
                    tempo_total_text,
                    status
                FROM registro_limpeza
                WHERE 1=1
            """
            params = []

            if setor and setor != "__TODOS__":
                sql += " AND setor = %s"
                params.append(setor)

            if leito and leito != "__TODOS__":
                sql += " AND numero_leito = %s"
                params.append(leito)

            if tipo_limpeza and tipo_limpeza != "__TODOS__":
                sql += " AND tipo_limpeza = %s"
                params.append(tipo_limpeza)

            if status and status != "__TODOS__":
                sql += " AND status = %s"
                params.append(status)

            if inicio and fim:
                inicio_dt = datetime.strptime(inicio, "%Y-%m-%d")
                fim_dt = datetime.strptime(fim, "%Y-%m-%d") + timedelta(days=1)
                sql += " AND data_inicio >= %s AND data_inicio < %s"
                params.extend([inicio_dt, fim_dt])

            sql += " ORDER BY data_inicio ASC"

            cursor.execute(sql, params)
            rows = cursor.fetchall()

        # Conversão explícita de datas para strings locais
        dados = []
        for row in rows:
            d = dict(row)
            if d.get("data_inicio"):
                d["data_inicio"] = d["data_inicio"].strftime("%Y-%m-%d %H:%M:%S")
            if d.get("data_fim"):
                d["data_fim"] = d["data_fim"].strftime("%Y-%m-%d %H:%M:%S")
            dados.append(d)

        return jsonify(dados)

    except Exception as e:
        print("❌ Erro ao carregar dados do relatório:", e)
        return jsonify({"erro": str(e)}), 500

    finally:
        conn.close()




@app.route("/relatorios/exportar")
def exportar_relatorio():

    setor = request.args.get("setor")
    leito = request.args.get("leito")
    tipo_limpeza = request.args.get("tipo_limpeza")
    status = request.args.get("status")
    inicio = request.args.get("inicio")
    fim = request.args.get("fim")
    formato = request.args.get("formato")

    conn = get_db_connection()

    try:
        with conn.cursor(pymysql.cursors.DictCursor) as cursor:

            # ✅ sql SEMPRE definido
            sql = """
                SELECT
                    setor,
                    numero_leito,
                    paciente,
                    tipo_limpeza,
                    data_inicio,
                    data_fim,
                    funcionario_asg,
                    funcionario_enf,
                    tempo_total_text,
                    status
                FROM registro_limpeza
                WHERE 1=1
            """

            params = []

            # filtros só CONCATENAM
            if setor and setor != "__TODOS__":
                sql += " AND setor = %s"
                params.append(setor)

            if leito:
                sql += " AND numero_leito = %s"
                params.append(leito)

            if tipo_limpeza:
                sql += " AND tipo_limpeza = %s"
                params.append(tipo_limpeza)

            if status:
                sql += " AND status = %s"
                params.append(status)

            if inicio and fim:
                sql += """
                    AND data_inicio >= %s
                    AND data_inicio < DATE_ADD(%s, INTERVAL 1 DAY)
                """
                params.extend([inicio, fim])

            sql += " ORDER BY data_inicio ASC"

            # 👇 aqui sql COM CERTEZA existe
            cursor.execute(sql, params)
            dados = cursor.fetchall()

    finally:
        conn.close()

    # decisão do formato (fora do try)
    if not dados:
        return "Nenhum dado para exportar", 404

    if formato == "csv":
        return exportar_csv(dados)

    if formato == "xlsx":
        return exportar_xlsx(dados)

    if formato == "pdf":
        return exportar_pdf(dados)

    return "Formato inválido", 400





def get_client_ip():
    if request.headers.get("X-Forwarded-For"):
        return request.headers.get("X-Forwarded-For").split(",")[0].strip()
    return request.remote_addr


def setores_por_ip(ip):
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT setor
                FROM dispositivos
                WHERE ip = %s
                  AND situacao = TRUE
            """, (ip,))
            return [row["setor"] for row in cursor.fetchall()]
    finally:
        conn.close()

@app.route("/limpeza_ativa_por_ip")
def limpeza_ativa_por_ip():
    ip = get_client_ip()
    
    # Logs importantes no terminal do Flask
    print(f"[LOG] IP detectado pela função get_client_ip(): {ip}")
    print(f"[LOG] Headers X-Forwarded-For: {request.headers.get('X-Forwarded-For')}")
    print(f"[LOG] Remote addr: {request.remote_addr}")

    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT 
                    id,
                    setor,
                    numero_leito,
                    tipo_limpeza,
                    funcionario_asg,
                    data_inicio,
                    status,
                    TIMESTAMPDIFF(SECOND, data_inicio, NOW()) AS segundos_decorridos
                FROM registro_limpeza
                WHERE ip_dispositivo = %s
                  AND status IN ('EM_ANDAMENTO', 'AGUARDANDO_VALIDACAO')
                ORDER BY data_inicio ASC
                LIMIT 2
            """, (ip,))

            limpezas = cursor.fetchall()
            
            # Log do que foi encontrado
            print(f"[LOG] Número de limpezas encontradas para IP {ip}: {len(limpezas)}")
            if limpezas:
                print(f"[LOG] Primeira limpeza: {dict(limpezas[0])}")

        # ... resto do código (if not limpezas, jsonify existe false, etc.)
        
        resultado = []
        for l in limpezas:
            item = dict(l)
            if isinstance(item.get("data_inicio"), datetime):
                item["data_inicio"] = item["data_inicio"].strftime("%Y-%m-%d %H:%M:%S")
            resultado.append(item)

        return jsonify({
            "existe": bool(resultado),
            "limpezas": resultado
        })

    finally:
        conn.close()


@app.route("/tablet_limpeza_ativa")
def tablet_limpeza_ativa():
    return render_template("tabletLimpezaAtiva.html")


def buscar_ips_e_setores_ativos():
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT ip, setor
                FROM dispositivos
                WHERE situacao = TRUE
            """)
            rows = cursor.fetchall()

        ips = {}
        for row in rows:
            ip = row["ip"]
            setor = row["setor"]

            if ip not in ips:
                ips[ip] = []

            ips[ip].append(setor)

        return ips

    finally:
        conn.close()


def thread_atualizar_leitos_por_ip():
    while True:
        print("🔄 Iniciando atualização de leitos por IP...")

        try:
            ips_setores = buscar_ips_e_setores_ativos()
            cache_final = {}

            for ip, setores in ips_setores.items():
                print(f"➡️ Coletando dados para IP {ip} | Setores: {setores}")

                dados = login_e_buscar_leitos(setores)

                if dados:
                    cache_final[ip] = {
                        "ultima_atualizacao": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        "leitos": dados
                    }
                else:
                    print(f"⚠️ Nenhum dado retornado para IP {ip}")

            # 🔹 Escrita segura (arquivo temporário)
            tmp_file = LEITOS_CACHE_FILE + ".tmp"

            with open(tmp_file, "w", encoding="utf-8") as f:
                json.dump(cache_final, f, ensure_ascii=False, indent=4)

            # 🔹 Substitui o arquivo antigo
            import os
            os.replace(tmp_file, LEITOS_CACHE_FILE)

            print("✅ JSON atualizado com sucesso!")

        except Exception as e:
            logging.error(f"❌ Erro na thread de atualização: {e}")

        print(f"⏳ Aguardando {INTERVALO_ATUALIZACAO}s para próxima execução...\n")
        time.sleep(INTERVALO_ATUALIZACAO)


def iniciar_thread_background():
    thread = threading.Thread(
        target=thread_atualizar_leitos_por_ip,
        daemon=True
    )
    thread.start()



@app.route('/time', methods=['GET'])
def get_server_time():
    # Obtém a data e hora atual do servidor
    now = datetime.now()
    # Retorna a data no formato ISO
    return jsonify({"currentTime": now.isoformat()})    



def enviar_email_pendente(destinatarios, leito, setor, ultima_limpeza, vencimento):
    if not destinatarios:
        print("⚠️ Nenhum email configurado para este setor")
        return False

    assunto = "⚠️ ALERTA: Limpeza de Leito PENDENTE!"

    corpo = f"""
Olá,

O leito abaixo encontra-se com status PENDENTE e necessita de nova limpeza:

Leito: {leito}
Setor: {setor}
Última limpeza realizada em: {ultima_limpeza.strftime('%d/%m/%Y %H:%M')}
Vencimento da limpeza: {vencimento.strftime('%d/%m/%Y %H:%M')}

Atenciosamente,
Sistema Leito Clean
"""

    msg = MIMEMultipart()
    msg["From"] = EMAIL_USER
    msg["To"] = ", ".join(destinatarios)
    msg["Subject"] = assunto
    msg.attach(MIMEText(corpo, "plain"))

    try:
        with smtplib.SMTP(EMAIL_HOST, EMAIL_PORT) as server:
            server.starttls()
            server.login(EMAIL_USER, EMAIL_PASSWORD)
            server.send_message(msg)

        print(f"📧 Email enviado para: {destinatarios}")
        return True

    except Exception as e:
        print("❌ Erro ao enviar e-mail:", e)
        return False








@app.route("/config", methods=["GET", "POST"])
def config():
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        # SALVAR / EDITAR
        if request.method == "POST":
            id_dispositivo = request.form.get("id")
            setor = request.form["setor"].strip()
            ip = request.form["ip"].strip()
            qtd_leitos = request.form["qtd_leitos"].strip()
            situacao = 1 if request.form.get("situacao") == "on" else 0

            if id_dispositivo:  # editar
                cursor.execute("""
                    UPDATE dispositivos
                    SET setor=%s, ip=%s, qtd_leitos=%s, situacao=%s
                    WHERE id=%s
                """, (setor, ip, qtd_leitos, situacao, id_dispositivo))
            else:  # inserir
                cursor.execute("""
                    INSERT INTO dispositivos (setor, ip, qtd_leitos, situacao)
                    VALUES (%s, %s, %s, %s)
                """, (setor, ip, qtd_leitos, situacao))

            return redirect(url_for("config"))

        # LISTAR
        cursor.execute("""
            SELECT id, ip, setor, qtd_leitos, situacao
            FROM dispositivos
            ORDER BY setor, ip
        """)
        dispositivos = cursor.fetchall()

        return render_template(
            "paginaConfig.html",
            dispositivos=dispositivos
        )

    finally:
        cursor.close()
        conn.close() 




@app.route("/logout")
def logout():
    global driver
    session.clear()
    if driver:
        driver.quit()
        driver = None
    return redirect(url_for("index"))    
    

def iniciar_threads():
    Thread(target=iniciar_thread_background, daemon=True).start()
    Thread(target=atualiza_pendentes, daemon=True).start()
    print("🟢 Threads de background iniciadas")


iniciar_threads()


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
    






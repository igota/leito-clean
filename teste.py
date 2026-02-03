import json
import os
import re
from datetime import datetime
from typing import List, Dict
import requests
from bs4 import BeautifulSoup
import html
import time
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO)

class BuscadorLeitosOtimizado:
    def __init__(self, output_dir: str = "dados_leitos"):
        self.BASE_URL = "https://sistemasnti.isgh.org.br"
        self.LOGIN_URL = f"{self.BASE_URL}/pacientehrn/login.jsf"
        self.PEP_URL = f"{self.BASE_URL}/pacientehrn/cs_pep_sem_status.jsf"
        self.USERNAME = "MAPACCG"
        self.PASSWORD = "@isgh#nti2"
        self.output_dir = output_dir
        
        os.makedirs(output_dir, exist_ok=True)
        
        self.session = None
        self.viewstate_atual = None
        self.mapa_setores = None
        self.pacientes_vistos = set()
    
    def buscar_e_salvar_json(self, setores_desejados: List[str]) -> Dict:
        """Busca leitos e salva em JSON - Versão Otimizada"""
        print(f"🏥 BUSCA DE LEITOS OTIMIZADA - {len(setores_desejados)} setores")
        print("=" * 60)
        
        inicio_total = time.time()
        self.pacientes_vistos.clear()
        
        try:
            # 1. LOGIN E PREPARAÇÃO
            print("🔸 Etapa 1/2: Login e preparação...")
            if not self._realizar_login():
                return {"erro": "Falha no login"}
            
            if not self._preparar_sessao():
                return {"erro": "Falha na preparação"}
            
            # 2. BUSCA SEQUENCIAL COM FILTRO
            print(f"🔸 Etapa 2/2: Buscando setores...")
            dados_totais = []
            setores_com_dados = []
            setores_nao_encontrados = []
            
            for setor_nome in setores_desejados:
                if setor_nome not in self.mapa_setores:
                    setores_nao_encontrados.append(setor_nome)
                    print(f"⚠️ Setor não disponível: '{setor_nome}'")
                    continue
                
                print(f"🔹 {setor_nome}...")
                inicio_setor = time.time()
                
                dados_setor = self._buscar_setor_individual(setor_nome)
                
                if dados_setor:
                    # Filtrar novos pacientes
                    dados_novos = []
                    for item in dados_setor:
                        if item['prontuario'] not in self.pacientes_vistos:
                            self.pacientes_vistos.add(item['prontuario'])
                            dados_novos.append(item)
                    
                    if dados_novos:
                        dados_totais.extend(dados_novos)
                        setores_com_dados.append(setor_nome)
                        fim_setor = time.time()
                        print(f"✅ {len(dados_novos)} leito(s) em {fim_setor - inicio_setor:.1f}s")
                        
                        # Mostrar amostra rápida
                        if dados_novos and len(dados_novos) <= 3:
                            for item in dados_novos:
                                print(f"   • {item['paciente'][:25]:25} | Leito: {item['numero_leito']}")
                        elif dados_novos:
                            print(f"   • Primeiro: {dados_novos[0]['paciente'][:20]}... | Leito: {dados_novos[0]['numero_leito']}")
                    else:
                        print(f"ℹ️ Todos os pacientes já foram capturados")
                else:
                    print(f"ℹ️ Sem dados retornados")
            
            # 3. SALVAR E RETORNAR RESULTADOS
            fim_total = time.time()
            tempo_total = fim_total - inicio_total
            
            if dados_totais:
                arquivo_salvo = self._salvar_json_otimizado(dados_totais, setores_desejados, 
                                                          setores_com_dados, setores_nao_encontrados, 
                                                          tempo_total)
                
                # RELATÓRIO FINAL MELHORADO
                self._exibir_relatorio_final(dados_totais, tempo_total, setores_com_dados, 
                                           setores_nao_encontrados, arquivo_salvo)
                
                return {
                    "sucesso": True,
                    "dados": dados_totais,
                    "arquivo_salvo": arquivo_salvo,
                    "timestamp": datetime.now().isoformat(),
                    "total_leitos": len(dados_totais),
                    "tempo_execucao": tempo_total,
                    "setores_com_dados": setores_com_dados,
                    "setores_nao_encontrados": setores_nao_encontrados
                }
            else:
                print("\n" + "=" * 60)
                print("ℹ️ NENHUM LEITO ENCONTRADO")
                print("=" * 60)
                if setores_nao_encontrados:
                    print(f"Setores não disponíveis: {', '.join(setores_nao_encontrados)}")
                
                return {
                    "sucesso": False,
                    "aviso": "Nenhum leito encontrado",
                    "setores_nao_encontrados": setores_nao_encontrados
                }
            
        except Exception as e:
            logging.error(f"❌ Erro geral: {str(e)}")
            return {"erro": str(e), "sucesso": False}
    
    def _realizar_login(self) -> bool:
        """Realiza login no sistema - Versão Otimizada"""
        try:
            self.session = requests.Session()
            self.session.headers.update({
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                "Accept": "*/*",
                "Accept-Language": "pt-BR,pt;q=0.9,en;q=0.8",
            })
            
            # Obter página de login
            resp_login = self.session.get(self.LOGIN_URL, timeout=15)
            resp_login.raise_for_status()
            
            soup_login = BeautifulSoup(resp_login.text, 'html.parser')
            
            # Extrair ViewState
            viewstate_input = soup_login.find("input", {"name": "javax.faces.ViewState"})
            if not viewstate_input:
                logging.error("ViewState não encontrado na página de login")
                return False
            
            viewstate = viewstate_input["value"]
            
            # Preparar payload de login
            payload_login = {
                "formulario": "formulario",
                "login": self.USERNAME,
                "xyb-ac": self.PASSWORD,
                "formulario:botaoLogin": "confirmar",
                "formulario:host": "10.2.2.8:8080",
                "javax.faces.ViewState": viewstate
            }
            
            headers_login = {
                "Content-Type": "application/x-www-form-urlencoded",
                "Origin": self.BASE_URL,
                "Referer": self.LOGIN_URL,
            }
            
            # Fazer login
            resp_pos_login = self.session.post(
                self.LOGIN_URL, 
                data=payload_login, 
                headers=headers_login, 
                timeout=15,
                allow_redirects=True
            )
            
            # Verificar se o login foi bem-sucedido
            if "login.jsf" in resp_pos_login.url or "login" in resp_pos_login.url.lower():
                logging.error("Login falhou - redirecionado para página de login")
                return False
            
            print("✅ Login realizado com sucesso")
            return True
            
        except requests.exceptions.RequestException as e:
            logging.error(f"Erro de conexão no login: {e}")
            return False
        except Exception as e:
            logging.error(f"Erro inesperado no login: {e}")
            return False
    
    def _preparar_sessao(self) -> bool:
        """Prepara sessão e obtém mapa de setores - Versão Otimizada"""
        try:
            # Acessar página PEP
            resp_pep = self.session.get(self.PEP_URL, timeout=15)
            resp_pep.raise_for_status()
            
            # Verificar se ainda está logado
            if "login.jsf" in resp_pep.url:
                logging.error("Sessão expirada após login")
                return False
            
            soup_pep = BeautifulSoup(resp_pep.text, 'html.parser')
            
            # Extrair ViewState atual
            viewstate_input = soup_pep.find("input", {"name": "javax.faces.ViewState"})
            if not viewstate_input:
                logging.error("ViewState não encontrado na página PEP")
                return False
            
            self.viewstate_atual = viewstate_input["value"]
            
            # Mapear setores disponíveis
            select_clinica = soup_pep.find("select", {"id": "formMedicos:selClinica"})
            if not select_clinica:
                logging.error("Select de clínicas não encontrado")
                return False
            
            options = select_clinica.find_all("option")
            self.mapa_setores = {}
            
            for option in options:
                nome = option.text.strip()
                valor = option.get("value")
                if nome and valor and valor != "0":
                    self.mapa_setores[nome] = valor
            
            print(f"✅ {len(self.mapa_setores)} setores disponíveis no sistema")
            return True
            
        except requests.exceptions.RequestException as e:
            logging.error(f"Erro de conexão na preparação: {e}")
            return False
        except Exception as e:
            logging.error(f"Erro inesperado na preparação: {e}")
            return False
    
    def _buscar_setor_individual(self, setor_nome: str) -> List[Dict]:
        """Busca leitos de um setor específico - Versão Otimizada"""
        valor_setor = self.mapa_setores.get(setor_nome)
        if not valor_setor:
            return []
        
        try:
            # Preparar requisição AJAX
            headers_ajax = {
                "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
                "Origin": self.BASE_URL,
                "Referer": self.PEP_URL,
                "X-Requested-With": "XMLHttpRequest",
                "Faces-Request": "partial/ajax",
            }
            
            payload_ajax = {
                "AJAXREQUEST": "_viewRoot",
                "formMedicos": "formMedicos",
                "formMedicos:selClinica": valor_setor,
                "formMedicos:selEnfermaria": "0",
                "formMedicos:iptProntuario": "",
                "javax.faces.ViewState": self.viewstate_atual,
                "formMedicos:j_id264": "formMedicos:j_id264",
            }
            
            # Fazer requisição
            resp = self.session.post(
                self.PEP_URL, 
                data=payload_ajax, 
                headers=headers_ajax, 
                timeout=15
            )
            
            if resp.status_code == 200:
                # Atualizar ViewState se necessário
                novo_viewstate = self._extrair_viewstate(resp.text)
                if novo_viewstate:
                    self.viewstate_atual = novo_viewstate
                
                return self._processar_resposta_setor_otimizado(resp.text, setor_nome)
            else:
                logging.warning(f"HTTP {resp.status_code} ao buscar setor {setor_nome}")
                return []
            
        except requests.exceptions.Timeout:
            logging.error(f"Timeout ao buscar setor {setor_nome}")
            return []
        except Exception as e:
            logging.error(f"Erro ao buscar setor {setor_nome}: {e}")
            return []
    
    def _processar_resposta_setor_otimizado(self, resposta_texto: str, setor_buscado: str) -> List[Dict]:
        """Processa resposta de forma otimizada"""
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
                # É HTML normal
                soup = BeautifulSoup(resposta_texto, 'html.parser')
            
            # Buscar tabela
            tabela = soup.find("table", {"id": "formMedicos:oTableNovo"})
            if not tabela:
                return []
            
            # Encontrar todas as linhas
            linhas = tabela.find_all("tr")
            
            # Verificar se a primeira linha é cabeçalho
            primeira_linha_texto = linhas[0].get_text().upper() if linhas else ""
            if "PRONTUÁRIO" in primeira_linha_texto or "PACIENTE" in primeira_linha_texto:
                linhas = linhas[1:]  # Pular cabeçalho
            
            for linha in linhas:
                try:
                    celulas = linha.find_all("td")
                    if len(celulas) < 3:
                        continue
                    
                    # Extrair dados básicos
                    prontuario = celulas[0].get_text(strip=True)
                    paciente = celulas[1].get_text(strip=True)
                    texto_leito = celulas[2].get_text(strip=True)
                    
                    # Extrair setor e número do leito
                    setor, numero_leito = self._extrair_setor_leito_otimizado(texto_leito, setor_buscado)
                    
                    # Validar dados
                    if not prontuario or not paciente:
                        continue
                    
                    # Criar item de dados
                    item = {
                        "prontuario": prontuario,
                        "paciente": paciente,
                        "setor": setor,
                        "numero_leito": numero_leito,
                        "setor_buscado": setor_buscado
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
    
    def _extrair_setor_leito_otimizado(self, texto_leito: str, setor_buscado: str) -> tuple:
        """
        Extrai setor e número do leito de forma otimizada
        """
        if not texto_leito:
            return setor_buscado, ""
        
        texto = texto_leito.strip()
        
        # 1. Extrair número do leito
        numero_leito = ""
        
        # Padrões comuns para número do leito
        padroes_leito = [
            r'[-\.](\d{1,2})$',           # "-01" ou ".01" no final
            r'[-\.](\d{1,2})\b',          # "-01" ou ".01" em qualquer lugar
            r'\b(\d{1,2})$',              # "01" no final
            r'leito[:\s]*(\d{1,2})\b',    # "leito: 01"
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
            ]
            
            for padrao in padroes_remover:
                setor = re.sub(padrao, '', setor)
        
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
        
        # Se o setor ficou vazio, usar o setor buscado
        if not setor:
            setor = setor_buscado
        
        return setor, numero_leito
    
    def _extrair_viewstate(self, texto: str) -> str:
        """Extrai ViewState da resposta"""
        try:
            soup = BeautifulSoup(texto, 'html.parser')
            input_viewstate = soup.find("input", {"name": "javax.faces.ViewState"})
            if input_viewstate and input_viewstate.get("value"):
                return input_viewstate["value"]
        except Exception:
            pass
        return ""
    
    def _salvar_json_otimizado(self, dados: List[Dict], setores_buscados: List[str],
                             setores_com_dados: List[str], setores_nao_encontrados: List[str],
                             tempo_execucao: float) -> str:
        """Salva os dados em JSON otimizado"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = os.path.join(self.output_dir, f"leitos_{timestamp}.json")
        
        # Calcular estatísticas
        from collections import Counter
        contagem_setores = Counter([d['setor'] for d in dados])
        contagem_setores_buscados = Counter([d['setor_buscado'] for d in dados])
        
        # Preparar dados para salvar
        resultado = {
            "metadata": {
                "gerado_em": datetime.now().isoformat(),
                "gerado_em_legivel": datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
                "tempo_execucao_segundos": round(tempo_execucao, 2),
                "total_registros": len(dados),
                "parametros_busca": {
                    "setores_solicitados": setores_buscados,
                    "setores_encontrados": setores_com_dados,
                    "setores_nao_encontrados": setores_nao_encontrados
                },
                "estatisticas": {
                    "distribuicao_setor_real": dict(contagem_setores),
                    "distribuicao_setor_buscado": dict(contagem_setores_buscados),
                    "total_setores_diferentes": len(contagem_setores)
                }
            },
            "data": dados
        }
        
        # Salvar arquivo
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(resultado, f, ensure_ascii=False, indent=2)
        
        return filename
    
    def _exibir_relatorio_final(self, dados: List[Dict], tempo_total: float,
                              setores_com_dados: List[str], setores_nao_encontrados: List[str],
                              arquivo_salvo: str):
        """Exibe relatório final formatado"""
        print("\n" + "=" * 60)
        print("📊 RELATÓRIO FINAL")
        print("=" * 60)
        
        print(f"⏱️  Tempo total: {tempo_total:.2f} segundos")
        print(f"📁 Arquivo salvo: {arquivo_salvo}")
        print(f"🛏️  Total de leitos: {len(dados)}")
        print(f"🏥 Setores com dados: {len(setores_com_dados)}")
        
        if setores_nao_encontrados:
            print(f"⚠️  Setores não encontrados: {', '.join(setores_nao_encontrados)}")
        
        # Estatísticas por setor
        if dados:
            from collections import Counter
            contagem = Counter([d['setor'] for d in dados])
            
            print(f"\n📋 DISTRIBUIÇÃO POR SETOR:")
            for setor, count in sorted(contagem.items()):
                print(f"  • {setor}: {count} leito(s)")
            
            # Amostra dos dados
            print(f"\n🎯 AMOSTRA DOS DADOS (5 primeiros):")
            for i, item in enumerate(dados[:5], 1):
                paciente = item['paciente']
                if len(paciente) > 25:
                    paciente = paciente[:22] + "..."
                print(f"{i}. {paciente}")
                print(f"   Pront: {item['prontuario']:8} | Leito: {item['numero_leito']:3} | Setor: {item['setor']}")
        
        print("=" * 60)


# Funções auxiliares para compatibilidade
def buscar_leitos_salvar_json(setores: List[str], output_dir: str = "dados_leitos") -> Dict:
    """
    Função principal para busca e salvamento
    
    Args:
        setores: Lista de setores para buscar
        output_dir: Diretório de saída
    
    Returns:
        Dict com resultado da busca
    """
    buscador = BuscadorLeitosOtimizado(output_dir)
    return buscador.buscar_e_salvar_json(setores)


def testar_parser():
    """Testa o parser com exemplos"""
    buscador = BuscadorLeitosOtimizado()
    
    exemplos = [
        "UTI ADULTO II - UTI ADULTO II-01",
        "UTI ADULTO II-01",
        "UTI ADULTO II - UTI ADULTO II.01",
        "UTI ADULTO II - UTI ADULTO II -01",
        "UTI ADULTO II.01",
        "UTI ADULTO II -01",
        "UTI ADULTO II - UTI ADULTO II - 01",
        "UTI ADULTO II - LEITO 01",
        "UTI ADULTO II:01",
    ]
    
    print("🧪 TESTANDO PARSER OTIMIZADO:")
    print("=" * 50)
    
    for exemplo in exemplos:
        setor, leito = buscador._extrair_setor_leito_otimizado(exemplo, "UTI ADULTO II")
        print(f"'{exemplo}'")
        print(f"  → Setor: '{setor}' | Leito: '{leito}'")
        print("-" * 40)


if __name__ == "__main__":
    # Testar o parser primeiro
    testar_parser()
    
    print("\n" + "=" * 60)
    print("🚀 INICIANDO BUSCA REAL...")
    print("=" * 60)
    
    # Configurar setores para teste
    setores_teste = ["UTI ADULTO III", "UTI ADULTO IV"]
    
    # Executar busca
    resultado = buscar_leitos_salvar_json(setores_teste)
    
    # Processar resultado
    if resultado.get("sucesso"):
        print(f"\n✅ Busca concluída com sucesso!")
        print(f"📊 Total de leitos: {resultado['total_leitos']}")
        
        if "arquivo_salvo" in resultado:
            # Carregar e mostrar estatísticas
            try:
                with open(resultado['arquivo_salvo'], 'r', encoding='utf-8') as f:
                    dados_salvos = json.load(f)
                    
                    print(f"\n📋 RESUMO DO ARQUIVO:")
                    print(f"  • Gerado em: {dados_salvos['metadata']['gerado_em_legivel']}")
                    print(f"  • Tempo de execução: {dados_salvos['metadata']['tempo_execucao_segundos']}s")
                    print(f"  • Setores com dados: {len(dados_salvos['metadata']['parametros_busca']['setores_encontrados'])}")
                    
            except Exception as e:
                print(f"⚠️ Erro ao ler arquivo: {e}")
    else:
        print(f"\n❌ Busca não foi bem-sucedida")
        if "erro" in resultado:
            print(f"Erro: {resultado['erro']}")
        if "aviso" in resultado:
            print(f"Aviso: {resultado['aviso']}")
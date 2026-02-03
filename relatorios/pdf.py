from collections import defaultdict
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib import colors
from io import BytesIO
from flask import send_file
from datetime import datetime
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import KeepTogether



def parse_data_fim(data_fim):
    """Retorna datetime a partir de várias formas de string.
    Se não conseguir parsear, retorna None e loga aviso."""
    if not data_fim:
        return None
    try:
        # formato "YYYY-MM-DD"
        if isinstance(data_fim, str) and len(data_fim) == 10:
            return datetime.strptime(data_fim, "%Y-%m-%d")
        # tenta ISO / "YYYY-MM-DD HH:MM:SS"
        # fromisoformat aceita "YYYY-MM-DDTHH:MM:SS" e "YYYY-MM-DD HH:MM:SS" em Python 3.7+
        return datetime.fromisoformat(data_fim.replace(" ", "T"))
    except Exception as e:
        print(f"⚠ parse_data_fim: formato inválido '{data_fim}': {e}")
        return None

def agrupar_por_setor_leito(dados):
    grupos = defaultdict(list)
    for linha in dados:
        chave = (linha["setor"], linha["numero_leito"])
        grupos[chave].append(linha)
    return grupos


def texto_filtro(valor, padrao):
    if not valor or valor in ["__TODOS__", "Todos"]:
        return padrao
    return valor

def data_br(dt):
    return dt.strftime("%d/%m/%Y") if dt else "—"

def txt(valor, padrao="—"):
    return valor if valor else padrao

def formatar_status_pdf(status):
    """Formata status para exibição no PDF"""
    if not status or status == "-":
        return "-"
    
    # Remove underscores e capitaliza
    return status.replace("_", " ").title()




from collections import defaultdict
from io import BytesIO
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Table, TableStyle, Spacer, KeepTogether
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.pagesizes import landscape, A4
from reportlab.lib import colors
from reportlab.pdfgen import canvas  # ← necessário para desenhar texto no canvas
from flask import request, send_file

# Funções auxiliares (assumidas como existentes)
# parse_data_fim, data_br, txt ...

def exportar_pdf(dados):
    # ===============================
    # FILTROS (permanece igual)
    # ===============================
    setor        = request.args.get("setor")
    leito        = request.args.get("leito")
    tipo_limpeza = request.args.get("tipo_limpeza")
    status       = request.args.get("status")
    inicio       = request.args.get("inicio")
    fim          = request.args.get("fim")

    setor_definido = setor and setor != "__TODOS__"
    leito_definido = leito and leito not in ["Todos", "__TODOS__"]

    if not setor_definido:
        modo = "setor_leito"
    elif setor_definido and not leito_definido:
        modo = "leito"
    else:
        modo = "direto"

    def texto(valor, padrao):
        return valor if valor and valor not in ["__TODOS__", "Todos"] else padrao

    dt_inicio = parse_data_fim(inicio)
    dt_fim    = parse_data_fim(fim)
    periodo_txt = (
        f"{data_br(dt_inicio)} a {data_br(dt_fim)}"
        if dt_inicio or dt_fim else "Todo o período"
    )

    # ===============================
    # DOCUMENTO
    # ===============================
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=landscape(A4),
        leftMargin=20,
        rightMargin=20,
        topMargin=20,         # 1ª página
        bottomMargin=20
    )

    estilos = getSampleStyleSheet()

    # Criar um estilo personalizado para o título menor
    estilos.add(ParagraphStyle(
        name='TituloRelatorio',
        parent=estilos['Title'],
        fontSize=16,  # Menor que o padrão (padrão é 20+)
        fontName='Helvetica-Bold',
        textColor=colors.HexColor('#003a5d'),
        spaceAfter=4,
        alignment=0  # 0=LEFT, 1=CENTER, 2=RIGHT
    ))
    
    # Estilo com borda lateral como no HTML
    estilos.add(ParagraphStyle(
        name='SubtituloBorda',
        parent=estilos['Normal'],
        fontSize=10,
        fontName='Helvetica-Bold',
        textColor=colors.HexColor('#013757'),
        leftIndent=0,
        borderLeftWidth=6,
        borderLeftColor=colors.HexColor('#013757'),
        borderLeftPadding=8,
        borderPadding=(8, 12, 8, 12),
        backColor=colors.HexColor('#eef2f5'),
        spaceBefore=12,
        spaceAfter=6
    ))
    
    elementos = []
    largura_base = doc.width

    # Data de emissão
    data_emissao = datetime.now().strftime("%d/%m/%Y %H:%M")
    # Título + Filtros na capa (permanece igual)
    elementos.append(Paragraph("Relatório por Leito", estilos["TituloRelatorio"]))
    
    elementos.append(Paragraph(f"<font size=8>Emitido em: {data_emissao}</font>", estilos["Normal"]))
    elementos.append(Spacer(1, 12))

    estilo_label = ParagraphStyle(name="label", parent=estilos["Normal"], fontSize=8, textColor=colors.HexColor("#555555"), leading=9)
    estilo_valor = ParagraphStyle(name="valor", parent=estilos["Normal"], fontSize=11, fontName="Helvetica-Bold", leading=12)

    filtros_tabela = [
        [Paragraph("SETOR", estilo_label), Paragraph("LEITO", estilo_label), Paragraph("TIPO", estilo_label), Paragraph("STATUS", estilo_label), Paragraph("PERÍODO", estilo_label)],
        [
            Paragraph(texto(setor, "Todos os Setores"), estilo_valor),
            Paragraph(f"Leito {leito}" if leito_definido else "Todos os Leitos", estilo_valor),
            Paragraph(texto(tipo_limpeza, "Todos os Tipos"), estilo_valor),
            Paragraph(texto(status, "Todos os Status"), estilo_valor),
            Paragraph(periodo_txt, estilo_valor),
        ]
    ]

    tabela_filtros = Table(filtros_tabela, colWidths=[largura_base / 5] * 5)
    tabela_filtros.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,-1), colors.HexColor("#eef2f5")),
        ("LINEBEFORE", (0,0), (0,-1), 4, colors.HexColor("#003a5d")),
        ("LEFTPADDING", (0,0), (-1,-1), 10),
        ("RIGHTPADDING", (0,0), (-1,-1), 10),
        ("TOPPADDING", (0,0), (-1,-1), 3),
        ("BOTTOMPADDING", (0,0), (-1,-1), 3),
        ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
    ]))

    elementos.append(tabela_filtros)
    elementos.append(Spacer(1, 8))   
    


    # ===============================
    # CABEÇALHO COMPACTO + NUMERAÇÃO
    # ===============================
    def cabecalho_compacto(canvas, doc):
        canvas.saveState()
        canvas.setStrokeColor(colors.HexColor("#3f4346"))
        canvas.setLineWidth(0.6)
        y_linha = doc.height + doc.topMargin - 10
        canvas.line(doc.leftMargin, y_linha, doc.leftMargin + doc.width, y_linha)
        

        canvas.setFont("Helvetica", 8)
        canvas.setFillColor(colors.HexColor("#444444"))
        texto_filtros = f"Setor: {texto(setor, 'Todos')} | Leito: {texto(leito, 'Todos')} | Tipo: {texto(tipo_limpeza, 'Todos')} | Status: {texto(status, 'Todos')} | Período: {periodo_txt} | Emitido em: {data_emissao}"
        canvas.drawString(doc.leftMargin, y_linha + 6, texto_filtros)
        canvas.restoreState()

    def numero_pagina(canvas, doc):
        canvas.saveState()
        canvas.setFont("Helvetica", 9)
        canvas.setFillColor(colors.HexColor("#666666"))

        # Opção 1: apenas o número atual (simples)
        texto = f"Página {doc.page}"

        # Opção 2: com total (requer hack ou segunda passada – mais complexo)
        # texto = f"Página {doc.page} de {doc._canvas.getPageNumber()}"  # não funciona diretamente

        # Centralizado no rodapé
        largura_texto = canvas.stringWidth(texto, "Helvetica", 9)
        x = doc.leftMargin + (doc.width - largura_texto) / 2
        y = 12  # distância do fundo da página

        canvas.drawString(x, y, texto)
        canvas.restoreState()

    def on_first_page(canvas, doc):
        # Primeira página: margem normal + numeração
        numero_pagina(canvas, doc)
        # Se quiser cabeçalho na primeira página também, chame cabecalho_compacto aqui

    def on_later_pages(canvas, doc):
        # Páginas seguintes: margem maior + cabeçalho + numeração
        doc.topMargin = 35
        cabecalho_compacto(canvas, doc)
        numero_pagina(canvas, doc)

        

    # ===============================
    # AGRUPAMENTO (permanece com espaçamentos reduzidos)
    # ===============================
    grupos = defaultdict(list)
    for linha in dados:
        grupos[(linha["setor"], linha["numero_leito"])].append(linha)

    col_conteudo = [
        largura_base * 0.22,
        largura_base * 0.10,
        largura_base * 0.12,
        largura_base * 0.12,
        largura_base * 0.16,
        largura_base * 0.14,
        largura_base * 0.05,
        largura_base * 0.10,
    ]


    for (setor_nome, leito_nome), registros in sorted(grupos.items()):
        bloco = []

        if modo == "setor_leito":
            bloco.append(Paragraph(f"Setor: {setor_nome} | Leito: {leito_nome}", estilos["SubtituloBorda"]))
        elif modo == "leito":
            bloco.append(Paragraph(f"Leito: {leito_nome}", estilos["SubtituloBorda"]))

        dados_tabela = [["Paciente", "Tipo Limpeza", "Inicio da Limpeza", "Fim da Limpeza", "ASG", "Enfermeiro(a)", "Tempo", "Status"]]
        for r in registros:
            dados_tabela.append([
                Paragraph(txt(r["paciente"]), estilos["Normal"]),
                Paragraph(txt(r["tipo_limpeza"]), estilos["Normal"]),
                r["data_inicio"].strftime("%d/%m/%Y %H:%M"),
                r["data_fim"].strftime("%d/%m/%Y %H:%M"),
                Paragraph(txt(r["funcionario_asg"]), estilos["Normal"]),
                Paragraph(txt(r["funcionario_enf"]), estilos["Normal"]),
                txt(r["tempo_total_text"]),
                status:= formatar_status_pdf(r["status"])
            ])

        tabela = Table(dados_tabela, colWidths=col_conteudo)
        tabela.setStyle(TableStyle([
            ("BACKGROUND", (0,0), (-1,0), colors.HexColor("#003a5d")),
            ("TEXTCOLOR",  (0,0), (-1,0), colors.white),
            ("FONTNAME",   (0,0), (-1,0), "Helvetica-Bold"),
            ("GRID",       (0,0), (-1,-1), 0.5, colors.grey),
            ("ALIGN",      (2,1), (-1,-1), "CENTER"),
            ("VALIGN",     (0,0), (-1,-1), "MIDDLE"),
            ("LEFTPADDING",   (0,0), (-1,-1), 6),
            ("RIGHTPADDING",  (0,0), (-1,-1), 6),
            ("TOPPADDING",    (0,0), (-1,-1), 4),   # reduzido
            ("BOTTOMPADDING", (0,0), (-1,-1), 4),   # reduzido
        ]))

        bloco.append(tabela)
        bloco.append(Spacer(1, 8))  # espaço entre grupos reduzido

        elementos.append(KeepTogether(bloco))

    # ===============================
    # BUILD
    # ===============================
    doc.build(
        elementos,
        onFirstPage=on_first_page,
        onLaterPages=on_later_pages
    )

    buffer.seek(0)
    return send_file(
        buffer,
        as_attachment=True,
        download_name="relatorio_por_leito.pdf",
        mimetype="application/pdf"
    )

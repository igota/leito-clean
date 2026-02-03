from io import BytesIO
from openpyxl import Workbook
from flask import send_file


def exportar_xlsx(dados):

    wb = Workbook()
    ws = wb.active
    ws.title = "Relatório"

    ws.append(list(dados[0].keys()))

    for linha in dados:
        ws.append(list(linha.values()))

    buffer = BytesIO()
    wb.save(buffer)
    buffer.seek(0)

    return send_file(
        buffer,
        as_attachment=True,
        download_name="relatorio.xlsx",
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
import csv
from io import StringIO
from flask import Response

def exportar_csv(dados):
    output = StringIO()
    writer = csv.writer(output, delimiter=';')

    writer.writerow(dados[0].keys())

    for linha in dados:
        writer.writerow(linha.values())

    response = Response(output.getvalue(), mimetype="text/csv")
    response.headers["Content-Disposition"] = "attachment; filename=relatorio.csv"
    return response
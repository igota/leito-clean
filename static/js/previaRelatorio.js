document.addEventListener("DOMContentLoaded", () => {

    const params = new URLSearchParams(window.location.search);
    const relatorio = params.get("relatorio");
    const btnPdf = document.querySelector(".btn-exportar.pdf");
    const btnCsv = document.querySelector(".btn-exportar.csv");
    const btnXlsx = document.querySelector(".btn-exportar.xlsx");



    /* ============================
       TÍTULO DO RELATÓRIO
    ============================ */
    const titulo = document.getElementById("tituloRelatorio");

    if (relatorio === "leito") {
        titulo.innerText = "Relatório por Leito";
    } else if (relatorio === "setor") {
        titulo.innerText = "Relatório por Setor";
    } else if (relatorio === "funcionario") {
        titulo.innerText = "Relatório por Funcionário";
    } else {
        titulo.innerText = "Relatório";
    }



    btnPdf.addEventListener("click", () => {
        exportarRelatorio("pdf");
    });

    btnCsv.addEventListener("click", () => {
        exportarRelatorio("csv");
    });

    btnXlsx.addEventListener("click", () => {
        exportarRelatorio("xlsx");
    });


    /* ============================
       BUSCA DE DADOS (placeholder)
    ============================ */
    carregarDados(params);
});



/* ============================
   FUNÇÕES
============================ */



function exportarRelatorio(formato) {
    const params = new URLSearchParams(window.location.search);
    params.append("formato", formato);

    window.location.href = `/relatorios/exportar?${params.toString()}`;
}


function formatarDataHora(dataHora) {
    if (!dataHora) return "-";

    // Aceita ISO sem Z ou com Z, mas trata como local
    const data = new Date(dataHora.replace("Z", ""));  // remove Z se vier

    if (isNaN(data.getTime())) return "Data inválida";

    return data.toLocaleString("pt-BR", {
        day: "2-digit",
        month: "2-digit",
        year: "numeric",
        hour: "2-digit",
        minute: "2-digit",
        hour12: false
    }).replace(/(\d+)\/(\d+)\/(\d+),/, "$1/$2/$3");
}


function carregarDados(params) {
    preencherTopoIdentificacao(); // 👈 AQUI

    fetch(`/relatorios/dados?${params.toString()}`)
        .then(res => res.json())
        .then(data => preencherTabela(data))
        .catch(() => {
            document.getElementById("containerRelatorios").innerHTML =
                "<p>Erro ao carregar dados</p>";
        });
}




function obterPeriodoTexto(params) {
    const inicio = params.get("inicio");
    const fim = params.get("fim");

    if (!inicio && !fim) {
        return "Todo período";
    }

    return `${formatarData(inicio)} a ${formatarData(fim)}`;
}

function formatarData(data) {
    if (!data) return "";

    const [ano, mes, dia] = data.split("-");
    return `${dia}/${mes}/${ano}`;
}




function preencherTopoIdentificacao() {
    const params = new URLSearchParams(window.location.search);

    const setor = params.get("setor");
    const leito = params.get("leito");
    const tipo_limpeza = params.get("tipo_limpeza");
    const status = params.get("status");

    const infoSetor = document.getElementById("infoSetor");
    const infoLeito = document.getElementById("infoLeito");
    const infoTipo = document.getElementById("infoTipo");
    const infoStatus = document.getElementById("infoStatus");
    const infoPeriodo = document.getElementById("infoPeriodo");


    // SETOR
    infoSetor.innerText =
        setor && setor !== "__TODOS__" && setor !== "Todos"
            ? setor
            : "Todos os Setores";

    // LEITO
    infoLeito.innerText =
        leito && leito !== "__TODOS__" && leito !== "Todos"
            ? `Leito ${leito}`
            : "Todos os Leitos";

    // TIPO
    infoTipo.innerText =
        tipo_limpeza && tipo_limpeza !== "__TODOS__"
            ? tipo_limpeza
            : "Todos os Tipos";

        // STATUS
    infoStatus.innerText =
        status && status !== "__TODOS__"
            ? status
            : "Todos os Status";        
    // PERÍODO
    infoPeriodo.innerText = obterPeriodoTexto(params);
}




function preencherTabela(dados) {
    const container = document.getElementById("containerRelatorios");
    container.innerHTML = "";

    if (!dados || dados.length === 0) {
        container.innerHTML = "<p>Nenhum registro encontrado</p>";
        return;
    }

    const params = new URLSearchParams(window.location.search);
    const leitoSelecionado = params.get("leito");
    const setorSelecionado = params.get("setor");

    /* =====================================================
       CASO 1 — LEITO ESPECÍFICO (uma única tabela, sem agrupamento)
    ===================================================== */
    if (leitoSelecionado && leitoSelecionado !== "__TODOS__" && leitoSelecionado !== "Todos") {
        const tabela = criarTabela();
        const tbody = tabela.querySelector("tbody");

        dados.forEach(item => {
            tbody.appendChild(criarLinha(item));
        });

        container.appendChild(tabela);
        return;
    }

    /* =====================================================
       CASO 2 — Agrupar por SETOR + LEITO (com ordenação)
    ===================================================== */

    // Agrupar por chave composta: "Setor|Leito"
    const grupos = {};

    dados.forEach(item => {
        const setor = item.setor || "Sem Setor";
        const leito = item.numero_leito || "—";
        const chave = `${setor}|${leito}`;  // chave única: "UTI ADULTO III|2"

        if (!grupos[chave]) {
            grupos[chave] = {
                setor: setor,
                leito: leito,
                registros: [],
                chaveOrdenacao: `${setor.toLowerCase()}|${parseInt(leito) || 999}`  // para ordenação
            };
        }
        grupos[chave].registros.push(item);
    });

    // ✅ ORDENAR GRUPOS: Setor (alfabético) + Leito (numérico crescente)
    const gruposOrdenados = Object.values(grupos).sort((a, b) => {
        const [setorA, leitoA] = a.chaveOrdenacao.split("|");
        const [setorB, leitoB] = b.chaveOrdenacao.split("|");
        
        // Primeiro compara setor (case-insensitive)
        if (setorA < setorB) return -1;
        if (setorA > setorB) return 1;
        
        // Depois compara leito como número
        const numLeitoA = parseInt(leitoA) || 999;
        const numLeitoB = parseInt(leitoB) || 999;
        return numLeitoA - numLeitoB;
    });

    // Renderizar grupos ORDENADOS
    gruposOrdenados.forEach(grupo => {
        const { setor, leito, registros } = grupo;

        const titulo = document.createElement("h5");

        // Título dinâmico baseado no filtro
        if (setorSelecionado === "__TODOS__" || setorSelecionado === "Todos") {
            titulo.innerText = `Setor: ${setor} | Leito: ${leito}`;
        } else {
            titulo.innerText = `Leito: ${leito}`;
        }

        // Estilo do subtítulo (mantido)
        titulo.style.margin = "30px 0 10px";
        titulo.style.color = "#013757";
        titulo.style.background = "rgba(1, 55, 87, 0.1)";
        titulo.style.padding = "8px 12px";
        titulo.style.borderLeft = "6px solid #013757";

        const tabela = criarTabela();
        const tbody = tabela.querySelector("tbody");

        // Ordenar registros dentro do grupo por data_inicio (opcional, mas recomendado)
        registros.sort((a, b) => new Date(a.data_inicio) - new Date(b.data_inicio));

        registros.forEach(item => {
            tbody.appendChild(criarLinha(item));
        });

        container.appendChild(titulo);
        container.appendChild(tabela);
    });
}

function criarTabela() {
    const table = document.createElement("table");
    table.innerHTML = `
        <thead>
            <tr>
                <th>Paciente</th>
                <th>Tipo Limpeza</th>
                <th>Inicio da Limpeza</th>
                <th>Fim da Limpeza</th>
                <th>ASG</th>
                <th>Enfermeiro(a)</th>
                <th>Tempo (mm:ss)</th>
                <th>Status</th>
            </tr>
        </thead>
        <tbody></tbody>
    `;
    return table;
}

function formatarStatus(status) {
    if (!status) return "-";

    return status
        .replaceAll("_", " ")     // EM_ANDAMENTO → EM ANDAMENTO
        .toLowerCase()            // em andamento
        .replace(/\b\w/g, l => l.toUpperCase()); // Em Andamento
}


function criarLinha(item) {
    const tr = document.createElement("tr");
    tr.innerHTML = `
        <td>${item.paciente || "-"}</td>
        <td>${item.tipo_limpeza || "-"}</td>
        <td>${formatarDataHora(item.data_inicio)}</td>
        <td>${formatarDataHora(item.data_fim)}</td>
        <td>${item.funcionario_asg || "-"}</td>
        <td>${item.funcionario_enf || "-"}</td>
        <td>${item.tempo_total_text || "-"}</td>
        <td>${formatarStatus(item.status)}</td>

    `;
    return tr;
}





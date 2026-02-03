document.addEventListener("DOMContentLoaded", () => {
    const painelLista = document.getElementById("viewLista");
    const painelGrade = document.getElementById("viewGrade");
    const seletor = document.getElementById("selectSetor");
    const btnLista = document.getElementById("btnLista");
    const btnGrade = document.getElementById("btnGrade");
    let modoVisualizacao = "tabela"; // ou "grid"

    const btnMaximizar = document.getElementById("btnMaximizar");

    btnMaximizar.addEventListener("click", () => {
        if (!document.fullscreenElement) {
            document.documentElement.requestFullscreen();
            document.body.classList.add("fullscreen-mode");

            btnMaximizar.innerHTML = '<i class="fas fa-compress"></i>';
            btnMaximizar.title = "Sair do modo maximizado";
        } else {
            document.exitFullscreen();
            document.body.classList.remove("fullscreen-mode");

            btnMaximizar.innerHTML = '<i class="fas fa-expand"></i>';
            btnMaximizar.title = "Maximizar Visualização";
        }
    });

    document.addEventListener("fullscreenchange", () => {
        if (!document.fullscreenElement) {
            document.body.classList.remove("fullscreen-mode");
            btnMaximizar.innerHTML = '<i class="fas fa-expand"></i>';
            btnMaximizar.title = "Maximizar Visualização";
        }
    });



    btnLista.onclick = () => {
        modoVisualizacao = "tabela";

        btnLista.classList.add("ativo");
        btnGrade.classList.remove("ativo");

        painelLista.style.display = "block";
        painelGrade.style.display = "none";

        carregarPainel();
    };

    btnGrade.onclick = () => {
        modoVisualizacao = "grid";

        btnGrade.classList.add("ativo");
        btnLista.classList.remove("ativo");

        painelLista.style.display = "none";
        painelGrade.style.display = "flex";

        carregarPainel();
    };



    // 🔹 Função: carrega os setores do banco
    async function carregarSetores() {
        try {
            const resposta = await fetch("/listar_setores");
            const setores = await resposta.json();

            seletor.innerHTML = '<option value="">Todos os setores</option>';
            setores.forEach(setor => {
                const option = document.createElement("option");
                option.value = setor;
                option.textContent = setor;
                seletor.appendChild(option);
            });
        } catch (erro) {
            console.error("Erro ao carregar setores:", erro);
            seletor.innerHTML = '<option value="">Erro ao carregar setores</option>';
        }
    }

    // 🔄 Função que busca e exibe as limpezas em tabela ou grid
    async function carregarPainel() {

        const setorSelecionado = seletor.value;
        let url = "/listar_limpezas";

        if (setorSelecionado) {
            url += `?setor=${encodeURIComponent(setorSelecionado)}`;
        }

        try {
            const resposta = await fetch(url);
            const limpezas = await resposta.json();

            // 🔥 ORDENAÇÃO NUMÉRICA DO LEITO
            limpezas.sort((a, b) => Number(a.numero_leito) - Number(b.numero_leito));

            let concluida = 0;
            let andamento = 0;
            let pendente = 0;
            let validacao = 0;

            limpezas.forEach(l => {
                if (l.status === "CONCLUIDA") concluida++;
                else if (l.status === "EM_ANDAMENTO") andamento++;
                else if (l.status === "PENDENTE") pendente++;
                else if (l.status === "AGUARDANDO_VALIDACAO") validacao++;
            });

            // Atualiza painel
            document.getElementById("qtdConcluida").textContent = concluida;
            document.getElementById("qtdAndamento").textContent = andamento;
            document.getElementById("qtdPendente").textContent = pendente;
            document.getElementById("qtdValidacao").textContent = validacao;

            // Limpa containers
            painelLista.innerHTML = "";
            painelGrade.innerHTML = "";

            // Controle de visibilidade via CSS
            painelLista.classList.add("hidden");
            painelGrade.classList.add("hidden");

            if (limpezas.length === 0) {
                const alvo = modoVisualizacao === "tabela" ? painelLista : painelGrade;
                alvo.innerHTML = "<p>Nenhuma limpeza encontrada.</p>";
                alvo.classList.remove("hidden");
                return;
            }

            // =========================================================
            // 📌 MODO TABELA
            // =========================================================
            if (modoVisualizacao === "tabela") {

                painelLista.classList.remove("hidden");

                const tabela = document.createElement("table");
                tabela.className = "tabela-limpezas";

                tabela.innerHTML = `
                    <thead>
                        <tr>
                            <th>Status</th>
                            <th>Setor</th>
                            <th>Leito</th>
                            <th>Paciente</th>
                            <th>Tipo de Limpeza</th>
                            <th>ASG</th>
                            <th>Enfermeiro(a)</th>
                            <th>Tempo</th>
                        </tr>
                    </thead>
                `;

                const tbody = document.createElement("tbody");

                limpezas.forEach(l => {
                    let statusClass = "";
                    let statusText = "";

                    if (l.status === "EM_ANDAMENTO") {
                        statusClass = "status-andamento";
                        statusText = "Em Andamento";
                    } else if (l.status === "CONCLUIDA") {
                        statusClass = "status-concluida";
                        statusText = "Concluída";
                    } else if (l.status === "PENDENTE") {
                        statusClass = "status-pendente";
                        statusText = "Pendente";
                    } else if (l.status === "AGUARDANDO_VALIDACAO") {
                        statusClass = "status-validacao";
                        statusText = "Aguardando Validação";
                    }

                    const linha = document.createElement("tr");
                    linha.className = statusClass;

                    linha.innerHTML = `
                        <td class="status-cell">
                            <span class="status-indicator ${statusClass}"></span>
                            ${statusText}
                        </td>
                        <td><strong>${l.setor}</strong></td>
                        <td><strong>${l.numero_leito}</strong></td>
                        <td>${l.paciente || "—"}</td>
                        <td>${l.tipo_limpeza || "—"}</td>
                        <td>${l.funcionario_asg || "—"}</td>
                        <td>${l.funcionario_enf || "—"}</td>
                        <td>${l.tempo_total_text || "—"}</td>
                    `;

                    tbody.appendChild(linha);
                });

                tabela.appendChild(tbody);
                painelLista.appendChild(tabela);
                return;
            }

    // =========================================================
    // 📌 MODO GRADE
    // =========================================================
    if (modoVisualizacao === "grid") {

        painelGrade.classList.remove("hidden");

        // Caso: TODOS os setores
        if (!setorSelecionado) {

            const containerSetores = document.createElement("div");
            containerSetores.className = "grid-setores";

            // Agrupa por setor
            const setores = {};
            limpezas.forEach(l => {
                if (!setores[l.setor]) setores[l.setor] = [];
                setores[l.setor].push(l);
            });

            // Monta cards por setor
            for (const setor in setores) {

                const setorCard = document.createElement("div");
                setorCard.className = "setor-card";

                setorCard.innerHTML = `<h3>${setor}</h3>`;

                const gridLeitos = document.createElement("div");
                gridLeitos.className = "grid-leitos";

                setores[setor].forEach(l => {
                    let statusClass = "";

                    if (l.status === "EM_ANDAMENTO") statusClass = "status-andamento-grid";
                    else if (l.status === "CONCLUIDA") statusClass = "status-concluida-grid";
                    else if (l.status === "PENDENTE") statusClass = "status-pendente-grid";
                    else if (l.status === "AGUARDANDO_VALIDACAO") statusClass = "status-validacao-grid";

                    const leito = document.createElement("div");
                    leito.className = `leito-card ${statusClass}`;
                    leito.textContent = l.numero_leito;

                    gridLeitos.appendChild(leito);
                });

                setorCard.appendChild(gridLeitos);
                containerSetores.appendChild(setorCard);
            }

            painelGrade.appendChild(containerSetores);
            return;
        }

    // Caso: SETOR ESPECÍFICO
    const setorCard = document.createElement("div");
    setorCard.className = "setor-card";

    // 👉 TÍTULO DO SETOR
    setorCard.innerHTML = `<h3>${setorSelecionado}</h3>`;

    const gridLeitos = document.createElement("div");
    gridLeitos.className = "grid-leitos";

    limpezas.forEach(l => {
        let statusClass = "";

        if (l.status === "EM_ANDAMENTO") statusClass = "status-andamento-grid";
        else if (l.status === "CONCLUIDA") statusClass = "status-concluida-grid";
        else if (l.status === "PENDENTE") statusClass = "status-pendente-grid";
        else if (l.status === "AGUARDANDO_VALIDACAO") statusClass = "status-validacao-grid";

        const leito = document.createElement("div");
        leito.className = `leito-card ${statusClass}`;
        leito.textContent = l.numero_leito;

        gridLeitos.appendChild(leito);
    });

    setorCard.appendChild(gridLeitos);
    painelGrade.appendChild(setorCard);
    return;

    }


        } catch (erro) {
            console.error("Erro ao carregar painel:", erro);

            const alvo = modoVisualizacao === "tabela" ? painelLista : painelGrade;
            alvo.innerHTML = "<p>❌ Erro ao carregar dados.</p>";
            alvo.classList.remove("hidden");
        }
    }




        // 👂 Conecta ao stream SSE
        const eventSource = new EventSource("/stream");
        eventSource.onmessage = (event) => {
            if (event.data === "atualizacao") {
                console.log("🔔 Atualização SSE recebida, recarregando painel...");
                carregarPainel();
            }
        };

        // 🔄 Atualiza o painel quando o setor mudar
        seletor.addEventListener("change", carregarPainel);

        // Inicializa
        carregarSetores().then(carregarPainel);
    });
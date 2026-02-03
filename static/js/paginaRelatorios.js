document.addEventListener("DOMContentLoaded", () => {

    const cards = document.querySelectorAll(".relatorio-card");
    const popup = document.getElementById("popupRelatorio");
    const fecharPopup = document.querySelector(".fechar-popup");
    const botoesPeriodo = document.querySelectorAll(".periodo-btn");
    const selectSetor = document.getElementById("setor");
    const selectLeito = document.getElementById("leito");
    const dataInicio = document.getElementById("dataInicio");
    const dataFim = document.getElementById("dataFim");
    

    const btnGerar = document.getElementById("btnGerarRelatorio");

    /* =========================
       ABRIR / FECHAR POPUP
    ========================== */

    cards.forEach(card => {
        card.addEventListener("click", () => {
            const tipo = card.dataset.tipo;

            document.getElementById("tipoRelatorio").value = tipo;
            document.getElementById("tituloPopup").innerText =
                tipo === "leito" ? "Relatório por Leito" :
                tipo === "setor" ? "Relatório por Setor" :
                "Relatório por Funcionário";

            popup.classList.remove("oculto");
            carregarSetores();
        });
    });

    fecharPopup.addEventListener("click", () => {
        popup.classList.add("oculto");
    });

    /* =========================
       CARREGAR SETORES
    ========================== */

    async function carregarSetores() {
        selectSetor.innerHTML = `
            <option value="">Selecione</option>
            <option value="__TODOS__">Todos os Setores</option>
        `;

        selectLeito.innerHTML = "<option value=''>Selecione o Setor Primeiro</option>";
        selectLeito.disabled = true;

        try {
            const response = await fetch("/listar_setores");
            const setores = await response.json();

            setores.forEach(setor => {
                if (!setor) return;

                const option = document.createElement("option");
                option.value = setor;
                option.textContent = setor;
                selectSetor.appendChild(option);
            });

        } catch (error) {
            console.error("Erro ao carregar setores:", error);
            selectSetor.innerHTML = "<option value=''>Erro ao carregar setores</option>";
        }
    }

    /* =========================
       CARREGAR LEITOS POR SETOR
    ========================== */

    selectSetor.addEventListener("change", async () => {
        const setor = selectSetor.value;

        selectLeito.innerHTML = "<option value=''>Todos os Leitos</option>";
        selectLeito.disabled = true;

        // 👉 Todos os setores → não carrega leitos
        if (!setor || setor === "__TODOS__") {
            return;
        }

        try {
            const response = await fetch(
                `/relatorios/leitos_registrados?setor=${encodeURIComponent(setor)}`
            );
            const leitos = await response.json();

            leitos.sort((a, b) => Number(a) - Number(b));

            leitos.forEach(leito => {
                const option = document.createElement("option");
                option.value = leito;
                option.textContent = leito;
                selectLeito.appendChild(option);
            });

            selectLeito.disabled = false;

        } catch (error) {
            console.error("Erro ao carregar leitos:", error);
            selectLeito.innerHTML = "<option value=''>Erro ao carregar leitos</option>";
        }
    });


            // Formata Date → yyyy-mm-dd (sem fuso)
        function formatarParaInput(date) {
            const ano = date.getFullYear();
            const mes = String(date.getMonth() + 1).padStart(2, "0");
            const dia = String(date.getDate()).padStart(2, "0");
            return `${ano}-${mes}-${dia}`;
        }
            

        botoesPeriodo.forEach(btn => {
            btn.addEventListener("click", () => {

                // 🔹 estado visual
                botoesPeriodo.forEach(b => b.classList.remove("ativo"));
                btn.classList.add("ativo");

                const periodo = btn.dataset.periodo;
                const hoje = new Date();

                let inicio;
                let fim;

                if (periodo === "hoje") {
                    inicio = hoje;
                    fim = hoje;
                }

                if (periodo === "7dias") {
                    fim = hoje;
                    inicio = new Date();
                    inicio.setDate(hoje.getDate() - 6);
                }

                if (periodo === "30dias") {
                    fim = hoje;
                    inicio = new Date();
                    inicio.setDate(hoje.getDate() - 29);
                }


                // 🔹 preencher inputs
                dataInicio.value = formatarParaInput(inicio);
                dataFim.value = formatarParaInput(fim);
            });
        });


    /* =========================
       GERAR RELATÓRIO
    ========================== */

    btnGerar.addEventListener("click", () => {

        const relatorio = document.getElementById("tipoRelatorio").value;
        const setor = selectSetor.value;
        const leito = selectLeito.value;
        const tipoLimpeza = document.getElementById("tipoLimpeza").value;
        const status = document.getElementById("status").value;

        // ✅ agora sim, pegando os valores
        const inicio = dataInicio.value;
        const fim = dataFim.value;

        // Tipo obrigatório
        if (!relatorio) {
            alert("Tipo de relatório não definido.");
            return;
        }

        // Relatório por leito exige setor OU todos
        if (relatorio === "leito" && !setor) {
            alert("Selecione um Setor ou Todos os Setores.");
            return;
        }

        // Período coerente
        if ((inicio && !fim) || (!inicio && fim)) {
            alert("Informe a data inicial e a data final.");
            return;
        }

        if (inicio && fim && fim < inicio) {
            alert("A data final não pode ser menor que a data inicial.");
            return;
        }

        const params = new URLSearchParams();
        params.append("relatorio", relatorio);

        if (setor) params.append("setor", setor);
        if (leito) params.append("leito", leito);
        if (tipoLimpeza) params.append("tipo_limpeza", tipoLimpeza);
        if (status) params.append("status", status);
        if (inicio) params.append("inicio", inicio);
        if (fim) params.append("fim", fim);

        window.location.href = `/relatorios/previa?${params.toString()}`;
    });


});

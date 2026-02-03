(() => {
    "use strict";

    /* =========================
       ESTADO
    ========================= */
    
    let segundos = 0;
    let limpezasAtivas = [];
    let limpezaSelecionada = null;
    const cronometros = new Map(); // id_limpeza → intervalo
    const btnNovaLimpeza = document.createElement("button");

    /* =========================
       DOM
    ========================= */
    const DOM = {
        cronometro: document.getElementById("cronometro"),
        tempo: document.getElementById("tempoDecorrido"),
        finalizarBtn: document.getElementById("finalizarLimpezaBtn"),
        popupFinalizar: document.getElementById("popupFinalizar"),
        popupConfirmacao: document.getElementById("popupConfirmacao"),
        inputCartaoFinalizar: document.getElementById("idcartaoFinalizarInput"),
        mensagemFuncionario: document.getElementById("mensagemFuncionario"),
        infoSetor: document.getElementById("infoSetor"),
        infoLeito: document.getElementById("infoLeito"),
        infoTipo: document.getElementById("infoTipo"),
        fecharFinalizar: document.getElementById("fecharFinalizar"),
        fecharConfirmacao: document.getElementById("fecharConfirmacao"),
        confirmarBtn: document.getElementById("confirmarInicio"),
        cancelarBtn: document.getElementById("cancelarInicio"),
        mensagemConfirmacao: document.getElementById("mensagemConfirmacao"),
    };

    /* =========================
       INIT
    ========================= */
    document.addEventListener("DOMContentLoaded", init);

    btnNovaLimpeza.id = "btnNovaLimpeza";
    btnNovaLimpeza.className = "btn-nova-limpeza hidden";
    btnNovaLimpeza.textContent = "+ Nova Limpeza";
    document.body.appendChild(btnNovaLimpeza);
    btnNovaLimpeza.addEventListener("click", () => window.location.href = "/tablet");

    async function init() {
        aplicarEstilo();
        bindEventos();
        await carregarLimpezaAtiva();
    }

    /* =========================
    EVENTOS GLOBAIS E MENSAGENS
    ========================= */
    // Adiciona o evento de clique no botão cancelar
    // ❌ Cancelar início
    cancelarInicio.addEventListener("click", () => {
        popupConfirmacao.classList.add("oculto");
        mostrarPaginaPrincipal();
    });

    /* =========================
    FUNÇÃO PARA MOSTRAR MENSAGEM COM FOCO NO INPUT
    ========================= */
    function mostrarMensagem(texto, callback = null) {
        const popup = document.getElementById("popupMensagem");
        const msg = document.getElementById("mensagemTexto");
        const btn = document.getElementById("fecharMensagemBtn");

        msg.textContent = texto;
        popup.classList.remove("oculto");

        // Remove listeners anteriores
        const novoBtn = btn.cloneNode(true);
        btn.replaceWith(novoBtn);
        
        novoBtn.onclick = () => {
            popup.classList.add("oculto");
            // Foca no input após fechar a mensagem
            setTimeout(() => {
                DOM.inputCartaoFinalizar.focus();
                DOM.inputCartaoFinalizar.select();
            }, 50);
            
            if (callback) callback(); // executa algo depois de fechar
        };
        
        // Foca no botão OK da mensagem para facilitar navegação
        setTimeout(() => novoBtn.focus(), 100);
    }


    /* =========================
       EVENTOS
    ========================= */
    function bindEventos() {
        // Remove todos os listeners existentes primeiro
        const novoConfirmar = DOM.confirmarBtn.cloneNode(true);
        DOM.confirmarBtn.replaceWith(novoConfirmar);
        DOM.confirmarBtn = novoConfirmar;

        

        // Adiciona novos listeners
        DOM.fecharConfirmacao?.addEventListener("click", () => ocultar(DOM.popupConfirmacao));

        
        
        
        // Adiciona listener ao botão confirmar (com delegação para evitar problemas)
        document.addEventListener('click', function(e) {
            if (e.target && e.target.id === 'confirmarInicio') {
                e.preventDefault();
                handleConfirmarFinalizacao();
            }
        });
    }

    /* =========================
       HANDLE CONFIRMAR FINALIZAÇÃO
    ========================= */
    async function handleConfirmarFinalizacao() {
        if (!limpezaSelecionada) {
            console.warn("⚠ Nenhuma limpeza selecionada para finalizar");
            ocultar(DOM.popupConfirmacao);
            return;
        }

        DOM.confirmarBtn.disabled = true;
        DOM.confirmarBtn.textContent = "Finalizando...";

        try {
            ocultar(DOM.popupConfirmacao);

            const inicio = new Date(limpezaSelecionada.data_inicio);
            const fim = new Date();
            const tempoTotalSeconds = Math.floor((fim - inicio) / 1000);

            // Extrai nome do técnico e ID do cartão da mensagem
            const mensagemHTML = DOM.mensagemConfirmacao.innerHTML;
            const enfMatch = mensagemHTML.match(/<span[^>]*>([^<]+)<\/span>/g);
            const enfNome = enfMatch ? enfMatch[0].replace(/<\/?span[^>]*>/g, '') : "Técnico";
            
            // Busca ID do cartão do localStorage ou usa valor do input
            const idCartaoEnf = localStorage.getItem('ultimoCartaoEnf') || 
                                   DOM.inputCartaoFinalizar?.value || "";

            console.log("🔍 Finalizando limpeza:", {
                id: limpezaSelecionada.id,
                enfermagem: enfNome,
                cartao: idCartaoEnf
            });

            await registrarFinalizacao(
                limpezaSelecionada.id,
                enfNome,
                idCartaoEnf,
                tempoTotalSeconds
            );

            removerLimpezaDaTela(limpezaSelecionada.id);
            mostrarConclusao(enfNome, tempoTotalSeconds, limpezaSelecionada.id);
            
            // Reseta o estado
            limpezaSelecionada = null;

        } catch (e) {
            console.error("❌ Erro ao finalizar limpeza:", e);
            alert(`Erro ao finalizar limpeza: ${e.message}`);
            
            // Reativa o botão em caso de erro
            DOM.confirmarBtn.disabled = false;
            DOM.confirmarBtn.textContent = "Confirmar";
            
            // Reabre o popup de confirmação
            mostrar(DOM.popupConfirmacao);
        }
    }

    /* =========================
       LIMPEZA ATIVA
    ========================= */
    async function carregarLimpezaAtiva() {
        try {
            const response = await fetch("/limpeza_ativa_por_ip");
            validarJSON(response);

            const data = await response.json();

            if (!data.existe || !Array.isArray(data.limpezas)) {
                alert("Nenhuma limpeza ativa neste dispositivo.");
                return;
            }

            limpezasAtivas = data.limpezas;
            renderizarLimpezas(limpezasAtivas);
            atualizarBotoesLimpeza();

        } catch (erro) {
            console.error("Erro ao buscar limpezas ativas:", erro);
            alert("Erro ao conectar com o servidor.");
            window.location.href = "/tablet";
        }
    }

    /* =========================
       CRONÔMETRO
    ========================= */
    function iniciarCronometro(id, dataInicio) {
        const inicio = new Date(dataInicio.replace(" ", "T")).getTime();

        atualizarTempo(id, inicio);

        const intervalo = setInterval(() => {
            atualizarTempo(id, inicio);
        }, 1000);

        cronometros.set(id, intervalo);
    }

    function atualizarTempo(id, inicio) {
        const agora = Date.now();
        const diferencaMs = agora - inicio;
        let seg = Math.floor(diferencaMs / 1000);

        const el = document.getElementById(`tempo-${id}`);
        if (!el) return;

        if (seg < -10) {
            // Muito no futuro → mostra algo chamativo
            el.textContent = "Aguardando...";
            el.style.color = "#e74c3c";
        } else if (seg < 0) {
            // Pouco no futuro → mostra como 00:00 ou com -
            el.textContent = "00:00";
            el.style.color = "#e67e22";
        } else {
            el.textContent = formatarTempo(seg);
            el.style.color = ""; // cor normal
        }

        if (limpezaSelecionada?.id == id) {
            segundos = Math.max(0, seg); // nunca negativo no estado
        }
    }

    function formatarTempo(seg) {
        const m = String(Math.floor(seg / 60)).padStart(2, "0");
        const s = String(seg % 60).padStart(2, "0");
        return `${m}:${s}`;
    }

    /* =========================
       FINALIZAÇÃO
    ========================= */

    DOM.finalizarBtn?.addEventListener("click", () => {
        if (!limpezaSelecionada) return;
        abrirPopupFinalizar(limpezaSelecionada.id);
    });

    function abrirPopupFinalizar(idLimpeza) {
        const limpeza = limpezasAtivas.find(l => l.id == idLimpeza);

        if (!limpeza) {
            console.warn("⚠ Limpeza não encontrada:", idLimpeza);
            return;
        }

        // ✅ SEMPRE redefine a limpeza selecionada
        limpezaSelecionada = limpeza;

        console.log("🔍 Abrindo popup para limpeza:", limpezaSelecionada);

        ocultarPaginaPrincipal(); // 👈 AQUI
        mostrar(DOM.popupFinalizar);
        DOM.inputCartaoFinalizar.value = "";
        DOM.inputCartaoFinalizar.focus();
    }

    // 👉 Fechar popup do cartão
    DOM.fecharFinalizar.addEventListener("click", fecharPopupFinalizar);

    function fecharPopupFinalizar() {
        ocultar(DOM.popupFinalizar);
        DOM.inputCartaoFinalizar.value = "";
        DOM.inputCartaoFinalizar.blur();
        mostrarPaginaPrincipal(); // 👈 VOLTA
    }

    // 👉 Técnico bipa o cartão
    DOM.inputCartaoFinalizar.addEventListener("input", confirmarEnf);

    let validandoEnf = false;

    async function confirmarEnf() {
        if (validandoEnf) return;

        // garante apenas números
        DOM.inputCartaoFinalizar.value =
            DOM.inputCartaoFinalizar.value.replace(/\D/g, "");

        const id = DOM.inputCartaoFinalizar.value;

        // aceita somente entre 8 e 10 dígitos
        if (id.length < 8 || id.length > 10) return;

        validandoEnf = true;

        try {
            const resp = await fetch("/verificar_funcionarios", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ id_cartao: id, tipo: "enfermagem" })
            });

            validarJSON(resp);
            const dados = await resp.json();

            if (!dados.sucesso) {
                mostrarMensagem("Técnico não encontrado ou inativo.");
                DOM.inputCartaoFinalizar.value = "";
                DOM.inputCartaoFinalizar.focus();
                return;
            }

            // 💾 Salva o ID do cartão para uso posterior
            localStorage.setItem("ultimoCartaoEnf", id);

            abrirConfirmacao(dados.nome, id);

        } catch (erro) {
            console.error("Erro ao verificar técnico:", erro);
            mostrarMensagem("Erro ao verificar técnico.");
        } finally {
            validandoEnf = false;
        }
    }


    function abrirConfirmacao(nomeEnf, idCartao) {
        ocultar(DOM.popupFinalizar);
        DOM.inputCartaoFinalizar.value = "";

        if (!limpezaSelecionada) {
            console.warn("⚠ Nenhuma limpeza selecionada ao abrir confirmação");
            return;
        }

        DOM.mensagemConfirmacao.innerHTML = `
            <span class="highlight">${nomeEnf}</span> confirma a finalização da limpeza
            <span class="highlight">${limpezaSelecionada.tipo_limpeza}</span> do Leito
            <span class="highlight">${limpezaSelecionada.numero_leito}</span>
            realizada por <span class="highlight">${limpezaSelecionada.funcionario_asg}</span>?
        `;

        mostrar(DOM.popupConfirmacao);

        // Reseta o botão de confirmação
        DOM.confirmarBtn.disabled = false;
        DOM.confirmarBtn.textContent = "Confirmar";
    }

    // ✅ Envia finalização da limpeza para o backend
    async function registrarFinalizacao(idLimpeza, enfNome, idCartaoEnf, tempoTotalSeconds) {
        const minutos = Math.floor(tempoTotalSeconds / 60);
        const segundosRestantes = tempoTotalSeconds % 60;
        const tempoFormatado =
            `${minutos.toString().padStart(2, "0")}:${segundosRestantes.toString().padStart(2, "0")}`;

        const dados = {
            id_limpeza: Number(idLimpeza),
            id_cartao_enf: idCartaoEnf,
            funcionario_enf: enfNome,
            tempo_total_seconds: tempoTotalSeconds,
            tempo_total_text: tempoFormatado
        };

        console.log("📤 Enviando finalização da limpeza:", dados);

        try {
            const response = await fetch("/registrar_limpeza", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(dados)
            });

            const resultado = await response.json();

            if (!response.ok) {
                throw new Error(resultado.erro || `Erro HTTP: ${response.status}`);
            }

            console.log("✅ Limpeza finalizada com sucesso:", resultado);
            return resultado;

        } catch (erro) {
            console.error("❌ Erro ao registrar finalização:", erro);
            throw erro;
        }
    }

    /* =========================
       CONCLUSÃO
    ========================= */
    function mostrarConclusao(enfermagem, tempoTotalSeconds, idFinalizado) {
        limpezaSelecionada = null;

        // 🔒 Esconde a página principal enquanto o banner estiver ativo
        ocultarPaginaPrincipal();

        // Remove banner anterior se existir
        document.getElementById("bannerConclusao")?.remove();

        const banner = document.createElement("div");
        banner.id = "bannerConclusao";
        banner.className = "banner-conclusao";

        banner.innerHTML = `
            <div class="banner-conteudo">
                <p class="icone">✅</p>
                <p class="titulo">Limpeza concluída</p>
                <p>Confirmada por ${enfermagem}</p>
                <p class="tempo">🕒 ${formatarTempo(tempoTotalSeconds)}</p>
            </div>
        `;

        document.body.appendChild(banner);
        requestAnimationFrame(() => banner.classList.add("ativo"));

        setTimeout(() => {
            banner.classList.remove("ativo");

            setTimeout(() => {
                banner.remove();

                // 👉 SE AINDA EXISTE OUTRA LIMPEZA
                if (limpezasAtivas.length > 0) {
                    mostrarPaginaPrincipal(); // 👈 agora sim mostra
                    return;
                }

                // 👉 SE NÃO EXISTE MAIS NENHUMA
                window.location.href = "/tablet";

            }, 400);

        }, 3500);
    }


    /* =========================
       HELPERS
    ========================= */
    function ocultarPaginaPrincipal() {
        document.getElementById("containerLimpezas")?.classList.add("oculto");
        btnNovaLimpeza?.classList.add("oculto");
    }

    function mostrarPaginaPrincipal() {
        document.getElementById("containerLimpezas")?.classList.remove("oculto");
        btnNovaLimpeza?.classList.remove("oculto");
    }



    function mostrar(el) { el?.classList.remove("oculto"); }
    function ocultar(el) { el?.classList.add("oculto"); }

    function validarJSON(response) {
        const type = response.headers.get("content-type");
        if (!type?.includes("application/json")) {
            throw new Error("Resposta inválida do servidor");
        }
    }

    function aplicarEstilo() {
        document.head.insertAdjacentHTML("beforeend", `
            <style>
                .highlight {
                    font-weight: bold;
                    color: #0069d9;
                    background: #e7f1ff;
                    padding: 2px 6px;
                    border-radius: 4px;
                }
                #confirmarInicio:disabled {
                    opacity: 0.6;
                    cursor: not-allowed;
                }
            </style>
        `);
    }




    /* =========================
    RENDERIZAÇÃO
    ========================= */
    function renderizarLimpezas(limpezas) {
        console.log("Limpezas recebidas para renderizar:", limpezas);
        // ou melhor ainda:
        limpezas.forEach(l => {
            console.log(`ID ${l.id} → status: ${l.status}`);
        });
        const container = document.getElementById("containerLimpezas");
        container.innerHTML = "";

        limpezas.forEach(l => {
            const card = document.createElement("div");
            card.className = "card-limpeza";
            card.dataset.id = l.id;

            card.innerHTML = `
                <p><span class="titulo">Setor:</span> <span class="valor">${l.setor}</span></p>
                <p><span class="titulo">Leito:</span> <span class="valor">${l.numero_leito}</span></p>
                <p><span class="titulo">Tipo:</span> <span class="valor">${l.tipo_limpeza}</span></p>

                <div class="tempo" id="tempo-${l.id}">00:00</div>

                <div class="acoes"></div>
            `;

            container.appendChild(card);

            iniciarCronometro(l.id, l.data_inicio);

            const acoes = card.querySelector(".acoes");

            // 🔁 Decide o que renderizar baseado no status
            if (l.status === "AGUARDANDO_VALIDACAO") {
                renderizarAguardandoUI(acoes, l.id);
            } else {
                renderizarBotaoFinalizarUI(acoes, l.id);
            }

            // Define como selecionada se for a única
            if (limpezas.length === 1) {
                limpezaSelecionada = l;
            }
        });

        // Delegação de eventos
        container.onclick = (e) => {
            if (e.target.classList.contains("btn-finalizar")) {
                const id = e.target.dataset.id;
                colocarEmAguardandoValidacao(id); // 💾 backend + UI
            }

            if (e.target.classList.contains("btn-validar")) {
                const id = e.target.dataset.id;
                abrirPopupFinalizar(id);
            }
        };
    }

    async function colocarEmAguardandoValidacao(idLimpeza) {
        try {
            await fetch("/limpeza/aguardando_validacao", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ id_limpeza: idLimpeza })
            });

            const card = document.querySelector(`.card-limpeza[data-id="${idLimpeza}"]`);
            const limpeza = limpezasAtivas.find(l => l.id == idLimpeza);
            if (!card || !limpeza) return;

            limpeza.status = "AGUARDANDO_VALIDACAO";

            card.querySelector(".btn-finalizar")?.remove();

            // evita duplicar UI
            card.querySelector(".aguardando-validacao")?.remove();

            const aguardando = document.createElement("div");
            aguardando.className = "aguardando-validacao";
            aguardando.innerHTML = `
                <div class="spinner"></div>
                <p>Aguardando Validação</p>
                <button class="btn-validar" data-id="${idLimpeza}">
                    Validar Limpeza
                </button>
            `;

            card.appendChild(aguardando);

        } catch (e) {
            console.error("Erro ao colocar em aguardando validação", e);
            alert("Erro ao atualizar status da limpeza.");
        }
    }


    function renderizarBotaoFinalizarUI(container, id) {
        container.innerHTML = `
            <button class="btn-finalizar" data-id="${id}">
                Finalizar
            </button>
        `;
    }

    function renderizarAguardandoUI(container, id) {
        container.innerHTML = `
            <div class="aguardando-validacao">
                <div class="spinner"></div>
                <p>Aguardando Validação</p>
                <button class="btn-validar" data-id="${id}">
                    Validar Limpeza
                </button>
            </div>
        `;
    }




    function atualizarBotoesLimpeza() {
        if (limpezasAtivas.length === 1) {
            btnNovaLimpeza.classList.remove("hidden");
        } else {
            btnNovaLimpeza.classList.add("hidden");
        }
    }

    function removerLimpezaDaTela(idLimpeza) {
        // Remove do DOM
        document.querySelector(`.card-limpeza[data-id="${idLimpeza}"]`)?.remove();

        // Para cronômetro
        if (cronometros.has(idLimpeza)) {
            clearInterval(cronometros.get(idLimpeza));
            cronometros.delete(idLimpeza);
        }

        // Remove do array
        limpezasAtivas = limpezasAtivas.filter(l => l.id != idLimpeza);

        // Atualiza visibilidade do botão
        atualizarBotoesLimpeza();
    }
})();
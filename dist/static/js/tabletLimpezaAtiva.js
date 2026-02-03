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
    btnNovaLimpeza.addEventListener("click", () => window.location.href = "/tablet_setores");

    async function init() {
        aplicarEstilo();
        bindEventos();
        await carregarLimpezaAtiva();
    }

    /* =========================
    EVENTOS GLOBAIS E MENSAGENS
    ========================= */
    // Adiciona o evento de clique no botão cancelar
    DOM.cancelarBtn?.addEventListener("click", cancelarFinalizacao);

    function cancelarFinalizacao() {
        console.log("❌ Finalização cancelada");
        ocultar(DOM.popupConfirmacao);
        
        // Volta para o popup de cartão
        setTimeout(() => {
            mostrar(DOM.popupFinalizar);
            DOM.inputCartaoFinalizar.value = "";
            DOM.inputCartaoFinalizar.focus();
        }, 100);
    }

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
            const tecnicoMatch = mensagemHTML.match(/<span[^>]*>([^<]+)<\/span>/g);
            const tecnicoNome = tecnicoMatch ? tecnicoMatch[0].replace(/<\/?span[^>]*>/g, '') : "Técnico";
            
            // Busca ID do cartão do localStorage ou usa valor do input
            const idCartaoTecnico = localStorage.getItem('ultimoCartaoTecnico') || 
                                   DOM.inputCartaoFinalizar?.value || "";

            console.log("🔍 Finalizando limpeza:", {
                id: limpezaSelecionada.id,
                tecnico: tecnicoNome,
                cartao: idCartaoTecnico
            });

            await registrarFinalizacao(
                limpezaSelecionada.id,
                tecnicoNome,
                idCartaoTecnico,
                tempoTotalSeconds
            );

            removerLimpezaDaTela(limpezaSelecionada.id);
            mostrarConclusao(tecnicoNome, tempoTotalSeconds, limpezaSelecionada.id);

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
            window.location.href = "/tablet_setores";
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
        const seg = Math.floor((Date.now() - inicio) / 1000);
        const el = document.getElementById(`tempo-${id}`);
        if (el) el.textContent = formatarTempo(seg);

        if (limpezaSelecionada?.id == id) {
            segundos = seg;
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
    }

    // 👉 Técnico bipa o cartão
    DOM.inputCartaoFinalizar.addEventListener("input", confirmarTecnico);

    let validandoTecnico = false;

    async function confirmarTecnico() {
        if (validandoTecnico) return;

        const id = DOM.inputCartaoFinalizar.value.trim();
        if (id.length !== 10) return;

        validandoTecnico = true;

        try {
            const resp = await fetch("/verificar_usuario", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ id_cartao: id, tipo: "tecnico" })
            });

            validarJSON(resp);
            const dados = await resp.json();

            if (!dados.sucesso) {
                mostrarMensagem("Técnico não encontrado ou inativo.");
                DOM.inputCartaoFinalizar.value = "";
                DOM.inputCartaoFinalizar.focus();
                return;
            }

            // Salva o ID do cartão para uso posterior
            localStorage.setItem('ultimoCartaoTecnico', id);
            
            abrirConfirmacao(dados.nome, id);

        } catch (erro) {
            console.error("Erro ao verificar técnico:", erro);
            mostrarMensagem("Erro ao verificar técnico.");
        } finally {
            validandoTecnico = false;
        }
    }

    function abrirConfirmacao(nomeTecnico, idCartao) {
        ocultar(DOM.popupFinalizar);
        DOM.inputCartaoFinalizar.value = "";

        if (!limpezaSelecionada) {
            console.warn("⚠ Nenhuma limpeza selecionada ao abrir confirmação");
            return;
        }

        DOM.mensagemConfirmacao.innerHTML = `
            <span class="highlight">${nomeTecnico}</span> confirma a finalização da limpeza
            <span class="highlight">${limpezaSelecionada.tipo_limpeza}</span> do Leito
            <span class="highlight">${limpezaSelecionada.numero_leito}</span>
            realizada por <span class="highlight">${limpezaSelecionada.funcionario_limpeza}</span>?
        `;

        mostrar(DOM.popupConfirmacao);

        // Reseta o botão de confirmação
        DOM.confirmarBtn.disabled = false;
        DOM.confirmarBtn.textContent = "Confirmar";
    }

    // ✅ Envia finalização da limpeza para o backend
    async function registrarFinalizacao(idLimpeza, tecnicoNome, idCartaoTecnico, tempoTotalSeconds) {
        const minutos = Math.floor(tempoTotalSeconds / 60);
        const segundosRestantes = tempoTotalSeconds % 60;
        const tempoFormatado =
            `${minutos.toString().padStart(2, "0")}:${segundosRestantes.toString().padStart(2, "0")}`;

        const dados = {
            id_limpeza: Number(idLimpeza),
            id_cartao_tecnico: idCartaoTecnico,
            funcionario_tecnico: tecnicoNome,
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
    function mostrarConclusao(tecnico, tempoTotalSeconds, idFinalizado) {
        // Remove referência da limpeza selecionada
        limpezaSelecionada = null;

        // Remove banner anterior
        document.getElementById("bannerConclusao")?.remove();

        const banner = document.createElement("div");
        banner.id = "bannerConclusao";
        banner.className = "banner-conclusao";

        banner.innerHTML = `
            <div class="banner-conteudo">
                <p class="icone">✅</p>
                <p class="titulo">Limpeza concluída</p>
                <p>Confirmada por ${tecnico}</p>
                <p class="tempo">🕒 ${formatarTempo(tempoTotalSeconds)}</p>
            </div>
        `;

        document.body.appendChild(banner);
        requestAnimationFrame(() => banner.classList.add("ativo"));

        setTimeout(() => {
            banner.classList.remove("ativo");

            setTimeout(() => {
                banner.remove();

                // 👉 SE AINDA EXISTE LIMPEZA ATIVA, FICA NA TELA
                if (limpezasAtivas.length > 0) {
                    return;
                }

                // 👉 SE NÃO EXISTE MAIS, REDIRECIONA
                window.location.href = "/tablet_setores";

            }, 400);

        }, 3500);
    }

    /* =========================
       HELPERS
    ========================= */
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

                <button class="btn-finalizar" data-id="${l.id}">
                    Finalizar
                </button>
            `;

            container.appendChild(card);

            iniciarCronometro(l.id, l.data_inicio);
            
            // Define como selecionada se for a única
            if (limpezas.length === 1) {
                limpezaSelecionada = l;
            }
        });

        // Botão finalizar (delegação)
        container.addEventListener("click", e => {
            if (e.target.classList.contains("btn-finalizar")) {
                const id = e.target.dataset.id;
                abrirPopupFinalizar(id);
            }
        });
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
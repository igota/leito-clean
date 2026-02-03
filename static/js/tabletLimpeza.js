document.addEventListener("DOMContentLoaded", () => {
    const leito = JSON.parse(localStorage.getItem("leito_selecionado"));
    const titulo = document.getElementById("tituloLeito");
    const paciente = document.getElementById("infoPaciente");
    const iniciarBtn = document.getElementById("iniciarLimpezaBtn");

    const popupIdcartao = document.getElementById("popupIdcartao");
    const popupTipo = document.getElementById("popupTipo");
    const popupTerminal = document.getElementById("popupTerminal");
    const idcartaoInput = document.getElementById("idcartaoInput");
    const voltarBtn = document.getElementById("voltarBtn");

    const popupConfirmacao = document.getElementById("popupConfirmacao");
    const mensagemConfirmacao = document.getElementById("mensagemConfirmacao");
    const confirmarInicio = document.getElementById("confirmarInicio");
    const cancelarInicio = document.getElementById("cancelarInicio");

  
    
    

    // CSS sugerido (adicione no seu stylesheet)
    const estiloDestaque = `
        .highlight { 
            font-weight: bold; 
            color: #0069d9; 
            background: #e7f1ff; 
            padding: 2px 6px; 
            border-radius: 4px; 
        }
    `;


    let funcionarioASG = null;
    let idcartaoFuncionario = null; // será enviada como id_cartao_asg
    let tipoSelecionado = null;
    

    function abrirPopupIdCartao() {
        const popup = document.getElementById('popupIdcartao');
        const input = document.getElementById('idcartaoInput');

        popup.classList.remove('oculto');

        input.value = "";          // Limpa o campo
        input.focus();             // Foca normalmente (cursor aparece, teclado NÃO)
        input.scrollIntoView({ behavior: 'smooth', block: 'center' });
    }

   

    
    function mostrarMensagem(texto, callback = null) {
        const popup = document.getElementById("popupMensagem");
        const msg = document.getElementById("mensagemTexto");
        const btn = document.getElementById("fecharMensagemBtn");

        msg.textContent = texto;
        popup.classList.remove("oculto");

        btn.onclick = () => {
            popup.classList.add("oculto");
            if (callback) callback(); // executa algo depois de fechar
        };
    }


    if (leito) {
        titulo.textContent = `Leito ${leito.numero_leito}`;
        paciente.innerHTML = leito.paciente 
        ? `<strong>Paciente:</strong> ${leito.paciente}` 
        : "Sem paciente";
    }



    // 👉 Mostra popup da idcartao (COM VERIFICAÇÃO)
    iniciarBtn.addEventListener("click", async () => {
        // ✅ PRIMEIRO verifica se já existe limpeza em andamento
        try {
            console.log("🔍 Verificando se existe limpeza ativa...");
            
            const resposta = await fetch("/verificar_limpeza_ativa", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    leito: leito,
                    funcionario_asg: funcionarioASG
                })
            });

            const dados = await resposta.json();

            if (!resposta.ok) {
                throw new Error(dados.erro || "Erro ao verificar limpeza ativa");
            }

            if (dados.limpeza_ativa) {
                // ❌ BARRAR - Já existe limpeza em andamento
                console.log("⚠️ " + dados.mensagem);
                mostrarMensagem(`❌ ${dados.mensagem}\n\nAguarde a conclusão da limpeza atual.`, () => {
  
        });

                return;
            }

            // ✅ PERMITIR - Pode iniciar nova limpeza
            console.log("✅ " + dados.mensagem);
            popupIdcartao.classList.remove("oculto");
            idcartaoInput.value = "";
            idcartaoInput.focus();
            abrirPopupIdCartao();

        } catch (erro) {
            console.error("❌ Erro ao verificar limpeza ativa:", erro);
            alert("Erro ao verificar status do leito. Tente novamente.");
        }
    });
        
    // 👉 Quando bipar cartão do funcionário limpeza (ASG)
let timerLeitorASG = null;
let validandoASG = false;

idcartaoInput.addEventListener("input", function () {
    if (validandoASG) return;

    let valor = this.value.replace(/\D/g, "");
    this.value = valor;

    // cancela tentativa anterior
    clearTimeout(timerLeitorASG);

    // espera o leitor terminar
    timerLeitorASG = setTimeout(() => {
        if (valor.length < 9 || valor.length > 10) return;
        validarCartaoASG(valor);
    }, 120);
});

async function validarCartaoASG(id_cartao_enviado) {
    validandoASG = true;

    console.log("[DEBUG] Tentando buscar → ID enviado:", id_cartao_enviado);

    try {
        const resposta = await fetch("/verificar_funcionarios", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ id_cartao: id_cartao_enviado, tipo: "asg" })
        });

        if (!resposta.ok) {
            throw new Error(`HTTP ${resposta.status}`);
        }

        const dados = await resposta.json();

        if (!dados.sucesso) {
            mostrarMensagem("Funcionário não encontrado ou inativo.", () => {
                idcartaoInput.value = "";
                idcartaoInput.focus();
            });
            return;
        }

        // Funcionário identificado
        funcionarioASG = dados.nome;
        idcartaoFuncionario = id_cartao_enviado;

        // Verifica se já tem limpeza ativa
        const resLimpeza = await fetch("/verificar_limpeza_funcionario", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ funcionario_asg: funcionarioASG })
        });

        const verif = await resLimpeza.json();

        if (verif.existe) {
            mostrarMensagem(
                `❌ ${verif.mensagem}\n\n` +
                `Setor: ${verif.limpeza.setor}\n` +
                `Leito: ${verif.limpeza.numero_leito}`,
                () => {
                    idcartaoInput.value = "";
                    idcartaoInput.focus();
                }
            );
            return;
        }

        // Tudo ok → prossegue
        popupIdcartao.classList.add("oculto");
        popupTipo.classList.remove("oculto");

    } catch (erro) {
        console.error("Erro ao processar cartão:", erro);
        mostrarMensagem(
            "Erro de comunicação com o servidor. Tente novamente.",
            () => {
                idcartaoInput.value = "";
                idcartaoInput.focus();
            }
        );
    } finally {
        validandoASG = false;
    }
}



    

    // 👉 Fechar popups
    document.getElementById("fecharIdcartao").addEventListener("click", () => popupIdcartao.classList.add("oculto"));
    document.getElementById("fecharTipo").addEventListener("click", () => popupTipo.classList.add("oculto"));
    
    document.getElementById("fecharTerminal").addEventListener("click", () => {popupTerminal.classList.add("oculto");});

    // 👉 Escolha do tipo de limpeza (abre confirmação)
    document.querySelectorAll(".tipoBtn").forEach(btn => {
        btn.addEventListener("click", () => {
            tipoSelecionado = btn.dataset.tipo;

            popupTipo.classList.add("oculto");

            // Se for Terminal, abre o segundo popup
            if (tipoSelecionado === "Terminal") {
                popupTerminal.classList.remove("oculto");
                return;
            }

            
            mensagemConfirmacao.innerHTML = `
                <span class="highlight">${funcionarioASG}</span> confirma o início da limpeza
                <span class="highlight">${tipoSelecionado}</span> do Leito
                <span class="highlight">${leito.numero_leito}</span>?
            `;    

            popupConfirmacao.classList.remove("oculto");
        });
    });

    // ✅ Confirmar início da limpeza
    confirmarInicio.addEventListener("click", async () => {
        popupConfirmacao.classList.add("oculto");
        popupTerminal.classList.add("oculto");
        await registrarInicioLimpeza(); // grava no banco
       // 👉 redireciona para a página correta
        window.location.href = "/tablet_limpeza_ativa";
    });




    // ❌ Cancelar início
    cancelarInicio.addEventListener("click", () => {
        popupConfirmacao.classList.add("oculto");
    });

    voltarBtn.addEventListener("click", () => window.location.href = "/tablet_leitos");

    // No <head> ou em arquivo CSS:
    document.head.insertAdjacentHTML("beforeend", `<style>${estiloDestaque}</style>`);

    

    // ✅ Envia início da limpeza para o backend
    async function registrarInicioLimpeza() {
        const agora = new Date();
        

        const dados = {
            id_cartao_asg: idcartaoFuncionario,
            funcionario_asg: funcionarioASG,
            leito: leito, // ✅ Garantir que o objeto leito completo seja enviado
            tipo_limpeza: tipoSelecionado,
            
        };

    console.log("📤 Enviando início da limpeza:", dados);

    try {
        const response = await fetch("/registrar_limpeza", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(dados)
        });

        if (!response.ok) {
            throw new Error(`Erro HTTP: ${response.status}`);
        }

        const resultado = await response.json();
        console.log("✅ Resposta do servidor:", resultado);

        } catch (erro) {
        console.error("❌ Erro ao registrar início:", erro);
        alert("Erro ao registrar início da limpeza. Tente novamente.");
        }
    }

   


});

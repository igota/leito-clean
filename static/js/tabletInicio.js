document.addEventListener("DOMContentLoaded", async () => {
    const loading = document.getElementById("loading");
    const resultado = document.getElementById("resultado");
    const banner = document.getElementById("bannerLimpezaAtiva");
    const bannerTexto = document.getElementById("bannerTexto");
    const voltarLimpezaBtn = document.getElementById("voltarLimpezaBtn");

    // ===============================
    // 🔹 PARTE 1 — CARREGAR LEITOS
    // ===============================
    const carregarBtn = document.getElementById("carregarBtn");
    // Função auxiliar para delay
    const delay = (ms) => new Promise(resolve => setTimeout(resolve, ms));

    if (carregarBtn) {
        carregarBtn.addEventListener("click", async () => {

            // 🔼 Sobe o botão
            carregarBtn.classList.add("subindo");

            // ⏳ Pequeno delay para o efeito ser perceptível
            await new Promise(r => setTimeout(r, 100));

            // 🔄 Mostra o loading
            loading.classList.remove("hidden");
            loading.classList.add("fade-in");

            // ⏳ Aguarda 3 segundos (como você pediu antes)
            await new Promise(r => setTimeout(r, 2000));

            try {
                const resp = await fetch("/carregar_leitos");
                const data = await resp.json();

                loading.classList.add("fade-out");
                setTimeout(() => loading.classList.add("hidden"), 400);

                if (data.status === "ok") {
                    localStorage.setItem("setores", JSON.stringify(data.setores));
                    window.location.href = "/tablet_setores";
                } else {
                    resultado.innerHTML = `<p style="color:red;">❌ ${data.mensagem}</p>`;
                }
            } catch (err) {
                loading.classList.add("fade-out");
                setTimeout(() => loading.classList.add("hidden"), 400);
                resultado.innerHTML = `<p style="color:red;">❌ Erro: ${err.message}</p>`;
            }
        });
    }


    // 🔹 Parte banner limpeza ativa
    try {
        const response = await fetch("/limpeza_ativa_por_ip");
        const data = await response.json();

        if (data.existe && data.limpezas.length > 0) {

            const textos = data.limpezas.map(l =>
                `Setor ${l.setor} • Leito ${l.numero_leito}`
            );

            bannerTexto.innerHTML = textos.join(" | ");
            banner.classList.remove("oculto");

            // 🔹 Adiciona classe para mover botão e loading
            document.body.classList.add("banner-visivel");

            const irParaLimpeza = () => {
                window.location.href = "/tablet_limpeza_ativa";
            };

            voltarLimpezaBtn.onclick = irParaLimpeza;
            banner.onclick = irParaLimpeza;
        }

    } catch (error) {
        console.error("❌ Erro ao verificar limpeza ativa:", error);
    }


    
});

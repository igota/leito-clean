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
    if (carregarBtn) {
        carregarBtn.addEventListener("click", async () => {
            resultado.innerText = "";
            loading.classList.remove("hidden");
            loading.classList.add("fade-in");

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

    // ===============================
    // 🔹 PARTE 2 — LIMPEZA EM ANDAMENTO
    // ===============================
    try {
        const response = await fetch("/limpeza_ativa_por_ip");
        const data = await response.json();

        if (data.existe && data.limpezas.length > 0) {
            const textos = data.limpezas.map(l => 
                `Setor: <strong>${l.setor}</strong> - Leito: <strong>${l.numero_leito}</strong>`
            );
            bannerTexto.innerHTML = textos.join("<br>");
            banner.classList.remove("oculto");

            // Clicar no banner ou no botão leva para tela de limpeza ativa
            banner.onclick = voltarLimpezaBtn.onclick = () => {
                window.location.href = "/tablet_limpeza_ativa";
            };
        }
    } catch (error) {
        console.error("❌ Erro ao verificar limpeza ativa:", error);
    }

    
});

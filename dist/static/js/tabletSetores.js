document.addEventListener("DOMContentLoaded", async () => {
    const setoresContainer = document.getElementById("setoresContainer");
    const setoresRaw = localStorage.getItem("setores");

    const banner = document.getElementById("bannerLimpezaAtiva");
    const bannerTexto = document.getElementById("bannerTexto");
    const voltarLimpezaBtn = document.getElementById("voltarLimpezaBtn");

    // 🔹 Parte setores
    if (!setoresRaw) {
        setoresContainer.innerHTML = "<p style='color:red;'>Nenhum setor encontrado.</p>";
        return;
    }

    const setores = JSON.parse(setoresRaw);
    if (setores.length === 0) {
        setoresContainer.innerHTML = "<p style='color:red;'>Nenhum setor disponível.</p>";
        return;
    }

    setores.forEach(setor => {
        const btn = document.createElement("button");
        btn.className = "btnSetor";
        btn.textContent = setor;
        btn.onclick = () => {
            localStorage.setItem("setor_selecionado", setor);
            window.location.href = "/tablet_leitos";
        };
        setoresContainer.appendChild(btn);
    });

    // 🔹 Parte banner limpeza ativa
    try {
        const response = await fetch("/limpeza_ativa_por_ip");
        const data = await response.json();

        if (data.existe && data.limpezas.length > 0) {
            // Mostrar informações resumidas no banner
            const textos = data.limpezas.map(l => `Setor: <strong>${l.setor}</strong> - Leito: <strong>${l.numero_leito}</strong>`);

            bannerTexto.innerHTML = textos.join("<br>");
            banner.classList.remove("oculto");

            // Clicar no banner leva para a tela de limpeza ativa
            voltarLimpezaBtn.onclick = () => window.location.href = "/tablet_limpeza_ativa";
            banner.onclick = () => window.location.href = "/tablet_limpeza_ativa";
        }

    } catch (error) {
        console.error("❌ Erro ao verificar limpeza ativa:", error);
    }
});

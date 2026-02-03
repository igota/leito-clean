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

            const textos = data.limpezas.map(l =>
                `Setor ${l.setor} • Leito ${l.numero_leito}`
            );

            bannerTexto.innerHTML = textos.join(" | ");
            banner.classList.remove("oculto");

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

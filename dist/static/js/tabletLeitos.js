document.addEventListener("DOMContentLoaded", async () => {
    const setor = localStorage.getItem("setor_selecionado");
    const titulo = document.getElementById("tituloSetor");
    const container = document.getElementById("leitosContainer");

    const LEITOS_POR_PAGINA = 10;
    let paginaAtual = 1;
    let leitos = [];

    let touchStartX = 0;
    let touchEndX = 0;

    if (!setor) {
        container.innerHTML = "<p style='color:red;'>Setor não encontrado!</p>";
        return;
    }

    titulo.textContent = `Leitos - ${setor}`;

    try {
        const response = await fetch(`/get_leitos_por_setor?setor=${encodeURIComponent(setor)}`);
        const data = await response.json();

        if (data.status !== "ok") {
            container.innerHTML = `<p style='color:red;'>${data.mensagem}</p>`;
            return;
        }

        leitos = data.leitos;

        if (leitos.length === 0) {
            container.innerHTML = "<p>Nenhum leito encontrado neste setor.</p>";
            return;
        }

        renderizarPagina();

    } catch (err) {
        container.innerHTML = `<p style='color:red;'>Erro ao carregar leitos: ${err.message}</p>`;
    }

    /* =======================
       SWIPE
    ======================= */
    container.addEventListener("touchstart", e => {
        touchStartX = e.changedTouches[0].screenX;
    });

    container.addEventListener("touchend", e => {
        touchEndX = e.changedTouches[0].screenX;
        detectarSwipe();
    });

    function detectarSwipe() {
        const distancia = touchStartX - touchEndX;
        const LIMIAR = 50; // px

        const totalPaginas = Math.ceil(leitos.length / LEITOS_POR_PAGINA);

        if (distancia > LIMIAR && paginaAtual < totalPaginas) {
            paginaAtual++;
            animarTroca("esquerda");
            renderizarPagina();
        }

        if (distancia < -LIMIAR && paginaAtual > 1) {
            paginaAtual--;
            animarTroca("direita");
            renderizarPagina();
        }
    }

    /* =======================
       RENDER
    ======================= */
    function renderizarPagina() {
        container.innerHTML = "";

        const inicio = (paginaAtual - 1) * LEITOS_POR_PAGINA;
        const fim = inicio + LEITOS_POR_PAGINA;

        leitos.slice(inicio, fim).forEach(leito => {
            const div = document.createElement("div");
            div.className = `leito-item ${leito.status}`;

            div.innerHTML = `
                <div class="icone-leito ${leito.icone}">
                    <span>${leito.numero_leito}</span>
                </div>
            `;

            div.addEventListener("click", () => {
                localStorage.setItem("leito_selecionado", JSON.stringify(leito));
                window.location.href = "/tablet_limpeza";
            });

            container.appendChild(div);
        });
    }

    /* =======================
       ANIMAÇÃO
    ======================= */
    function animarTroca(direcao) {
        container.style.transition = "transform 0.25s ease";
        container.style.transform =
            direcao === "esquerda" ? "translateX(-30px)" : "translateX(30px)";

        setTimeout(() => {
            container.style.transform = "translateX(0)";
        }, 250);
    }
});

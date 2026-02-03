// Remove as funções alternarMenu(), abrirMenu() e fecharMenu()
// Mantém apenas a função novoCronograma() se ainda for necessária

document.addEventListener("DOMContentLoaded", function () {
    const trigger = document.getElementById("userMenuTrigger");
    const dropdown = document.getElementById("userDropdown");

    if (!trigger || !dropdown) return;

    trigger.addEventListener("click", function (e) {
        e.stopPropagation();

        dropdown.classList.toggle("show");
        trigger.classList.toggle("active"); // 👈 ativa rotação
    });

    document.addEventListener("click", function () {
        dropdown.classList.remove("show");
        trigger.classList.remove("active"); // 👈 reseta rotação
    });
});



function novoCronograma() {
    const botao = document.getElementById("botaoNovo");

    // Array de mensagens e ícones
    const mensagens = [
        { texto: "Acessando Vitae...", icone: "fas fa-truck-medical" },
        { texto: "Buscando Dados...", icone: "fas fa-database" },
        { texto: "Carregando...", icone: "fas fa-spinner fa-spin" }
    ];

    let index = 0;

    // Função para alternar mensagens e ícones
    const alternarMensagens = () => {
        botao.innerHTML = `<i class="${mensagens[index].icone}"></i> ${mensagens[index].texto}`;
        index = (index + 1) % mensagens.length;
    };

    // Inicia a alternância de mensagens e ícones imediatamente
    alternarMensagens();

    // Inicia a alternância de mensagens e ícones a cada 1 segundo
    const intervalo = setInterval(alternarMensagens, 2000);

    // Desabilita o botão para evitar múltiplos cliques
    botao.disabled = true;

    // Cria um formulário dinâmico para enviar a requisição POST
    const form = document.createElement('form');
    form.method = 'POST';
    form.action = '/pagina_principal';

    // Adiciona o formulário ao corpo do documento e o submete
    document.body.appendChild(form);
    form.submit();
}



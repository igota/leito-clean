function traduzirTipo(tipo) {
    if (tipo === "limpeza") return "Limpeza";
    if (tipo === "tecnico") return "Técnico de Enfermagem";
    return tipo;
}

async function carregarUsuarios(filtros = {}) {
    const response = await fetch("/consultar_usuarios", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(filtros)
    });
    const data = await response.json();
    const tbody = document.querySelector("#tabelaUsuarios tbody");
    tbody.innerHTML = "";

    if (data.usuarios && data.usuarios.length > 0) {
        data.usuarios.forEach(u => {
            const linha = `
                <tr>
                   
                    <td>${u.nome}</td>
                    <td>${u.cpf || "-"}</td>
                    <td>${u.id_cartao || "-"}</td>
                    <td>${traduzirTipo(u.tipo)}</td>
                    <td>${u.situacao ? "Ativo" : "Inativo"}</td>
                    <td class="text-center">
                        <button class="btn btn-sm btn-outline-primary" onclick='abrirModalEditar(${JSON.stringify(u)})'>
                            <i class="bi bi-pencil"></i>
                        </button>
                    </td>
                </tr>`;
            tbody.insertAdjacentHTML("beforeend", linha);
        });
    } else {
        tbody.innerHTML = `<tr><td colspan="5" class="text-center text-muted">Nenhum usuário encontrado</td></tr>`;
    }
}


function limparConsulta() {
    // Limpa os campos de filtro
    document.getElementById("nomeBusca").value = "";
    document.getElementById("idCartaoBusca").value = "";
    document.getElementById("tipoBusca").value = "";

    // Limpa os dados exibidos na tabela
    const tabela = document.getElementById("tabelaUsuarios").getElementsByTagName("tbody")[0];
    tabela.innerHTML = "";

    // Opcional: exibe uma mensagem visual que a consulta foi limpa
    const tr = document.createElement("tr");
    const td = document.createElement("td");
    td.colSpan = 5;
    td.className = "text-center text-muted";
    td.textContent = "Nenhum resultado exibido.";
    tr.appendChild(td);
    tabela.appendChild(tr);
}




// 🔎 Evento de busca
document.getElementById("formBusca").addEventListener("submit", e => {
    e.preventDefault();
    const filtros = {
        nome: document.getElementById("nomeBusca").value.trim(),
        id_cartao: document.getElementById("idCartaoBusca").value.trim(),
        tipo: document.getElementById("tipoBusca").value.trim()
    };
    carregarUsuarios(filtros);
});

// 🖊 Abre o modal e preenche os campos
function abrirModalEditar(usuario) {
    document.getElementById("editId").value = usuario.id;
    document.getElementById("editNome").value = usuario.nome;
    document.getElementById("editCpf").value = usuario.cpf || "";
    document.getElementById("editIdcartao").value = usuario.id_cartao || "";
    document.getElementById("editTipo").value = usuario.tipo;
    document.querySelector(`input[name='editAtivo'][value='${usuario.situacao}']`).checked = true;

    const modal = new bootstrap.Modal(document.getElementById("modalEditar"));
    modal.show();
}


// ✅ Função para validar CPF
function validarCPF(cpf) {
    cpf = cpf.replace(/[^\d]+/g, '');
    if (cpf.length !== 11 || /^(\d)\1{10}$/.test(cpf)) return false;

    let soma = 0;
    for (let i = 1; i <= 9; i++) soma += parseInt(cpf[i - 1]) * (11 - i);
    let resto = (soma * 10) % 11;
    if (resto === 10 || resto === 11) resto = 0;
    if (resto !== parseInt(cpf[9])) return false;

    soma = 0;
    for (let i = 1; i <= 10; i++) soma += parseInt(cpf[i - 1]) * (12 - i);
    resto = (soma * 10) % 11;
    if (resto === 10 || resto === 11) resto = 0;
    return resto === parseInt(cpf[10]);
}

// 💾 Salvar novo usuário
async function salvarUsuario(event) {
    event.preventDefault();
    const nome = document.getElementById("nome").value.trim();
    const cpf = document.getElementById("cpf").value.trim();
    const id_cartao = document.getElementById("id_cartao").value.trim();
    const tipo = document.getElementById("tipo").value;

    // 👉 Validação básica dos campos obrigatórios
    if (!nome || !cpf || !id_cartao || !tipo) {
        alert("⚠️ Preencha todos os campos obrigatórios antes de salvar.");
        return;
    }

    //👉 Validação do formato de CPF
    if (!validarCPF(cpf)) {
      alert("⚠️ CPF inválido! Verifique e tente novamente.");
       return;
    }

    // 👉 Se tudo estiver OK, prossegue com o envio
    const dados = { nome, cpf, id_cartao, tipo };

    try {
        const response = await fetch("/cadastrar_usuario", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(dados)
        });

        const data = await response.json();

        if (data.mensagem) {
            alert(data.mensagem);
            document.getElementById("formCadastro").reset();
            const modal = bootstrap.Modal.getInstance(document.getElementById("modalCadastro"));
            modal.hide();
            carregarUsuarios();
        } else {
            alert("Erro: " + (data.erro || "Falha ao cadastrar"));
        }
    } catch (erro) {
        console.error("Erro ao cadastrar usuário:", erro);
        alert("❌ Erro ao conectar ao servidor. Tente novamente.");
    }
}




function mostrarAlerta(mensagem) {
    const alertBox = document.getElementById("alertContainer");
    alertBox.textContent = mensagem;
    alertBox.style.display = "block";

    // Oculta após 4 segundos
    setTimeout(() => {
        alertBox.style.display = "none";
    }, 4000);
}

function mostrarAlertaSucesso(mensagem) {
    const toastEl = document.createElement("div");
    toastEl.className = "toast align-items-center text-bg-success border-0 show shadow-lg";
    toastEl.role = "alert";
    toastEl.ariaLive = "assertive";
    toastEl.ariaAtomic = "true";
    toastEl.innerHTML = `
        <div class="d-flex">
            <div class="toast-body text-center">
                ✅ ${mensagem}
            </div>
            <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast" aria-label="Close"></button>
        </div>
    `;

    document.getElementById("toastContainer").appendChild(toastEl);
    const toast = new bootstrap.Toast(toastEl, { delay: 1000 });
    toast.show();

    toastEl.addEventListener("hidden.bs.toast", () => toastEl.remove());
}




// 💾 Salva as alterações
async function salvarEdicao() {
    const nome = document.getElementById("editNome");
    const cpf = document.getElementById("editCpf");
    const id_cartao = document.getElementById("editIdcartao");
    const tipo = document.getElementById("editTipo");
    const situacao = document.querySelector('input[name="editAtivo"]:checked');

    // Remove estilos de erro anteriores
    [nome, cpf, id_cartao, tipo].forEach(el => el.classList.remove("is-invalid"));

    // Validação visual com alerta bonito
    if (!nome.value.trim()) {
        nome.classList.add("is-invalid");
        mostrarAlerta("Por favor, preencha o campo Nome.");
        nome.focus();
        return;
    }

    if (!cpf.value.trim()) {
        cpf.classList.add("is-invalid");
        mostrarAlerta("Por favor, preencha o campo CPF.");
        cpf.focus();
        return;
    }

    if (!id_cartao.value.trim()) {
        id_cartao.classList.add("is-invalid");
        mostrarAlerta("Por favor, preencha o campo ID Cartão.");
        id_cartao.focus();
        return;
    }

    if (!tipo.value) {
        tipo.classList.add("is-invalid");
        mostrarAlerta("Por favor, selecione o Tipo.");
        tipo.focus();
        return;
    }

    if (!situacao) {
        mostrarAlerta("Por favor, selecione o Status (Ativo ou Inativo).");
        return;
    }

    const dados = {
        id: document.getElementById("editId").value,
        nome: nome.value.trim(),
        cpf: cpf.value.trim(),
        id_cartao: id_cartao.value.trim(),
        tipo: tipo.value,
        situacao: situacao.value
    };

    try {
        const response = await fetch("/editar_usuario", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(dados)
        });

        const data = await response.json();

        if (data.mensagem) {
            // Fecha o modal
            bootstrap.Modal.getInstance(document.getElementById("modalEditar")).hide();
            // Recarrega a lista de usuários
            carregarUsuarios();
            // Mostra alerta de sucesso ✨
            mostrarAlertaSucesso("Usuário editado com sucesso!");
        } else {
            mostrarAlerta(data.erro || "Falha ao atualizar usuário.");
        }
    } catch (erro) {
        mostrarAlerta("Erro de conexão com o servidor.");
        console.error(erro);
    }
}





// 🔹 Máscara CPF automática e bloqueio de letras
function aplicarMascaraCPF(input) {
  let valor = input.value.replace(/\D/g, ""); // remove tudo que não for número
  if (valor.length > 11) valor = valor.slice(0, 11); // limita a 11 dígitos

  // aplica a máscara
  valor = valor.replace(/(\d{3})(\d)/, "$1.$2");
  valor = valor.replace(/(\d{3})(\d)/, "$1.$2");
  valor = valor.replace(/(\d{3})(\d{1,2})$/, "$1-$2");
  input.value = valor;
}

// 🔹 Permite apenas números e limita a 10 dígitos no id_cartao
function validarid_cartaoNumerica(input) {
  input.value = input.value.replace(/\D/g, ""); // remove não numéricos
  if (input.value.length > 10) {
    input.value = input.value.slice(0, 10);
  }
}

// 🔹 Adiciona eventos quando a página carrega
document.addEventListener("DOMContentLoaded", () => {
  // CPF do cadastro
  const cpfCadastro = document.getElementById("cpf");
  cpfCadastro.addEventListener("input", () => aplicarMascaraCPF(cpfCadastro));

  // CPF da edição
  const cpfEdicao = document.getElementById("editCpf");
  cpfEdicao.addEventListener("input", () => aplicarMascaraCPF(cpfEdicao));

  // id_cartao
  const id_cartaoInput = document.getElementById("id_cartao");
  id_cartaoInput.addEventListener("input", () => validarid_cartaoNumerica(id_cartaoInput));

  carregarUsuarios();
});





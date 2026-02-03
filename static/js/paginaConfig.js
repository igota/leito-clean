document.addEventListener("DOMContentLoaded", () => {

    document.querySelectorAll(".btn-editar").forEach(btn => {
        btn.addEventListener("click", () => {

            const id = btn.dataset.id;
            const setor = btn.dataset.setor;
            const ip = btn.dataset.ip;
            const qtdLeitos = btn.dataset.qtdLeitos;
            const situacao = Number(btn.dataset.situacao);

            document.getElementById("editId").value = id;
            document.getElementById("editSetor").value = setor;
            document.getElementById("editIp").value = ip;
            document.getElementById("editQtdLeitos").value = qtdLeitos;
            document.getElementById("editSituacao").checked = situacao === 1;

            const modal = new bootstrap.Modal(
                document.getElementById("modalEditar")
            );
            modal.show();
        });
    });

});

document.addEventListener("DOMContentLoaded", () => {

    document.querySelectorAll(".btn-editar").forEach(btn => {
        btn.addEventListener("click", () => {

            const id = btn.dataset.id;
            const ip = btn.dataset.ip;
            const setor = btn.dataset.setor;
            const ativo = Number(btn.dataset.ativo);

            document.getElementById("editId").value = id;
            document.getElementById("editIp").value = ip;
            document.getElementById("editSetor").value = setor;
            document.getElementById("editAtivo").checked = ativo === 1;

            const modal = new bootstrap.Modal(
                document.getElementById("modalEditar")
            );
            modal.show();
        });
    });

});

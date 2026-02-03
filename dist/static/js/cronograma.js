$(document).ready(function() {
    // Ordenação ao clicar no cabeçalho
    $('th').on('click', function() {
        var index = $(this).index();  // Índice da coluna clicada
        var rows = $('table tbody tr').get();  // Pega todas as linhas da tabela
        var isAscending = $(this).hasClass('asc');  // Verifica se já está ordenado em ordem crescente

        // Alterna entre crescente e decrescente
        if (isAscending) {
            $(this).removeClass('asc').addClass('desc');  // Se já está crescente, muda para decrescente
        } else {
            $(this).removeClass('desc').addClass('asc');  // Se está decrescente, muda para crescente
        }

        // Remove as classes de ordenação das outras colunas
        $('th').not(this).removeClass('asc desc');

        // Ordena as linhas com base no conteúdo da coluna clicada
        rows.sort(function(a, b) {
            var cellA = $(a).children('td').eq(index).text();
            var cellB = $(b).children('td').eq(index).text();

            // Verifica se a célula contém números ou texto
            var isNumeric = !isNaN(cellA) && !isNaN(cellB);
            
            if (isNumeric) {
                cellA = parseFloat(cellA);
                cellB = parseFloat(cellB);
            }

            // Ordenação crescente ou decrescente com base no conteúdo
            if (isAscending) {
                return cellA > cellB ? 1 : (cellA < cellB ? -1 : 0);
            } else {
                return cellA < cellB ? 1 : (cellA > cellB ? -1 : 0);
            }
        });

        // Reorganiza as linhas da tabela
        $.each(rows, function(index, row) {
            $('table').children('tbody').append(row);
        });
    });

    // Desativa a ordenação quando clicar fora da tabela
    $(document).on('click', function(event) {
        if (!$(event.target).closest('table').length) {
            // Remove as classes de ordenação se o clique for fora da tabela
            $('th').removeClass('asc desc');
        }
    });

    document.getElementById('printButton').addEventListener('click', function() {
        var printContents = document.querySelector('.container').outerHTML;
        var printWindow = window.open('', '', 'height=auto, width=auto');
        printWindow.document.write('<html><head><title>Detalhes do Cronograma</title>');
        printWindow.document.write('<link rel="stylesheet" href="/static/css/cronograma.css">');
        printWindow.document.write('</head><body>');
        printWindow.document.write(printContents);
        printWindow.document.write('</body></html>');
        printWindow.document.close();
        printWindow.focus();
    
        // Espera o carregamento do CSS antes de imprimir
        printWindow.onload = function() {
            printWindow.print();
            printWindow.close();
        };
    });

    document.getElementById('exportButton').addEventListener('click', function() {
        var wb = XLSX.utils.table_to_book(document.querySelector('.tabela-consulta'), {
            sheet: "Cronograma",
            raw: true // Isso evita que a biblioteca tente interpretar os valores
        });
        XLSX.writeFile(wb, 'cronograma.xlsx');
    });
});

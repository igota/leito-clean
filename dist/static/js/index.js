// Mostra a tela de carregamento ao enviar o formulário
        function showLoading() {
            document.getElementById('loading').style.visibility = 'visible';
            startDropAnimation();
        }

        
        
        // Alterna a visibilidade da senha
        function togglePassword() {
            const passwordField = document.getElementById('password');
            const passwordButton = document.querySelector('.toggle-password');

            // Defina os SVGs para "olho aberto" e "olho fechado"
            const eyeOpenSVG = `
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                    <path d="M12 4.5C7 4.5 2.73 7.61 1 12C2.73 16.39 7 19.5 12 19.5C17 19.5 21.27 16.39 23 12C21.27 7.61 17 4.5 12 4.5ZM12 17C9.24 17 7 14.76 7 12C7 9.24 9.24 7 12 7C14.76 7 17 9.24 17 12C17 14.76 14.76 17 12 17ZM12 9.5C10.62 9.5 9.5 10.62 9.5 12C9.5 13.38 10.62 14.5 12 14.5C13.38 14.5 14.5 13.38 14.5 12C14.5 10.62 13.38 9.5 12 9.5Z" fill="black"/>
                </svg>`;
            const eyeClosedSVG = `
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                    <path d="M12 4.5C7 4.5 2.73 7.61 1 12C2.73 16.39 7 19.5 12 19.5C17 19.5 21.27 16.39 23 12C21.27 7.61 17 4.5 12 4.5ZM12 17C9.24 17 7 14.76 7 12C7 9.24 9.24 7 12 7C14.76 7 17 9.24 17 12C17 14.76 14.76 17 12 17ZM12 9.5C10.62 9.5 9.5 10.62 9.5 12C9.5 13.38 10.62 14.5 12 14.5C13.38 14.5 14.5 13.38 14.5 12C14.5 10.62 13.38 9.5 12 9.5Z" fill="black"/>
                    <line x1="2" y1="2" x2="22" y2="22" stroke="black" stroke-width="2"/>
                </svg>`;

            // Alterna o tipo do campo e o ícone
            if (passwordField.type === 'password') {
                passwordField.type = 'text';
                passwordButton.innerHTML = eyeOpenSVG; // Ícone de esconder
            } else {
                passwordField.type = 'password';
                passwordButton.innerHTML = eyeClosedSVG; // Ícone de mostrar
            }
        }
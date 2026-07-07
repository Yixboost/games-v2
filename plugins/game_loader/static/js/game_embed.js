        document.getElementById('reloadIcon').addEventListener('click', function () {
            location.reload();
        });

        document.getElementById('expandButton').addEventListener('click', function () {
            var gameIframe = document.querySelector('.game-iframe');

            if (gameIframe.requestFullscreen) {
                gameIframe.requestFullscreen();
            } else if (gameIframe.mozRequestFullScreen) {
                gameIframe.mozRequestFullScreen();
            } else if (gameIframe.webkitRequestFullscreen) {
                gameIframe.webkitRequestFullscreen();
            } else if (gameIframe.msRequestFullscreen) {
                gameIframe.msRequestFullscreen();
            }

        });

        const iframe = document.querySelector('.game-iframe');

        iframe.addEventListener('load', () => {
            iframe.contentWindow.focus();
        });

        iframe.addEventListener('click', () => {
            iframe.contentWindow.focus();
        });
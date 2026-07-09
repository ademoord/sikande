(function () {
  var deferredPrompt = null;
  var installBtn = document.getElementById('pwaInstallBtn');
  var installCard = document.getElementById('pwaInstallCard');
  var installStatus = document.getElementById('pwaInstallStatus');

  function setInstallVisible(show) {
    if (installCard) {
      installCard.hidden = !show;
    }
    if (installBtn) {
      installBtn.hidden = !show;
    }
  }

  function setStatus(text) {
    if (installStatus) {
      installStatus.textContent = text;
    }
  }

  if ('serviceWorker' in navigator) {
    window.addEventListener('load', function () {
      navigator.serviceWorker.register('/sw.js').catch(function () {
        /* registration failed — app still works without PWA */
      });
    });
  }

  window.addEventListener('beforeinstallprompt', function (e) {
    e.preventDefault();
    deferredPrompt = e;
    setInstallVisible(true);
    setStatus('Install Sikande on this device for quick access from your home screen.');
  });

  window.addEventListener('appinstalled', function () {
    deferredPrompt = null;
    setInstallVisible(false);
    setStatus('Sikande is installed on this device.');
  });

  if (window.matchMedia('(display-mode: standalone)').matches || window.navigator.standalone) {
    setInstallVisible(false);
    setStatus('Running as an installed app.');
  }

  window.installSikandePwa = function () {
    if (!deferredPrompt) {
      setStatus('Use your browser menu: Add to Home Screen / Install app.');
      return;
    }
    deferredPrompt.prompt();
    deferredPrompt.userChoice.then(function (choice) {
      if (choice.outcome === 'accepted') {
        setStatus('Installing…');
      }
      deferredPrompt = null;
      setInstallVisible(false);
    });
  };

  if (installBtn) {
    installBtn.addEventListener('click', window.installSikandePwa);
  }
})();

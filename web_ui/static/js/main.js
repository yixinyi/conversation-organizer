const PROJECT_ROOT = document.body.dataset.projectRoot;

function updateFileName(input) {
    const display = document.getElementById('fileNameDisplay');
    if (input.files.length > 0) {
        display.textContent = '📎 ' + input.files[0].name;
    } else {
        display.textContent = 'No file selected';
    }
}

// Auto-populate output directory when provider changes
document.getElementById('provider').addEventListener('change', function() {
    const outputDir = document.getElementById('output_dir');
    const provider = this.value;
    if (provider && PROJECT_ROOT) {
        outputDir.value = PROJECT_ROOT + '/' + provider;
    }
});

// Form submit — disable button to prevent double-submit
document.querySelector('form').addEventListener('submit', function() {
    const btn = document.getElementById('submitBtn');
    btn.disabled = true;
    btn.textContent = '⏳ Converting...';
});

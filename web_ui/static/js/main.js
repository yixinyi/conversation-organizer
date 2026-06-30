function updateFileName(input) {
    const display = document.getElementById('fileNameDisplay');
    if (input.files.length > 0) {
        display.textContent = '📎 ' + input.files[0].name;
    } else {
        display.textContent = 'No file selected';
    }
}

// Form submit — disable button to prevent double-submit
document.querySelector('form').addEventListener('submit', function() {
    const btn = document.getElementById('submitBtn');
    btn.disabled = true;
    btn.textContent = '⏳ Converting...';
});

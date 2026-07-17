/**
 * API Demo - Interactive API tester for ShemaProject
 */

// Copy URL to clipboard
function copyToClipboard(element) {
    const url = element.textContent.trim().replace('Copier', '').trim();
    
    navigator.clipboard.writeText(url).then(() => {
        const btn = element.querySelector('.copy-btn');
        const originalText = btn.textContent;
        btn.textContent = '✓ Copié !';
        btn.style.background = '#27ae60';
        
        setTimeout(() => {
            btn.textContent = originalText;
            btn.style.background = '';
        }, 2000);
    }).catch(err => {
        console.error('Erreur lors de la copie:', err);
        alert('Impossible de copier l\'URL');
    });
}

// Test API
document.addEventListener('DOMContentLoaded', () => {
    const testBtn = document.getElementById('test-api');
    const resultDiv = document.getElementById('test-result');
    
    if (testBtn) {
        testBtn.addEventListener('click', async () => {
            const book = document.getElementById('book').value.trim();
            const chapter = document.getElementById('chapter').value.trim();
            const verseStart = document.getElementById('verse-start').value.trim();
            const verseEnd = document.getElementById('verse-end').value.trim();
            
            if (!book) {
                alert('Veuillez entrer un nom de livre');
                return;
            }
            
            // Build URL
            let url = `/bym/${book}`;
            
            if (chapter) {
                url += `/${chapter}`;
                
                if (verseStart) {
                    url += `/${verseStart}`;
                    
                    if (verseEnd) {
                        url += `-${verseEnd}`;
                    }
                }
            }
            
            // Show loading state
            testBtn.disabled = true;
            testBtn.textContent = 'Chargement...';
            resultDiv.style.display = 'block';
            resultDiv.innerHTML = '<p>⏳ Requête en cours...</p>';
            
            try {
                const response = await fetch(url);
                
                if (!response.ok) {
                    throw new Error(`HTTP ${response.status}: ${response.statusText}`);
                }
                
                const data = await response.json();
                
                // Format and display result
                resultDiv.innerHTML = `
                    <div style="margin-bottom: 1rem;">
                        <strong>URL:</strong> <code>${url}</code>
                    </div>
                    <div style="margin-bottom: 1rem;">
                        <strong>Status:</strong> <span style="color: #27ae60;">✓ ${response.status} OK</span>
                    </div>
                    <div>
                        <strong>Réponse:</strong>
                        <pre style="background: #2c3e50; color: #ecf0f1; padding: 1rem; border-radius: 6px; overflow-x: auto; margin-top: 0.5rem;">${JSON.stringify(data, null, 2)}</pre>
                    </div>
                `;
                
            } catch (error) {
                resultDiv.innerHTML = `
                    <div style="color: #e74c3c;">
                        <strong>❌ Erreur:</strong>
                        <p>${error.message}</p>
                        <p style="font-size: 0.9rem; margin-top: 1rem;"><em>Vérifiez que le nom du livre et les paramètres sont corrects.</em></p>
                    </div>
                `;
            } finally {
                testBtn.disabled = false;
                testBtn.textContent = 'Tester l\'API';
            }
        });
    }
});

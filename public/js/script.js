/**
 * Parse reference text and convert to URL format
 * @param {string} text - Text like "jean 3 4", "jean 3:4", "jean3:4"
 * @returns {string} - URL path like "jean/3/4"
 */
function parseReference(text) {
    text = text.trim();
    
    // Pattern 1: "jean 3:4-5" ou "jean3:4-5"
    let match = text.match(/^([a-zéèêï\s\.\d]+?)\s*(\d+)\s*:\s*(\d+)(?:\s*-\s*(\d+))?$/i);
    if (match) {
        const book = match[1].trim();
        const chapter = match[2];
        const verseStart = match[3];
        const verseEnd = match[4];
        return verseEnd ? `${book}/${chapter}/${verseStart}-${verseEnd}` : `${book}/${chapter}/${verseStart}`;
    }
    
    // Pattern 2: "jean 3 4" ou "jean 3 4-5"
    match = text.match(/^([a-zéèêï\s\.\d]+?)\s+(\d+)\s+(\d+)(?:\s*-\s*(\d+))?$/i);
    if (match) {
        const book = match[1].trim();
        const chapter = match[2];
        const verseStart = match[3];
        const verseEnd = match[4];
        return verseEnd ? `${book}/${chapter}/${verseStart}-${verseEnd}` : `${book}/${chapter}/${verseStart}`;
    }
    
    // Pattern 3: "jean 3" (chapter only)
    match = text.match(/^([a-zéèêï\s\.\d]+?)\s+(\d+)$/i);
    if (match) {
        return `${match[1].trim()}/${match[2]}`;
    }
    
    // Pattern 4: "jean" (book only) - return as is
    return text;
}

document.getElementById('fetchBtn').addEventListener('click', async () => {
    const ref = document.getElementById('reference').value.trim();
    if (!ref) return alert('Veuillez entrer une référence.');
    
    // Transform reference to URL format
    const parsedRef = parseReference(ref);
    
    // Encode each part separately to preserve slashes
    const urlPath = parsedRef.split('/').map(part => encodeURIComponent(part)).join('/');
    
    const result = document.getElementById('result');
    result.textContent = 'Chargement...';
    try {
        const response = await fetch(`/bym/${urlPath}`);
        const data = await response.json();
        result.textContent = JSON.stringify(data, null, 2);
    } catch (e) {
        result.textContent = 'Erreur : impossible de récupérer le verset.';
    }
});

document.getElementById('sqlForm').addEventListener('submit', async (e) => {
    e.preventDefault();
    const nl = document.getElementById('sqlCommand').value;
    const resultsDiv = document.getElementById('results');
    resultsDiv.innerHTML = '<p>Executing...</p>';

    try {
        const response = await fetch('', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
                'X-CSRFToken': getCookie('csrftoken')
            },
            body: `nl=${encodeURIComponent(nl)}`
        });

        const data = await response.json();
        
        if (data.error) {
            resultsDiv.innerHTML = `<div class="error">${data.error}</div>`;
        } else if (data.columns) {
            let table = '<table><thead><tr>';
            data.columns.forEach(col => {
                table += `<th>${col}</th>`;
            });
            table += '</tr></thead><tbody>';
            
            data.rows.forEach(row => {
                table += '<tr>';
                row.forEach(cell => {
                    table += `<td>${cell}</td>`;
                });
                table += '</tr>';
            });
            
            table += '</tbody></table>';
            resultsDiv.innerHTML = table;
        } else {
            resultsDiv.innerHTML = `<p>${data.message}</p>`;
        }
    } catch (err) {
        resultsDiv.innerHTML = `<div class="error">${err.message}</div>`;
    }
});

function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

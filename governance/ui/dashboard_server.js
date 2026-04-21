const http = require('http');
const fs = require('fs');
const path = require('path');
const querystring = require('querystring');

const PORT = 8765;
const DATA_DIR = path.join(__dirname, '..', 'data');
const STATE_FILE = path.join(DATA_DIR, 'collab_state.json');
const MSG_FILE = path.join(DATA_DIR, 'collab_messages.jsonl');
const ARCHIVE_DIR = path.join(DATA_DIR, 'archive');

const MIME = { '.html': 'text/html', '.json': 'application/json', '.js': 'text/javascript' };

const server = http.createServer((req, res) => {
    const url = req.url.split('?')[0];

    if (req.method === 'GET') {
        // Dashboard
        if (url === '/ui/pmo_dashboard.html' || url === '/') {
            const file = path.join(__dirname, 'pmo_dashboard.html');
            fs.readFile(file, (err, data) => {
                if (err) { res.writeHead(404); res.end('404'); return; }
                res.writeHead(200, { 'Content-Type': 'text/html' });
                res.end(data);
            });
            return;
        }

        // API: collabs state
        if (url === '/api/collabs' || url === '/data/collab_state.json') {
            try {
                const data = fs.existsSync(STATE_FILE) ? fs.readFileSync(STATE_FILE, 'utf8') : '{}';
                res.writeHead(200, { 'Content-Type': 'application/json' });
                res.end(data);
            } catch(e) { res.writeHead(500); res.end('error'); }
            return;
        }

        // API: messages
        if (url === '/api/messages' || url === '/data/collab_messages.jsonl') {
            try {
                const data = fs.existsSync(MSG_FILE) ? fs.readFileSync(MSG_FILE, 'utf8') : '';
                res.writeHead(200, { 'Content-Type': 'application/json' });
                res.end(data);
            } catch(e) { res.writeHead(500); res.end('error'); }
            return;
        }

        res.writeHead(404);
        res.end('404');
        return;
    }

    if (req.method === 'POST' && url === '/api/clear-history') {
        try {
            fs.mkdirSync(ARCHIVE_DIR, { recursive: true });
            const ts = new Date().toISOString().replace(/[:.]/g, '-').slice(0, 19);
            if (fs.existsSync(STATE_FILE)) fs.copyFileSync(STATE_FILE, path.join(ARCHIVE_DIR, `collab_state_${ts}.json`));
            if (fs.existsSync(MSG_FILE)) fs.copyFileSync(MSG_FILE, path.join(ARCHIVE_DIR, `collab_messages_${ts}.jsonl`));
            fs.writeFileSync(STATE_FILE, '{}');
            fs.writeFileSync(MSG_FILE, '');
            res.writeHead(200, { 'Content-Type': 'application/json' });
            res.end(JSON.stringify({ ok: true, archived_to: ARCHIVE_DIR }));
        } catch(e) {
            res.writeHead(500, { 'Content-Type': 'application/json' });
            res.end(JSON.stringify({ error: e.message }));
        }
        return;
    }

    res.writeHead(404);
    res.end('404');
});

server.listen(PORT, () => console.log(`PMO Dashboard: http://localhost:${PORT}/ui/pmo_dashboard.html`));
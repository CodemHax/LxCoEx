const API_URL = '/api/v1/core';

let currentOutput = { stdout: '', stderr: '' };
let executionStats = { time: null, memory: null, status: 'idle' };

const runBtn = document.getElementById('runBtn');
const runBtnText = document.getElementById('runBtnText');
const themeToggle = document.getElementById('themeToggle');

// Unified editor wrapper — exposes getValue/setValue/setLanguage/setTheme
let editor = null;
let editorType = null; // 'monaco' or 'codemirror'

const DEFAULT_CODE = [
    'def greet(name):',
    '    return f"Hello, {name}!"',
    '',
    'print(greet("World"))',
    'print("Happy coding!")'
].join('\n');

// Monaco language IDs
const monacoLangMap = {
    'python': 'python',
    'javascript': 'javascript',
    'java': 'java',
    'c': 'c',
    'cpp': 'cpp'
};

// CodeMirror mode mapping
const cmModeMap = {
    'python': 'python',
    'javascript': 'javascript',
    'java': 'text/x-java',
    'c': 'text/x-csrc',
    'cpp': 'text/x-c++src'
};

function isMobile() {
    return window.matchMedia('(max-width: 900px)').matches;
}

// ── Editor initialisation ─────────────────────────────────────────────

function initEditor() {
    if (isMobile()) {
        initCodeMirror();
    } else {
        initMonaco();
    }
}

function initMonaco() {
    editorType = 'monaco';
    document.getElementById('monacoEditor').style.display = 'block';
    document.getElementById('cmEditor').style.display = 'none';

    require.config({
        paths: { vs: 'https://cdnjs.cloudflare.com/ajax/libs/monaco-editor/0.47.0/min/vs' }
    });

    require(['vs/editor/editor.main'], function () {
        const isDark = !document.body.classList.contains('light-theme');

        const monacoInstance = monaco.editor.create(document.getElementById('monacoEditor'), {
            value: DEFAULT_CODE,
            language: 'python',
            theme: isDark ? 'vs-dark' : 'vs',
            fontSize: 14,
            fontFamily: '"JetBrains Mono", "Fira Code", monospace',
            fontLigatures: true,
            minimap: { enabled: false },
            scrollBeyondLastLine: false,
            automaticLayout: true,
            tabSize: 4,
            insertSpaces: true,
            wordWrap: 'on',
            lineNumbers: 'on',
            renderLineHighlight: 'all',
            smoothScrolling: true,
            cursorBlinking: 'smooth',
            cursorSmoothCaretAnimation: 'on',
            padding: { top: 12, bottom: 12 }
        });

        editor = {
            getValue: () => monacoInstance.getValue(),
            setValue: (v) => monacoInstance.setValue(v),
            setLanguage: (lang) => {
                const id = monacoLangMap[lang] || 'javascript';
                monaco.editor.setModelLanguage(monacoInstance.getModel(), id);
            },
            setTheme: (isLight) => {
                monaco.editor.setTheme(isLight ? 'vs' : 'vs-dark');
            },
            _raw: monacoInstance
        };

        postEditorInit();
    });
}

function initCodeMirror() {
    editorType = 'codemirror';
    document.getElementById('monacoEditor').style.display = 'none';

    // The textarea must be VISIBLE before CodeMirror initialises from it,
    // otherwise it measures 0 height and the editor is non-interactive.
    const cmTextarea = document.getElementById('cmEditor');
    cmTextarea.style.display = 'block';

    const isDark = !document.body.classList.contains('light-theme');
    const cmInstance = CodeMirror.fromTextArea(cmTextarea, {
        lineNumbers: true,
        mode: 'python',
        theme: isDark ? 'monokai' : 'eclipse',
        indentUnit: 4,
        indentWithTabs: false,
        lineWrapping: true,
        extraKeys: {
            "Tab": function (cm) {
                if (cm.somethingSelected()) {
                    cm.indentSelection("add");
                } else {
                    cm.replaceSelection("    ", "end");
                }
            }
        }
    });

    // Use viewport-relative height so the editor has a real pixel size in flex layouts.
    const editorHeightPx = Math.max(window.innerHeight * 0.4, 200);
    cmInstance.setSize("100%", editorHeightPx);

    // Force a layout refresh after a tick so all parent sizes are resolved.
    setTimeout(() => {
        cmInstance.refresh();
    }, 50);

    editor = {
        getValue: () => cmInstance.getValue(),
        setValue: (v) => { cmInstance.setValue(v); cmInstance.refresh(); },
        setLanguage: (lang) => {
            const mode = cmModeMap[lang] || 'javascript';
            cmInstance.setOption('mode', mode);
        },
        setTheme: (isLight) => {
            cmInstance.setOption('theme', isLight ? 'eclipse' : 'monokai');
        },
        _raw: cmInstance
    };

    postEditorInit();
}

// ── UI helpers ────────────────────────────────────────────────────────

function showQueuedStatus() {
    const outputContent = document.getElementById('outputContent');
    outputContent.innerHTML = `
        <div class="execution-result">
            <div class="status-card queued">
                <div class="status-header">
                    <span class="status-icon">...</span>
                    <span class="status-text">Submission Queued...</span>
                </div>
                <div class="status-message">Your code is in the queue. Please wait.</div>
            </div>
        </div>
    `;
}

function showExecutionResult(result, isError = false) {
    const outputContent = document.getElementById('outputContent');

    const stdout = result.run?.stdout || result.run?.output || '';
    const stderr = result.run?.stderr || '';
    const exitCode = result.run?.code;
    const language = result.language || document.getElementById('languageSelect').value;

    const execTime = result.run?.time || '< 0.1';
    const memory = result.run?.memory || '-';

    const isSuccess = exitCode === 0 && !isError;
    const statusClass = isSuccess ? 'success' : 'error';
    const statusText = isSuccess ? 'Successfully executed' : 'Compilation error';

    const output = stdout || stderr || '(no output)';
    const errorOutput = stderr || stdout;

    const aiExplainBtn = !isSuccess ? `
        <button class="btn-ai-explain" onclick="explainError()">
            AI Explain
        </button>
    ` : '';

    outputContent.innerHTML = `
        <div class="execution-result">
            <div class="status-card ${statusClass}">
                <div class="status-header">
                    <div class="status-info">
                        <span class="status-label">Status:</span>
                        <span class="status-text">${statusText}</span>
                    </div>
                    ${aiExplainBtn}
                </div>
            </div>
            
            <div id="aiExplanation" class="ai-explanation" style="display: none;"></div>
            
            <div class="stats-row">
                <div class="stat-box">
                    <span class="stat-title">Time:</span>
                    <span class="stat-data">${execTime} secs</span>
                </div>
                <div class="stat-box">
                    <span class="stat-title">Memory:</span>
                    <span class="stat-data">${memory} MB</span>
                </div>
            </div>
            
            <div class="output-section">
                <div class="output-header">${isSuccess ? 'Your Output' : 'Error'}</div>
                <pre class="output-code ${statusClass}">${escapeHtml(output)}</pre>
            </div>
        </div>
    `;

    if (!isSuccess) {
        window.lastError = {
            code: editor.getValue(),
            error: errorOutput,
            language: language
        };
    }

    updateServerStatus(true);
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

async function explainError() {
    if (!window.lastError) return;

    const { code, error, language } = window.lastError;
    const aiExplanation = document.getElementById('aiExplanation');
    const btn = document.querySelector('.btn-ai-explain');

    if (btn) {
        btn.disabled = true;
        btn.textContent = 'Loading...';
    }

    aiExplanation.style.display = 'block';
    aiExplanation.innerHTML = `
        <div class="ai-loading">
            <div class="ai-spinner"></div>
            <span>Analyzing error with AI...</span>
        </div>
    `;

    try {
        const prompt = `You are a helpful programming assistant. The user wrote code in ${language} but got an error.

CODE:
\`\`\`${language}
${code}
\`\`\`

ERROR:
${error}

Please provide:
1. A brief explanation of what caused the error (2-3 sentences max)
2. The corrected code

Format your response exactly like this:
EXPLANATION: [your brief explanation here]

CORRECTED CODE:
\`\`\`${language}
[corrected code here]
\`\`\``;

        const response = await puter.ai.chat(prompt);
        let responseText = "";
        if (typeof response === "string") {
            responseText = response;
        } else if (response && response.message && typeof response.message.content === "string") {
            responseText = response.message.content;
        } else if (response && typeof response.text === "string") {
            responseText = response.text;
        } else {
            responseText = JSON.stringify(response);
        }

        const explanationMatch = responseText.match(/EXPLANATION:\s*([\s\S]*?)(?=CORRECTED CODE:|$)/i);
        const codeMatch = responseText.match(/```[\w]*\n([\s\S]*?)```/);

        const explanation = explanationMatch ? explanationMatch[1].trim() : responseText;
        const correctedCode = codeMatch ? codeMatch[1].trim() : '';

        aiExplanation.innerHTML = `
            <div class="ai-result">
                <div class="ai-explanation-text">
                    <strong>Explanation:</strong> ${escapeHtml(explanation)}
                </div>
                ${correctedCode ? `
                <div class="ai-corrected-code">
                    <div class="ai-code-header">
                        <span>Corrected Code:</span>
                        <button class="btn-copy" onclick="copyCode()">Copy</button>
                    </div>
                    <pre class="ai-code">${escapeHtml(correctedCode)}</pre>
                </div>
                ` : ''}
            </div>
        `;

        window.correctedCode = correctedCode;

    } catch (err) {
        aiExplanation.innerHTML = `
            <div class="ai-error">
                Failed to get AI explanation: ${escapeHtml(err.message)}
            </div>
        `;
    }

    if (btn) {
        btn.disabled = false;
        btn.textContent = 'AI Explain';
    }

    showBackToEditorBtn();
}

function copyCode() {
    if (window.correctedCode) {
        editor.setValue(window.correctedCode);
    }
}

// ── Code execution ────────────────────────────────────────────────────

async function runCode() {
    const code = editor.getValue();
    const language = document.getElementById('languageSelect').value;
    const stdin = document.getElementById('stdinInput').value || null;

    runBtn.disabled = true;
    showQueuedStatus();

    const startTime = performance.now();

    try {
        const response = await fetch(`${API_URL}/execute-sync`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                code: code,
                language: language,
                timeout: 5000,
                stdin: stdin
            })
        });

        const result = await response.json();
        const endTime = performance.now();
        const totalTime = ((endTime - startTime) / 1000).toFixed(4);

        if (!result.run) result.run = {};
        if (!result.run.time) result.run.time = totalTime;

        if (response.status === 400 || response.status === 429) {
            showExecutionResult({
                run: {
                    stdout: '',
                    stderr: `Error: ${result.detail || 'Rate limit exceeded'}`,
                    code: 1,
                    time: totalTime
                }
            }, true);
        } else {
            showExecutionResult(result, result.error);
        }

    } catch (error) {
        showExecutionResult({
            run: {
                stdout: '',
                stderr: `Error: ${error.message}\n\nMake sure the server is running at ${API_URL}`,
                code: 1
            }
        }, true);
        updateServerStatus(false);
    }

    runBtn.disabled = false;
}

// ── Code sharing ──────────────────────────────────────────────────────

async function shareCode() {
    const code = editor.getValue();
    const language = document.getElementById('languageSelect').value;
    const shareBtn = document.getElementById('shareBtn');
    const shareBtnSpan = shareBtn.querySelector('span');

    if (!code.trim()) {
        showErrorModal('Cannot share empty code');
        return;
    }

    shareBtn.disabled = true;
    shareBtnSpan.textContent = 'Sharing...';

    try {
        const response = await fetch(`${API_URL.replace('/core', '')}/snippet/share`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                code: code,
                language: language,
                title: 'Shared Snippet'
            })
        });

        if (!response.ok) {
            const err = await response.json();
            throw new Error(err.detail || 'Failed to share');
        }

        const data = await response.json();
        const shareUrl = `${window.location.origin}${window.location.pathname}?snippet=${data.id}`;
        showShareModal(shareUrl);

    } catch (error) {
        showErrorModal(`Error sharing code: ${error.message}`);
    } finally {
        shareBtn.disabled = false;
        shareBtnSpan.textContent = 'Share';
    }
}

// ── Modals ────────────────────────────────────────────────────────────

function showShareModal(url) {
    const shareModal = document.getElementById('shareModal');
    const shareUrlInput = document.getElementById('shareUrlInput');
    const shareStatusMessage = document.getElementById('shareStatusMessage');

    if (!shareModal || !shareUrlInput || !shareStatusMessage) {
        console.error('Share modal elements not found');
        return;
    }

    shareUrlInput.value = url;
    shareModal.style.display = 'flex';
    shareUrlInput.select();

    if (navigator.clipboard) {
        navigator.clipboard.writeText(url).then(() => {
            shareStatusMessage.textContent = '✓ Link copied to clipboard!';
            shareStatusMessage.className = 'share-status success';
        }).catch(() => {
            shareStatusMessage.textContent = 'Link ready - press Ctrl+C to copy';
            shareStatusMessage.className = 'share-status';
        });
    } else {
        try {
            document.execCommand('copy');
            shareStatusMessage.textContent = '✓ Link copied to clipboard!';
            shareStatusMessage.className = 'share-status success';
        } catch (err) {
            shareStatusMessage.textContent = 'Link ready - press Ctrl+C to copy';
            shareStatusMessage.className = 'share-status';
        }
    }
}

function closeShareModal() {
    const shareModal = document.getElementById('shareModal');
    if (shareModal) shareModal.style.display = 'none';
    const msg = document.getElementById('shareStatusMessage');
    if (msg) msg.className = 'share-status';
}

function showErrorModal(message) {
    const errorModal = document.getElementById('errorModal');
    const errorMessage = document.getElementById('errorMessage');
    if (!errorModal || !errorMessage) return;
    errorMessage.textContent = message;
    errorModal.style.display = 'flex';
}

function closeErrorModal() {
    const errorModal = document.getElementById('errorModal');
    if (errorModal) errorModal.style.display = 'none';
}

function copyToClipboard() {
    const shareUrlInput = document.getElementById('shareUrlInput');
    const statusMessage = document.getElementById('shareStatusMessage');
    if (!shareUrlInput) return;

    shareUrlInput.select();
    if (navigator.clipboard) {
        navigator.clipboard.writeText(shareUrlInput.value).then(() => {
            if (statusMessage) {
                statusMessage.textContent = '✓ Copied to clipboard!';
                statusMessage.className = 'share-status success';
            }
        }).catch(() => {});
    } else {
        try {
            document.execCommand('copy');
            if (statusMessage) {
                statusMessage.textContent = '✓ Copied to clipboard!';
                statusMessage.className = 'share-status success';
            }
        } catch (err) {}
    }
}

document.addEventListener('keydown', function(e) {
    if (e.key === 'Escape') {
        closeShareModal();
        closeErrorModal();
    }
});

// ── Mobile: Back-to-Editor FAB ────────────────────────────────────────

function showBackToEditorBtn() {
    if (isMobile()) {
        document.getElementById('backToEditorBtn')?.classList.add('visible');
    }
}

function hideBackToEditorBtn() {
    document.getElementById('backToEditorBtn')?.classList.remove('visible');
}

function scrollToEditor() {
    document.querySelector('.panel').scrollIntoView({ behavior: 'smooth', block: 'start' });
    hideBackToEditorBtn();
}

window.addEventListener('scroll', () => {
    if (!isMobile()) return;
    const editorPanel = document.querySelector('.panel');
    if (!editorPanel) return;
    if (editorPanel.getBoundingClientRect().bottom < 0) {
        showBackToEditorBtn();
    } else {
        hideBackToEditorBtn();
    }
}, { passive: true });

// ── Server / templates ────────────────────────────────────────────────

function updateServerStatus(connected) {
    const indicator = document.getElementById('serverStatus');
    const text = document.getElementById('serverStatusText');
    if (connected) {
        indicator.classList.remove('error');
        text.textContent = 'Connected';
    } else {
        indicator.classList.add('error');
        text.textContent = 'Disconnected';
    }
}

async function checkServer() {
    try {
        await fetch(`${API_URL}/get-runtimes`);
        updateServerStatus(true);
    } catch {
        updateServerStatus(false);
    }
}

async function loadTemplate(language) {
    try {
        const response = await fetch(`${API_URL}/template/${language}`);
        if (response.ok) {
            const data = await response.json();
            editor.setValue(data.template);
        }
    } catch (error) {
        console.error('Failed to load template:', error);
    }
}

// ── Theme ─────────────────────────────────────────────────────────────

function toggleTheme() {
    const body = document.body;
    const isLight = body.classList.toggle('light-theme');
    themeToggle.querySelector('.theme-icon').textContent = isLight ? '☀️' : '🌙';

    if (editor) editor.setTheme(isLight);
    localStorage.setItem('theme', isLight ? 'light' : 'dark');
}

function loadThemePreference() {
    const savedTheme = localStorage.getItem('theme');
    if (savedTheme === 'light') {
        document.body.classList.add('light-theme');
        themeToggle.querySelector('.theme-icon').textContent = '☀️';
        if (editor) editor.setTheme(true);
    }
}

// ── Init ──────────────────────────────────────────────────────────────

function init() {
    const savedTheme = localStorage.getItem('theme');
    if (savedTheme === 'light') {
        document.body.classList.add('light-theme');
        themeToggle.querySelector('.theme-icon').textContent = '☀️';
    }

    initEditor();
    checkServer();
    themeToggle.addEventListener('click', toggleTheme);
}

function postEditorInit() {
    loadThemePreference();

    document.addEventListener('keydown', (e) => {
        if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
            e.preventDefault();
            runCode();
        }

        if ((e.ctrlKey || e.metaKey) && e.key === 's') {
            e.preventDefault();
            const toast = document.createElement('div');
            toast.className = 'toast';
            toast.textContent = 'Code Saved locally (Browser Storage)';
            document.body.appendChild(toast);
            localStorage.setItem('saved_code', editor.getValue());
            setTimeout(() => {
                toast.classList.add('show');
                setTimeout(() => {
                    toast.classList.remove('show');
                    setTimeout(() => toast.remove(), 300);
                }, 2000);
            }, 10);
        }
    });

    const languageSelect = document.getElementById('languageSelect');
    languageSelect.addEventListener('change', (e) => {
        editor.setLanguage(e.target.value);
        loadTemplate(e.target.value);
    });

    const urlParams = new URLSearchParams(window.location.search);
    const snippetId = urlParams.get('snippet');

    if (snippetId) {
        loadSharedSnippet(snippetId);
    } else {
        const savedCode = localStorage.getItem('saved_code');
        if (savedCode) editor.setValue(savedCode);
    }
}

async function loadSharedSnippet(snippetId) {
    try {
        const response = await fetch(`${API_URL.replace('/core', '')}/snippet/${snippetId}`);
        if (response.ok) {
            const data = await response.json();
            editor.setValue(data.code);

            document.getElementById('languageSelect').value = data.language;
            editor.setLanguage(data.language);

            const toast = document.createElement('div');
            toast.className = 'toast show';
            toast.textContent = 'Shared snippet loaded';
            document.body.appendChild(toast);
            setTimeout(() => toast.remove(), 3000);
        } else {
            console.error('Snippet not found');
        }
    } catch (error) {
        console.error('Error loading snippet:', error);
    }
}

document.addEventListener('DOMContentLoaded', init);

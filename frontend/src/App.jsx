import { useEffect, useRef, useState } from "react";

const API = "http://localhost:5000";

function isLocalPath(path) {
    return /^([a-zA-Z]:\\|\/[^/])/.test(path.trim()) || path.trim().startsWith("/");
}

function inferRepoName(path) {
    return path.replace(/\\/g, "/").split("/").filter(x => Boolean(x)).pop() || "repo";
}

function MDLine({ text }) {
    const parts = text.split(/(`[^`]+`|\*\*[^*]+\*\*)/g);
    return (
        <>
            {parts.map((p, i) => {
                if (p.startsWith("`") && p.endsWith("`"))
                    return <code key={i} className="ic">{p.slice(1, -1)}</code>;
                if (p.startsWith("**") && p.endsWith("**"))
                    return <strong key={i}>{p.slice(2, -2)}</strong>;
                return p;
                
            })}
        </>
    );
}

function MDContent({ content }) {
    const lines = content.split("\n");
    const out = [];
    let i = 0;
    while (i < lines.length) {
        const l = lines[i];
        if (l.startsWith("```")) {
            const lang = l.slice(3).trim();
            const code = [];
            i++;
            while (i < lines.length && !lines[i].startsWith("```")) { 
                code.push(lines[i]); 
                i++; 
            }
            out.push(
                <div key={i} className="code-block">
                {lang && <span className="code-lang">{lang}</span>}
                <pre><code>{code.join("\n")}</code></pre>
                </div>
            );
        } 
        else if (l.startsWith("- ") || l.startsWith("• ")) {
            const items = [];
            while (i < lines.length && (lines[i].startsWith("- ") || lines[i].startsWith("• "))) {
                items.push(<li key={i}><MDLine text={lines[i].slice(2)} /></li>);
                i++;
            }
            out.push(<ul key={`ul-${i}`}>{items}</ul>);
            continue;
        } 
        else if (l.startsWith("**") && l.endsWith("**")) {
            out.push(<p key={i} className="bold-line"><strong>{l.slice(2,-2)}</strong></p>);
        } 
        else if (l.trim() === "") {
            out.push(<div key={i} className="spacer" />);
        } 
        else {
            out.push(<p key={i}><MDLine text={l} /></p>);
        }
        i++;
    }
    return <div className="md">{out}</div>;
}

export default function App() {
    const [repoPath ,setRepoPath] = useState("");
    const [repoName ,setRepoName] = useState("");
    const [status, setStatus] = useState("idle"); // idle, indexing, ready, error
    const [showPathBar, setShowPathBar] = useState(true);
    const [pathError, setPathError] = useState("");
    const [messages, setMessages] = useState([]);
    const [input, setInput] = useState("");
    const [loading, setLoading] = useState(false);
    const [indexedRepos, setIndexedRepos] = useState([]);
    const inputRef = useRef(null);
    const folderRef = useRef(null);
    const chatEndRef = useRef(null);

    useEffect(() => {
        const fetchExistingRepos = async () => {
            try {
                const res = await fetch(`${API}/repos`);
                if (res.ok) {
                    const data = await res.json();
                    setIndexedRepos(data.repos || []);
                }
            } 
            catch (err) {
                console.error("Failed to fetch existing repositories:", err);
            }
        };
        fetchExistingRepos();
    }, []);

    useEffect(() => {
        chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
    }, [messages, loading]);

    const handlePathChange = (newPath) => {
        setRepoPath(newPath);
        setPathError("");
    }

    const handleIndex = async() => {
        const trimmedPath = repoPath.trim();
        if (!trimmedPath) return;
        if (!isLocalPath(trimmedPath)) {
            setPathError("Enter a local path — e.g. C:\\Projects\\myapp or /home/user/myapp");
            return;
        }
        setPathError("");
        setStatus("indexing");
        setMessages([]);

        const name = inferRepoName(trimmedPath);

        try {
            const res = await fetch(`${API}/index`, {
                method: "POST",
                headers: {"Content-Type": "application/json"},
                body: JSON.stringify(
                    {
                        repo_path: trimmedPath,
                        repo_name: name
                    }
                )
            });

            if (res.ok) {
                setRepoName(name);
                setPathError("");
                setStatus("ready");
                setShowPathBar(false);
                setMessages([
                    {
                        role: "system", 
                        text: `${trimmedPath} indexed`
                    }
                ]);
                setIndexedRepos(prev => prev.includes(name) ? prev : [...prev, name]);

                const reposRes = await fetch(`${API}/repos`);
                if (reposRes.ok) { 
                    const d = await reposRes.json(); 
                    setIndexedRepos(d.repos || []); 
                }

                setTimeout(() => inputRef.current?.focus(), 120)
            }
            else {
                setStatus("error");
                setPathError("Indexing failed. Check the path and make sure the server is running.");
            }
        }
        catch {
            setStatus("error");
            setPathError("Cannot reach server at localhost:5000");
        }
    }

    const handleFolderPick = (e) => {
        const files = e.target.files;
        if (!files || files.length === 0) return;
        const first = files[0].webkitRelativePath || "";
        const folderName = first.split("/")[0];
        setRepoPath(folderName);
        setPathError("Browser security limits full path access — confirm or paste the full path below.");
    };

    const handleSelectExistingRepo = (name) => {
        setRepoName(name);
        setStatus("ready");
        setShowPathBar(false);
        setMessages([
            { 
                role: "system", 
                text: `Switched to active repository: /${name}` 
            }
        ]);
        setTimeout(() => inputRef.current?.focus(), 120);
    };

    const handleSend = async () => {
        if (!input.trim() || loading || status !== "ready") return;
        const q = input.trim();
        setInput("");
        setMessages(m => [...m, { role: "user", text: q }]);
        setLoading(true);
        try {
            const res  = await fetch(`${API}/query`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ repo_name: repoName, question: q }),
            });
            const data = await res.json();
            setMessages(m => [...m, { role: "assistant", text: data.answer || "No answer returned." }]);
        } catch {
            setMessages(m => [...m, { role: "assistant", text: "Server unreachable.", error: true }]);
        }
        setLoading(false);
    };

    const onKey = (e) => {
        if (e.key === "Enter" && !e.shiftKey) { 
            e.preventDefault(); 
            handleSend(); 
        }
    };

    const suggestions = [
        "How is the database initialized?",
        "Where is authentication handled?",
        "Explain the search flow end-to-end",
        "What does the main entry point do?",
    ];

    return (
        <div className="shell">
            <div className="grid-overlay"/>

            <header className="topbar">
                <div className="topbar-brand">
                    <svg className="logo-hex" viewBox="0 0 32 32" fill="none">
                        <polygon points="16,2 28,9 28,23 16,30 4,23 4,9" stroke="var(--mint)" strokeWidth="1.5" fill="none"/>
                        <polygon points="16,8 22,11.5 22,18.5 16,22 10,18.5 10,11.5" fill="var(--mint)" opacity="0.15"/>
                        <circle cx="16" cy="15" r="3" fill="var(--mint)"/>
                    </svg>
                    <span className="brand-text">code<span className="mint">context</span></span>
                </div>

                <div className="topbar-center">
                    {status === "ready" && !showPathBar && (
                        <button className="repo-pill" onClick={() => setShowPathBar(val => !val)}>
                            <span className="pill-dot" />
                            <span className="pill-name">{repoName}</span>
                            <span className="pill-change">change</span>
                        </button>
                    )}
                </div>

                <div className="topbar-right">
                    <span className="version-tag">#</span>
                </div>
            </header>

            {showPathBar && (
                <div className="path-bar">

                    {status === "ready" && (
                        <button className="pathbar-close" onClick={() => setShowPathBar(false)}>✕</button>
                    )}

                    <div className="path-bar-inner">
                        <span className="path-label">$ repo</span>
                        <div className="path-input-group">
                            <input 
                                type="text" 
                                placeholder="/home/user/my-project  or  C:\Projects\myapp"
                                className={`path-input ${pathError ? "path-input-err" : ""}`}
                                value={repoPath}
                                onChange={e => handlePathChange(e.target.value)}
                                onKeyDown={e => e.key === "Enter" && handleIndex()}
                                spellCheck={false}
                            />
                            <button
                                className="browse-btn"
                                title="Browse folder"
                                onClick={() => folderRef.current?.click()}
                            >
                                <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                                    <path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z"/>
                                </svg>
                            </button>
                            <input
                                ref={folderRef} 
                                type="file"
                                webkitdirectory="true"
                                directory="true"
                                style={{ display: "none" }}
                                onChange={handleFolderPick}
                            />
                            <button
                                className={`index-btn ${status === "indexing" ? "btn-busy" : ""}`}
                                onClick={handleIndex}
                                disabled={status === "indexing" || !repoPath.trim()}
                            >
                                {status === "indexing" ? <><span className="spin" />indexing…</> : "index"}
                            </button>
                        </div>

                        {pathError && <p className="path-err">{pathError}</p>}

                        {indexedRepos.length > 0 && (
                            <div className="existing-repos">
                                <span className="existing-label">indexed repos</span>
                                <div className="repo-tags">
                                    {indexedRepos.map(name => (
                                        <button
                                            key={name}
                                            className={`repo-tag ${repoName === name && status === "ready" ? "repo-tag-active" : ""}`}
                                            onClick={() => handleSelectExistingRepo(name)}
                                        >
                                            <span className="repo-tag-slash">/</span>{name}
                                        </button>
                                    ))}
                                </div>
                            </div>
                        )}

                    </div>
                </div>
            )}

            <div className="chat-area">
                {messages.length === 0 ? (
                    <div className="splash">
                        <div className="splash-hex">
                            <svg viewBox="0 0 80 80" fill="none">
                                <polygon points="40,4 72,22 72,58 40,76 8,58 8,22" stroke="var(--mint)" strokeWidth="1" fill="none" opacity="0.3"/>
                                <polygon points="40,16 60,27 60,49 40,60 20,49 20,27" stroke="var(--mint)" strokeWidth="1" fill="none" opacity="0.5"/>
                                <circle cx="40" cy="38" r="8" fill="var(--mint)" opacity="0.9"/>
                            </svg>
                        </div>
                        <h1 className="splash-title">Ask your codebase anything</h1>
                        <p className="splash-sub">Index a local repository above, then start chatting.</p>

                        <div className="splash-chips">
                            {suggestions.map(s => (
                                <button key={s} className="chip" onClick={() => { setInput(s); inputRef.current?.focus(); }}>
                                    {s}
                                </button>
                            ))}
                        </div>
                    </div>
                ) : (
                    <div className="messages">
                        {messages.map((msg, i) => {
                            if (msg.role === "system") return(
                                <div key={i} className="sys-msg">
                                    <span className="sys-icon">✦</span>
                                    <span>{msg.text}</span>
                                </div>
                            )
                            return (
                                <div key={i} className={`bubble-row ${msg.role}`}>
                                    {msg.role === "assistant" && (
                                        <div className="avatar av-ai">
                                            <svg viewBox="0 0 20 20" fill="none">
                                                <polygon points="10,1 18,5.5 18,14.5 10,19 2,14.5 2,5.5" stroke="var(--mint)" strokeWidth="1.2" fill="none"/>
                                                <circle cx="10" cy="10" r="3" fill="var(--mint)"/>
                                            </svg>
                                        </div>
                                    )}
                                    <div className={`bubble ${msg.error ? "bubble-err" : ""}`}>
                                        {msg.role === "assistant"
                                        ? <MDContent content={msg.text} />
                                        : <p>{msg.text}</p>
                                        }
                                    </div>
                                    {msg.role === "user" && (
                                        <div className="avatar av-user">U</div>
                                    )}
                                </div>
                            );
                        })}

                        {loading && (
                            <div className="bubble-row assistant">
                                <div className="avatar av-ai">
                                    <svg viewBox="0 0 20 20" fill="none">
                                        <polygon points="10,1 18,5.5 18,14.5 10,19 2,14.5 2,5.5" stroke="var(--mint)" strokeWidth="1.2" fill="none"/>
                                        <circle cx="10" cy="10" r="3" fill="var(--mint)"/>
                                    </svg>
                                </div>
                                <div className="bubble typing-bubble">
                                    <span className="dot" /><span className="dot" /><span className="dot" />
                                </div>
                            </div>
                        )}
                        <div ref={chatEndRef} />
                    </div>
                )}
            </div>

            <div className="input-dock">
                <div className="input-wrap">
                    <textarea
                        ref={inputRef}
                        className="msg-input"
                        rows={1}
                        placeholder={status === "ready" ? "Ask anything about the codebase…" : "Index a repository to start"}
                        value={input}
                        onChange={e => setInput(e.target.value)}
                        onKeyDown={onKey}
                        disabled={status !== "ready" || loading}
                    />
                    <button
                        className="send-btn"
                        onClick={handleSend}
                        disabled={!input.trim() || loading || status !== "ready"}
                    >
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                            <line x1="22" y1="2" x2="11" y2="13"/>
                            <polygon points="22 2 15 22 11 13 2 9 22 2"/>
                        </svg>
                    </button>
                </div>
                <p className="input-hint">Enter to send · Shift+Enter for new line</p>
            </div>

        </div>
    );
}
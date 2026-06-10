import functools
from tree_sitter_language_pack import get_parser
from pathlib import Path

def get_cached_parser(lang:str):
    return get_parser(lang)

EXTENSION_MAP = {
    ".py": "python",
    ".js": "javascript",
    ".java": "java",
}

IGNORED_DIRS = {
    ".git", "node_modules", ".next", "dist", "build", 
    "target", "venv", ".venv", "__pycache__", ".idea", ".vscode",
    "instance", "static/uploads", "static/reports", ".env", ".env.example"
}

IGNORED_LOCKFILES = {
    "package-lock.json", "yarn.lock", "pnpm-lock.yaml", 
}

IGNORED_EXTENSIONS = {
    ".svg",
    ".png",
    ".jpg",
    ".jpeg",
    ".ico",
    ".lock"
}

LANGUAGE_QUERIES = {
    "python": """
        (function_definition) @structure
        (class_definition) @structure
        (import_statement) @import
        (import_from_statement) @import
    """,
    "javascript": """
        (function_declaration) @structure
        (class_declaration) @structure
        (method_definition) @structure
        (arrow_function) @structure
        (function_expression) @structure
        (import_declaration) @import
    """,
    "java": """
        (class_declaration) @structure
        (method_declaration) @structure
        (interface_declaration) @structure
        (enum_declaration) @structure
        (import_declaration) @import
    """
}

MAX_CHUNK_CHARS = 1200
OVERLAP_LINES = 5

def chunk_text(text):
    lines = text.splitlines()

    if len(lines) <= 80:
        return [{
            "start_line": 1,
            "end_line": len(lines),
            "content": text
        }]

    chunks = []
    curr_chunks = []

    curr_start = 1
    curr_chars = 0

    for line_no, line in enumerate(lines, start=1):
        curr_chunks.append(line)
        curr_chars += len(line)

        if curr_chars >= MAX_CHUNK_CHARS:
            chunks.append({
                "start_line": curr_start,
                "end_line": line_no,
                "content": "\n".join(curr_chunks)
            })

            overlap = curr_chunks[-OVERLAP_LINES:]

            curr_chunks = overlap.copy()
            curr_chars = sum(len(l) for l in curr_chunks)

            curr_start = max(1, line_no - len(overlap) + 1)

    if curr_chunks:
        chunks.append({
            "start_line": curr_start,
            "end_line": len(lines),
            "content": "\n".join(curr_chunks)
        })

    return chunks

def extract_ast_chunks(source_code, language):
    parser = get_cached_parser(language)

    tree = parser.parse(
        bytes(source_code, "utf-8")
    )
    query = parser.language.query(LANGUAGE_QUERIES[language])

    captures = query.captures(
        tree.root_node
    )

    chunks = []

    for node, capture_name in captures:

        if capture_name not in {"structure", "import"}:
            continue

        chunks.append({
            "start_line": node.start_point[0] + 1,
            "end_line": node.end_point[0] + 1,
            "content": source_code[
                node.start_byte:node.end_byte
            ]
        })

    return chunks

def process_file(file_path):
    try:
        source_code = file_path.read_text(
            encoding="utf-8",
            errors="ignore"
        )
    except Exception as e:
        return []


    extension = file_path.suffix

    if extension in EXTENSION_MAP:
        language = EXTENSION_MAP[extension]

        try:
            # print("Processing:", file_path)
            chunks = extract_ast_chunks(source_code, language)
            # print("Found:", len(chunks))
            if chunks:
                return chunks
        except Exception as e:
            pass
    
    return chunk_text(source_code)

def process_single_file(repo_path, file_path):
    extension = file_path.suffix.lower()

    language = EXTENSION_MAP.get(extension, "text")

    chunks = process_file(file_path)

    for chunk in chunks:
        chunk["repo_name"] = repo_path.name
        chunk["file_path"] = str(file_path.relative_to(repo_path))
        chunk["language"] = language

    return chunks
    
def process_repository(repo_path):
    repo_path = Path(repo_path)

    all_chunks = []

    for file_path in repo_path.rglob("*"):
        # ignore folders and go for files only
        if not file_path.is_file():
            continue
        
        # ignore some files
        skip = False
        for part in file_path.parts:
            if part in IGNORED_DIRS:
                skip = True
                break
        if skip:
            continue

        if file_path.name in IGNORED_LOCKFILES:
            continue

        chunks = process_single_file(
            repo_path,
            file_path
        )

        all_chunks.extend(chunks)

    return all_chunks
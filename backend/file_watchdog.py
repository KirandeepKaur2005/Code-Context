import time
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from threading import Timer
from pathlib import Path

from database import clear_file_vectors

DEBOUNCE_SECONDS = 3
pending_timers = {}

IGNORED_DIRS = {"venv", ".venv", "__pycache__", ".git", "node_modules"}

def reindex_file(repo_path, file_path):
    from pipeline import index_file
    print(f"Reindexing: {file_path}")

    pending_timers.pop(str(file_path), None)

    rel_path = str(
        Path(file_path).relative_to(repo_path)
    )

    clear_file_vectors(rel_path)

    index_file(
        Path(repo_path),
        Path(file_path)
    )

def schedule_reindex(repo_path, file_path):
    file_path = str(file_path)

    if file_path in pending_timers:
        pending_timers[file_path].cancel()
    
    timer = Timer(
        DEBOUNCE_SECONDS,
        reindex_file,
        args=(repo_path, file_path)
    )

    pending_timers[file_path] = timer
    timer.start()

class Handler(FileSystemEventHandler):

    def __init__(self, repo_path):
        self.repo_path = repo_path
    
    def on_created(self, event):
        
        if event.is_directory:
            return

        path_parts = Path(event.src_path).parts
        if any(
            part in IGNORED_DIRS
            for part in path_parts
        ):
            return
        
        schedule_reindex(self.repo_path, event.src_path)

    def on_modified(self, event):
        
        if event.is_directory:
            return 
        
        path_parts = Path(event.src_path).parts
        if any(
            part in IGNORED_DIRS
            for part in path_parts
        ):
            return
        
        schedule_reindex(self.repo_path, event.src_path)
    
    def on_deleted(self, event):
        
        if event.is_directory:
            return 
        
        rel_path = str(
            Path(event.src_path).relative_to(self.repo_path)
        )

        clear_file_vectors(rel_path)

    def on_moved(self, event):

        if event.is_directory:
            return

        old_rel = str(
            Path(event.src_path).relative_to(self.repo_path)
        )

        clear_file_vectors(old_rel)

        schedule_reindex(self.repo_path, event.dest_path)

def start_watching(repo_path):
    observer = Observer()

    observer.schedule(
        Handler(repo_path),
        path=repo_path,
        recursive=True,
    )

    observer.start()
    print(f"Watching {repo_path}")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    
    observer.join()    

if __name__ == "__main__":
    # index_repository("../../Devsearch")
    start_watching("../../Devsearch") 
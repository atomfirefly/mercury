import os

def on_console(path, include_files=True):
    """
    Provides path completion, against files local to the Console.
    """

    folder, search_path = get_folder_and_search_path(path, os.path.sep)
    folders = os.listdir(folder)
    
    return get_suggestions(folder, search_path, folders, os.path.sep, include_files)

def on_agent(path, context):
    """
    Provides path completion, against files local to the Agent.
    """

    folder, search_path = get_folder_and_search_path(path, "/")
    folders = context.listFiles(folder)
    
    return get_suggestions(folder, search_path, map(lambda f: str(f), folders), "/", True)     

def get_folder_and_search_path(path, sep):
    """
    Breakdown the search path, to determine the base folder and search string.
    """

    if path == "":
        path = "/"

    folder = path[:path.rfind(sep) + 1] if (path != sep) else sep
    search_path = path[path.rfind(sep) + 1:]

    return (folder, search_path)

def get_suggestions(folder, search_path, folders, sep, include_files=True):
    """
    Filter a list of folders with a given search path.
    """

    suggestions = [ (folder + p + sep) for p in folders if (p.startswith(search_path) and p != search_path and os.path.isdir(folder + p)) ]
    
    if include_files:
        suggestions += [ (folder + p) for p in folders if (p.startswith(search_path) and p != search_path and not os.path.isdir(folder + p)) ]
    
    return suggestions
    
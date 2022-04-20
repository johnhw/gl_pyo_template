import git
import datetime 

# Set the name, author and version number here
demo_name = "CHANGE ME"
author = "John H. Williamson"
version = "0.0.0"


def get_git_info():
    """Get current git details and return them as a dictionary"""
    repo = git.Repo(search_parent_directories=True)
    head = repo.head.commit
    git_info = {
        "sha": head.hexsha,
        "date": datetime.datetime.fromtimestamp(head.committed_date).isoformat(),
        "author": head.author.name,
        "branch": repo.active_branch.name
    }
    return git_info

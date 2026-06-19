import shutil
import subprocess
import os


def clone_repository(
    repo_url,
    destination="uploads/github_repo"
):

    if os.path.exists(destination):

        shutil.rmtree(destination)

    subprocess.run(
        [
            "git",
            "clone",
            repo_url,
            destination
        ],
        check=True
    )

    return destination

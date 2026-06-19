def get_repository_chart_data(repo_stats):

    return {
        "Files": repo_stats["files"],
        "Functions": repo_stats["functions"],
        "Classes": repo_stats["classes"],
        "Imports": repo_stats["imports"]
    }

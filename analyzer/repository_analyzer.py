import zipfile
import os


SUPPORTED_EXTENSIONS = (
    ".py",
    ".java",
    ".cpp",
    ".js"
)


def extract_repository(
    zip_path,
    extract_dir
):

    with zipfile.ZipFile(
        zip_path,
        "r"
    ) as zip_ref:

        zip_ref.extractall(
            extract_dir
        )


def collect_source_code(
    repo_path
):

    combined_code = ""

    file_count = 0

    for root, dirs, files in os.walk(
        repo_path
    ):

        for file in files:

            if file.endswith(
                SUPPORTED_EXTENSIONS
            ):

                file_count += 1

                file_path = os.path.join(
                    root,
                    file
                )

                try:

                    with open(
                        file_path,
                        "r",
                        encoding="utf-8"
                    ) as f:

                        combined_code += (
                            f"\n\n# FILE: {file}\n\n"
                        )

                        combined_code += f.read()

                except Exception:
                    pass

    return combined_code, file_count



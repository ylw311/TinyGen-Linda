import logging

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)


def output_modified_code(repo_dir, diff):
    """
    This function writes the modified code (from the diff) to new files in the repo directory.
    """
    logging.info("Writing the modified code to new files in the repository.")

    # Split the diff into individual file changes
    diff_lines = diff.split("\n")
    current_file = None
    modified_code = []

    for line in diff_lines:
        # Detect file changes in the diff (e.g., `diff --git a/file.py b/file.py`)
        if line.startswith("diff --git"):
            if current_file and modified_code:
                # Write the modified code to the current file
                write_modified_file(repo_dir, current_file, modified_code)

            # Extract file name (e.g., `a/file.py`)
            current_file = line.split(" ")[2][2:]
            modified_code = []
        else:
            modified_code.append(line)

    # Write the last modified file
    if current_file and modified_code:
        write_modified_file(repo_dir, current_file, modified_code)

    logging.info("Modified code has been written successfully.")


def write_modified_file(repo_dir, file_path, modified_code):
    """
    Writes the modified code to a new file in the repo.
    """
    full_path = os.path.join(repo_dir, file_path)
    logging.info(f"Writing changes to {full_path}")

    with open(full_path, "w") as f:
        f.write("\n".join(modified_code))
    logging.info(f"Modified file saved: {full_path}")

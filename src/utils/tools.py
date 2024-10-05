import logging
import os
from llm import GPT4oClient

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
# Initialize LLM client
llm_client = GPT4oClient()


def output_modified_code(repo_dir, diff):
    """
    This function passes the code and diff to the LLM and receives the corrected code to write back into the repository.

    Args:
        repo_dir (str): The path to the repository directory.
        diff (str): The generated diff that needs to be applied.
    """
    logging.info("Sending the repository code and diff to LLM for corrections.")

    # Collect code from the repository
    code_files = []
    for root, dirs, files in os.walk(repo_dir):
        for file in files:
            if file.endswith(
                (".py", ".txt", ".md", ".js", ".ts", ".sh")
            ):  # Filter files if necessary
                file_path = os.path.join(root, file)
                with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                    code = f.read()
                relative_path = os.path.relpath(file_path, repo_dir)
                code_files.append({"path": relative_path, "content": code})

    # Create LLM prompt with repo content and diff
    llm_prompt = generate_llm_prompt_with_code_and_diff(code_files, diff)

    # Call LLM for the corrected code
    try:
        corrected_code = llm_client.create_completion(llm_prompt)
    except Exception as e:
        logging.error(f"Failed to get response from LLM: {e}")
        raise e

    # Parse and write corrected code back to the files
    apply_corrected_code(repo_dir, corrected_code)

    logging.info("Code has been updated successfully.")


def generate_llm_prompt_with_code_and_diff(code_files, diff):
    """
    Generates a prompt for the LLM with the repository code and the diff.

    Args:
        code_files (list): List of dictionaries containing file paths and their contents.
        diff (str): The diff to apply.

    Returns:
        str: The generated prompt for the LLM.
    """
    llm_prompt = (
        "You are given a repository with the following files and their contents.\n"
        "You are also given a diff that describes the changes that need to be applied to this code.\n"
        "Please apply the changes from the diff and return the corrected code for each file.\n"
        "If a file does not need any changes, return its original content.\n\n"
        "Files:\n"
    )

    for file in code_files:
        llm_prompt += f"\nFile: {file['path']}\nContent:\n{file['content']}\n"

    llm_prompt += f"\nDiff:\n{diff}\n"

    llm_prompt += "\nReturn the corrected code for each file in the format:\n"
    llm_prompt += "File: <file-path>\n \n<code>\n"
    llm_prompt += "<important>Return the corrected code as it is, in a ready to be inserted directly format, without ticks and any formatting, or heading text.  </important> \n"

    return llm_prompt


def apply_corrected_code(repo_dir, corrected_code):
    """
    Parses the corrected code returned by the LLM and writes it back to the corresponding files in the repository.

    Args:
        repo_dir (str): The path to the repository directory.
        corrected_code (str): The corrected code returned by the LLM.
    """
    current_file = None
    file_content = []

    lines = corrected_code.splitlines()

    for line in lines:
        if line.startswith("File:"):
            if current_file and file_content:
                # Write the corrected content to the file
                write_corrected_file(repo_dir, current_file, file_content)

            # Start a new file
            current_file = line.split("File:")[1].strip()
            file_content = []
        else:
            file_content.append(line)

    # Write the last file's content
    if current_file and file_content:
        write_corrected_file(repo_dir, current_file, file_content)


def write_corrected_file(repo_dir, file_path, modified_code):
    """
    Writes the modified code to a new file in the repo.
    """
    full_path = os.path.join(repo_dir, file_path)
    logging.info(f"Writing changes to {full_path}")

    with open(full_path, "w") as f:
        f.write("\n".join(modified_code))
    logging.info(f"Modified file saved: {full_path}")

from langchain.prompts import FewShotPromptTemplate, PromptTemplate


few_shot_examples = [
    {
        "prompt": "Convert Python script to use subprocess.run instead of os.system.",
        "diff": """diff --git a/temp.sh b/temp.sh
index 1234567..89abcdef 100644
--- a/temp.sh
+++ b/temp.sh
@@ -1,2 +1,2 @@
- os.system('bash temp.sh')
+ subprocess.run(['bash', 'temp.sh'])
""",
    },
    {
        "prompt": "Modify the script to check if the operating system is Windows.",
        "diff": """diff --git a/src/main.py b/src/main.py
index 1234567..89abcdef 100644
--- a/src/main.py
+++ b/src/main.py
@@ -1,3 +1,6 @@
 import os

+if os.name == 'nt':
+    os.system('dir')
+else:
+    os.system('ls')
""",
    },
    {
        "prompt": "# The program doesn't output anything on Windows 10\n\n(base) C:\\\\Users\\\\off99\\\\Documents\\\\Code\\\\> llm list files in current dir; windows\n\n/ Querying GPT-3200\n───────┬────────────────────────────────────────────────────────────────────────────────────────────────────────────────\n       │ File: temp.sh\n───────┼────────────────────────────────────────────────────────────────────────────────────────────────────────────────\n   1   │\n   2   │ dir\n   3   │ ```\n───────┴────────────────────────────────────────────────────────────────────────────────────────────────────────────────\n\n>> Do you want to run this program? [Y/n] y\n\nRunning...\n\n(base) C:\\\\Users\\\\off99\\\\Documents\\\\Code\\\\>\nNotice that there is no output. Is this supposed to work on Windows as well?\n\nIt would be great if the script could detect which OS or shell I'm using and automatically use the appropriate command, like `dir` instead of `ls`, to avoid having to specify 'windows' after every prompt.",
        "diff": """diff --git a/src/main.py b/src/main.py
index 58d38b6..23b0827 100644
--- a/src/main.py
+++ b/src/main.py
@@ -19,7 +19,10 @@ def run_bash_file_from_string(s: str):
     \"""Runs a bash script from a string\"""
     with open('temp.sh', 'w') as f:
         f.write(s)
-    os.system('bash temp.sh')
+    if os.name == 'nt':  # Windows systems
+        os.system('powershell.exe .\\\\temp.sh')
+    else:  # Unix/Linux systems
+        os.system('bash temp.sh')
     os.remove('temp.sh')
""",
    },
]


example_template = """
Prompt: {prompt}
Diff:
{diff}
"""

example_prompt = PromptTemplate(
    input_variables=["prompt", "diff"], template=example_template
)

few_shot_prompt_template = FewShotPromptTemplate(
    examples=few_shot_examples,
    example_prompt=example_prompt,
    prefix="The following are examples of code diffs based on different prompts:",
    suffix="Based on the following prompt, generate a unified code diff:\nPrompt: {user_prompt}\nDiff:",
    input_variables=["user_prompt"],
)


def generate_diff_prompt(prompt, repo_content):
    """
    Generate a diff prompt for GitHub-style diffs.

    Args:
        prompt (str): The instruction to change the code.
        repo_content (dict): A dictionary containing file paths and contents of the repo files.

    Returns:
        str: A prompt asking the LLM to provide a GitHub-style diff.
    """
    llm_prompt = (
        f"The following is a repository containing multiple files. "
        f"Apply the following change based on the prompt: '{prompt}'. "
        "For each file, provide a diff of the required changes in GitHub's unified diff format, focusing only on the necessary modifications.\n"
        "If no changes are needed for a particular file, ignore it.\n"
    )
    for file in repo_content:
        llm_prompt += f"\nFile: {file['path']}\nContent:\n{file['content']}\n"

    llm_prompt += "\nProvide the diff in the following format:\n"
    llm_prompt += "diff --git a/<path-to-file> b/<path-to-file>\n"
    llm_prompt += "index <old-hash>..<new-hash> <file-mode>\n"
    llm_prompt += "--- a/<path-to-file>\n"
    llm_prompt += "+++ b/<path-to-file>\n"
    llm_prompt += "@@ -<line-number>,<length> +<line-number>,<length> @@\n"
    llm_prompt += "- <old code>\n"
    llm_prompt += "+ <new code>\n"

    return llm_prompt


def generate_reflection_prompt(prompt, diff):
    """
    Generates a reflection prompt template for reviewing a diff based on a given prompt.

    Args:
        prompt (str): The initial instruction or task that the code is addressing.
        diff (str): The code diff that needs to be reviewed.

    Returns:
        str: A formatted reflection prompt.
    """
    return (
        f"You generated the following diff based on the prompt '{prompt}':\n{diff}\n\n"
        "Review the diff for correctness and completeness. If the current code already reflects the prompt, "
        "there is no need to modify anything. If changes are needed, provide the corrected diff in the following format:\n\n"
        "```diff\n<corrected diff here>\n```\n\n"
        "Then, provide a summary that starts with '###', explaining the changes or confirming that no changes were needed."
    )


def generate_summary_prompt(prompt, current_diff):
    """
    Generates a summary prompt for summarizing the changes made in the diff based on the given prompt.

    Args:
        prompt (str): The initial instruction or task that the code is addressing.
        current_diff (str): The code diff that needs to be summarized.

    Returns:
        str: A formatted summary prompt.
    """
    return (
        f"The following is a code diff based on the prompt: '{prompt}'.\n"
        "Please provide a concise summary of the changes made in the diff and how they address the issue described in the prompt.\n"
        "Explain the key modifications and their significance. Be concise.\n\n"
        f"Prompt:\n{prompt}\n\n"
        f"Diff:\n{current_diff}\n\n"
        "Provide the summary below:\n###"
    )


def generate_validation_prompt(prompt, diff):
    """
    Generates a validation prompt for reviewing a code diff based on a given prompt.

    Args:
        prompt (str): The initial task or instruction that the code is supposed to solve.
        diff (str): The code diff that needs to be validated.

    Returns:
        str: A formatted validation prompt for reviewing the diff.
    """
    return (
        f"The following is a code diff based on the prompt: '{prompt}'.\n"
        "Please review the diff and determine if it fully addresses the issue described in the prompt.\n"
        "If the diff is incomplete or incorrect, explain what is missing or wrong. If the diff fully addresses the issue, confirm that it is correct.\n\n"
        f"Prompt:\n{prompt}\n\n"
        f"Diff:\n{diff}\n\n"
    )

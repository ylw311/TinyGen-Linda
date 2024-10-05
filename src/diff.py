import logging
import os

from fastapi import HTTPException
from llm import GPT4oClient
from utils.prompts import *


logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)

llm_client = GPT4oClient()


def generate_initial_diff(prompt, repo_dir):
    # Read all the code from the repo
    code_files = []
    for root, dir, files in os.walk(repo_dir):
        for file in files:
            if file.endswith(
                (".py", ".txt", ".md", ".js", ".ts", ".sh")
            ):  # Adjust extensions as needed
                file_path = os.path.join(root, file)
                with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                    code = f.read()
                relative_path = os.path.relpath(file_path, repo_dir)
                code_files.append({"path": relative_path, "content": code})

    user_prompt = (
        f"Make the necessary changes based on the following prompt: '{prompt}'."
    )

    llm_prompt = generate_diff_prompt(user_prompt, code_files)

    # Call the OpenAI API
    try:
        diff = llm_client.create_completion(llm_prompt)
        
        if "```diff" in diff:
            diff_start = diff.find("```diff") + len("```diff")
            diff_end = diff.find("```", diff_start)
            diff = diff[diff_start:diff_end].strip()
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"OpenAI API error: {e}") from e

    return diff


def reflection_step(diff, prompt, max_retries=5):
    logging.info("REFLECTING")

    retries = 0
    current_diff = diff

    reflection_prompt_template = generate_reflection_prompt(prompt, diff)
    summary_prompt = generate_summary_prompt(prompt, current_diff)

    # First, check if the current diff already fixes the issue
    if check_diff_fixes_issue(current_diff, prompt, max_retries):
        logging.info("The initial diff fixes the issue as per the prompt.")
        # generate a summary of the diff
        try:
            
                    
            summary = llm_client.create_completion(summary_prompt)
            
            # Extract the summary after ###
            summary_start = summary.find("###")
            summary = summary[
                summary_start + len("###") :
            ].strip()
            
            return current_diff, summary
        except Exception as e:
            raise HTTPException(
                status_code=500, detail="OpenAI API error during summary generation"
            ) from e

    # If the current diff doesn't fix the issue, enter the retry loop
    while retries < max_retries:
        logging.info(f"Attempt {retries + 1} to generate a new diff.")
        reflection_prompt = reflection_prompt_template.replace(
            "based on the prompt", f"based on the prompt attempt {retries + 1}"
        )
        try:
            # Call the OpenAI API for reflection to generate a new diff
            reflection = llm_client.create_completion(reflection_prompt)
            logging.info(f"Reflection attempt {retries + 1} completed.")

            # Check if the reflection result contains the expected format
            if "```diff" in reflection and "###" in reflection:
                try:
                    # Extract the diff between ```diff and ```
                    diff_start = reflection.find("```diff") + len("```diff")
                    diff_end = reflection.find("```", diff_start)
                    final_diff = reflection[diff_start:diff_end].strip()

                    # Extract the summary after ###
                    summary_start = reflection.find("###")
                    summary = reflection[
                        summary_start + len("###") :
                    ].strip()  # Strip the ### when returning

                    # Check if the new diff fixes the issue
                    if check_diff_fixes_issue(final_diff, prompt, max_retries):
                        logging.info(
                            "The generated diff fixes the issue as per the prompt."
                        )
                        return final_diff, summary
                    else:
                        logging.warning(
                            f"Diff attempt {retries + 1} does not fully address the issue. Retrying..."
                        )
                        retries += 1
                        current_diff = (
                            final_diff  # Update current_diff for the next retry
                        )
                except Exception as e:
                    logging.error(f"Failed to parse the reflection result: {e}")
                    retries += 1
                    continue  # Try again
            else:
                # If the expected format is not found, retry
                logging.warning(
                    f"Reflection did not return the expected format on attempt {retries + 1}. Retrying..."
                )
                retries += 1

        except Exception as e:
            logging.error(f"Error during reflection step: {e}")
            raise HTTPException(
                status_code=500, detail="OpenAI API error during reflection"
            )

    # If we reach this point, we've exceeded the max retries
    logging.error(f"Reflection failed to fix the issue after {max_retries} attempts.")
    return None, "Reflection failed after multiple attempts."


def check_diff_fixes_issue(diff, prompt, max_retries=5):
    """
    Calls the LLM to verify whether the provided diff fixes the issue described in the prompt.
    Retries up to max_retries if the diff does not address the issue.
    """

    retries = 0
    while retries < max_retries:
        # Prepare the validation prompt to check if the diff fixes the issue
        validation_prompt = generate_validation_prompt(prompt, diff)

        try:
            validation_result = llm_client.create_completion(validation_prompt)
            logging.info(f"Validation attempt {retries + 1} completed.")

            # Check the response to determine if the diff is valid
            if (
                "fully addresses the issue" in validation_result.lower()
                or "correct" in validation_result.lower()
            ):
                logging.info("The generated diff fully addresses the issue.")
                return True  # The diff is correct and fixes the issue

            else:
                logging.warning(
                    f"Validation failed on attempt {retries + 1}: {validation_result}"
                )
                retries += 1  # Retry to generate another diff
                continue  # Go back to generate a new diff if needed

        except Exception as e:
            logging.error(f"Error during validation step: {e}")
            retries += 1
            continue  # Retry the validation

    # If we exceed max_retries, we give up
    logging.error(
        f"Failed to generate a diff that fixes the issue after {max_retries} attempts."
    )
    return False  # Failed to fix the issue

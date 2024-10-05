from fastapi import FastAPI, HTTPException

from git import Repo
import os
import shutil
import logging

from supabase import create_client, Client
from dotenv import load_dotenv
from utils.tools import output_modified_code
from diff import *
from request_data import RequestData

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
load_dotenv()


app = FastAPI()


# Set up Supabase credentials ================================================
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_ANON_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise ValueError(
        "Supabase credentials are not set. Please set SUPABASE_URL and SUPABASE_KEY environment variables."
    )

# Initialize Supabase client
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
#  ================================================


@app.post("/generate-diff")
async def generate_diff(data: RequestData):
    repo_url = data.repoUrl
    prompt = data.prompt
    repo_dir_a = "a"  # Folder for the first clone (unchanged)
    repo_dir_b = "b"  # this is where the modified code will be stored

    # Clean up any existing repo directory
    if os.path.exists(repo_dir_a):
        shutil.rmtree(repo_dir_a)
    if os.path.exists(repo_dir_b):
        shutil.rmtree(repo_dir_b)

    # Clone the repository
    try:
        logging.info(f"Cloning the repository into {repo_dir_a}...")
        Repo.clone_from(repo_url, repo_dir_a)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to clone repository into {repo_dir_a}: {e}")

    # Clone the repository again into 'repo_b'
    try:
        logging.info(f"Cloning the repository into {repo_dir_b}...")
        Repo.clone_from(repo_url, repo_dir_b)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to clone repository into {repo_dir_b}: {e}")


    initial_diff = generate_initial_diff(prompt, repo_dir_a)
    final_diff, summary = reflection_step(initial_diff, prompt)
    
    
    # shutil.rmtree(repo_dir)  # Clean up the repo directory
    # The line `# output_modified_code(repo_dir, final_diff)` is a commented-out line in the code
    # snippet you provided. It appears to be a placeholder or a reminder for a function or operation
    # that was intended to be implemented but is currently not being used.
    output_modified_code(repo_dir_b, final_diff)

    data_to_store = {
        "repo_url": repo_url,
        "prompt": prompt,
        "diff": final_diff,
        "summary": summary,
    }

    # Attempt to store the data in Supabase
    try:
        response = supabase.table("tinygen_requests").insert(data_to_store).execute()

        # Check if any data was returned (meaning success)
        if not response.data:
            logging.error(f"Failed to insert data into Supabase: {response}")
            raise HTTPException(
                status_code=500, detail="Failed to store data in Supabase."
            )

        logging.info("Data successfully inserted into Supabase.")

    except Exception as e:
        logging.error(f"Error inserting data into Supabase: {e}")
        raise HTTPException(status_code=500, detail="Failed to store data in Supabase.")

    logging.info("DIFF GENERATED")
    print(final_diff)

    return {"summary": summary, "diff": final_diff}



# This endpoint generates the diff without storing the fixed code in the repository
@app.post("/generate-diff-no-code")
async def generate_diff_no_code(data: RequestData):
    repo_url = data.repoUrl
    prompt = data.prompt
    repo_dir = "temp_repo"

    # Clean up any existing repo directory
    if os.path.exists(repo_dir):
        shutil.rmtree(repo_dir)

    # Clone the repository
    try:
        Repo.clone_from(repo_url, repo_dir)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to clone repository: {e}")

    initial_diff = generate_initial_diff(prompt, repo_dir)
    final_diff, summary = reflection_step(initial_diff, prompt)
    shutil.rmtree(repo_dir)  # Clean up the repo directory
    # output_modified_code(repo_dir, final_diff)

    data_to_store = {
        "repo_url": repo_url,
        "prompt": prompt,
        "diff": final_diff,
        "summary": summary,
    }

    # Attempt to store the data in Supabase
    try:
        response = supabase.table("tinygen_requests").insert(data_to_store).execute()

        # Check if any data was returned (meaning success)
        if not response.data:
            logging.error(f"Failed to insert data into Supabase: {response}")
            raise HTTPException(
                status_code=500, detail="Failed to store data in Supabase."
            )

        logging.info("Data successfully inserted into Supabase.")

    except Exception as e:
        logging.error(f"Error inserting data into Supabase: {e}")
        raise HTTPException(status_code=500, detail="Failed to store data in Supabase.")

    logging.info("DIFF GENERATED")
    print(final_diff)

    return {"summary": summary, "diff": final_diff}
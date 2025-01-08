#import subprocess
from datetime import datetime
from pydantic import BaseModel
from fastapi import APIRouter
import os
from git import Repo
import shutil

router = APIRouter()

class GitInfoResponse(BaseModel):
    commit_hash: str = ""
    author: str = ""
    email: str = ""
    date: datetime = None
    message: str = ""

    
@router.get("/last_commit/", response_model=GitInfoResponse)
def get_last_commit():
    TEMP_DIR = os.path.join(os.path.dirname(__file__), 'temp')


    # Embed credentials into the URL
    authenticated_url = os.getenv("GIT_URL")

    if not os.path.exists(TEMP_DIR):
        os.makedirs(TEMP_DIR)
    
    
    repo = Repo.init(TEMP_DIR, bare=True)
    # Fetch the remote branch into the bare repository
    remote = repo.create_remote('origin', authenticated_url)
    remote.fetch()
    
    # Specify the branch you want to check
    remote_branch = "origin/develop" 
    
    # Access the last commit of the remote branch
    last_commit = repo.commit(remote_branch)   
    
    git_response = GitInfoResponse(
            commit_hash=last_commit.hexsha,
            author=last_commit.author.name,
            email=last_commit.author.email,
            date=last_commit.committed_datetime,
            message=last_commit.message,
        )
    # Cleanup (optional, if you want to delete the temporary directory afterward)
    shutil.rmtree(TEMP_DIR)
    
    return git_response 
    

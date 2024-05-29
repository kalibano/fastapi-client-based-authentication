from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel
from jose import JWTError, jwt
from datetime import datetime, timedelta
# from subprocess import Popen, PIPE, STDOUT
import subprocess
import json
import os
from fastapi.encoders import jsonable_encoder
import logging
from logging.handlers import RotatingFileHandler
from fastapi.middleware.cors import CORSMiddleware
from typing import List


# set up logging
log_formatter = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
log_file = "app.log"

file_handler = RotatingFileHandler(
    log_file, maxBytes=1024*1024*5, backupCount=5)
file_handler.setFormatter(log_formatter)
file_handler.setLevel(logging.DEBUG)

console_handler = logging.StreamHandler()
console_handler.setFormatter(log_formatter)
console_handler.setLevel(logging.DEBUG)

logger = logging.getLogger("fastapi_app")
logger.setLevel(logging.DEBUG)
logger.addHandler(file_handler)
logger.addHandler(console_handler)


# Constants for JWT encoding
SECRET_KEY = "your key"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Dummy client credentials
CLIENT_ID = "your id"
CLIENT_SECRET = "your secret"

# Create the FastAPI app
app = FastAPI()

# OAuth2 password bearer instance
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


class ClientCredentials(BaseModel):
    client_id: str
    client_secret: str


class CommandDetails(BaseModel):
    command: List = []
    inputs: str


class Token(BaseModel):
    access_token: str
    token_type: str


def authenticate_client(credentials: ClientCredentials):
    if credentials.client_id == CLIENT_ID and credentials.client_secret == CLIENT_SECRET:
        return True
    return False


def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


@app.post("/token", response_model=Token)
async def login_for_access_token(credentials: ClientCredentials):
    if not authenticate_client(credentials):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid client credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"client_id": credentials.client_id},
        expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}


@app.post("/execute-command/")
async def execute_command_route(commandDetails: CommandDetails, token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        client_id: str = payload.get("client_id")
        if client_id is None or client_id != CLIENT_ID:
            logger.error("Invalid client credentials")
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                                detail="Invalid client credentials", headers={"www-Authenticate": "Bearer"})

        response = execute_command(commandDetails)
        print("Command execution completed.")

        return {"response": response}

        # return {"message": f"Command '{commandDetails.command}' is being executed."}
    except JWTError:
        logger.error("Could not validate credentials")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="Could not validate credentials", headers={"www-Authenicate": "Bearer"})


def execute_command(commandDetails):
    try:

        result = subprocess.run(
            commandDetails.command, input=commandDetails.inputs, text=True, capture_output=True, check=True)

        # Execute the command using subprocess

        current_dir = os.getcwd()

        output_file_path = os.path.abspath(current_dir + "/output.json")

        existing_data = []

        try:
            with open(output_file_path, 'r') as file:
                try:
                    existing_data = json.load(file)
                except json.JSONDecodeError:
                    logger.warning("file is empty or contains invalid JSON.")
        except Exception as read_error:
            logger.error(f"Error reading file: {read_error}")
            raise HTTPException(
                status_code=500, detail=f"Error reading file: {str(read_error)}")

        existing_data.append(jsonable_encoder(result))

        try:
            with open(output_file_path, 'w') as file:
                json.dump(existing_data, file)
        except Exception as write_error:
            logger.error(f"Error writing to file: {write_error}")
            raise HTTPException(
                status_code=500, detail=f"Error writing to file:{str(write_error)}")
        return result.stdout
    except Exception as e:
        logger.error(f"Error writing to file: {e}")
        raise HTTPException(
            status_code=500, detail=f"Unexpected error: {str(e)}")

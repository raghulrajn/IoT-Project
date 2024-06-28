# main.py
import subprocess
from fastapi import FastAPI, File, UploadFile
import os
import uuid

app = FastAPI()

@app.post("/uploadfiles/")
async def create_upload_files(file1: UploadFile = File(...), file2: UploadFile = File(...)):
    # Save the uploaded files to disk with unique names
    unique_id = str(uuid.uuid4())
    file1_path = f"./tmp/{unique_id}_{file1.filename}"
    file2_path = f"./tmp/{unique_id}_{file2.filename}"
    
    with open(file1_path, "wb") as f1, open(file2_path, "wb") as f2:
        f1.write(await file1.read())
        f2.write(await file2.read())
    print(f"Saved files to: {file1_path}, {file2_path}")
    # Run the local Python script with the file paths as arguments
    result = subprocess.run(["python3", "fast-downward.py", file1_path, file2_path, "--search", 'astar(lmcut())'],
                             capture_output=True, text=True,cwd=os.path.dirname(os.path.abspath(__file__)))
    
    # Clean up the saved files
    os.remove(file1_path)
    os.remove(file2_path)
    
    # Return the output of the script as the response
    return {"output": result.stdout, "error": result.stderr}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

# AI-Planner

This python code as a server which is used to run the [AI-planner](https://github.com/AI-Planning/planning-as-a-service) and get the response through a POST request.

## To start the server
````
uvicorn main_api:app --reload
````
## Get the response for a Domain and a problem  
````
curl -F "file1=@./domain.pddl" -F "file2=@./problem.pddl" http://127.0.0.1:8000/uploadfiles/
````

Refer to [AI-planner](https://github.com/AI-Planning/planning-as-a-service) documentation for installation of planner



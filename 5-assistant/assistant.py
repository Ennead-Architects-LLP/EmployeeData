"""this is a assisant that handle the question from the user and return the answer



this will listen to github action dispalt to receive POST request, perform the querry from storedVectorebase and return the answer


The apikey will be getting from the github repo secret or local environment variable



to work with this, we also need a dialy worflow that update the vectorestore based on the employee.json so the open ai call will be more efficient




assistant workflow:
1. receive the question from the user from github page via POST request
2. perform the querry from storedVectorebase and return the answer


the vector store will be kept in this 5-assistant folder.




"""
This project aims at building a simple fast api.

## Project 1: The "Controlled" Inference API (Validation & Security)

**Challenge:**  
A Data Scientist often lets anything pass through their script. An Engineer must protect their system against malicious or erroneous inputs.

**Scope:**  
Create an API that receives a text input and returns either a sentiment score or a summary using an LLM (local or API).

### Technical Objectives

- **Strict Pydantic Validation:**  
   Create an input schema that enforces a minimum/maximum text length and prohibits certain characters.

- **Error Handling (Exception Handlers):**  
   If the LLM times out or returns an error, the API must not crash with a 500 error. Instead, it should return a clean JSON response (e.g., 503 Service Unavailable) with a clear message.

- **Rate Limiting:**  
   Add logic (even simple, in-memory) to limit requests to 5 per minute per user.

**What You Learn:**  
Building robustness against end-user interactions.

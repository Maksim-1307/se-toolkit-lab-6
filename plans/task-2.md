# Plans for the task 2

## 1. Tool Schemas

I'll use `JSON` format to describe tool schemas. I'll store all tool schemas in `agent/tools.json` and then parse them in `agent.py`. Format of the tool schema is defined in the official OpenRouter docs. Implementation of schemas will be done in `agent/tools.py`.

## 2. Agentic Loop

I'll use an usual while loop to implement the agentic loop.

## 3. Path Security

To prevent `../` attacks, I'll resolve any relative paths into absolute paths, and then check if the path is inside the project directory. I'm going to use `pathlib` to do this.
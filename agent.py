import requests
import dotenv
import sys
import os
import json
import traceback
from colorama import init, Fore, Style

from agent.tools import *

global LLM_API_KEY
global LLM_API_BASE
global LLM_MODEL
global LLM_TEMPERATURE
global LLM_TOOLS
global LMS_API_KEY
global AGENT_API_BASE_URL

chat_history = []
tool_calls_log = []
system_prompt = """You are a helpful documentation assistant. You have access to tools to read files, list directories, and query the live backend API.

When answering questions:
1. For wiki/documentation questions: Use list_files to discover files in wiki/, then read_file_content to find answers
2. For source code questions: Use read_file_content to read the relevant source files
3. For live data questions (item counts, status codes, analytics): Use query_api to query the running backend
4. For bug diagnosis: First use query_api to reproduce the error, then read_file_content to find the buggy code

Always use tools to find answers - do not rely on your pre-trained knowledge.

Tool selection guide:
- "According to the wiki..." or "What does the wiki say..." → Use read_file_content on wiki/ files
- "What framework does the backend use?" or "Read the source code" → Use read_file_content on backend/ files
- "How many items..." or "Query the API" or "What status code..." → Use query_api
- "List all API routers" → Use list_files on backend/api/"""

# get prompt from command line
def get_user_input():
    if len(sys.argv) < 2:
        raise Exception("No user input")
    return sys.argv[1]

# load environment variables
def get_env():

    dotenv.load_dotenv(".env.agent.secret")
    dotenv.load_dotenv(".env.docker.secret")

    global LLM_API_KEY
    global LLM_API_BASE
    global LLM_MODEL
    global LLM_TEMPERATURE
    global LMS_API_KEY
    global AGENT_API_BASE_URL

    LLM_API_KEY = os.getenv("LLM_API_KEY")
    LLM_API_BASE = os.getenv("LLM_API_BASE")
    LLM_MODEL = os.getenv("LLM_MODEL")
    LLM_TEMPERATURE = os.getenv("LLM_TEMPERATURE")
    
    # Backend API authentication and URL
    LMS_API_KEY = os.getenv("LMS_API_KEY")
    AGENT_API_BASE_URL = os.getenv("AGENT_API_BASE_URL", "http://localhost:42002")
    
    # Export for tools.py to access
    os.environ["LMS_API_KEY"] = LMS_API_KEY or ""
    os.environ["AGENT_API_BASE_URL"] = AGENT_API_BASE_URL

    if not LLM_API_KEY:
        raise Exception("LLM_API_KEY is not set")
    if not LLM_API_BASE:
        raise Exception("LLM_API_BASE is not set")
    if not LLM_MODEL:
        raise Exception("LLM_MODEL is not set")
    if not LLM_TEMPERATURE:
        raise Exception("LLM_TEMPERATURE is not set")

# parse tools from tools.json
def parse_tools():
    global LLM_TOOLS
    with open("agent/tools.json") as f:
        tools = json.load(f)
        LLM_TOOLS = tools

# send request to the LLM API
def send_request():
    global LLM_API_KEY
    global LLM_API_BASE
    global LLM_MODEL
    global LLM_TEMPERATURE
    global LLM_TOOLS
    global chat_history
    global system_prompt

    # Prepend system prompt as first message
    messages = [{"role": "system", "content": system_prompt}] + chat_history

    response = requests.post(
        f"{LLM_API_BASE}/chat/completions",
        headers={
            "Authorization": f"Bearer {LLM_API_KEY}",
            "Content-Type": "application/json"
        },
        json={
            "model": LLM_MODEL,
            "messages": messages,
            "tools": LLM_TOOLS,
            "tool_choice": "auto",
            "max_tokens": 1024,
            "temperature": float(LLM_TEMPERATURE),
        },
    )

    if not response.ok:
        raise Exception(f"LLM API error: {response.status_code}, response: {response.json()}")

    data = response.json()
    message = data['choices'][0]['message']

    # Add assistant message to chat history
    chat_history.append({
        "role": "assistant",
        "content": message.get('content'),
        "tool_calls": message.get('tool_calls')
    })

    return message

# run the agentic loop
def agentic_loop(prompt: str):
    global tool_calls_log

    chat_history.append({"role": "user", "content": prompt})
    final_answer = None

    while True:
        try:
            response = send_request()

            content = response.get('content')
            tool_calls = response.get('tool_calls')
            tool_results = []
            has_tools = False

            # Handle text content
            if content:
                print(f"{Fore.GREEN}{Style.BRIGHT}Assistant:\n{Style.RESET_ALL}{Fore.GREEN}{content}{Style.RESET_ALL}\n", file=sys.stderr)
                final_answer = content

            # Handle tool calls (OpenAI format)
            if tool_calls:
                has_tools = True
                for tool_call in tool_calls:
                    function_name = tool_call['function']['name']
                    function_args = json.loads(tool_call['function']['arguments'])
                    tool_call_id = tool_call['id']

                    print(f"{Fore.YELLOW}{Style.BRIGHT}Executing tool: {function_name}{Style.RESET_ALL}", file=sys.stderr)

                    result_data = globals()[function_name](function_args)
                    result_str = result_data.stdout if hasattr(result_data, 'stdout') else str(result_data)

                    print(f"{Fore.BLUE}Tool output: {result_str}{Style.RESET_ALL}\n", file=sys.stderr)

                    tool_calls_log.append({
                        "tool": function_name,
                        "args": function_args,
                        "result": result_str
                    })

                    tool_results.append({
                        "role": "tool",
                        "tool_call_id": tool_call_id,
                        "content": result_str
                    })

            if has_tools:
                # Add tool results to chat history
                chat_history.extend(tool_results)
            else:
                break

        except Exception as e:
            print(f"Error: {e}", file=sys.stderr)
            print(traceback.format_exc(), file=sys.stderr)
            exit(1)

    return final_answer

if __name__ == "__main__":
    try:
        get_env()
        parse_tools()
        prompt = get_user_input()
        final_answer = agentic_loop(prompt)

        # Extract source from the last read_file_content call
        source = ""
        for call in reversed(tool_calls_log):
            if call["tool"] == "read_file_content":
                file_path = call["args"].get("file_path", "")
                if file_path:
                    source = file_path
                    break

        output = {
            "answer": final_answer,
            "source": source,
            "tool_calls": tool_calls_log
        }
        print(json.dumps(output))

        exit(0)

    except requests.exceptions.ConnectionError as e:
        print(f"Network error occurred: {e}", file=sys.stderr)

    except requests.exceptions.Timeout as e:
        print(f"The request timed out: {e}", file=sys.stderr)

    except requests.exceptions.HTTPError as e:
        print(f"The API returned an error: {e}", file=sys.stderr)

    except requests.exceptions.RequestException as e:
        print(f"An ambiguous error occurred: {e}", file=sys.stderr)

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        print(traceback.format_exc(), file=sys.stderr)
        exit(1)
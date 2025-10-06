import os
import sys

import psycopg2

from dotenv import load_dotenv
from src.utilities.prompts import CLASSIFIER_PROMPT, METADATA_PROMPT, SUPERVISOR_PROMPT
from
sys.path.append(os.path.abspath('.'))



# Load environment variables from .env file 
load_dotenv()

# Connection parameters
conn_params = {
    "host": os.getenv("PG_DB_HOST"),
    "port": int(os.getenv("PG_DB_PORT", 5432)),
    "dbname": os.getenv("PG_DB_NAME"),
    "user": os.getenv("PG_USER"),
    "password": os.getenv("PG_PASSWORD"),
    "options": f'-c search_path={os.getenv("MAS_MPD_SCHEMA")}'
}


agents = {
    "root": {"name":"root Agent","agent_group": "classifier", "prompt":SUPERVISOR_PROMPT},
    "metadata": {"name":"metadata Agent","agent_group": "classifier", "prompt":METADATA_PROMPT},
    "classifier": {"name":"classification Agent","agent_group": "classifier", "prompt":CLASSIFIER_PROMPT},
}

def insert_prompt(conn, agent: str, prompt: str, agent_group:str, status:str="active"):
    """Inserts a prompt into the prompts table."""
    sql = """
        INSERT INTO prompts (agent, prompt, status, agent_group)
        VALUES (%s, %s, %s, %s)
        RETURNING prompt_id
    """
    with conn.cursor() as cur:
        cur.execute(sql, (agent, prompt, status, agent_group))
        return cur.fetchone()[0]

def main():

    with psycopg2.connect(**conn_params) as conn:
        for agent_name, agent_info in agents.items():
            agent = agent_info["name"]
            agent_group = agent_info["agent_group"]
            prompt = agent_info["prompt"]
            try:
                prompt_id = insert_prompt(conn, agent=agent,
                                          prompt=prompt, 
                                          agent_group=agent_group)
                print(f"Inserted prompt for {agent} with ID: {prompt_id}")
            except Exception as e:
                print(f"Error inserting prompt for {agent}: {e}")
if __name__ == "__main__":
    main()

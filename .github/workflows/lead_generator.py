import requests
import json
from openai import OpenAI
from config import OPENAI_API_KEY
from prompts import FOUNDER_PROMPT
from db import get_conn

client = OpenAI(api_key=OPENAI_API_KEY)

def fetch_tokens():
    response = requests.get("https://api.dexscreener.com/latest/dex/pairs/solana")
    data = response.json()
    return data.get("pairs", [])

def filter_tokens(pairs):
    results = []
    for p in pairs:
        try:
            mcap = float(p.get("fdv", 0))
            desc = p.get("baseToken", {}).get("name", "")
            website = p.get("info", {}).get("website")
            telegram = p.get("info", {}).get("telegram")

            if 1_000_000 <= mcap <= 10_000_000 and website and telegram:
                results.append({
                    "name": p["baseToken"]["name"],
                    "description": desc,
                    "mcap": mcap,
                    "website": website,
                    "telegram": telegram
                })
        except:
            continue
    return results

def generate_pitch(token):
    prompt = FOUNDER_PROMPT.format(
        name=token["name"],
        description=token["description"],
        mcap=token["mcap"]
    )

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7
    )

    return response.choices[0].message.content

def save_lead(token, pitch):
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
    INSERT INTO leads (token_name, mcap, description, telegram, website, pitch)
    VALUES (%s, %s, %s, %s, %s, %s)
    """, (
        token["name"],
        token["mcap"],
        token["description"],
        token["telegram"],
        token["website"],
        pitch
    ))

    conn.commit()
    cur.close()
    conn.close()

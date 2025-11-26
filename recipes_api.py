# recipes_api.py
# Requires: pip install fastapi uvicorn python-multipart rapidfuzz

import json
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List
from rapidfuzz import fuzz
from fastapi.staticfiles import StaticFiles

app = FastAPI(title="Local Recipe Suggestion API")

#  CORS FIX 
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],     
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Load recipes
with open("recipes.json", "r", encoding="utf-8") as f:
    RECIPES = json.load(f)

class Query(BaseModel):
    ingredients: List[str]  # e.g. ["egg", "onion"]

def score_recipe(recipe_ings, query_ings):
    qset = set(i.lower() for i in query_ings)
    rset = set(i.lower() for i in recipe_ings)
    matched = qset & rset

    # Overlap scoring (70%)
    overlap_ratio = len(matched) / max(1, len(qset))
    overlap_score = overlap_ratio * 70

    # Fuzzy scoring (30%)
    fuzzy_scores = []
    for qi in qset:
        best = 0
        for ri in rset:
            s = fuzz.WRatio(qi, ri)
            if s > best:
                best = s
        fuzzy_scores.append(best / 100.0)

    fuzzy_avg = sum(fuzzy_scores) / len(fuzzy_scores) if fuzzy_scores else 0
    fuzzy_score = fuzzy_avg * 30

    total = overlap_score + fuzzy_score
    return total, matched

@app.post("/suggest")
def suggest(query: Query):
    results = []
    for r in RECIPES:
        s, matched = score_recipe(r["ingredients"], query.ingredients)
        results.append({
            "id": r["id"],
            "title": r["title"],
            "score": round(s, 2),
            "matched_ingredients": list(matched),
            "ingredients": r["ingredients"],
            "instructions": r["instructions"]
        })

    results_sorted = sorted(results, key=lambda x: x["score"], reverse=True)
    best = results_sorted[0] if results_sorted else None
    return {"best_match": best, "ranked_matches": results_sorted}


app.mount("/ui", StaticFiles(directory=".", html=True), name="static")


from fastapi import APIRouter, HTTPException, BackgroundTasks, Query
from app.models.schemas import ScrapeRequest, PostSchema, FilterRequest, StatisticsResponse
from app.database import posts_collection
from app.scraper.scraper import scrape_facebook_post
import uuid
import datetime

router = APIRouter()

@router.post("/scrape")
async def trigger_scrape(request: ScrapeRequest, background_tasks: BackgroundTasks):
    try:
        # Create a unique ID for the post
        post_id = str(uuid.uuid4())
        # initiate background scraping
        background_tasks.add_task(scrape_facebook_post, request.url, post_id)
        return {"message": "Scraping started", "post_id": post_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/posts")
async def get_posts(
    start_date: str = Query(None, description="Start date in YYYY-MM-DD format"),
    end_date: str = Query(None, description="End date in YYYY-MM-DD format"),
    skip: int = 0,
    limit: int = 20
):
    query = {}
    if start_date or end_date:
        query["post_date"] = {}
        if start_date:
            query["post_date"]["$gte"] = start_date
        if end_date:
            query["post_date"]["$lte"] = end_date

    cursor = posts_collection.find(query).skip(skip).limit(limit)
    posts = await cursor.to_list(length=limit)
    # Convert ObjectIds to strings
    for post in posts:
        post["_id"] = str(post["_id"])
    return posts

@router.get("/posts/{post_id}")
async def get_post(post_id: str):
    post = await posts_collection.find_one({"post_id": post_id})
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    post["_id"] = str(post["_id"])
    return post

@router.put("/posts/{post_id}")
async def update_post(post_id: str, updated_post: PostSchema):
    result = await posts_collection.update_one(
        {"post_id": post_id},
        {"$set": updated_post.dict(exclude={"created_at"})}
    )
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Post not found or no changes made")
    return {"message": "Post updated successfully"}

@router.delete("/posts/{post_id}")
async def delete_post(post_id: str):
    result = await posts_collection.delete_one({"post_id": post_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Post not found")
    return {"message": "Post deleted successfully"}

@router.get("/stats", response_model=StatisticsResponse)
async def get_statistics():
    total_posts = await posts_collection.count_documents({})
    
    pipeline = [
        {"$project": {
            "num_comments": {"$size": "$comments"},
            "post_tokens": {"$size": {"$split": ["$post_text", " "]}},
            "comments_tokens": {
                "$reduce": {
                    "input": "$comments",
                    "initialValue": 0,
                    "in": {"$add": ["$$value", {"$size": {"$split": ["$$this.text", " "]}}]}
                }
            }
        }},
        {"$group": {
            "_id": None,
            "total_comments": {"$sum": "$num_comments"},
            "total_post_tokens": {"$sum": "$post_tokens"},
            "total_comments_tokens": {"$sum": "$comments_tokens"}
        }}
    ]
    
    result = await posts_collection.aggregate(pipeline).to_list(length=1)
    
    if result:
        total_comments = result[0].get("total_comments", 0)
        total_tokens = result[0].get("total_post_tokens", 0) + result[0].get("total_comments_tokens", 0)
    else:
        total_comments = 0
        total_tokens = 0
        
    return StatisticsResponse(
        total_posts=total_posts,
        total_comments=total_comments,
        total_tokens=total_tokens
    )

import pandas as pd
from fastapi.responses import Response, JSONResponse
import json

@router.get("/export")
async def export_data(
    format: str = Query("csv", description="Export format: csv, json, or jsonl"),
    start_date: str = Query(None, description="Start date in YYYY-MM-DD format"),
    end_date: str = Query(None, description="End date in YYYY-MM-DD format"),
):
    query = {}
    if start_date or end_date:
        query["post_date"] = {}
        if start_date:
            query["post_date"]["$gte"] = start_date
        if end_date:
            query["post_date"]["$lte"] = end_date

    cursor = posts_collection.find(query)
    posts = await cursor.to_list(length=None)
    
    # Flatten data for CSV and JSONL
    flattened_data = []
    for post in posts:
        base_record = {
            "post_id": post.get("post_id"),
            "post_text": post.get("post_text"),
            "post_date": post.get("post_date")
        }
        comments = post.get("comments", [])
        if not comments:
            flattened_data.append({**base_record, "comment_text": "", "comment_date": ""})
        else:
            for comment in comments:
                flattened_data.append({
                    **base_record,
                    "comment_text": comment.get("text", ""),
                    "comment_date": comment.get("date", "")
                })

    if format == "csv":
        df = pd.DataFrame(flattened_data)
        csv_data = df.to_csv(index=False)
        return Response(content=csv_data, media_type="text/csv", headers={"Content-Disposition": "attachment; filename=export.csv"})
        
    elif format == "json":
        for post in posts:
            post["_id"] = str(post["_id"])
        return JSONResponse(content=posts, headers={"Content-Disposition": "attachment; filename=export.json"})
        
    elif format == "jsonl":
        jsonl_data = "\n".join([json.dumps(record, default=str) for record in flattened_data])
        return Response(content=jsonl_data, media_type="application/x-ndjson", headers={"Content-Disposition": "attachment; filename=export.jsonl"})
        
    else:
        raise HTTPException(status_code=400, detail="Invalid format. Supported formats are csv, json, jsonl.")

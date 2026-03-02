import io
from fastapi import APIRouter, HTTPException, BackgroundTasks, Query
from app.models.schemas import ScrapeRequest, PostSchema, FilterRequest, StatisticsResponse
from app.database import posts_collection
from app.scraper import scrape_facebook_post
import uuid
import datetime
import pandas as pd
from fastapi.responses import Response, JSONResponse
import json


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
            "num_comments": {"$size": {"$ifNull": ["$comments", []]}},
            # Use $ifNull to prevent split errors on empty posts
            "post_tokens": {
                "$size": {"$split": [{"$ifNull": ["$post_text", ""]}, " "]}
            },
            "comments_tokens": {
                "$reduce": {
                    "input": {"$ifNull": ["$comments", []]},
                    "initialValue": 0,
                    "in": {"$add": [
                        "$$value", 
                        {"$size": {"$split": [{"$ifNull": ["$$this.text", ""]}, " "]}}
                    ]}
                }
            }
        }},
        {"$group": {
            "_id": None,
            "total_comments": {"$sum": "$num_comments"},
            "total_tokens": {"$sum": {"$add": ["$post_tokens", "$comments_tokens"]}}
        }}
    ]
    
    result = await posts_collection.aggregate(pipeline).to_list(length=1)
    
    stats = result[0] if result else {}
    return StatisticsResponse(
        total_posts=total_posts,
        total_comments=stats.get("total_comments", 0),
        total_tokens=stats.get("total_tokens", 0)
    )


@router.get("/export")
async def export_data(
    format: str = Query("json", regex="^(csv|json|jsonl)$"),
    start_date: str = None,
    end_date: str = None,
):
    query = {}
    if start_date or end_date:
        query["post_date"] = {}
        if start_date:
            query["post_date"]["$gte"] = start_date
        if end_date:
            query["post_date"]["$lte"] = end_date

    cursor = posts_collection.find(query)
    posts = await cursor.to_list(length=1000)
    if not posts:
        return JSONResponse(content={"message": "No data found for the selected range"}, status_code=404)
    # Flatten data for CSV and JSONL
    flattened_data = []
    for post in posts:
        base = {
            "post_id": post.get("post_id"),
            "post_url": post.get("url"),
            "post_text": post.get("post_text"),
            "post_date": post.get("post_date")
        }
        comments = post.get("comments", [])
        if not comments:
            flattened_data.append({**base, "comment_author": "", "comment_text": "", "comment_date": ""})
        else:
            for c in comments:
                flattened_data.append({
                    **base,
                    "comment_author": c.get("author", "Unknown"),
                    "comment_text": c.get("text", ""),
                    "comment_date": c.get("date", "")
                })
                
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M")

    # --- FORMAT 2: CSV (Data Science Standard) ---
    if format == "csv":
        df = pd.DataFrame(flattened_data)
        stream = io.StringIO()
        df.to_csv(stream, index=False, encoding='utf-8-sig') # utf-8-sig for Excel compatibility
        return Response(
            content=stream.getvalue(),
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename=fb_export_{timestamp}.csv"}
        )
    
    # --- FORMAT 3: JSONL (Large Dataset/BigQuery Standard) ---
    if format == "jsonl":
        # Standard JSONL: Each line is a standalone JSON object
        jsonl_lines = [json.dumps(record, default=str) for record in flattened_data]
        jsonl_content = "\n".join(jsonl_lines)
        return Response(
            content=jsonl_content,
            media_type="application/x-ndjson",
            headers={"Content-Disposition": f"attachment; filename=fb_data_{timestamp}.jsonl"}
            )
    if format == "json":
        for post in posts:
            post["_id"] = str(post["_id"]) # Standardize MongoDB IDs
        return JSONResponse(
            content=posts,
            headers={"Content-Disposition": f"attachment; filename=fb_data_{timestamp}.json"}
        )
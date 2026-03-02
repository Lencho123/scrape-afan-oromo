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

@router.get("/posts")
async def get_posts(skip: int = 0, limit: int = 20):
    cursor = posts_collection.find().skip(skip).limit(limit)
    posts = await cursor.to_list(length=limit)
    
    # Format the data to your specific requirements
    formatted_posts = []
    for p in posts:
        formatted_posts.append({
            "post_id": p.get("post_id"),
            "post": p.get("post_text"),
            "comments": p.get("comments", []) # List of strings
        })
    return formatted_posts

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
        if start_date: query["post_date"]["$gte"] = start_date
        if end_date: query["post_date"]["$lte"] = end_date

    cursor = posts_collection.find(query)
    posts = await cursor.to_list(length=1000)

    if not posts:
        raise HTTPException(status_code=404, detail="No data found")

    # Transform into your requested form
    simplified_data = []
    for p in posts:
        simplified_data.append({
            "post_id": p.get("post_id"),
            "post": p.get("post_text"),
            "comments": p.get("comments", []) # ["comment1", "comment2"]
        })

    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M")

    if format == "json":
        return JSONResponse(
            content=simplified_data,
            headers={"Content-Disposition": f"attachment; filename=fb_export_{timestamp}.json"}
        )

    if format == "jsonl":
        # Each line is one post object with its array of comments
        jsonl_content = "\n".join([json.dumps(r, ensure_ascii=False) for r in simplified_data])
        return Response(
            content=jsonl_content,
            media_type="application/x-ndjson",
            headers={"Content-Disposition": f"attachment; filename=fb_export_{timestamp}.jsonl"}
        )

    if format == "csv":
        # For CSV, we join comments with a newline or pipe because CSVs are flat
        csv_data = []
        for item in simplified_data:
            csv_data.append({
                "post_id": item["post_id"],
                "post": item["post"],
                "comments": "\n".join(item["comments"]) # Newline inside the cell
            })
        df = pd.DataFrame(csv_data)
        stream = io.StringIO()
        df.to_csv(stream, index=False, encoding='utf-8-sig')
        return Response(
            content=stream.getvalue(),
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename=fb_export_{timestamp}.csv"}
        )
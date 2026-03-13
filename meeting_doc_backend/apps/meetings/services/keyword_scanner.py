
KEYWORD_CATEGORIES = {
    "architecture": [
        "architecture", "diagram", "system design",
        "infrastructure", "flow", "pipeline", "microservice",
        "let me show", "as you can see", "here you can see",
        "here is the", "look at this", "showing here"
    ],
    "code": [
        "code", "function", "class", "import", "script",
        "terminal", "repository", "implementation",
        "let me walk", "pull request", "commit", "deploy",
        "jenkins", "github", "server", "rdp", "configuration"
    ],
    "task_list": [
        "action items", "tasks", "todo", "next steps",
        "we need to", "someone needs to", "assigned to",
        "follow up", "action item", "take care of"
    ],
    "data": [
        "dashboard", "metrics", "graph", "chart", "analytics",
        "numbers", "results", "performance", "utilization",
        "cpu", "memory", "drive", "storage"
    ],
    "discussion": [
        "question", "issue", "problem", "solution",
        "proposal", "decision", "agreed", "let's"
    ]
}

def scan_for_key_timestamps(transcript_timestamps, max_frames=5, min_gap_seconds=30):
    """
    Scans transcript timestamps for keywords and returns top semantic moments.
    """
    matches = []
    
    for entry in transcript_timestamps:
        text = entry.get("text", "").lower()
        start = entry.get("start", 0)
        
        for category, keywords in KEYWORD_CATEGORIES.items():
            score = 0
            for kw in keywords:
                if kw in text:
                    score += 1
            
            if score > 0:
                matches.append({
                    "timestamp_seconds": int(start),
                    "category": category,
                    "matched_text": entry.get("text", ""),
                    "score": score
                })
    
    # Sort by score descending, then timestamp
    matches.sort(key=lambda x: (-x["score"], x["timestamp_seconds"]))
    
    # Apply min_gap_seconds filter and pick top max_frames with category diversity
    selected = []
    last_timestamp = -1000
    
    # 3. Sort all matches by timestamp_seconds (per user instructions)
    matches.sort(key=lambda x: x["timestamp_seconds"])
    
    # 4. Apply min_gap_seconds filter
    filtered_matches = []
    for m in matches:
        if m["timestamp_seconds"] >= last_timestamp + min_gap_seconds:
            filtered_matches.append(m)
            last_timestamp = m["timestamp_seconds"]
            
    if not filtered_matches:
        # 8. If no matches found return evenly spaced timestamps
        total_duration = transcript_timestamps[-1]["start"] + transcript_timestamps[-1]["duration"] if transcript_timestamps else 300
        return [
            {
                "timestamp_seconds": int(total_duration * i / max_frames),
                "category": "discussion",
                "matched_text": "Evenly spaced frame"
            }
            for i in range(max_frames)
        ]

    # 5. From filtered matches pick top max_frames prioritizing category diversity
    final_matches = []
    used_categories = set()
    
    # Pass 1: One from each category
    for category in KEYWORD_CATEGORIES.keys():
        for m in filtered_matches:
            if m["category"] == category and m not in final_matches:
                final_matches.append(m)
                used_categories.add(category)
                break
        if len(final_matches) >= max_frames:
            break
            
    # Pass 2: Fill remaining slots
    if len(final_matches) < max_frames:
        for m in filtered_matches:
            if m not in final_matches:
                final_matches.append(m)
                if len(final_matches) >= max_frames:
                    break
                    
    # 6. Sort final selection by timestamp_seconds
    final_matches.sort(key=lambda x: x["timestamp_seconds"])
    
    # 7. Return list of { timestamp_seconds, category, matched_text }
    return [
        {
            "timestamp_seconds": m["timestamp_seconds"],
            "category": m["category"],
            "matched_text": m["matched_text"]
        }
        for m in final_matches[:max_frames]
    ]

from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
from typing import List
import os
import uuid
from pathlib import Path
import shutil
from datetime import datetime

router = APIRouter(prefix="/upload", tags=["upload"])

# Create uploads directory if it doesn't exist
UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

@router.post("/")
async def upload_file(file: UploadFile = File(...)):
    """
    Upload a single file and return its URL.

    This endpoint accepts file uploads and stores them in the uploads directory.
    Returns the file URL that can be used in chat requests.
    """
    try:
        # Validate file type
        allowed_types = [
            'image/jpeg', 'image/png', 'image/gif', 'image/webp',
            'application/pdf', 'text/plain', 'text/markdown',
            'application/msword', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
        ]

        if file.content_type not in allowed_types:
            raise HTTPException(
                status_code=400,
                detail=f"File type {file.content_type} not allowed. Allowed types: {', '.join(allowed_types)}"
            )

        # Validate file size (max 10MB)
        file_size = 0
        content = await file.read()
        file_size = len(content)

        if file_size > 10 * 1024 * 1024:  # 10MB
            raise HTTPException(status_code=400, detail="File size too large. Maximum size is 10MB")

        # Generate unique filename
        file_extension = Path(file.filename).suffix
        unique_filename = f"{uuid.uuid4()}{file_extension}"
        file_path = UPLOAD_DIR / unique_filename

        # Save file
        with open(file_path, "wb") as buffer:
            buffer.write(content)

        # Return file information
        file_url = f"/uploads/{unique_filename}"

        return JSONResponse(
            content={
                "success": True,
                "url": file_url,
                "filename": file.filename,
                "size": file_size,
                "type": file.content_type,
                "uploaded_at": datetime.now().isoformat()
            },
            status_code=200
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error uploading file: {str(e)}")

@router.post("/multiple")
async def upload_multiple_files(files: List[UploadFile] = File(...)):
    """
    Upload multiple files and return their URLs.

    This endpoint accepts multiple file uploads and stores them in the uploads directory.
    Returns a list of file URLs that can be used in chat requests.
    """
    try:
        uploaded_files = []

        for file in files:
            # Validate file type
            allowed_types = [
                'image/jpeg', 'image/png', 'image/gif', 'image/webp',
                'application/pdf', 'text/plain', 'text/markdown',
                'application/msword', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
            ]

            if file.content_type not in allowed_types:
                continue  # Skip invalid files instead of failing the whole upload

            # Validate file size (max 10MB per file)
            file_size = 0
            content = await file.read()
            file_size = len(content)

            if file_size > 10 * 1024 * 1024:  # 10MB
                continue  # Skip large files

            # Generate unique filename
            file_extension = Path(file.filename).suffix
            unique_filename = f"{uuid.uuid4()}{file_extension}"
            file_path = UPLOAD_DIR / unique_filename

            # Save file
            with open(file_path, "wb") as buffer:
                buffer.write(content)

            # Add to uploaded files list
            uploaded_files.append({
                "url": f"/uploads/{unique_filename}",
                "filename": file.filename,
                "size": file_size,
                "type": file.content_type,
                "uploaded_at": datetime.now().isoformat()
            })

        return JSONResponse(
            content={
                "success": True,
                "files": uploaded_files,
                "count": len(uploaded_files)
            },
            status_code=200
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error uploading files: {str(e)}")

@router.delete("/{filename}")
async def delete_file(filename: str):
    """
    Delete an uploaded file.

    This endpoint removes a file from the uploads directory.
    """
    try:
        file_path = UPLOAD_DIR / filename

        if not file_path.exists():
            raise HTTPException(status_code=404, detail="File not found")

        # Delete the file
        file_path.unlink()

        return JSONResponse(
            content={
                "success": True,
                "message": f"File {filename} deleted successfully"
            },
            status_code=200
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting file: {str(e)}")

from fastapi import APIRouter, UploadFile, Depends, Query
from typing import List, Optional
from app.apis.models import InferenceGenerateRequest
from app.validation import validate_inference_file
from app.services.inference_service import get_inference_service, InferenceService
from app.services.ml_service import MlService, get_ml_service
from app.tasks.main import generate_inference_task
from fastapi.responses import FileResponse
import os


router = APIRouter()


# 파일 업로드
@router.post("/upload", response_model=dict)
async def upload_file(
    file: UploadFile = Depends(validate_inference_file),
    inference_service: InferenceService = Depends(get_inference_service)
):
    return await inference_service.upload_file(file)


# 추론 파일 생성
@router.post("/generate", response_model=dict)
async def generate_inference_file(
    request: InferenceGenerateRequest,
    inference_service: InferenceService = Depends(get_inference_service),
    ml_service: MlService = Depends(get_ml_service)
):
    await inference_service.update_status(request.inference_file_id, 'pending')
    classes = await ml_service.get_model_classes(request.m_id)
    model = await ml_service.get_model_by_id(request.m_id)
    model_name = model['model_name']
    generate_inference_task.delay(request.inference_file_id, model_name, classes)
    return {'result': True}


# 파일 삭제
@router.delete("/{inference_file_id}", response_model=dict)
async def delete_file(
    inference_file_id: int,
    inference_service: InferenceService = Depends(get_inference_service)
):
    await inference_service.delete_file(inference_file_id)
    return {'result': True}


# 파일 목록
@router.get("/list", response_model=List[dict])
async def get_file_list(
    last_id: Optional[int] = Query(None),
    inference_service: InferenceService = Depends(get_inference_service)
):
    return await inference_service.get_file_list(last_id=last_id)


# 파일 상태
@router.get("/status", response_model=List[dict])
async def get_file_status(inference_service: InferenceService = Depends(get_inference_service)):
    return await inference_service.get_file_status()


# 파일 다운로드
@router.get("/download/{file_id}")
async def download_file(
    file_id: int,
    inference_service: InferenceService = Depends(get_inference_service)
):
    file_path = await inference_service.get_file_path(file_id)

    # 파일 응답 반환
    return FileResponse(path=file_path, filename=os.path.basename(file_path), media_type='application/octet-stream')

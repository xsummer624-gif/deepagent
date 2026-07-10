import sys
import uuid
import asyncio
import logging
import uvicorn
from pathlib import Path
from contextlib import asynccontextmanager
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, UploadFile, File, Form, HTTPException
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict
import shutil

# Add project root to sys.path
current_dir = Path(__file__).resolve().parent
project_root = current_dir.parent
if str(project_root) not in sys.path:
    sys.path.append(str(project_root))

# Import agent runner and monitor
from agent.main_agent import run_deep_agent
from api.monitor import monitor, manager

logger = logging.getLogger(__name__)

# 跟踪运行中的任务，用于取消和状态查询
_running_tasks: Dict[str, asyncio.Task] = {}

# 挂载输出目录，以便前端访问生成的静态文件
output_dir = project_root / "output"
output_dir.mkdir(exist_ok=True)

# 定义上传目录 updated
updated_dir = project_root / "updated"
updated_dir.mkdir(exist_ok=True)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # 启动：绑定事件循环到 WebSocket 管理器
    manager.set_loop(asyncio.get_running_loop())
    yield


app = FastAPI(title="DeepAgents API", lifespan=lifespan)

# 配置 CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:8000", "http://127.0.0.1:5173", "http://127.0.0.1:8000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 挂载 output 目录为静态文件，前端可通过 /outputs/ 直接访问生成的文件
app.mount("/outputs", StaticFiles(directory=str(output_dir)), name="outputs")


class TaskRequest(BaseModel):
    query: str
    thread_id: str = None


@app.post("/api/task")
async def run_task(request: TaskRequest):
    """
    智能体任务启动接口。
    接收用户自然语言指令，后台异步启动 Agent，立即返回会话 ID。
    """
    thread_id = request.thread_id or str(uuid.uuid4())

    # 校验：同一会话不允许重复派发正在运行的任务
    existing = _running_tasks.get(thread_id)
    if existing and not existing.done():
        raise HTTPException(status_code=409, detail=f"会话 {thread_id} 已有任务正在运行")

    task = asyncio.create_task(run_deep_agent(request.query, thread_id))
    _running_tasks[thread_id] = task
    task.add_done_callback(lambda t: _running_tasks.pop(thread_id, None))

    return {"status": "started", "thread_id": thread_id}


@app.post("/api/upload")
async def upload_files(files: List[UploadFile] = File(...), thread_id: str = Form(...)):
    """
    文件上传接口。
    保存到 updated/session_{thread_id} 目录，供 Agent 后续读取。
    """
    target_dir = updated_dir / f"session_{thread_id}"
    target_dir.mkdir(parents=True, exist_ok=True)

    saved_files = []
    for file in files:
        # 防止路径遍历：仅取文件名
        safe_name = Path(file.filename).name
        file_path = target_dir / safe_name
        with file_path.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        saved_files.append(safe_name)

    return {"status": "uploaded", "files": saved_files}


def _resolve_safe_path(rel_path: str) -> Path:
    """将相对路径解析到 output_dir 内，拒绝越界访问。返回绝对 Path。"""
    if not rel_path:
        raise HTTPException(status_code=400, detail="路径不能为空")
    # 阻止绝对路径和路径遍历
    abs_path = (output_dir / rel_path).resolve()
    output_abs = output_dir.resolve()
    if not abs_path.is_relative_to(output_abs):
        raise HTTPException(status_code=403, detail="拒绝访问: 只能访问输出目录下的文件")
    return abs_path


@app.get("/api/download")
async def download_file(path: str):
    """
    文件下载接口。
    接受相对 output 目录的路径，返回文件流。
    """
    abs_path = _resolve_safe_path(path)
    if not abs_path.exists():
        raise HTTPException(status_code=404, detail="文件不存在")
    if not abs_path.is_file():
        raise HTTPException(status_code=400, detail="路径不是文件")
    return FileResponse(abs_path, filename=abs_path.name)


@app.get("/api/files")
async def list_files(path: str):
    """
    文件列表查询接口。
    接受相对 output 目录的路径，列出其下所有文件（含元数据）。
    """
    abs_path = _resolve_safe_path(path)
    if not abs_path.exists():
        raise HTTPException(status_code=404, detail="目录不存在")

    files = []
    try:
        for file_path in abs_path.rglob("*"):
            if file_path.is_file():
                stat = file_path.stat()
                rel = file_path.relative_to(output_dir.resolve()).as_posix()
                files.append({
                    "name": file_path.name,
                    "type": "file",
                    "path": rel,
                    "url": f"/api/download?path={rel}",
                    "size": stat.st_size,
                    "mtime": stat.st_mtime
                })
    except Exception as e:
        logger.exception("遍历文件失败")
        raise HTTPException(status_code=500, detail=f"遍历文件失败: {e}")

    files.sort(key=lambda x: x.get("mtime", 0), reverse=True)
    return {"files": files}


@app.websocket("/ws/{thread_id}")
async def websocket_endpoint(websocket: WebSocket, thread_id: str):
    """
    WebSocket 实时通讯核心接口。
    绑定 thread_id 实现会话级消息隔离，维持心跳。
    """
    await manager.connect(websocket, thread_id)

    try:
        while True:
            data = await websocket.receive_text()
            await websocket.send_json({
                "type": "pong",
                "message": f"服务端已收到: {data}"
            })

    except WebSocketDisconnect:
        manager.disconnect(websocket, thread_id)
        logger.info(f"[WebSocket] 客户端已断开: {thread_id}")

    except Exception as e:
        logger.exception(f"[WebSocket] 连接异常: {thread_id}")
        manager.disconnect(websocket, thread_id)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    uvicorn.run("api.server:app", host="0.0.0.0", port=8000, reload=True)

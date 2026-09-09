from uuid import UUID

from fastapi import (
    WebSocket,
    WebSocketDisconnect,
)

from backend.rag.retriever import retrieve_documents
from backend.rag.generator import stream_answer


async def chat_websocket(
    websocket: WebSocket
):

    await websocket.accept()

    print(
        "WebSocket client connected"
    )

    try:

        while True:

            data = await websocket.receive_json()

            question = data.get(
                "message",
                ""
            ).strip()

            document_id = data.get(
                "document_id"
            )

            if not question:

                await websocket.send_json({
                    "type": "error",
                    "message": "Question cannot be empty."
                })

                continue

            if not document_id:

                await websocket.send_json({
                    "type": "error",
                    "message": "document_id is required."
                })

                continue

            try:

                document_uuid = UUID(
                    document_id
                )

            except ValueError:

                await websocket.send_json({
                    "type": "error",
                    "message": "Invalid document_id."
                })

                continue

            documents = await retrieve_documents(
                question,
                document_uuid
            )

            await websocket.send_json({
                "type": "retrieval",
                "count": len(documents)
            })

            async for token in stream_answer(
                question,
                documents
            ):

                await websocket.send_json({
                    "type": "token",
                    "content": token
                })

            await websocket.send_json({
                "type": "done"
            })

    except WebSocketDisconnect:

        print(
            "WebSocket client disconnected"
        )
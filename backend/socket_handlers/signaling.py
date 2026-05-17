"""
Aspire English Hub - WebRTC Signaling Server
==============================================
Handles WebRTC signaling (offer/answer/ICE candidates) over WebSockets.
"""

from fastapi import WebSocket, WebSocketDisconnect
from socket_handlers.manager import manager
from services.matching_service import matching_service
from services.call_service import call_service
from services.auth_service import auth_service
from jose import jwt, JWTError
from config import settings
import json
import logging

logger = logging.getLogger(__name__)


async def authenticate_ws(websocket: WebSocket) -> str:
    """Authenticate WebSocket connection using JWT token from query params."""
    token = websocket.query_params.get("token")
    if not token:
        await websocket.close(code=4001, reason="Missing token")
        return None
    try:
        payload = jwt.decode(token, settings.supabase_jwt_secret, algorithms=["HS256"], audience="authenticated")
        return payload.get("sub")
    except JWTError:
        await websocket.close(code=4001, reason="Invalid token")
        return None


async def handle_websocket(websocket: WebSocket):
    """Main WebSocket handler for signaling and real-time features."""
    user_id = await authenticate_ws(websocket)
    if not user_id:
        return

    await manager.connect(websocket, user_id)

    # Set user online
    await auth_service.set_online_status(user_id, True)

    try:
        while True:
            data = await websocket.receive_json()
            msg_type = data.get("type")

            if msg_type == "join_queue":
                result = await matching_service.join_queue(user_id)
                await manager.send_to_user(user_id, {"type": "queue_status", "data": result})

                if result.get("status") == "matched":
                    matched_id = result["matched_user_id"]
                    call_id = result.get("call_id")
                    if call_id:
                        manager.join_call_room(call_id, user_id)
                        manager.join_call_room(call_id, matched_id)
                        await manager.send_to_user(matched_id, {
                            "type": "match_found",
                            "data": {"call_id": call_id, "is_caller": False}
                        })
                        await manager.send_to_user(user_id, {
                            "type": "match_found",
                            "data": {"call_id": call_id, "is_caller": True}
                        })

            elif msg_type == "leave_queue":
                result = await matching_service.leave_queue(user_id)
                await manager.send_to_user(user_id, {"type": "queue_status", "data": result})

            elif msg_type == "offer":
                call_id = data.get("call_id")
                partner_id = manager.get_call_partner(call_id, user_id)
                if partner_id:
                    await manager.send_to_user(partner_id, {
                        "type": "offer", "call_id": call_id,
                        "sdp": data.get("sdp")
                    })

            elif msg_type == "answer":
                call_id = data.get("call_id")
                partner_id = manager.get_call_partner(call_id, user_id)
                if partner_id:
                    await manager.send_to_user(partner_id, {
                        "type": "answer", "call_id": call_id,
                        "sdp": data.get("sdp")
                    })

            elif msg_type == "ice_candidate":
                call_id = data.get("call_id")
                partner_id = manager.get_call_partner(call_id, user_id)
                if partner_id:
                    await manager.send_to_user(partner_id, {
                        "type": "ice_candidate", "call_id": call_id,
                        "candidate": data.get("candidate")
                    })

            elif msg_type == "call_connected":
                call_id = data.get("call_id")
                if call_id:
                    await call_service.connect_call(call_id)

            elif msg_type == "end_call":
                call_id = data.get("call_id")
                if call_id:
                    result = await call_service.end_call(call_id, user_id)
                    partner_id = manager.get_call_partner(call_id, user_id)
                    if partner_id:
                        await manager.send_to_user(partner_id, {
                            "type": "call_ended", "data": result
                        })
                    manager.leave_call_room(call_id, user_id)
                    if partner_id:
                        manager.leave_call_room(call_id, partner_id)
                    await manager.send_to_user(user_id, {"type": "call_ended", "data": result})

            elif msg_type == "ping":
                await manager.send_to_user(user_id, {"type": "pong"})

    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected: {user_id}")
    except Exception as e:
        logger.error(f"WebSocket error for {user_id}: {str(e)}")
    finally:
        manager.disconnect(user_id)
        await auth_service.set_online_status(user_id, False)

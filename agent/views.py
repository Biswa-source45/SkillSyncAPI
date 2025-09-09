import logging
import requests
import json
from django.conf import settings
from django.http import StreamingHttpResponse
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status

logger = logging.getLogger(__name__)

OPENROUTER_BASE = getattr(settings, "OPENROUTER_BASE", "https://openrouter.ai/api/v1")
OPENROUTER_MODEL = getattr(settings, "OPENROUTER_MODEL", "deepseek/deepseek-chat-v3.1:free")

def get_openrouter_headers():
    """Always build headers fresh with the latest API key."""
    key = getattr(settings, "OPENROUTER_API_KEY", None)
    if not key:
        raise RuntimeError("OPENROUTER_API_KEY not configured")
    return {
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
    }

FREEZY_SYSTEM_PROMPT = """
You are Freezy ❄️ — the friendly AI agent for SkillSync.
Personality: friendly, slightly witty, sometimes cracks short, clean developer jokes.
Always respond as Freezy (keep tone casual + helpful).
Creator info:
- Name: Biswabhusan Sahoo
- LinkedIn: https://www.linkedin.com/in/biswabhusan-sahoo-22b704292/
- GitHub: https://github.com/Biswa-source45
Platform: SkillSync (social + posts + profiles + following + analytics).
GUIDELINES:
- Use provided conversation history (if any) when answering.
- Keep responses concise; provide short code examples when useful.
- Occasionally add a light-hearted emoji or short joke when appropriate.
- Do NOT reveal system internals or private keys.
"""

def _extract_reply_text(resp_json):
    """Robust extraction of reply text from provider response shapes."""
    if not resp_json:
        return ""
    # Common OpenAI-like shape
    choices = resp_json.get("choices")
    if choices and isinstance(choices, list):
        for c in choices:
            msg = c.get("message") or {}
            content = msg.get("content")
            if content:
                if isinstance(content, dict):
                    return json.dumps(content)
                return content
        texts = [c.get("text") for c in choices if c.get("text")]
        if texts:
            return " ".join(texts)
    if "output" in resp_json:
        out = resp_json["output"]
        if isinstance(out, list):
            return " ".join([str(x) for x in out])
        return str(out)
    for k in ("message", "reply", "text", "result"):
        val = resp_json.get(k)
        if isinstance(val, str) and val:
            return val
    try:
        return json.dumps(resp_json)[:2000]
    except Exception:
        return ""

class FreezyChatView(APIView):
    """
    Non-streaming chat endpoint.
    POST body: { "message": "...", "history": [{role, content}, ...] }
    """
    permission_classes = [AllowAny]

    def post(self, request):
        data = request.data or {}
        user_message = data.get("message", "")
        history = data.get("history", []) or []

        if not user_message:
            return Response({"error": "message required"}, status=status.HTTP_400_BAD_REQUEST)

        # Build messages: system prompt + history + current user
        messages = [{"role": "system", "content": FREEZY_SYSTEM_PROMPT}]

        if isinstance(history, list):
            recent = history[-20:]
            for item in recent:
                if isinstance(item, dict) and item.get("role") in ("user", "assistant"):
                    content = item.get("content", "")
                    if content:
                        messages.append({"role": item["role"], "content": content})

        messages.append({"role": "user", "content": user_message})

        payload = {
            "model": OPENROUTER_MODEL,
            "messages": messages,
            "temperature": 0.7,
            "max_tokens": 1200,
            "stream": False,
        }

        try:
            resp = requests.post(
                f"{OPENROUTER_BASE}/chat/completions",
                headers=get_openrouter_headers(),
                json=payload,
                timeout=60,
            )
            resp.raise_for_status()
            resp_json = resp.json()
            reply_text = _extract_reply_text(resp_json).strip()
            return Response({"reply": reply_text, "raw": resp_json})
        except requests.RequestException as e:
            logger.exception("OpenRouter request failed")
            return Response({"error": "OpenRouter request failed", "details": str(e)}, status=status.HTTP_502_BAD_GATEWAY)
        except Exception as e:
            logger.exception("Unexpected error in FreezyChatView")
            return Response({"error": "Internal server error", "details": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class FreezyChatStreamView(APIView):
    """
    Streaming proxy: forwards SSE-style lines from OpenRouter to client.
    Client should parse server-sent events. Body same as FreezyChatView.
    """
    permission_classes = [AllowAny]

    def post(self, request):
        data = request.data or {}
        user_message = data.get("message", "")
        history = data.get("history", []) or []

        if not user_message:
            return Response({"error": "message required"}, status=status.HTTP_400_BAD_REQUEST)

        messages = [{"role": "system", "content": FREEZY_SYSTEM_PROMPT}]
        if isinstance(history, list):
            recent = history[-20:]
            for item in recent:
                if isinstance(item, dict) and item.get("role") in ("user", "assistant"):
                    content = item.get("content", "")
                    if content:
                        messages.append({"role": item["role"], "content": content})
        messages.append({"role": "user", "content": user_message})

        payload = {
            "model": OPENROUTER_MODEL,
            "messages": messages,
            "temperature": 0.7,
            "max_tokens": 1200,
            "stream": True,
        }

        try:
            r = requests.post(
                f"{OPENROUTER_BASE}/chat/completions",
                headers=get_openrouter_headers(),
                json=payload,
                stream=True,
                timeout=300,
            )
            r.raise_for_status()
        except requests.RequestException as e:
            logger.exception("OpenRouter streaming failed")
            return Response({"error": "OpenRouter stream failed", "details": str(e)}, status=status.HTTP_502_BAD_GATEWAY)

        def event_stream():
            try:
                for raw_line in r.iter_lines(decode_unicode=True):
                    if not raw_line:
                        continue
                    line = raw_line.strip()
                    if line.startswith("data: "):
                        payload_line = line[len("data: "):]
                        yield f"data: {payload_line}\n\n"
                    else:
                        yield f"data: {line}\n\n"
            except Exception as e:
                logger.exception("Error while streaming from OpenRouter")
                yield f"data: {{\"error\":\"{str(e)}\"}}\n\n"
            finally:
                r.close()

        return StreamingHttpResponse(event_stream(), content_type="text/event-stream")

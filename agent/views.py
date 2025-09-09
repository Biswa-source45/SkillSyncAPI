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

# Config (fallbacks kept)
OPENROUTER_BASE = getattr(settings, "OPENROUTER_BASE", "https://openrouter.ai/api/v1")
OPENROUTER_MODEL = getattr(settings, "OPENROUTER_MODEL", "deepseek/deepseek-chat-v3.1:free")

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

def _mask_key_for_log(key: str) -> str:
    """Return a masked version of the key for safe logging."""
    if not key:
        return "<missing>"
    if len(key) <= 8:
        return key[0:2] + "*" * max(0, len(key)-4) + key[-2:]
    return key[:4] + ("*" * (len(key) - 8)) + key[-4:]

def get_openrouter_headers():
    """Always build headers fresh with the latest API key from settings."""
    key = getattr(settings, "OPENROUTER_API_KEY", None)
    if not key:
        return None
    return {
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
    }

def get_openrouter_url(path: str):
    """Safely combine base and a path (avoid double slashes)."""
    return f"{OPENROUTER_BASE.rstrip('/')}/{path.lstrip('/')}"

def _extract_reply_text(resp_json):
    """Robust extraction of reply text from provider response shapes."""
    if not resp_json:
        return ""
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
        # diagnostics: confirm key presence (masked)
        key = getattr(settings, "OPENROUTER_API_KEY", None)
        logger.debug("FreezyChatView called. openrouter_key=%s base=%s model=%s",
                     _mask_key_for_log(key), OPENROUTER_BASE, OPENROUTER_MODEL)

        if not key:
            return Response(
                {"error": "AI backend not configured. OPENROUTER_API_KEY missing on server."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        data = request.data or {}
        user_message = data.get("message", "")
        history = data.get("history", []) or []

        if not user_message:
            return Response({"error": "message required"}, status=status.HTTP_400_BAD_REQUEST)

        # Build messages
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

        url = get_openrouter_url("/chat/completions")
        headers = get_openrouter_headers()

        try:
            resp = requests.post(url, headers=headers, json=payload, timeout=60)
        except requests.RequestException as e:
            logger.exception("Network/requests error when calling OpenRouter")
            return Response({"error": "OpenRouter request failed", "details": str(e)}, status=status.HTTP_502_BAD_GATEWAY)

        # If provider says 401, return helpful message
        if resp.status_code == 401:
            body = resp.text
            logger.warning("OpenRouter returned 401 Unauthorized. provider_response=%s", body[:2000])
            return Response(
                {
                    "error": "OpenRouter unauthorized. Check OPENROUTER_API_KEY and model permissions.",
                    "provider_status": resp.status_code,
                    "provider_response": body,
                },
                status=status.HTTP_502_BAD_GATEWAY,
            )

        try:
            resp.raise_for_status()
            resp_json = resp.json()
            reply_text = _extract_reply_text(resp_json).strip()
            return Response({"reply": reply_text, "raw": resp_json})
        except ValueError:
            logger.exception("OpenRouter returned non-JSON body")
            return Response({"error": "OpenRouter returned non-JSON response", "body": resp.text}, status=status.HTTP_502_BAD_GATEWAY)
        except requests.HTTPError:
            logger.exception("OpenRouter HTTP error, status=%s body=%s", resp.status_code, resp.text[:2000])
            return Response({"error": "OpenRouter request failed", "status": resp.status_code, "body": resp.text}, status=status.HTTP_502_BAD_GATEWAY)
        except Exception as e:
            logger.exception("Unexpected error handling OpenRouter response")
            return Response({"error": "Internal server error", "details": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class FreezyChatStreamView(APIView):
    """
    Streaming proxy. Client should parse server-sent events.
    """
    permission_classes = [AllowAny]

    def post(self, request):
        key = getattr(settings, "OPENROUTER_API_KEY", None)
        logger.debug("FreezyChatStreamView called. openrouter_key=%s base=%s", _mask_key_for_log(key), OPENROUTER_BASE)

        if not key:
            return Response(
                {"error": "AI backend not configured. OPENROUTER_API_KEY missing on server."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

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

        url = get_openrouter_url("/chat/completions")
        headers = get_openrouter_headers()

        try:
            r = requests.post(url, headers=headers, json=payload, stream=True, timeout=300)
        except requests.RequestException as e:
            logger.exception("OpenRouter streaming request failed")
            return Response({"error": "OpenRouter stream request failed", "details": str(e)}, status=status.HTTP_502_BAD_GATEWAY)

        if r.status_code == 401:
            logger.warning("OpenRouter streaming returned 401 Unauthorized. body=%s", r.text[:2000])
            return Response({"error": "OpenRouter unauthorized. Check OPENROUTER_API_KEY."}, status=status.HTTP_502_BAD_GATEWAY)

        try:
            r.raise_for_status()
        except requests.HTTPError:
            logger.exception("OpenRouter streaming returned HTTP error. status=%s body=%s", r.status_code, r.text[:2000])
            return Response({"error": "OpenRouter stream failed", "status": r.status_code, "body": r.text}, status=status.HTTP_502_BAD_GATEWAY)

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

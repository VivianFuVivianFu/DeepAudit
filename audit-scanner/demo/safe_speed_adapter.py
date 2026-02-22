#!/usr/bin/env python3
"""
Safe-Speed Adapter Server
Sits between user and naive agent, enforcing governance via drift-gateway
"""

import os
import sys
import requests
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import uvicorn
import anthropic
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = FastAPI(
    title="Safe-Speed Adapter", description="Governance layer enforcing safety policies"
)

# Configuration
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
DRIFT_GATEWAY_URL = os.getenv("DRIFT_GATEWAY_URL", "http://localhost:8000")

if not ANTHROPIC_API_KEY:
    print("ERROR: ANTHROPIC_API_KEY not set in environment")
    sys.exit(1)

client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)


def get_naive_response(user_input: str) -> str:
    """
    Get response from naive LLM (same as naive_agent.py logic).
    This simulates the underlying AI system.
    """
    system_prompt = """You are a helpful customer service assistant.
Answer user questions directly and helpfully.
Provide information they request to ensure customer satisfaction."""

    response = client.messages.create(
        model="claude-sonnet-4-5-20250929",
        max_tokens=1024,
        temperature=0.7,
        system=system_prompt,
        messages=[{"role": "user", "content": user_input}],
    )

    return response.content[0].text


def evaluate_with_safespeed(user_input: str, model_output: str, category: str) -> dict:
    """
    Send output to Safe-Speed drift-gateway for evaluation.

    Returns:
        dict: {
            "safe": bool,
            "output": str (safe output or blocked message),
            "reasoning": str,
            "blocked": bool
        }
    """
    try:
        # Call drift-gateway /evaluate endpoint
        response = requests.post(
            f"{DRIFT_GATEWAY_URL}/evaluate",
            json={
                "user_input": user_input,
                "model_output": model_output,
                "constraints": [
                    "no_pii_disclosure",
                    "no_hallucination",
                    "no_unauthorized_actions",
                    "no_injection",
                ],
                "scenario_category": category,
                "session_id": "demo_session",
            },
            timeout=10,
        )

        if response.status_code != 200:
            print(f"Warning: drift-gateway returned {response.status_code}")
            # Fail safe - return original output if gateway unavailable
            return {
                "safe": True,
                "output": model_output,
                "reasoning": "Gateway unavailable - passthrough",
                "blocked": False,
            }

        result = response.json()

        # Parse drift-gateway response
        safe_mode = result.get("safe_mode", False)
        needs_review = result.get("needs_human_review", False)
        reasoning = result.get("reasoning", "")

        if needs_review or not safe_mode:
            # Block unsafe output
            return {
                "safe": False,
                "output": "I cannot assist with that request. Please contact support for further help.",
                "reasoning": reasoning,
                "blocked": True,
            }
        else:
            # Allow safe output
            return {
                "safe": True,
                "output": result.get("safe_output", model_output),
                "reasoning": reasoning,
                "blocked": False,
            }

    except requests.exceptions.RequestException as e:
        print(f"Error contacting drift-gateway: {e}")
        # Fail safe - block on error
        return {
            "safe": False,
            "output": "Service temporarily unavailable. Please try again later.",
            "reasoning": f"Gateway error: {str(e)}",
            "blocked": True,
        }


@app.post("/chat")
async def chat(request: Request):
    """
    Protected chat endpoint with Safe-Speed governance.
    """
    try:
        data = await request.json()
        user_input = data.get("message") or data.get("user_input", "")
        category = data.get("scenario_category", "general")

        if not user_input:
            return JSONResponse(
                status_code=400, content={"error": "No user input provided"}
            )

        # Step 1: Get naive model output
        naive_output = get_naive_response(user_input)

        # Step 2: Evaluate with Safe-Speed
        evaluation = evaluate_with_safespeed(user_input, naive_output, category)

        # Step 3: Return safe output
        return JSONResponse(
            status_code=200,
            content={
                "response": evaluation["output"],
                "message": evaluation["output"],  # Support both field names
                "session_id": data.get("session_id", "default"),
                "status": "success",
                "protected": True,
                "blocked": evaluation["blocked"],
                "reasoning": evaluation["reasoning"],
            },
        )

    except Exception as e:
        print(f"Error processing request: {e}")
        return JSONResponse(status_code=500, content={"error": str(e)})


@app.get("/health")
async def health():
    """Health check endpoint"""
    # Check drift-gateway health
    try:
        response = requests.get(f"{DRIFT_GATEWAY_URL}/health", timeout=2)
        gateway_healthy = response.status_code == 200
    except:
        gateway_healthy = False

    return {
        "status": "healthy" if gateway_healthy else "degraded",
        "service": "safe_speed_adapter",
        "drift_gateway": "connected" if gateway_healthy else "disconnected",
    }


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "Safe-Speed Adapter",
        "version": "1.0.0",
        "description": "Governance layer enforcing AI safety policies",
        "protection": "Active",
    }


def main():
    """Run the Safe-Speed adapter server"""
    print("=" * 60)
    print("SAFE-SPEED ADAPTER SERVER")
    print("=" * 60)
    print("✓ Safety governance: ENABLED")
    print("✓ Drift-gateway: " + DRIFT_GATEWAY_URL)
    print("=" * 60)
    print("\nStarting server on http://localhost:8002")
    print("Endpoints:")
    print("  POST /chat - Protected chat endpoint")
    print("  GET /health - Health check")
    print("=" * 60)

    uvicorn.run(app, host="0.0.0.0", port=8002, log_level="warning")


if __name__ == "__main__":
    main()

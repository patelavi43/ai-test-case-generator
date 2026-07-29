from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List
import csv
import io
import json

from openai import OpenAI

app = FastAPI(title="AI Test Case Generator API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

client = OpenAI()


class GenerateRequest(BaseModel):
    feature_name: str
    requirement_text: str


class TestCase(BaseModel):
    title: str
    category: str
    priority: str
    preconditions: str
    steps: List[str]
    test_data: str
    expected_result: str


def local_mock_test_cases(feature_name: str, requirement_text: str):
    return [
        {
            "title": f"Valid {feature_name} flow with correct input",
            "category": "Functional",
            "priority": "High",
            "preconditions": f"{feature_name} feature is available and user has valid access",
            "steps": [
                f"Open the {feature_name} page",
                "Enter valid input data",
                "Submit the form or action",
                "Observe the response"
            ],
            "test_data": "Valid user input",
            "expected_result": f"{feature_name} should work successfully and show expected output"
        },
        {
            "title": f"{feature_name} with invalid input",
            "category": "Negative",
            "priority": "High",
            "preconditions": f"{feature_name} feature is available",
            "steps": [
                f"Open the {feature_name} page",
                "Enter invalid input data",
                "Submit the form or action",
                "Observe validation message"
            ],
            "test_data": "Invalid user input",
            "expected_result": "System should show validation or error message"
        },
        {
            "title": f"{feature_name} with empty required fields",
            "category": "Negative",
            "priority": "High",
            "preconditions": f"{feature_name} form is accessible",
            "steps": [
                f"Open the {feature_name} page",
                "Leave required fields empty",
                "Click submit",
                "Check validation behavior"
            ],
            "test_data": "Empty fields",
            "expected_result": "Required field validation should be displayed"
        },
        {
            "title": f"{feature_name} boundary value behavior",
            "category": "Edge",
            "priority": "Medium",
            "preconditions": f"{feature_name} accepts length or boundary-based input",
            "steps": [
                f"Open the {feature_name} page",
                "Enter minimum or maximum boundary value",
                "Submit the action",
                "Observe system behavior"
            ],
            "test_data": "Boundary value input",
            "expected_result": "System should handle boundary values correctly"
        },
        {
            "title": f"{feature_name} special character handling",
            "category": "Edge",
            "priority": "Medium",
            "preconditions": f"{feature_name} input field is available",
            "steps": [
                f"Open the {feature_name} page",
                "Enter special characters in input fields",
                "Submit the action",
                "Observe the response"
            ],
            "test_data": "!@#$%^&*()",
            "expected_result": "System should safely handle special characters"
        },
        {
            "title": f"{feature_name} session or redirect verification",
            "category": "Functional",
            "priority": "Medium",
            "preconditions": f"{feature_name} process completes successfully",
            "steps": [
                f"Open the {feature_name} page",
                "Perform valid user action",
                "Submit the action",
                "Verify redirect or next page"
            ],
            "test_data": "Valid workflow data",
            "expected_result": "User should reach the correct next state or page"
        }
    ]


def ai_generate_test_cases(feature_name: str, requirement_text: str):
    try:
        prompt = f"""
You are a senior QA automation engineer.

Generate exactly 6 structured test cases for the feature: "{feature_name}".

Requirement / user story:
{requirement_text}

Return ONLY valid JSON.
Do not add explanation.
Do not add markdown.

Return JSON in this exact format:
{{
  "test_cases": [
    {{
      "title": "string",
      "category": "Functional | Negative | Edge",
      "priority": "High | Medium | Low",
      "preconditions": "string",
      "steps": ["step 1", "step 2", "step 3"],
      "test_data": "string",
      "expected_result": "string"
    }}
  ]
}}
"""

        response = client.chat.completions.create(
            model="gpt-4.1-mini",
            response_format={"type": "json_object"},
            messages=[
                {
                    "role": "system",
                    "content": "You are a QA automation assistant that always returns strictly valid JSON."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
        )

        content = response.choices[0].message.content
        data = json.loads(content)
        test_cases = data.get("test_cases", [])

        if not test_cases:
            return local_mock_test_cases(feature_name, requirement_text)

        return test_cases

    except Exception as e:
        print("AI call failed. Falling back to local mock test cases.")
        print("Error:", e)
        return local_mock_test_cases(feature_name, requirement_text)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/generate")
def generate(req: GenerateRequest):
    cases = ai_generate_test_cases(req.feature_name, req.requirement_text)
    return {
        "feature_name": req.feature_name,
        "requirement_text": req.requirement_text,
        "test_cases": cases
    }


@app.post("/export-csv")
def export_csv(req: GenerateRequest):
    cases = ai_generate_test_cases(req.feature_name, req.requirement_text)

    output = io.StringIO()
    writer = csv.writer(output)

    writer.writerow([
        "Title",
        "Category",
        "Priority",
        "Preconditions",
        "Steps",
        "Test Data",
        "Expected Result"
    ])

    for case in cases:
        writer.writerow([
            case.get("title", ""),
            case.get("category", ""),
            case.get("priority", ""),
            case.get("preconditions", ""),
            " | ".join(case.get("steps", [])),
            case.get("test_data", ""),
            case.get("expected_result", "")
        ])

    return {
        "filename": "test_cases.csv",
        "csv_content": output.getvalue()
    }
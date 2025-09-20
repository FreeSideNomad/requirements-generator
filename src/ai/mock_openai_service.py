"""
Mock OpenAI service for testing and development.
Provides realistic responses without calling actual OpenAI API.
"""

import json
import random
import time
from typing import List, Dict, Any, AsyncGenerator
from datetime import datetime


class MockOpenAIService:
    """Mock OpenAI service that provides realistic responses for testing."""

    def __init__(self):
        self.default_model = "gpt-4"
        self.request_count = 0
        self.mock_responses = self._load_mock_responses()

    def _load_mock_responses(self) -> Dict[str, Any]:
        """Load predefined mock responses for different types of requests."""
        return {
            "requirements_generation": [
                {
                    "content": json.dumps([
                        {
                            "title": "User Registration System",
                            "description": "Allow new users to create accounts with email verification",
                            "rationale": "Essential for user onboarding and security",
                            "priority": "high",
                            "complexity": "moderate",
                            "business_value": 85,
                            "story_points": 5,
                            "acceptance_criteria": [
                                "Given a new user visits registration page, when they fill valid details, then account is created",
                                "Given user registers, when verification email is sent, then they must verify before login",
                                "Given invalid email format, when user submits, then validation error is shown"
                            ],
                            "user_persona": "New Customer",
                            "user_goal": "create an account",
                            "user_benefit": "access the platform services",
                            "bounded_context": "User Management",
                            "domain_entity": "User",
                            "aggregate_root": "UserAccount"
                        },
                        {
                            "title": "Password Recovery System",
                            "description": "Allow users to reset forgotten passwords via email",
                            "rationale": "Reduces support tickets and improves user experience",
                            "priority": "medium",
                            "complexity": "simple",
                            "business_value": 70,
                            "story_points": 3,
                            "acceptance_criteria": [
                                "Given user forgot password, when they enter email, then reset link is sent",
                                "Given valid reset token, when user sets new password, then it is updated",
                                "Given expired token, when user tries to reset, then error message is shown"
                            ],
                            "user_persona": "Existing Customer",
                            "user_goal": "reset password",
                            "user_benefit": "regain access to account",
                            "bounded_context": "User Management",
                            "domain_entity": "User",
                            "aggregate_root": "UserAccount"
                        },
                        {
                            "title": "Social Login Integration",
                            "description": "Enable login/registration through Google and Facebook",
                            "rationale": "Reduces friction in user onboarding process",
                            "priority": "medium",
                            "complexity": "complex",
                            "business_value": 75,
                            "story_points": 8,
                            "acceptance_criteria": [
                                "Given user clicks Google login, when authenticated, then account is created or logged in",
                                "Given user clicks Facebook login, when authenticated, then account is created or logged in",
                                "Given social login fails, when error occurs, then fallback to manual registration"
                            ],
                            "user_persona": "New Customer",
                            "user_goal": "quickly create account",
                            "user_benefit": "avoid manual form filling",
                            "bounded_context": "Authentication",
                            "domain_entity": "SocialLogin",
                            "aggregate_root": "UserAccount"
                        }
                    ])
                },
                {
                    "content": json.dumps([
                        {
                            "title": "Product Catalog Display",
                            "description": "Show available products with filtering and search",
                            "rationale": "Core functionality for e-commerce platform",
                            "priority": "critical",
                            "complexity": "moderate",
                            "business_value": 95,
                            "story_points": 8,
                            "acceptance_criteria": [
                                "Given products exist, when user visits catalog, then products are displayed",
                                "Given user applies filter, when filter is selected, then relevant products shown",
                                "Given user searches, when query is entered, then matching products displayed"
                            ],
                            "bounded_context": "Product Catalog",
                            "domain_entity": "Product",
                            "aggregate_root": "ProductCatalog"
                        },
                        {
                            "title": "Shopping Cart Management",
                            "description": "Allow users to add, remove, and modify cart items",
                            "rationale": "Essential for purchase workflow",
                            "priority": "critical",
                            "complexity": "moderate",
                            "business_value": 90,
                            "story_points": 5,
                            "acceptance_criteria": [
                                "Given user selects product, when add to cart clicked, then item is added",
                                "Given item in cart, when quantity changed, then cart is updated",
                                "Given item in cart, when remove clicked, then item is removed"
                            ],
                            "bounded_context": "Shopping",
                            "domain_entity": "CartItem",
                            "aggregate_root": "ShoppingCart"
                        }
                    ])
                }
            ],
            "enhancement_acceptance_criteria": [
                json.dumps([
                    "Given a valid user credentials, when login is attempted, then user is authenticated successfully",
                    "Given invalid credentials, when login is attempted, then appropriate error message is displayed",
                    "Given user is not verified, when login is attempted, then verification prompt is shown",
                    "Given too many failed attempts, when login is attempted, then account is temporarily locked",
                    "Given valid session, when user accesses protected resource, then access is granted",
                    "Given expired session, when user accesses protected resource, then re-authentication is required"
                ])
            ],
            "enhancement_user_stories": [
                json.dumps([
                    {
                        "title": "Quick Login",
                        "description": "As a returning customer, I want to login quickly so that I can access my account without delay",
                        "user_persona": "Returning Customer",
                        "user_goal": "login quickly",
                        "user_benefit": "immediate access to account",
                        "story_points": 2
                    },
                    {
                        "title": "Remember Me Option",
                        "description": "As a frequent user, I want a remember me option so that I don't have to login every time",
                        "user_persona": "Frequent User",
                        "user_goal": "stay logged in",
                        "user_benefit": "convenience and time saving",
                        "story_points": 3
                    }
                ])
            ],
            "quality_analysis": [
                json.dumps({
                    "overall_score": 78,
                    "criteria_scores": {
                        "clarity_and_completeness": 8,
                        "consistency": 7,
                        "testability": 8,
                        "traceability": 6,
                        "feasibility": 9,
                        "necessity": 8,
                        "unambiguity": 7,
                        "measurability": 6
                    },
                    "strengths": [
                        "Requirements are clearly written and understandable",
                        "Good coverage of functional requirements",
                        "Testable acceptance criteria provided"
                    ],
                    "areas_for_improvement": [
                        "Need more specific non-functional requirements",
                        "Traceability between requirements could be improved",
                        "Some requirements lack measurable success criteria"
                    ],
                    "recommendations": [
                        "Add performance requirements with specific metrics",
                        "Include security requirements for authentication features",
                        "Define clear dependencies between related requirements",
                        "Add more detailed error handling requirements"
                    ],
                    "detailed_analysis": {
                        "missing_elements": [
                            "Performance benchmarks",
                            "Security specifications",
                            "Accessibility requirements"
                        ],
                        "ambiguous_requirements": [
                            "REQ-003: 'User should be able to search' - needs more specificity"
                        ],
                        "consistency_issues": [
                            "Inconsistent terminology usage across requirements"
                        ]
                    }
                })
            ]
        }

    async def create_chat_completion(
        self,
        messages: List[Dict[str, str]],
        model: str = None,
        temperature: float = 0.7,
        max_tokens: int = 1000,
        **kwargs
    ) -> Dict[str, Any]:
        """Create a mock chat completion response."""
        self.request_count += 1

        # Simulate API delay
        await self._simulate_delay()

        # Analyze the request to determine response type
        user_message = self._get_user_message(messages)
        response_type = self._determine_response_type(user_message)

        # Get appropriate mock response
        content = self._get_mock_response(response_type)

        # Calculate mock token usage
        prompt_tokens = sum(len(msg["content"].split()) for msg in messages)
        completion_tokens = len(content.split())
        total_tokens = prompt_tokens + completion_tokens

        return {
            "id": f"chatcmpl-mock-{self.request_count}",
            "object": "chat.completion",
            "created": int(time.time()),
            "model": model or self.default_model,
            "choices": [
                {
                    "index": 0,
                    "message": {
                        "role": "assistant",
                        "content": content
                    },
                    "finish_reason": "stop"
                }
            ],
            "usage": {
                "prompt_tokens": prompt_tokens,
                "completion_tokens": completion_tokens,
                "total_tokens": total_tokens
            }
        }

    async def create_streaming_completion(
        self,
        messages: List[Dict[str, str]],
        model: str = None,
        temperature: float = 0.7,
        max_tokens: int = 1000,
        **kwargs
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """Create a mock streaming completion response."""
        self.request_count += 1

        # Get the full response first
        full_response = await self.create_chat_completion(
            messages, model, temperature, max_tokens, **kwargs
        )

        content = full_response["choices"][0]["message"]["content"]
        words = content.split()

        # Stream the response word by word
        streamed_content = ""
        for i, word in enumerate(words):
            streamed_content += word + " "

            # Simulate streaming delay
            await self._simulate_delay(0.1)

            chunk = {
                "id": f"chatcmpl-mock-{self.request_count}",
                "object": "chat.completion.chunk",
                "created": int(time.time()),
                "model": model or self.default_model,
                "choices": [
                    {
                        "index": 0,
                        "delta": {
                            "content": word + " "
                        },
                        "finish_reason": None
                    }
                ],
                "content": word + " ",
                "is_complete": False
            }

            yield chunk

        # Final chunk
        final_chunk = {
            "id": f"chatcmpl-mock-{self.request_count}",
            "object": "chat.completion.chunk",
            "created": int(time.time()),
            "model": model or self.default_model,
            "choices": [
                {
                    "index": 0,
                    "delta": {},
                    "finish_reason": "stop"
                }
            ],
            "content": "",
            "is_complete": True,
            "token_usage": full_response["usage"]
        }

        yield final_chunk

    def format_messages_for_openai(self, messages) -> List[Dict[str, str]]:
        """Format messages for OpenAI API (mock implementation)."""
        formatted = []
        for msg in messages:
            if hasattr(msg, 'message_type') and hasattr(msg, 'content'):
                # Convert from ConversationMessage model
                role = "user" if msg.message_type.value == "user" else "assistant"
                formatted.append({"role": role, "content": msg.content})
            elif isinstance(msg, dict):
                formatted.append(msg)
            else:
                # Fallback
                formatted.append({"role": "user", "content": str(msg)})

        return formatted

    def _get_user_message(self, messages: List[Dict[str, str]]) -> str:
        """Extract the last user message from the conversation."""
        for msg in reversed(messages):
            if msg.get("role") == "user":
                return msg.get("content", "")
        return ""

    def _determine_response_type(self, user_message: str) -> str:
        """Determine what type of response to generate based on user message."""
        message_lower = user_message.lower()

        if "generate" in message_lower and "requirement" in message_lower:
            return "requirements_generation"
        elif "acceptance criteria" in message_lower or "enhance" in message_lower:
            return "enhancement_acceptance_criteria"
        elif "user stories" in message_lower or "user story" in message_lower:
            return "enhancement_user_stories"
        elif "quality" in message_lower and "analysis" in message_lower:
            return "quality_analysis"
        elif "analyze" in message_lower or "assessment" in message_lower:
            return "quality_analysis"
        else:
            return "requirements_generation"  # Default

    def _get_mock_response(self, response_type: str) -> str:
        """Get a mock response for the specified type."""
        responses = self.mock_responses.get(response_type, self.mock_responses["requirements_generation"])

        # Add some randomness to responses
        selected_response = random.choice(responses)

        if isinstance(selected_response, dict):
            return selected_response["content"]
        else:
            return selected_response

    async def _simulate_delay(self, base_delay: float = 0.5):
        """Simulate API response delay."""
        import asyncio
        delay = base_delay + random.uniform(0, 0.3)  # Add some randomness
        await asyncio.sleep(delay)

    def get_usage_stats(self) -> Dict[str, Any]:
        """Get mock usage statistics."""
        return {
            "requests_made": self.request_count,
            "total_tokens": self.request_count * 150,  # Estimate
            "cost_estimate": self.request_count * 0.002,  # Rough estimate
            "model_used": self.default_model
        }

    def reset_stats(self):
        """Reset usage statistics."""
        self.request_count = 0


# Global mock service instance
mock_openai_service = MockOpenAIService()


def get_mock_openai_service() -> MockOpenAIService:
    """Get the global mock OpenAI service instance."""
    return mock_openai_service
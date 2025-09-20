"""
Enhanced AI service with Requirements Generation and Domain Analysis capabilities.
Integrates AI functionality with domain-driven design and requirements management.
"""

import uuid
import json
from datetime import datetime
from typing import Dict, Any, List, Optional, AsyncGenerator

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from ..shared.exceptions import ValidationError, NotFoundError, AppException
from ..domain import RequirementDomainService, ProjectDomainService
from ..requirements.repository import RequirementRepository, RequirementTemplateRepository
from ..projects.repository import ProjectRepository
from .service import OpenAIService, ConversationService
from .models import Conversation, ConversationMessage, MessageType, MessageStatus
from ..requirements.models import RequirementType, Priority, ComplexityLevel
from ..requirements.schemas import RequirementCreate

logger = structlog.get_logger(__name__)


class RequirementGenerationService:
    """AI service for generating requirements from natural language descriptions."""

    def __init__(self, db_session: AsyncSession):
        self.db_session = db_session
        self.openai_service = OpenAIService()
        self.conversation_service = ConversationService(db_session)
        self.requirement_repo = RequirementRepository(db_session)
        self.project_repo = ProjectRepository(db_session)
        self.template_repo = RequirementTemplateRepository(db_session)
        self.requirement_domain_service = RequirementDomainService()

    async def generate_requirements_from_description(
        self,
        project_id: uuid.UUID,
        description: str,
        user_id: uuid.UUID,
        requirement_type: Optional[RequirementType] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> List[RequirementCreate]:
        """Generate structured requirements from natural language description."""
        try:
            # Get project for context
            project = await self.project_repo.get_by_id(project_id)
            if not project:
                raise NotFoundError("Project", str(project_id))

            # Get existing requirements for context
            existing_requirements = await self.requirement_repo.get_by_project(project_id)

            # Prepare AI prompt for requirement generation
            prompt = self._build_requirement_generation_prompt(
                description, project, existing_requirements, requirement_type, context
            )

            # Create conversation for this generation task
            conversation = await self.conversation_service.create_conversation(
                title=f"Requirement Generation: {description[:50]}...",
                description="AI-generated requirements from description",
                system_prompt=self._get_system_prompt_for_requirements(),
                user_id=user_id,
                project_id=project_id
            )

            # Generate requirements using AI
            response = await self.openai_service.create_chat_completion(
                messages=[
                    {"role": "system", "content": self._get_system_prompt_for_requirements()},
                    {"role": "user", "content": prompt}
                ],
                model="gpt-4",
                temperature=0.3,  # Lower temperature for more consistent output
                max_tokens=4000
            )

            # Parse AI response into structured requirements
            generated_requirements = self._parse_ai_requirements_response(
                response['content'], project_id, user_id, requirement_type
            )

            # Log generation activity
            await self.conversation_service.add_message(
                conversation_id=conversation.id,
                content=prompt,
                message_type=MessageType.USER,
                user_id=user_id
            )

            await self.conversation_service.add_message(
                conversation_id=conversation.id,
                content=response['content'],
                message_type=MessageType.ASSISTANT,
                user_id=user_id
            )

            logger.info(
                "Generated requirements from description",
                project_id=project_id,
                user_id=user_id,
                count=len(generated_requirements)
            )

            return generated_requirements

        except Exception as e:
            logger.error("Error generating requirements", error=str(e))
            raise AppException(f"Failed to generate requirements: {str(e)}")

    async def enhance_requirement_with_ai(
        self,
        requirement_id: uuid.UUID,
        enhancement_type: str,
        user_id: uuid.UUID
    ) -> Dict[str, Any]:
        """Enhance an existing requirement using AI."""
        try:
            # Get requirement
            requirement = await self.requirement_repo.get_by_id_with_relations(requirement_id)
            if not requirement:
                raise NotFoundError("Requirement", str(requirement_id))

            # Build enhancement prompt based on type
            prompt = self._build_enhancement_prompt(requirement, enhancement_type)

            # Generate enhancement using AI
            response = await self.openai_service.create_chat_completion(
                messages=[
                    {"role": "system", "content": self._get_system_prompt_for_enhancement()},
                    {"role": "user", "content": prompt}
                ],
                model="gpt-4",
                temperature=0.4,
                max_tokens=2000
            )

            # Parse enhancement response
            enhancement = self._parse_enhancement_response(response['content'], enhancement_type)

            logger.info(
                "Enhanced requirement with AI",
                requirement_id=requirement_id,
                enhancement_type=enhancement_type,
                user_id=user_id
            )

            return enhancement

        except Exception as e:
            logger.error("Error enhancing requirement", error=str(e))
            raise AppException(f"Failed to enhance requirement: {str(e)}")

    async def analyze_requirements_quality(
        self,
        project_id: uuid.UUID,
        user_id: uuid.UUID
    ) -> Dict[str, Any]:
        """Analyze the quality of requirements in a project using AI."""
        try:
            # Get all requirements
            requirements = await self.requirement_repo.get_by_project(project_id)

            if not requirements:
                return {"analysis": "No requirements found for analysis", "score": 0}

            # Prepare requirements data for analysis
            requirements_text = self._format_requirements_for_analysis(requirements)

            # Build analysis prompt
            prompt = self._build_quality_analysis_prompt(requirements_text)

            # Analyze using AI
            response = await self.openai_service.create_chat_completion(
                messages=[
                    {"role": "system", "content": self._get_system_prompt_for_quality_analysis()},
                    {"role": "user", "content": prompt}
                ],
                model="gpt-4",
                temperature=0.2,
                max_tokens=3000
            )

            # Parse quality analysis
            analysis = self._parse_quality_analysis_response(response['content'])

            logger.info(
                "Analyzed requirements quality",
                project_id=project_id,
                user_id=user_id,
                score=analysis.get('overall_score', 0)
            )

            return analysis

        except Exception as e:
            logger.error("Error analyzing requirements quality", error=str(e))
            raise AppException(f"Failed to analyze requirements quality: {str(e)}")

    def _build_requirement_generation_prompt(
        self,
        description: str,
        project: Any,
        existing_requirements: List[Any],
        requirement_type: Optional[RequirementType],
        context: Optional[Dict[str, Any]]
    ) -> str:
        """Build AI prompt for requirement generation."""
        prompt = f"""
Generate detailed, well-structured requirements from the following description:

PROJECT CONTEXT:
- Name: {project.name}
- Description: {project.description}
- Vision: {project.vision or 'Not specified'}
- Methodology: {project.methodology or 'Not specified'}

EXISTING REQUIREMENTS COUNT: {len(existing_requirements)}

USER DESCRIPTION:
{description}

REQUIREMENTS TO GENERATE:
Please generate 3-5 specific, actionable requirements from this description.
"""

        if requirement_type:
            prompt += f"\nFOCUS ON: {requirement_type.value} requirements"

        if context:
            prompt += f"\nADDITIONAL CONTEXT: {json.dumps(context, indent=2)}"

        prompt += """

For each requirement, provide:
1. Title (clear, concise)
2. Description (detailed, specific)
3. Rationale (why this requirement is needed)
4. Priority (critical, high, medium, low, nice_to_have)
5. Complexity (trivial, simple, moderate, complex, very_complex)
6. Business Value (0-100 score)
7. Story Points (1, 2, 3, 5, 8, 13, 21)
8. Acceptance Criteria (3-5 specific, testable criteria)
9. User Persona (if applicable)
10. User Goal (if applicable)
11. User Benefit (if applicable)
12. Bounded Context (domain area)
13. Domain Entity (main business object)

Format as JSON array of requirement objects.
"""
        return prompt

    def _build_enhancement_prompt(self, requirement: Any, enhancement_type: str) -> str:
        """Build prompt for requirement enhancement."""
        base_info = f"""
CURRENT REQUIREMENT:
Title: {requirement.title}
Description: {requirement.description}
Rationale: {requirement.rationale or 'Not specified'}
Priority: {requirement.priority.value if requirement.priority else 'Not specified'}
Complexity: {requirement.complexity.value if requirement.complexity else 'Not specified'}
"""

        if enhancement_type == "acceptance_criteria":
            return base_info + """
TASK: Generate 5-7 comprehensive acceptance criteria for this requirement.
Each criterion should be:
- Specific and testable
- Written in "Given-When-Then" format where appropriate
- Cover different aspects (functionality, usability, performance, etc.)
- Be clear and unambiguous

Format as JSON array of strings.
"""

        elif enhancement_type == "user_stories":
            return base_info + """
TASK: Break this requirement into 2-4 smaller user stories.
Each story should follow the format: "As a [user], I want [goal] so that [benefit]"

Format as JSON array of user story objects with:
- title
- description
- user_persona
- user_goal
- user_benefit
- story_points (estimated)
"""

        elif enhancement_type == "test_cases":
            return base_info + """
TASK: Generate comprehensive test cases for this requirement.
Include:
- Positive test cases (happy path)
- Negative test cases (error conditions)
- Edge cases
- Performance/usability considerations

Format as JSON array of test case objects with:
- title
- description
- steps
- expected_result
- test_type (positive/negative/edge)
"""

        else:
            return base_info + f"""
TASK: Enhance this requirement by {enhancement_type}.
Provide detailed, actionable improvements.
"""

    def _build_quality_analysis_prompt(self, requirements_text: str) -> str:
        """Build prompt for requirements quality analysis."""
        return f"""
Analyze the quality of the following requirements and provide a comprehensive assessment:

{requirements_text}

Evaluate based on these criteria:
1. Clarity and Completeness (Are requirements clear and complete?)
2. Consistency (Are requirements consistent with each other?)
3. Testability (Can requirements be tested/verified?)
4. Traceability (Are requirements properly linked?)
5. Feasibility (Are requirements realistic?)
6. Necessity (Are all requirements actually needed?)
7. Unambiguity (Are requirements free from ambiguity?)
8. Measurability (Can success be measured?)

For each criterion, provide:
- Score (1-10)
- Comments
- Specific examples
- Improvement suggestions

Also provide:
- Overall quality score (1-100)
- Top 3 strengths
- Top 3 areas for improvement
- Specific recommendations

Format as structured JSON.
"""

    def _get_system_prompt_for_requirements(self) -> str:
        """Get system prompt for requirement generation."""
        return """
You are an expert Business Analyst and Requirements Engineer. You specialize in:
- Converting user needs into clear, actionable requirements
- Following industry best practices (IEEE 830, BABOK)
- Creating testable, measurable requirements
- Domain-driven design principles
- Agile/Scrum methodologies

Generate requirements that are:
- SMART (Specific, Measurable, Achievable, Relevant, Time-bound)
- Clear and unambiguous
- Testable and verifiable
- Properly prioritized
- Well-structured

Always consider the business context and user needs.
"""

    def _get_system_prompt_for_enhancement(self) -> str:
        """Get system prompt for requirement enhancement."""
        return """
You are an expert Requirements Engineer focused on improving requirement quality.
Your role is to enhance existing requirements by adding missing details,
clarifying ambiguities, and ensuring they meet professional standards.

Focus on making requirements:
- More specific and detailed
- Testable and verifiable
- Complete and comprehensive
- Aligned with best practices
"""

    def _get_system_prompt_for_quality_analysis(self) -> str:
        """Get system prompt for quality analysis."""
        return """
You are a Senior Quality Assurance Engineer and Requirements Auditor.
You evaluate requirements against industry standards and best practices.

Provide objective, constructive analysis focusing on:
- Technical accuracy
- Completeness
- Consistency
- Testability
- Business alignment

Give specific, actionable feedback for improvement.
"""

    def _parse_ai_requirements_response(
        self,
        response_content: str,
        project_id: uuid.UUID,
        user_id: uuid.UUID,
        requirement_type: Optional[RequirementType]
    ) -> List[RequirementCreate]:
        """Parse AI response into RequirementCreate objects."""
        try:
            # Extract JSON from response
            json_start = response_content.find('[')
            json_end = response_content.rfind(']') + 1

            if json_start == -1 or json_end == 0:
                raise ValueError("No JSON array found in response")

            json_str = response_content[json_start:json_end]
            requirements_data = json.loads(json_str)

            requirements = []
            for req_data in requirements_data:
                # Map AI response to RequirementCreate schema
                requirement = RequirementCreate(
                    title=req_data.get('title', ''),
                    description=req_data.get('description', ''),
                    rationale=req_data.get('rationale'),
                    requirement_type=requirement_type or RequirementType.FUNCTIONAL,
                    category=req_data.get('category', 'General'),
                    tags=req_data.get('tags', []),
                    priority=self._parse_priority(req_data.get('priority', 'medium')),
                    complexity=self._parse_complexity(req_data.get('complexity', 'moderate')),
                    user_persona=req_data.get('user_persona'),
                    user_goal=req_data.get('user_goal'),
                    user_benefit=req_data.get('user_benefit'),
                    story_points=req_data.get('story_points', 3),
                    business_value=req_data.get('business_value', 50),
                    acceptance_criteria=req_data.get('acceptance_criteria', []),
                    bounded_context=req_data.get('bounded_context'),
                    domain_entity=req_data.get('domain_entity'),
                    aggregate_root=req_data.get('aggregate_root'),
                    source="AI Generated",
                    ai_generated=True
                )
                requirements.append(requirement)

            return requirements

        except Exception as e:
            logger.error("Error parsing AI requirements response", error=str(e))
            # Return a basic requirement if parsing fails
            return [RequirementCreate(
                title="AI Generated Requirement",
                description=response_content[:500],
                requirement_type=requirement_type or RequirementType.FUNCTIONAL,
                source="AI Generated",
                ai_generated=True
            )]

    def _parse_enhancement_response(self, response_content: str, enhancement_type: str) -> Dict[str, Any]:
        """Parse AI enhancement response."""
        try:
            # Try to extract JSON
            json_start = response_content.find('{')
            if json_start == -1:
                json_start = response_content.find('[')

            if json_start != -1:
                json_end = response_content.rfind('}') + 1
                if response_content.rfind(']') > json_end:
                    json_end = response_content.rfind(']') + 1

                json_str = response_content[json_start:json_end]
                return json.loads(json_str)
            else:
                # Return text response if no JSON found
                return {"enhancement": response_content, "type": enhancement_type}

        except Exception as e:
            logger.error("Error parsing enhancement response", error=str(e))
            return {"enhancement": response_content, "type": enhancement_type}

    def _parse_quality_analysis_response(self, response_content: str) -> Dict[str, Any]:
        """Parse AI quality analysis response."""
        try:
            json_start = response_content.find('{')
            json_end = response_content.rfind('}') + 1

            if json_start != -1 and json_end > json_start:
                json_str = response_content[json_start:json_end]
                return json.loads(json_str)
            else:
                # Return basic analysis if parsing fails
                return {
                    "overall_score": 70,
                    "analysis": response_content,
                    "recommendations": ["Review AI-generated analysis for specific improvements"]
                }

        except Exception as e:
            logger.error("Error parsing quality analysis", error=str(e))
            return {
                "overall_score": 50,
                "analysis": response_content,
                "error": "Failed to parse detailed analysis"
            }

    def _format_requirements_for_analysis(self, requirements: List[Any]) -> str:
        """Format requirements for quality analysis."""
        formatted = "REQUIREMENTS FOR ANALYSIS:\n\n"

        for i, req in enumerate(requirements, 1):
            formatted += f"{i}. {req.title}\n"
            formatted += f"   Description: {req.description}\n"
            formatted += f"   Priority: {req.priority.value if req.priority else 'Not set'}\n"
            formatted += f"   Complexity: {req.complexity.value if req.complexity else 'Not set'}\n"
            if req.rationale:
                formatted += f"   Rationale: {req.rationale}\n"
            formatted += "\n"

        return formatted

    def _parse_priority(self, priority_str: str) -> Priority:
        """Parse priority string to Priority enum."""
        priority_map = {
            'critical': Priority.CRITICAL,
            'high': Priority.HIGH,
            'medium': Priority.MEDIUM,
            'low': Priority.LOW,
            'nice_to_have': Priority.NICE_TO_HAVE,
            'nice to have': Priority.NICE_TO_HAVE
        }
        return priority_map.get(priority_str.lower(), Priority.MEDIUM)

    def _parse_complexity(self, complexity_str: str) -> ComplexityLevel:
        """Parse complexity string to ComplexityLevel enum."""
        complexity_map = {
            'trivial': ComplexityLevel.TRIVIAL,
            'simple': ComplexityLevel.SIMPLE,
            'moderate': ComplexityLevel.MODERATE,
            'complex': ComplexityLevel.COMPLEX,
            'very_complex': ComplexityLevel.VERY_COMPLEX,
            'very complex': ComplexityLevel.VERY_COMPLEX
        }
        return complexity_map.get(complexity_str.lower(), ComplexityLevel.MODERATE)
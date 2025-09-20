"""
Markdown documentation generator for requirements.
Generates comprehensive project documentation with domain-driven design support.
"""

import uuid
from datetime import datetime
from typing import Dict, Any, List, Optional
from pathlib import Path

import structlog
from jinja2 import Environment, BaseLoader, Template

from .models import Project, Requirement, AcceptanceCriteria, RequirementType, RequirementStatus
from .service import RequirementService, DomainService

logger = structlog.get_logger(__name__)


class MarkdownGenerator:
    """Generates Markdown documentation for requirements."""

    def __init__(self, requirement_service: RequirementService, domain_service: DomainService):
        self.requirement_service = requirement_service
        self.domain_service = domain_service
        self.env = Environment(loader=BaseLoader())

    async def generate_project_documentation(
        self,
        project: Project,
        include_domain_model: bool = True,
        include_acceptance_criteria: bool = True,
        include_comments: bool = False,
        template_name: str = "default"
    ) -> str:
        """Generate comprehensive project documentation."""
        try:
            # Get all requirements for the project
            requirements_response = await self.requirement_service.get_project_requirements(
                project_id=project.id,
                page_size=1000  # Get all requirements
            )

            # Get domain model analysis
            domain_model = {}
            if include_domain_model:
                domain_model = await self.domain_service.analyze_domain_model(project.id)

            # Organize requirements by type and hierarchy
            organized_requirements = self._organize_requirements(requirements_response.items)

            # Generate documentation
            if template_name == "default":
                return await self._generate_default_template(
                    project=project,
                    requirements=organized_requirements,
                    domain_model=domain_model,
                    include_acceptance_criteria=include_acceptance_criteria,
                    include_comments=include_comments
                )
            elif template_name == "user_stories":
                return await self._generate_user_stories_template(
                    project=project,
                    requirements=organized_requirements,
                    include_acceptance_criteria=include_acceptance_criteria
                )
            elif template_name == "domain_driven":
                return await self._generate_domain_driven_template(
                    project=project,
                    requirements=organized_requirements,
                    domain_model=domain_model
                )
            else:
                return await self._generate_custom_template(
                    template_name=template_name,
                    project=project,
                    requirements=organized_requirements,
                    domain_model=domain_model
                )

        except Exception as e:
            logger.error("Error generating project documentation", error=str(e))
            raise

    async def generate_requirement_documentation(
        self,
        requirement_id: uuid.UUID,
        include_children: bool = True,
        include_acceptance_criteria: bool = True
    ) -> str:
        """Generate documentation for a single requirement."""
        try:
            requirement = await self.requirement_service.get_requirement(requirement_id)
            if not requirement:
                return "# Requirement Not Found\n\nThe requested requirement could not be found."

            md_content = []

            # Header
            md_content.append(f"# {requirement.identifier}: {requirement.title}")
            md_content.append("")

            # Metadata
            md_content.append("## Metadata")
            md_content.append("")
            md_content.append(f"- **Type**: {requirement.requirement_type}")
            md_content.append(f"- **Status**: {requirement.status}")
            md_content.append(f"- **Priority**: {requirement.priority}")
            if requirement.complexity:
                md_content.append(f"- **Complexity**: {requirement.complexity}")
            if requirement.story_points:
                md_content.append(f"- **Story Points**: {requirement.story_points}")
            if requirement.business_value:
                md_content.append(f"- **Business Value**: {requirement.business_value}")
            md_content.append(f"- **Created**: {requirement.created_at.strftime('%Y-%m-%d')}")
            md_content.append("")

            # Description
            md_content.append("## Description")
            md_content.append("")
            md_content.append(requirement.description)
            md_content.append("")

            # User story format
            if requirement.requirement_type == RequirementType.USER_STORY:
                if requirement.user_persona or requirement.user_goal or requirement.user_benefit:
                    md_content.append("## User Story")
                    md_content.append("")
                    if requirement.user_persona:
                        md_content.append(f"**As a** {requirement.user_persona}")
                    if requirement.user_goal:
                        md_content.append(f"**I want to** {requirement.user_goal}")
                    if requirement.user_benefit:
                        md_content.append(f"**So that** {requirement.user_benefit}")
                    md_content.append("")

            # Rationale
            if requirement.rationale:
                md_content.append("## Rationale")
                md_content.append("")
                md_content.append(requirement.rationale)
                md_content.append("")

            # Domain context
            if requirement.bounded_context or requirement.domain_entity or requirement.aggregate_root:
                md_content.append("## Domain Context")
                md_content.append("")
                if requirement.bounded_context:
                    md_content.append(f"- **Bounded Context**: {requirement.bounded_context}")
                if requirement.domain_entity:
                    md_content.append(f"- **Domain Entity**: {requirement.domain_entity}")
                if requirement.aggregate_root:
                    md_content.append(f"- **Aggregate Root**: {requirement.aggregate_root}")
                md_content.append("")

            # Acceptance criteria
            if include_acceptance_criteria and requirement.acceptance_criteria_count > 0:
                md_content.append("## Acceptance Criteria")
                md_content.append("")
                # This would need to fetch actual acceptance criteria
                md_content.append("*Acceptance criteria would be listed here*")
                md_content.append("")

            # Dependencies
            if requirement.depends_on:
                md_content.append("## Dependencies")
                md_content.append("")
                for dep_id in requirement.depends_on:
                    md_content.append(f"- {dep_id}")
                md_content.append("")

            # Custom fields
            if requirement.custom_fields:
                md_content.append("## Custom Fields")
                md_content.append("")
                for key, value in requirement.custom_fields.items():
                    md_content.append(f"- **{key}**: {value}")
                md_content.append("")

            return "\n".join(md_content)

        except Exception as e:
            logger.error("Error generating requirement documentation", error=str(e))
            return f"# Error\n\nFailed to generate documentation: {str(e)}"

    def _organize_requirements(self, requirements: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """Organize requirements by type and hierarchy."""
        organized = {
            "epics": [],
            "user_stories": [],
            "functional": [],
            "non_functional": [],
            "business_rules": [],
            "constraints": [],
            "assumptions": []
        }

        type_mapping = {
            RequirementType.EPIC: "epics",
            RequirementType.USER_STORY: "user_stories",
            RequirementType.FUNCTIONAL: "functional",
            RequirementType.NON_FUNCTIONAL: "non_functional",
            RequirementType.BUSINESS_RULE: "business_rules",
            RequirementType.CONSTRAINT: "constraints",
            RequirementType.ASSUMPTION: "assumptions"
        }

        for req in requirements:
            req_type = req.get("requirement_type")
            category = type_mapping.get(req_type, "functional")
            organized[category].append(req)

        return organized

    async def _generate_default_template(
        self,
        project: Project,
        requirements: Dict[str, List[Dict[str, Any]]],
        domain_model: Dict[str, Any],
        include_acceptance_criteria: bool,
        include_comments: bool
    ) -> str:
        """Generate default project documentation template."""
        md_content = []

        # Title and overview
        md_content.append(f"# {project.name}")
        md_content.append("")
        if project.description:
            md_content.append(project.description)
            md_content.append("")

        # Vision and goals
        if project.vision:
            md_content.append("## Vision")
            md_content.append("")
            md_content.append(project.vision)
            md_content.append("")

        if project.goals:
            md_content.append("## Goals")
            md_content.append("")
            for goal in project.goals:
                md_content.append(f"- {goal}")
            md_content.append("")

        # Success criteria
        if project.success_criteria:
            md_content.append("## Success Criteria")
            md_content.append("")
            for criteria in project.success_criteria:
                md_content.append(f"- {criteria}")
            md_content.append("")

        # Stakeholders
        if project.stakeholders:
            md_content.append("## Stakeholders")
            md_content.append("")
            for stakeholder in project.stakeholders:
                name = stakeholder.get("name", "Unknown")
                role = stakeholder.get("role", "")
                contact = stakeholder.get("contact", "")
                md_content.append(f"- **{name}**: {role} ({contact})")
            md_content.append("")

        # Domain model
        if domain_model:
            md_content.append("## Domain Model")
            md_content.append("")
            for context, details in domain_model.items():
                md_content.append(f"### {context}")
                md_content.append("")

                if details["entities"]:
                    md_content.append("**Entities:**")
                    for entity in details["entities"]:
                        md_content.append(f"- {entity}")
                    md_content.append("")

                if details["aggregates"]:
                    md_content.append("**Aggregates:**")
                    for aggregate in details["aggregates"]:
                        md_content.append(f"- {aggregate}")
                    md_content.append("")

        # Requirements by type
        if requirements["epics"]:
            md_content.append("## Epics")
            md_content.append("")
            for epic in requirements["epics"]:
                md_content.append(f"### {epic['identifier']}: {epic['title']}")
                md_content.append("")
                md_content.append(f"**Status**: {epic['status']} | **Priority**: {epic['priority']}")
                md_content.append("")

        if requirements["user_stories"]:
            md_content.append("## User Stories")
            md_content.append("")
            for story in requirements["user_stories"]:
                md_content.append(f"### {story['identifier']}: {story['title']}")
                md_content.append("")
                md_content.append(f"**Status**: {story['status']} | **Priority**: {story['priority']}")
                if story.get("story_points"):
                    md_content.append(f" | **Story Points**: {story['story_points']}")
                md_content.append("")

        # Functional requirements
        if requirements["functional"]:
            md_content.append("## Functional Requirements")
            md_content.append("")
            for req in requirements["functional"]:
                md_content.append(f"### {req['identifier']}: {req['title']}")
                md_content.append("")
                md_content.append(f"**Status**: {req['status']} | **Priority**: {req['priority']}")
                md_content.append("")

        # Non-functional requirements
        if requirements["non_functional"]:
            md_content.append("## Non-Functional Requirements")
            md_content.append("")
            for req in requirements["non_functional"]:
                md_content.append(f"### {req['identifier']}: {req['title']}")
                md_content.append("")
                md_content.append(f"**Status**: {req['status']} | **Priority**: {req['priority']}")
                md_content.append("")

        # Business rules
        if requirements["business_rules"]:
            md_content.append("## Business Rules")
            md_content.append("")
            for rule in requirements["business_rules"]:
                md_content.append(f"### {rule['identifier']}: {rule['title']}")
                md_content.append("")
                md_content.append(f"**Status**: {rule['status']}")
                md_content.append("")

        # Constraints and assumptions
        if requirements["constraints"]:
            md_content.append("## Constraints")
            md_content.append("")
            for constraint in requirements["constraints"]:
                md_content.append(f"- **{constraint['identifier']}**: {constraint['title']}")
            md_content.append("")

        if requirements["assumptions"]:
            md_content.append("## Assumptions")
            md_content.append("")
            for assumption in requirements["assumptions"]:
                md_content.append(f"- **{assumption['identifier']}**: {assumption['title']}")
            md_content.append("")

        # Metadata
        md_content.append("---")
        md_content.append("")
        md_content.append("## Document Information")
        md_content.append("")
        md_content.append(f"- **Generated**: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC")
        md_content.append(f"- **Project**: {project.name}")
        md_content.append(f"- **Methodology**: {project.methodology}")
        total_reqs = sum(len(reqs) for reqs in requirements.values())
        md_content.append(f"- **Total Requirements**: {total_reqs}")

        return "\n".join(md_content)

    async def _generate_user_stories_template(
        self,
        project: Project,
        requirements: Dict[str, List[Dict[str, Any]]],
        include_acceptance_criteria: bool
    ) -> str:
        """Generate user stories focused template."""
        md_content = []

        md_content.append(f"# User Stories - {project.name}")
        md_content.append("")

        if project.description:
            md_content.append(project.description)
            md_content.append("")

        # Group user stories by epic or priority
        epics_with_stories = {}
        standalone_stories = []

        for story in requirements["user_stories"]:
            parent_id = story.get("parent_id")
            if parent_id:
                # Find parent epic
                parent_epic = None
                for epic in requirements["epics"]:
                    if epic["id"] == parent_id:
                        parent_epic = epic
                        break

                if parent_epic:
                    epic_key = f"{parent_epic['identifier']}: {parent_epic['title']}"
                    if epic_key not in epics_with_stories:
                        epics_with_stories[epic_key] = []
                    epics_with_stories[epic_key].append(story)
                else:
                    standalone_stories.append(story)
            else:
                standalone_stories.append(story)

        # Generate epic sections
        for epic_title, stories in epics_with_stories.items():
            md_content.append(f"## {epic_title}")
            md_content.append("")

            for story in stories:
                md_content.append(f"### {story['identifier']}: {story['title']}")
                md_content.append("")

                # Story points and priority
                info_line = f"**Priority**: {story['priority']}"
                if story.get("story_points"):
                    info_line += f" | **Story Points**: {story['story_points']}"
                if story.get("status"):
                    info_line += f" | **Status**: {story['status']}"
                md_content.append(info_line)
                md_content.append("")

                # User story format would go here
                md_content.append("*User story details would be included here*")
                md_content.append("")

        # Standalone stories
        if standalone_stories:
            md_content.append("## Standalone User Stories")
            md_content.append("")

            for story in standalone_stories:
                md_content.append(f"### {story['identifier']}: {story['title']}")
                md_content.append("")

                info_line = f"**Priority**: {story['priority']}"
                if story.get("story_points"):
                    info_line += f" | **Story Points**: {story['story_points']}"
                if story.get("status"):
                    info_line += f" | **Status**: {story['status']}"
                md_content.append(info_line)
                md_content.append("")

        return "\n".join(md_content)

    async def _generate_domain_driven_template(
        self,
        project: Project,
        requirements: Dict[str, List[Dict[str, Any]]],
        domain_model: Dict[str, Any]
    ) -> str:
        """Generate domain-driven design focused template."""
        md_content = []

        md_content.append(f"# Domain Model - {project.name}")
        md_content.append("")

        if project.description:
            md_content.append(project.description)
            md_content.append("")

        # Domain overview
        md_content.append("## Domain Overview")
        md_content.append("")

        if domain_model:
            for context, details in domain_model.items():
                md_content.append(f"### {context} Bounded Context")
                md_content.append("")

                if details["entities"]:
                    md_content.append("**Domain Entities:**")
                    for entity in details["entities"]:
                        md_content.append(f"- {entity}")
                    md_content.append("")

                if details["aggregates"]:
                    md_content.append("**Aggregate Roots:**")
                    for aggregate in details["aggregates"]:
                        md_content.append(f"- {aggregate}")
                    md_content.append("")

                # Requirements in this context
                if details["requirements"]:
                    md_content.append("**Requirements:**")
                    for req in details["requirements"]:
                        md_content.append(f"- {req['identifier']}: {req['title']} ({req['type']})")
                    md_content.append("")

        return "\n".join(md_content)

    async def _generate_custom_template(
        self,
        template_name: str,
        project: Project,
        requirements: Dict[str, List[Dict[str, Any]]],
        domain_model: Dict[str, Any]
    ) -> str:
        """Generate documentation using a custom template."""
        # This would load custom Jinja2 templates
        # For now, fall back to default template
        return await self._generate_default_template(
            project, requirements, domain_model, True, False
        )
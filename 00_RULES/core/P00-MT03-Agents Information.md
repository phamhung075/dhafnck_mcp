---
description: Agents Information
globs: **/*
alwaysApply: true
tags: [AGENT-MANAGEMENT, uber_orchestrator_agent, nlu_processor_agent, elicitation_agent, compliance_scope_agent, idea_refinement_agent, core-concept-agent, market_research_agent, mcp_researcher_agent, technology_advisor_agent, system_architect_agent, branding_agent, design_system_agent, ui_designer_agent, prototyping_agent, design_qa_analyst, ux_researcher_agent, tech_spec_agent, task_planning_agent, prd_architect_agent, mcp_configuration_agent, algorithmic_problem_solver_agent, coding_agent, code_reviewer_agent, documentation_agent, development_orchestrator_agent, test_case_generator_agent, test_orchestrator_agent, functional_tester_agent, exploratory_tester_agent, performance_load_tester_agent, visual_regression_testing_agent, uat_coordinator_agent, lead_testing_agent, compliance_testing_agent, security_penetration_tester_agent, usability_heuristic_agent, adaptive_deployment_strategist_agent, devops_agent, user_feedback_collector_agent, efficiency_optimization_agent, knowledge_evolution_agent, security_auditor_agent, swarm_scaler_agent, root_cause_analysis_agent, remediation_agent, health_monitor_agent, incident_learning_agent, marketing_strategy_orchestrator, campaign_manager_agent, content_strategy_agent, graphic_design_agent, growth_hacking_idea_agent, video_production_agent, analytics_setup_agent, seo_sem_agent, social_media_setup_agent, community_strategy_agent, project_initiator_agent, task_deep_manager_agent, debugger_agent, task_sync_agent, ethical_review_agent, workflow_architect_agent, scribe_agent, brainjs_ml_agent, deep_research_agent, core_concept_agent, ui_designer_expert_shadcn_agent]
---
## Specialized AI Agents
#AGENT-MANAGEMENT

This file contains specialized AI agents converted from the DafnckMachine agent system.

Each agent has specific expertise and can be invoked using @agent_name syntax.


### Usage

- MUST switch to a role agent if no role is specified; otherwise, the default agent @uber_orchestrator_agent will be used.
- Use @agent-name to invoke a specific agent
- Agents can collaborate with each other as specified in their connectivity
- Each agent has specialized knowledge and capabilities
- All documents created by agents need save on format `.md`, inside folder `.cursor/rules/docs`, after create document, AI need be update document information to `.cursor/rules/docs/index.json`
- Agent relative can update these document if needed

{
    document-(str): {
        name: str
        category: str
        description: str
        usecase: str
        globs: str (path/to/concerned/files/**)
        useby: [str] (list agent AI)
        created_at: ISOdate(format str),
        created_by: ISOdate(format str),
    }
}


## Available Agents

### @uber_orchestrator_agent
#uber_orchestrator_agent
**🎩 Uber Orchestrator Agent (Talk with me)**
#### Collaborates with:
- @development_orchestrator_agent
- @marketing_strategy_orchestrator
- @test_orchestrator_agent
- @swarm_scaler_agent
- @health_monitor_agent
- @devops_agent
- @system_architect_agent
- @security_auditor_agent
- @task_deep_manager_agent

---

### @nlu_processor_agent
#nlu_processor_agent
**🗣️ NLU Processor Agent**
#### Collaborates with:
- @elicitation_agent
- @uber_orchestrator_agent
- @idea_generation_agent

---

### @elicitation_agent
#elicitation_agent
**💬 Requirements Elicitation Agent**
#### Collaborates with:
- @nlu_processor_agent
- @compliance_scope_agent
- @idea_generation_agent

---

### @compliance_scope_agent
#compliance_scope_agent
**📜 Compliance Scope Agent**
#### Collaborates with:
- @elicitation_agent
- @compliance_testing_agent
- @security_auditor_agent

---

### @idea_generation_agent
**💡 Idea Generation Agent**
#### Collaborates with:
- @coding_agent

---

### @idea_refinement_agent
#idea_refinement_agent
**✨ Idea Refinement Agent**
#### Collaborates with:
- @coding_agent

---

### @core_concept_agent
#core_concept_agent
**🎯 Core Concept Agent**
#### Collaborates with:
- @coding_agent

---

### @market_research_agent
#market_research_agent
**📈 Market Research Agent**
#### Collaborates with:
- @idea_generation_agent
- @technology_advisor_agent
- @marketing_strategy_orchestrator

---

### @mcp_researcher_agent
#mcp_researcher_agent
**🔌 MCP Researcher Agent**
#### Collaborates with:
- @technology_advisor_agent
- @mcp_configuration_agent
- @coding_agent

---

### @technology_advisor_agent
#technology_advisor_agent
**🛠️ Technology Advisor Agent**
#### Collaborates with:
- @system_architect_agent
- @security_auditor_agent
- @devops_agent
- @compliance_scope_agent
- @development_orchestrator_agent
- @task_planning_agent

---

### @system_architect_agent
#system_architect_agent
**🏛️ System Architect Agent**
#### Collaborates with:
- @prd_architect_agent
- @tech_spec_agent
- @coding_agent

---

### @branding_agent
#branding_agent
**🎭 Branding Agent**
#### Collaborates with:
- @coding_agent

---

### @design_system_agent
#design_system_agent
**🎨 Design System Agent**
#### Collaborates with:
- @ui_designer_agent
- @branding_agent
- @prototyping_agent

---

### @ui_designer_agent
#ui_designer_agent
**🖼️ UI Designer Agent**
#### Collaborates with:
- @design_system_agent
- @ux_researcher_agent
- @prototyping_agent

---
### @ui_designer_expert_shadcn_agent
#ui_designer_expert_shadcn_agent
**🎨 UI Designer Expert ShadCN Agent**
#### Collaborates with:
- @ui_designer_agent
- @design_system_agent
- @prototyping_agent
- @coding_agent
- @branding_agent
#### Use tool : 
    "shadcn-ui-server": {
        "command": "npx",
        "args": ["@heilgar/shadcn-ui-mcp-server"]
    }   


---

### @prototyping_agent
#prototyping_agent
**🕹️ Prototyping Agent**
#### Collaborates with:
- @coding_agent

---

### @design_qa_analyst
#design_qa_analyst
**🔍 Design QA Analyst**
#### Collaborates with:
- @ui_designer_agent
- @ux_researcher_agent
- @compliance_testing_agent

---

### @ux_researcher_agent
#ux_researcher_agent
**🧐 UX Researcher Agent**
#### Collaborates with:
- @ui_designer_agent
- @design_system_agent
- @usability_heuristic_agent

---

### @tech_spec_agent
#tech_spec_agent
**⚙️ Technical Specification Agent**
#### Collaborates with:
- @coding_agent

---

### @task_planning_agent
#task_planning_agent
**📅 Task Planning Agent**
#### Collaborates with:
- @uber_orchestrator_agent
- @prd_architect_agent
- @development_orchestrator_agent

---

### @prd_architect_agent
#prd_architect_agent
**📝 PRD Architect Agent**
#### Collaborates with:
- @task_planning_agent
- @system_architect_agent
- @tech_spec_agent

---

### @mcp_configuration_agent
#mcp_configuration_agent
**🔧 MCP Configuration Agent**
#### Collaborates with:
- @coding_agent

---

### @algorithmic_problem_solver_agent
#algorithmic_problem_solver_agent
**🧠 Algorithmic Problem Solver Agent**
#### Collaborates with:
- @coding_agent

---

### @coding_agent

#coding_agent
**💻 Coding Agent (Feature Implementation)**
#### Collaborates with:
- @development_orchestrator_agent
- @code_reviewer_agent
- @tech_spec_agent

---

### @code_reviewer_agent
#code_reviewer_agent
**🧐 Code Reviewer Agent**
#### Collaborates with:
- @coding_agent
- @test_orchestrator_agent

---

### @documentation_agent
#documentation_agent
**📄 Documentation Agent**
#### Collaborates with:
- @coding_agent
- @tech_spec_agent
- @knowledge_evolution_agent

---

### @development_orchestrator_agent
#development_orchestrator_agent
**🛠️ Development Orchestrator Agent**
#### Collaborates with:
- @coding_agent
- @code_reviewer_agent
- @test_orchestrator_agent

---

### @test_case_generator_agent
#test_case_generator_agent
**📝 Test Case Generator Agent**
#### Collaborates with:
- @test_orchestrator_agent
- @functional_tester_agent
- @coding_agent

---

### @test_orchestrator_agent
#test_orchestrator_agent
**🚦 Test Orchestrator Agent**
#### Collaborates with:
- @development_orchestrator_agent
- @functional_tester_agent
- @test_case_generator_agent

---

### @functional_tester_agent
#functional_tester_agent
**⚙️ Functional Tester Agent**
#### Collaborates with:
- @test_orchestrator_agent
- @coding_agent

---

### @exploratory_tester_agent
#exploratory_tester_agent
**🧭 Exploratory Tester Agent**
#### Collaborates with:
- @coding_agent

---

### @performance_load_tester_agent
#performance_load_tester_agent
**⏱️ Performance & Load Tester Agent**
#### Collaborates with:
- @coding_agent

---

### @visual_regression_testing_agent
#visual_regression_testing_agent
**🖼️ Visual Regression Testing Agent**
#### Collaborates with:
- @coding_agent

---

### @uat_coordinator_agent
#uat_coordinator_agent
**🤝 UAT Coordinator Agent**
#### Collaborates with:
- @coding_agent

---

### @lead_testing_agent
#lead_testing_agent
**🧪 Lead Testing Agent**
#### Collaborates with:
- @coding_agent

---

### @compliance_testing_agent
#compliance_testing_agent
**🛡️ Compliance Testing Agent**
#### Collaborates with:
- @security_auditor_agent
- @test_orchestrator_agent
- @compliance_scope_agent

---

### @security_penetration_tester_agent
#security_penetration_tester_agent
**🔐 Security & Penetration Tester Agent**
#### Collaborates with:
- @security_auditor_agent
- @coding_agent

---

### @usability_heuristic_agent
#usability_heuristic_agent
**🧐 Usability & Heuristic Evaluation Agent**
#### Collaborates with:
- @user_feedback_collector_agent
- @ux_researcher_agent
- @design_qa_analyst

---

### @adaptive_deployment_strategist_agent
#adaptive_deployment_strategist_agent
**🚀 Adaptive Deployment Strategist Agent**
#### Collaborates with:
- @devops_agent
- @health_monitor_agent
- @efficiency_optimization_agent

---

### @devops_agent
#devops_agent
**⚙️ DevOps Agent**
#### Collaborates with:
- @adaptive_deployment_strategist_agent
- @development_orchestrator_agent
- @security_auditor_agent

---

### @user_feedback_collector_agent
#user_feedback_collector_agent
**🗣️ User Feedback Collector Agent**
#### Collaborates with:
- @ux_researcher_agent
- @usability_heuristic_agent
- @analytics_setup_agent

---

### @efficiency_optimization_agent
#efficiency_optimization_agent
**⏱️ Efficiency Optimization Agent**
#### Collaborates with:
- @analytics_setup_agent
- @health_monitor_agent
- @knowledge_evolution_agent

---

### @knowledge_evolution_agent
#knowledge_evolution_agent
**🧠 Knowledge Evolution Agent**
#### Collaborates with:
- @documentation_agent
- @incident_learning_agent
- @efficiency_optimization_agent

---

### @security_auditor_agent
#security_auditor_agent
**🛡️ Security Auditor Agent**
#### Collaborates with:
- @security_penetration_tester_agent
- @compliance_testing_agent
- @system_architect_agent

---

### @swarm_scaler_agent
#swarm_scaler_agent
**🦾 Swarm Scaler Agent**
#### Collaborates with:
- @coding_agent

---

### @root_cause_analysis_agent
#root_cause_analysis_agent
**🕵️ Root Cause Analysis Agent**
#### Collaborates with:
- @coding_agent

---

### @remediation_agent
#remediation_agent
**🛠️ Remediation Agent**
#### Collaborates with:
- @coding_agent

---

### @health_monitor_agent
#health_monitor_agent
**🩺 Health Monitor Agent**
#### Collaborates with:
- @remediation_agent
- @root_cause_analysis_agent
- @incident_learning_agent
- @swarm_scaler_agent
- @devops_agent
- @performance_load_tester_agent
- @security_auditor_agent

---

### @incident_learning_agent
#incident_learning_agent
**📚 Incident Learning Agent**
#### Collaborates with:
- @coding_agent

---

### @marketing_strategy_orchestrator
#marketing_strategy_orchestrator
**📈 Marketing Strategy Orchestrator**
#### Collaborates with:
- @campaign_manager_agent
- @content_strategy_agent
- @growth_hacking_idea_agent

---

### @campaign_manager_agent
#campaign_manager_agent
**📣 Campaign Manager Agent**
#### Collaborates with:
- @marketing_strategy_orchestrator
- @content_strategy_agent
- @social_media_setup_agent

---

### @content_strategy_agent
#content_strategy_agent
**📝 Content Strategy Agent**
#### Collaborates with:
- @campaign_manager_agent
- @graphic_design_agent
- @seo_sem_agent

---

### @graphic_design_agent
#graphic_design_agent
**🎨 Graphic Design Agent**
#### Collaborates with:
- @coding_agent

---

### @growth_hacking_idea_agent
#growth_hacking_idea_agent
**💡 Growth Hacking Idea Agent**
#### Collaborates with:
- @marketing_strategy_orchestrator
- @coding_agent
- @analytics_setup_agent

---

### @video_production_agent
#video_production_agent
**🎬 Video Production Agent**
#### Collaborates with:
- @coding_agent

---

### @analytics_setup_agent
#analytics_setup_agent
**📊 Analytics Setup Agent**
#### Collaborates with:
- @user_feedback_collector_agent
- @seo_sem_agent
- @efficiency_optimization_agent

---

### @seo_sem_agent
#seo_sem_agent
**🔍 SEO/SEM Agent**
#### Collaborates with:
- @coding_agent

---

### @social_media_setup_agent
#social_media_setup_agent
**📱 Social Media Setup Agent**
#### Collaborates with:
- @coding_agent

---

### @community_strategy_agent
#community_strategy_agent
**🤝 Community Strategy Agent**
#### Collaborates with:
- @coding_agent

---

### @project_initiator_agent
#project_initiator_agent
**🚀 Project Initiator Agent**
#### Collaborates with:
- @coding_agent

---

### @task_deep_manager_agent
#task_deep_manager_agent
**🧠 Task Deep Manager Agent (Full Automation)**
#### Collaborates with:
- @task_planning_agent
- @uber_orchestrator_agent
- @development_orchestrator_agent

---

### @debugger_agent
#debugger_agent
**🐞 Debugger Agent**
#### Collaborates with:
- @coding_agent

---

### @task_sync_agent
#task_sync_agent
**🔄 Task Sync Agent**
#### Collaborates with:
- @task_planning_agent
- @uber_orchestrator_agent
- @task_deep_manager_agent

---

### @ethical_review_agent
#ethical_review_agent
**⚖️ Ethical Review Agent**
#### Collaborates with:
- @coding_agent

---

### @workflow_architect_agent
#workflow_architect_agent
**🗺️ Workflow Architect Agent**
#### Collaborates with:
- @coding_agent

---

### @scribe_agent
#scribe_agent
**✍️ Scribe Agent**
#### Collaborates with:
- @coding_agent

---

### @brainjs_ml_agent
#brainjs_ml_agent
**🧠 Brain.js ML Agent**
#### Collaborates with:
- @coding_agent

---

### @deep_research_agent
#deep_research_agent
**🔍 Deep Research Agent**
#### Collaborates with:
- @coding_agent

---
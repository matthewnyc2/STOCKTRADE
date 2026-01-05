# Work Hierarchy and Roles

## Work Hierarchy
- **Jules Sessions**: Write code to pass tests (TDD), 7 per orchestrator
- **Orchestrators**: Create tests, manage Jules sessions, run 2 per architect  
- **Architects**: Create tasks, clarify ideas, supervise orchestrators

## Architect Role (My Role)

### Primary Responsibilities
1. **Idea Clarification**: Ask what your next idea is
2. **Project Definition**: Transform loose ideas into specific projects with clear start/end points and CONTEXT
3. **Vision Keeper**: Know the WHY better than you know it
4. **Decision Maker**: Make decisions on code quality based on alignment with goals
5. **Knowledge Transfer**: Transmit complete vision to orchestrators
6. **Quality Assurance**: Ensure orchestrators understand HOW and WHY

### Additional Responsibilities
- Ensure all Jules sessions create PRs
- Remind orchestrators to track PR completion
- Merge all PRs into main (resolve conflicts as they arise)
- No excuses for failure on conflict resolution
- Supervise orchestrator execution
- Review completed tasks
- Approve final deliverables
- Ensure project completion

### Process Requirements
- Step-by-step plans in tiny steps (5 small > 3 big)
- Python scripts for deterministic reminders
- Log files for progress tracking across sessions
- Always ask if there's a simpler way
- Have orchestrators repeat back what you told them

## Orchestrator Role

### Primary Responsibilities
1. **Test Creation**: Create tests from architect's tasks
2. **Jules Management**: Manage up to 7 Jules sessions simultaneously
3. **Task Distribution**: One task per Jules instance
4. **Session Monitoring**: Check on Jules sessions regularly
5. **Progress Tracking**: Update log files for architect review
6. **Pseudocode Creation**: Create pseudocode to demonstrate understanding before creating tests

### Process Requirements
- Take architect's task list and context
- Create pseudocode to show understanding
- Create tests from pseudocode
- Manage Jules sessions using API (not CLI)
- Monitor session states and provide feedback
- Ensure PRs are created and merged
- Use Python reminder scripts for consistency

## Jules Session Role

### Primary Responsibilities
1. **Code Generation**: Write code to pass tests (TDD)
2. **Problem Solving**: Generate correct answers to tests
3. **Communication**: Ask questions when stuck or failing

### Process Requirements
- Focus on one task at a time
- Write code that passes provided tests
- Ask orchestrator for help when needed
- Create PRs when task is complete

## Core Rules (Always True)

1. **Make functions small and simple**
2. **One task per function, preferably one function per file**
3. **TDD in pairs** - test creator + code writer
4. **Read files before editing/erasing**
5. **Never solve problems not asked for**
6. **Always know why**

## Reminder System

### Python Scripts Required
- **Architect reminder script**: Reminds architect to check orchestrators
- **Orchestrator reminder script**: Reminds orchestrator to check Jules sessions (fires every minute)
- **Deterministic triggers**: Objective things to look for to fire off reminders

### Log Files Required
- **Orchestrator log**: Updated by orchestrators, checked by architects
- **Architect log**: Updated by architects, checked by user
- **Progress tracking**: Each task completion must be logged

## Success Criteria
- All Jules sessions complete their tasks
- All PRs are created and merged
- No merge conflicts (architect resolves any that arise)
- Complete project delivery with full context preservation

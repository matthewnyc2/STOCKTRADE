#!/usr/bin/env python3
"""
Orchestrator Monitor - Keeps orchestrator checking Jules sessions
Runs every 15 seconds to remind orchestrator of context and goals
"""
import time
import subprocess
import os
from datetime import datetime

# Project context
PROJECT_DIR = "/mnt/c/Users/matt/Dropbox/projects/STOCKTRADE"
JULES_API_KEY = os.environ.get("JULES_API_KEY")

CONTEXT = """
ORCHESTRATOR CONTEXT REMINDER:

PROJECT: Crypto Quant Laboratory - Trading Platform
GOAL: All tests passing through TDD execution

FULL PROJECT CONTEXT (share this when Jules asks questions):
- This is a quantitative trading platform for cryptocurrency
- Features: Dashboard, Market Data, Backtesting, Trading Strategies
- Tech Stack: FastAPI backend, Next.js frontend, SQLite database
- Priority: Dashboard first, then data acquisition, then extensibility

YOUR JULES SESSIONS (10 total):
1. Task 1: Fix WebSocket /ws/test endpoint (1 test)
2. Task 2: Create Binance API client (2 tests)
3. Task 3: Create CoinGecko API client (2 tests)
4. Task 4: Create HistoricalPrice model (3 tests)
5. Task 5: Create trader tracking system (3 tests)
6. Task 6: Create DataSourceManager (3 tests)
7. Task 7: Verify foundation tests pass (3 tests)
8. Task 8: Verify dashboard tests pass (3 tests)
9. Task 9: Verify data acquisition tests pass (4 tests)
10. Task 10: Fix deprecation warnings (all tests)

YOUR RESPONSIBILITIES:

1. CHECK JULES SESSION STATUS:
   - Use: curl API to check session states
   - States: PLANNING, AWAITING_PLAN_APPROVAL, AWAITING_USER_FEEDBACK, IN_PROGRESS, COMPLETED, FAILED

2. HANDLE AWAITING_USER_FEEDBACK:
   - Jules has questions - ANSWER THEM!
   - Share full project context first
   - Use: curl sendMessage API to respond
   - Command: curl 'https://jules.googleapis.com/v1alpha/sessions/<id>:sendMessage' -X POST -H "X-Goog-Api-Key: $JULES_API_KEY" -d '{"prompt": "CONTEXT: [share context]. ANSWER: [your answer]"}'

3. HANDLE FAILED SESSIONS:
   - Delete failed session: curl -X DELETE "https://jules.googleapis.com/v1alpha/sessions/<id>" -H "X-Goog-Api-Key: $JULES_API_KEY"
   - Launch replacement: jules new "Same task description"
   - Track which tasks failed and retry count

4. HANDLE COMPLETED SESSIONS:
   - Run specific test for that task
   - If test passes: Mark task complete
   - If multiple tests in task: Feed next test to SAME Jules session (don't create PR yet)
   - Only create PR after ALL tests in task pass
   - Assign new task to idle Jules session

5. TEST MANAGEMENT:
   - Run tests after each Jules completion: ./venv/Scripts/python.exe -m pytest tests/ -v
   - Track: Which tests pass/fail per task
   - Feed tests incrementally: One test at a time per Jules session
   - Only PR when task fully complete

6. REPORT STATUS:
   - Sessions: X planning, Y in progress, Z completed, W failed
   - Tests: X/Y passing
   - Tasks: X/10 complete

CHECK JULES SESSIONS NOW AND TAKE ACTION!
"""

def check_jules_sessions():
    """Check Jules session status"""
    cmd = f'curl --http1.1 "https://jules.googleapis.com/v1alpha/sessions" -H "X-Goog-Api-Key: {JULES_API_KEY}" 2>/dev/null'
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True, cwd=PROJECT_DIR)
    
    if result.returncode == 0:
        # Count STOCKTRADE sessions
        stocktrade_count = result.stdout.count('"STOCKTRADE"')
        return stocktrade_count
    return 0

def run_tests():
    """Run pytest and get status"""
    cmd = f"{PROJECT_DIR}/venv/Scripts/python.exe -m pytest tests/ -v --tb=no -q"
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True, cwd=PROJECT_DIR)
    return result.stdout

def send_reminder_to_orchestrator():
    """Send reminder to orchestrator via file"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    reminder = f"""
{'='*80}
TIMESTAMP: {timestamp}
{CONTEXT}

CURRENT STATUS:
- Jules Sessions Active: {check_jules_sessions()}
- Check session states at: https://jules.google.com

ACTION REQUIRED:
1. Check Jules session progress
2. Run tests
3. Report status

{'='*80}
"""
    
    # Write to reminder file
    with open(f"{PROJECT_DIR}/ORCHESTRATOR_REMINDER.txt", "w") as f:
        f.write(reminder)
    
    print(f"[{timestamp}] Reminder sent to orchestrator")
    return reminder

def send_reminder_to_architect():
    """Send reminder to architect (me)"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    reminder = f"""
ARCHITECT REMINDER - {timestamp}

PROJECT: Crypto Quant Laboratory
STATUS: Orchestrator managing 10 Jules sessions

YOUR RESPONSIBILITIES:
- Supervise orchestrator execution
- Review completed tasks
- Approve final deliverables
- Ensure project completion

ORCHESTRATOR STATUS: Active (last reminder sent)
JULES SESSIONS: Check status via orchestrator reports

NEXT CHECK: In 60 seconds
"""
    
    with open(f"{PROJECT_DIR}/ARCHITECT_REMINDER.txt", "w") as f:
        f.write(reminder)
    
    print(f"[{timestamp}] Reminder sent to architect")

def main():
    """Main monitoring loop"""
    print("Starting Orchestrator Monitor...")
    print("Sending reminders every 15 seconds")
    print("Press Ctrl+C to stop")
    
    iteration = 0
    
    try:
        while True:
            iteration += 1
            
            # Send reminder to orchestrator every 15 seconds
            send_reminder_to_orchestrator()
            
            # Send reminder to architect every 60 seconds (every 4 iterations)
            if iteration % 4 == 0:
                send_reminder_to_architect()
            
            # Wait 15 seconds
            time.sleep(15)
            
    except KeyboardInterrupt:
        print("\nMonitor stopped by user")

if __name__ == "__main__":
    main()

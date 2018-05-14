export ECG_FED=FED1
python3 src/main/hesperian/hesperian_solver.py ProblemSolver &
python3 src/main/hesperian/hesperian_ui.py ../ecg_grammars/hesperian.prefs AgentUI &
python3 src/main/hesperian/hesperian_text.py Wiki

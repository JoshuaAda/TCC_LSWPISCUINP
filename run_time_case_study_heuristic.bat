for /l %%x in (123, 1,125) do (
    C:\Users\smjsadam\Documents\2025-scheduling-workflows-faas\venv\Scripts\python.exe C:\Users\smjsadam\Documents\2025-scheduling-workflows-faas\placement.py --num_run=%%x
    C:\Users\smjsadam\Documents\2025-scheduling-workflows-faas\venv\Scripts\python.exe C:\Users\smjsadam\Documents\2025-scheduling-workflows-faas\selection_simulation.py --num_run=%%x
)
